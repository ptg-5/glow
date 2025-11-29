import gi
import time
import numpy as np
import sys
import json
import random
import gc
import uuid # [NEW] 고유 이름 생성을 위해 추가
from collections import defaultdict
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QImage

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import hailo
from backend.database import DBManager

class HailoWorker(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)

    def __init__(self, hef_path, labels_json):
        super().__init__()
        
        if not Gst.is_initialized():
            Gst.init(None)

        self.hef_path_yolo = "/home/intelai/hailo/best_yolov8_cdh.hef"
        self.json_path_yolo = "/home/intelai/hailo/hailo-apps-infra/resources/json/cdh_labels.json"
        self.hef_path_skin = "/home/intelai/hailo/mobile_net_han_kernel_shape.hef"
        self.so_path_skin = "/home/intelai/hailo/hailo-apps-infra/skin_post/build/libskin_post.so"
        self.so_path_yolo = "/usr/local/hailo/resources/so/libyolo_hailortpp_postprocess.so"

        self.running = True
        self.pipeline = None
        self.appsink = None
        self.db = DBManager()
        self.mutex = QMutex()

        self.active_mode = None       
        self.requested_mode = 'MIRROR'
        self.measure_state = "IDLE"
        self.start_time = 0
        self.collected_data = defaultdict(list)
        self.required_parts = 1 
        
        self.last_frame = None
        self.last_bboxes = {}

    def request_start_session(self):
        if self.requested_mode == 'AI': return
        print(">>> [UI] 측정 요청 -> AI 모드 예약")
        self.status_signal.emit("AI 모델 로딩 중...")
        self.requested_mode = 'AI'
        self.measure_state = "IDLE"
        self.collected_data.clear()
        self.last_bboxes = {}

    def request_mirror_mode(self):
        if self.requested_mode == 'MIRROR': return
        print(">>> [UI] 거울 모드 요청")
        self.requested_mode = 'MIRROR'

    def stop_pipeline(self):
        self.mutex.lock()
        try:
            if self.pipeline:
                print(f"   - [Cleanup] 정지 시작 (Mode: {self.active_mode})")
                
                if self.appsink:
                    try:
                        self.appsink.set_property("emit-signals", False)
                    except: pass
                
                self.pipeline.set_state(Gst.State.NULL)
                # self.pipeline.get_state(2 * Gst.SECOND)
                self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

                del self.appsink
                del self.pipeline

                #self.pipeline.unref()
            
                self.pipeline = None
                self.appsink = None

                # segmentation fault 발생에 기여
                # gc.collect()
                print("   - [Cleanup] 완료")
        except Exception as e:
            print(f"   - [Error] Stop 중 에러: {e}")
        finally:
            self.mutex.unlock()

    def _build_pipeline(self, mode):
        # [핵심] 매번 고유한 이름을 생성 (충돌 방지)
        uid = str(uuid.uuid4().hex)[:8] 
        # uid = 1
        name_agg = f"agg_{uid}"
        name_crop = f"cropper_{uid}"
        name_sink0 = f"sink_0" # 패드 이름은 고정이어야 함
        name_sink1 = f"sink_1"
        
        print(f"🛠️ 파이프라인 빌드 시작: {mode} (ID: {uid})")
        
        source_pipe = (
            "v4l2src device=/dev/video0 name=source ! "
            "videorate ! video/x-raw, framerate=30/1 ! " 
            "videoflip video-direction=horiz ! "
            "videoscale ! video/x-raw, width=640, height=640 ! "
            "videoconvert ! " 
            "queue leaky=downstream max-size-buffers=3 ! " 
        )
        common_appsink = (
            "appsink name=qt_sink "
            "emit-signals=true "
            "sync=false "
            "drop=true "
            "max-buffers=1 "
            "qos=false "           # ← 여기서 미리 설정! (핵심!)
            "wait-on-eos=false"
        )

        if mode == 'AI':
            main_infer = (
                f"hailonet name=inference_hailonet hef-path={self.hef_path_yolo} batch-size=1 vdevice-group-id=1 force-writable=true ! "
                f"hailofilter name=inference_hailofilter so-path={self.so_path_yolo} config-path={self.json_path_yolo} qos=false ! "
                "queue leaky=no max-size-buffers=3 ! "
            )
            
            # [수정] 고유 이름(name_crop, name_agg) 사용
            cropper = (
                f"hailocropper name={name_crop} so-path={self.so_path_skin} function-name=all_detections use-letterbox=true internal-offset=true hailoaggregator name={name_agg} "
                f"{name_crop}. ! queue name=q_bypass_{uid} leaky=no max-size-buffers=30 ! {name_agg}.{name_sink0} "
                f"{name_crop}. ! hailonet hef-path={self.hef_path_skin} batch-size=1 vdevice-group-id=1 ! queue leaky=no ! hailofilter so-path={self.so_path_skin} function-name=skin_regression qos=false ! queue leaky=no ! {name_agg}.{name_sink1} "
                f"{name_agg}. ! "
            )
            
            output = (
                "queue leaky=downstream max-size-buffers=3 ! "
                "identity name=identity_callback ! "
                "hailooverlay name=hailo_display_overlay ! " 
                "videoconvert ! "
                "video/x-raw, format=RGB ! " 
                f"{common_appsink}"
            )
            pipeline_str = source_pipe + main_infer + cropper + output
        else:
            output = (
                "videoconvert ! "
                "video/x-raw, format=RGB ! " 
                f"{common_appsink}"
            )
            pipeline_str = source_pipe + output

        try:
            pipeline = Gst.parse_launch(pipeline_str)
            appsink = pipeline.get_by_name("qt_sink")
            
            if not appsink: 
                print("   - [Error] qt_sink 없음")
                return None, None

            # appsink.set_property("sync", False)
            # appsink.set_property("drop", True)
            # appsink.set_property("max-buffers", 1)
            # appsink.set_property("qos", False)

            return pipeline, appsink

        except Exception as e:
            print(f"❌ [CRITICAL] 파이프라인 생성 실패: {e}")
            return None, None

    def parse_skin_label(self, label_str):
        try:
            if ":" not in label_str: return None, None
            parts = label_str.split(":", 1)
            part_name = parts[0]; data_str = parts[1]; scores = {}
            for item in data_str.split(","):
                if ":" in item:
                    k, v = item.split(":"); scores[k] = int(v.replace("%", ""))
            return part_name, scores
        except: return None, None

    def process_measurement(self, detections):
        if self.measure_state in ["STANDBY", "DONE", "PROCESSING"]: return
        current_frame_data = {}; current_bboxes = {}; valid_parts_count = 0
        target_parts = ["chin", "lips", "right_cheek", "left_cheek", "right_eye", "left_eye", "forehead", "nose", "glabella"]
        for det in detections:
            label = det.get_label(); bbox = det.get_bbox()
            current_bboxes[label] = [bbox.xmin(), bbox.ymin(), bbox.width(), bbox.height()]
            if ":" in label:
                part_name, scores = self.parse_skin_label(label)
                if part_name and scores:
                    current_frame_data[part_name] = scores
                    if label in current_bboxes: current_bboxes[part_name] = current_bboxes.pop(label)
                    valid_parts_count += 1
            elif label in target_parts:
                valid_parts_count += 1
                current_frame_data[label] = {"Dry": random.randint(10,40),"Oil":random.randint(30,70),"Acne":random.randint(0,30),"Wrinkle":random.randint(0,50),"Pigment":random.randint(0,20)}
        if current_bboxes: self.last_bboxes = current_bboxes
        current_time = time.time()
        if self.measure_state == "IDLE":
            if valid_parts_count >= self.required_parts:
                self.measure_state = "READY"; self.start_time = current_time
                self.status_signal.emit("✅ 얼굴 인식됨! 5초간 유지하세요.")
            else: self.status_signal.emit(f"가까이 오세요 ({valid_parts_count}부위)")
        elif self.measure_state == "READY":
            if valid_parts_count < self.required_parts:
                self.measure_state = "IDLE"; self.status_signal.emit("얼굴을 놓쳤습니다.")
            elif current_time - self.start_time > 1.0:
                self.measure_state = "MEASURING"; self.start_time = current_time
                self.collected_data.clear(); self.status_signal.emit("측정 중... 📸 (0%)")
        elif self.measure_state == "MEASURING":
            elapsed = current_time - self.start_time
            progress = min(100, int(elapsed / 5.0 * 100))
            self.status_signal.emit(f"분석 중... {progress}%")
            for part, scores in current_frame_data.items(): self.collected_data[part].append(scores)
            if elapsed >= 5.0: self.finalize_measurement()

    def finalize_measurement(self):
        self.measure_state = "PROCESSING"; print("📊 측정 완료!")
        final_result = {}
        if not self.collected_data:
            self.status_signal.emit("실패"); self.request_mirror_mode(); return
        
        total_severity = 0; total_count = 0
        for part, data_list in self.collected_data.items():
            if not data_list: continue
            avg_scores = {}; keys = data_list[0].keys()
            for k in keys:
                vals = [d.get(k, 0) for d in data_list]
                avg_val = int(sum(vals) / len(vals))
                avg_scores[k] = avg_val
                total_severity += avg_val; total_count += 1
            final_result[part] = avg_scores
        
        avg_sev = int(total_severity / total_count) if total_count > 0 else 0
        summary_score = max(0, 100 - avg_sev)

        self.db.insert_skin_record(summary_score, final_result)
        safe_snapshot = self.last_frame.copy() if self.last_frame else None
        result_pack = {"score":summary_score, "time":time.strftime("%Y-%m-%d %H:%M"), "details":final_result, "snapshot":safe_snapshot, "bboxes":self.last_bboxes}
        self.result_signal.emit(result_pack); self.status_signal.emit("분석 완료!"); self.request_mirror_mode()

    def run(self):
        print("🧠 스레드 루프 시작")
        while self.running:
            if self.requested_mode != self.active_mode:
                print(f"🔄 모드 변경: {self.active_mode} -> {self.requested_mode}")
                self.stop_pipeline()
                time.sleep(1.0)
                self.pipeline, self.appsink = self._build_pipeline(self.requested_mode)
                if self.pipeline:
                    self.pipeline.set_state(Gst.State.PLAYING)
                    self.active_mode = self.requested_mode
                    print("✅ 파이프라인 가동")
                else:
                    time.sleep(1); continue

            if self.pipeline and self.appsink:
                try:
                    sample = self.appsink.emit("pull-sample")
                    if sample:
                        buf = sample.get_buffer()
                        if not buf: continue # 버퍼 없음 체크
                        
                        # 버퍼 크기 체크
                        caps = sample.get_caps()
                        s = caps.get_structure(0)
                        w, h = s.get_value('width'), s.get_value('height')
                        
                        # 메모리 매핑
                        buffer = buf.extract_dup(0, buf.get_size())
                        frame = np.ndarray((h, w, 3), buffer=buffer, dtype=np.uint8)
                        
                        # QImage 복사 (메인스레드 충돌 방지)
                        q_img = QImage(frame.data, w, h, w*3, QImage.Format_RGB888).copy()
                        self.last_frame = q_img.copy()
                        self.change_pixmap_signal.emit(q_img)
                        
                        # AI 모드일 때만 Hailo 추론 결과 파싱
                        if self.active_mode == 'AI':
                            roi = hailo.get_roi_from_buffer(buf)
                            dets = roi.get_objects_typed(hailo.HAILO_DETECTION)
                            self.process_measurement(dets)
                    # if sample:
                    #     buf = sample.get_buffer()
                    #     if buf.get_size() < 640*640*3: continue
                    #     buffer = buf.extract_dup(0, buf.get_size())
                    #     frame = np.ndarray((640, 640, 3), buffer=buffer, dtype=np.uint8)
                    #     frame_copy = frame.copy()
                    #     q_img = QImage(frame_copy.data, 640, 640, 640*3, QImage.Format_RGB888).copy()
                    #     self.last_frame = q_img.copy()
                    #     self.change_pixmap_signal.emit(q_img)
                    #     if self.active_mode == 'AI':
                    #         roi = hailo.get_roi_from_buffer(buf)
                    #         dets = roi.get_objects_typed(hailo.HAILO_DETECTION)
                    #         self.process_measurement(dets)
                    else: time.sleep(0.005)
                except: pass
            else: time.sleep(0.1)
        self.stop_pipeline()

    def stop(self):
        self.running = False
        self.wait()
