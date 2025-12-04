import gi
import time
import numpy as np
import sys
import json
import random
import gc

import uuid 
import os
from collections import defaultdict, Counter
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
    mirror_ready_signal = pyqtSignal()

    def __init__(self, hef_path, labels_json):
        super().__init__()
        if not Gst.is_initialized(): Gst.init(None)

        # === 모델 경로 ===
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
        
        self.skin_type_buffer = []
        self.detected_skin_type = "분석 중..."
        self.skin_analysis_start_time = 0
        self.current_user_id = 0

    def set_current_user(self, user_id):
        print(f"set_current_user:{user_id}**************************")
        self.current_user_id = user_id

    def request_start_session(self):
        if self.requested_mode != 'MIRROR': return
        print(">>> [UI] 측정 요청 -> 1단계: ResNet 분석 시작")
        self.status_signal.emit("피부 타입을 분석 중입니다...")
        
        self.requested_mode = 'SKIN_TYPE'
        self.skin_type_buffer = []
        self.measure_state = "IDLE"
        self.collected_data.clear()
        self.last_bboxes = {}
        self.skin_analysis_start_time = time.time()

    def request_mirror_mode(self):
        if self.requested_mode == 'MIRROR': return
        print(">>> [UI] 거울 모드 요청")
        self.requested_mode = 'MIRROR'

    def stop_pipeline(self):
        self.mutex.lock()
        try:
            if self.pipeline:
                if self.appsink:
                    try: self.appsink.set_property("emit-signals", False)
                    except: pass
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline.get_state(1 * Gst.SECOND)
                self.pipeline = None
                self.appsink = None
                gc.collect()
        finally:
            self.mutex.unlock()

    # === [1단계] ResNet ===
    def process_skin_type_from_tensor(self, roi):
        # 타임아웃 (3초 지나면 강제 통과)
        if time.time() - self.skin_analysis_start_time > 3.0:
            print("⚠️ [Timeout] ResNet 응답 없음 -> 2단계 강제 이동")
            self.detected_skin_type = "복합성 (Combination)"
            self.status_signal.emit("타입 분석 완료 (기본값) -> 정밀 진단")
            self.requested_mode = 'AI'
            self.measure_state = "IDLE" # 상태 초기화
            return

        tensors = roi.get_tensors()
        if not tensors: return 

        tensor = tensors[0]
        data = np.array(tensor.get_data())
        idx = np.argmax(data)
        
        type_map = ["지성 (Oily)", "건성 (Dry)", "중성 (Normal)", "복합성 (Combination)"]
        final_type = type_map[idx % 4]
        
        self.skin_type_buffer.append(final_type)
        
        if len(self.skin_type_buffer) >= 30:
            count = Counter(self.skin_type_buffer)
            top_result = count.most_common(1)[0][0]
            self.detected_skin_type = top_result
            print(f"✅ [1단계 완료] 피부 타입 확정: {top_result}")
            self.status_signal.emit(f"타입: {top_result} -> 정밀 진단 시작")
            
            self.requested_mode = 'AI'
            self.measure_state = "IDLE" # 상태 초기화 (중요)

    # === [2단계] 정밀 진단 ===
    # def parse_skin_label(self, label_str):
    #     try:
    #         if ":" not in label_str: return None, None
    #         parts = label_str.split(":", 1)
    #         part_name = parts[0]; data_str = parts[1]; scores = {}
    #         for item in data_str.split(","):
    #             if ":" in item:
    #                 k, v = item.split(":"); scores[k] = int(v.replace("%", ""))
    #         return part_name, scores
    #     except: return None, None

    # def process_measurement(self, detections):
    #     if self.measure_state in ["STANDBY", "DONE", "PROCESSING"]: return

    #     current_frame_data = {}; current_bboxes = {}; valid_parts_count = 0
    #     target_parts = ["chin", "lips", "right_cheek", "left_cheek", "right_eye", "left_eye", "forehead", "nose", "glabella"]

    #     for det in detections:
    #         label = det.get_label(); bbox = det.get_bbox()
    #         current_bboxes[label] = [bbox.xmin(), bbox.ymin(), bbox.width(), bbox.height()]

    #         # 1. 정상 데이터 (점수 있음)
    #         if ":" in label:
    #             part_name, scores = self.parse_skin_label(label)
    #             if part_name and scores:
    #                 current_frame_data[part_name] = scores
    #                 if label in current_bboxes: current_bboxes[part_name] = current_bboxes.pop(label)
    #                 valid_parts_count += 1
            
    #         # 2. [수정] 안전장치: 점수 없어도 부위 인식되면 데이터 채워넣음
    #         # (이게 없으면 데이터 부족으로 영원히 대기함)
    #         elif label in target_parts:
    #             valid_parts_count += 1
    #             # 멈춤 방지용 기본값 생성
    #             current_frame_data[label] = {
    #                 "Dry": random.randint(10, 40), "Oil": random.randint(30, 70),
    #                 "Acne": random.randint(0, 30), "Wrinkle": random.randint(0, 50),
    #                 "Pigment": random.randint(0, 20)
    #             }

    #     if current_bboxes: self.last_bboxes = current_bboxes
    #     current_time = time.time()

    #     # 상태 머신
    #     if self.measure_state == "IDLE":
    #         if valid_parts_count >= self.required_parts:
    #             self.measure_state = "READY"; self.start_time = current_time
    #             self.status_signal.emit("✅ 얼굴 인식됨! 분석 시작...")
    #             print(">>> [2단계] 측정 시작 (READY)")
    #         else: 
    #             # 인식은 되는데 부위가 모자랄 때
    #             pass

    #     elif self.measure_state == "READY":
    #         if valid_parts_count < self.required_parts:
    #             self.measure_state = "IDLE"; self.status_signal.emit("얼굴을 놓쳤습니다.")
    #         elif current_time - self.start_time > 1.0:
    #             self.measure_state = "MEASURING"; self.start_time = current_time
    #             self.collected_data.clear(); self.status_signal.emit("데이터 수집 중... 📸")
    #             print(">>> [2단계] 데이터 수집 중 (MEASURING)")

    #     elif self.measure_state == "MEASURING":
    #         elapsed = current_time - self.start_time
    #         progress = min(100, int(elapsed / 5.0 * 100))
    #         self.status_signal.emit(f"진단 중... {progress}%")
            
    #         for part, scores in current_frame_data.items(): 
    #             self.collected_data[part].append(scores)
            
    #         if elapsed >= 5.0: 
    #             self.finalize_measurement()

    # def finalize_measurement(self):
    #     self.measure_state = "PROCESSING"; print("📊 측정 완료! 결과 집계 중...")
    #     final_result = {}
        
    #     # 데이터가 비었어도 멈추지 않게 빈 딕셔너리라도 처리
    #     if not self.collected_data:
    #         print("⚠️ [WARNING] 수집된 데이터 없음 (하지만 종료 처리함)")
    #         # 빈 결과라도 보내서 UI가 멈추지 않게 함
        
    #     total_score = 0; cnt = 0
    #     for part, data_list in self.collected_data.items():
    #         if not data_list: continue
    #         avg_scores = {}; keys = data_list[0].keys()
    #         for k in keys:
    #             vals = [d.get(k, 0) for d in data_list]
    #             avg_val = int(sum(vals) / len(vals))
    #             avg_scores[k] = avg_val
    #             total_score += avg_val; cnt += 1
    #         final_result[part] = avg_scores
        
    #     avg_bad = int(total_score / cnt) if cnt > 0 else 50
    #     summary_score = max(0, 100 - int(avg_bad * 0.8))

    #     # DB 저장 (main_window가 담당하므로 주석 처리 가능하지만, 안전을 위해 데이터만 생성)
    #     # self.db.insert_skin_record(...) 

    #     safe_snapshot = self.last_frame.copy() if self.last_frame else None
        
    #     result_pack = {
    #         "score": summary_score,
    #         "time": time.strftime("%Y-%m-%d %H:%M"),
    #         "details": final_result,
    #         "snapshot": safe_snapshot,
    #         "bboxes": self.last_bboxes,
    #         "skin_type": self.detected_skin_type,
    #         "user_id": self.current_user_id
    #     }
        
    #     self.result_signal.emit(result_pack)
    #     self.status_signal.emit("분석 완료!")
        
    #     # 거울 모드 복귀 요청
    #     self.request_mirror_mode()

    # def _build_pipeline(self, mode):
    #     uid = str(uuid.uuid4().hex)[:8]
    #     print(f"🛠️ 파이프라인 빌드: {mode} (ID: {uid})")
        
    #     source_pipe = "v4l2src device=/dev/video0 name=source ! videorate ! video/x-raw, framerate=30/1 ! videoflip video-direction=horiz ! "
        
    #     if mode == 'SKIN_TYPE':
    #         main_infer = (
    #             "videoscale ! video/x-raw, width=224, height=224 ! videoconvert ! "
    #             f"hailonet hef-path={self.hef_path_resnet} batch-size=1 vdevice-group-id=1 ! "
    #             "videoscale ! video/x-raw, width=640, height=640 ! videoconvert ! "
    #             "queue leaky=downstream max-size-buffers=3 ! "
    #         )
    #         output = "video/x-raw, format=RGB ! appsink name=qt_sink emit-signals=true sync=false drop=true max-buffers=1 wait-on-eos=false"
    #         pipeline_str = source_pipe + main_infer + output

    #     elif mode == 'AI':
    #         source_pipe += "videoscale ! video/x-raw, width=640, height=640 ! videoconvert ! queue leaky=downstream max-size-buffers=3 ! "
    #         main_infer = f"hailonet name=inference_hailonet hef-path={self.hef_path_yolo} batch-size=1 vdevice-group-id=1 force-writable=true ! hailofilter name=inference_hailofilter so-path={self.so_path_yolo} config-path={self.json_path_yolo} qos=false ! queue leaky=no max-size-buffers=3 ! "
    #         cropper = f"hailocropper name=crop_{uid} so-path={self.so_path_skin} function-name=all_detections use-letterbox=true internal-offset=true hailoaggregator name=agg_{uid} crop_{uid}. ! queue name=q_bypass_{uid} leaky=no max-size-buffers=30 ! agg_{uid}.sink_0 crop_{uid}. ! hailonet hef-path={self.hef_path_skin} batch-size=1 vdevice-group-id=1 ! queue leaky=no ! hailofilter so-path={self.so_path_skin} function-name=skin_regression qos=false ! queue leaky=no ! agg_{uid}.sink_1 agg_{uid}. ! "
    #         output = "queue leaky=downstream max-size-buffers=3 ! identity name=identity_callback ! hailooverlay name=hailo_display_overlay ! videoconvert ! video/x-raw, format=RGB ! appsink name=qt_sink emit-signals=true sync=false drop=true max-buffers=1 wait-on-eos=false"
    #         pipeline_str = source_pipe + main_infer + cropper + output
        
    #     else: # MIRROR
    #         source_pipe += "videoscale ! video/x-raw, width=640, height=640 ! videoconvert ! "
    #         output = "video/x-raw, format=RGB ! appsink name=qt_sink emit-signals=true sync=false drop=true max-buffers=1 wait-on-eos=false"
    #         print(f"   - [Cleanup] 정지 시작 (Mode: {self.active_mode})")
                
    #         if self.appsink:
    #             try:
    #                 self.appsink.set_property("emit-signals", False)
    #             except: pass
            
    #             self.pipeline.set_state(Gst.State.NULL)
    #             # self.pipeline.get_state(2 * Gst.SECOND)
    #             self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

    #             del self.appsink
    #             del self.pipeline

    #             #self.pipeline.unref()
            
    #             self.pipeline = None
    #             self.appsink = None

    #             # segmentation fault 발생에 4기여
    #             # gc.collect()
    #             print("   - [Cleanup] 완료")
    #             except Exception as e:
    #                 print(f"   - [Error] Stop 중 에러: {e}")
    #             finally:
    #                 self.mutex.unlock()

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
            if not appsink: return None, None
            appsink.set_property("sync", False); appsink.set_property("drop", True); appsink.set_property("max-buffers", 1); appsink.set_property("qos", False)
            return pipeline, appsink
        # except: return None, None

            # appsink.set_property("sync", False)
            # appsink.set_property("drop", True)
            # appsink.set_property("max-buffers", 1)
            # appsink.set_property("qos", False)

        except Exception as e:
            print(f"❌ [CRITICAL] 파이프라인 생성 실패: {e}")
            return None, None

    # def parse_skin_label(self, label_str):
    #     try:
    #         if ":" not in label_str: return None, None
    #         parts = label_str.split(":", 1)
    #         part_name = parts[0]; data_str = parts[1]; scores = {}
    #         for item in data_str.split(","):
    #             if ":" in item:
    #                 k, v = item.split(":"); scores[k] = int(v.replace("%", ""))
    #         return part_name, scores
    #     except: return None, None
    def parse_skin_label(self, label_str):
        try:
            if ":" not in label_str:
                return None, None

            # part_name 분리
            part_name, rest = label_str.split(":", 1)

            scores = {}
            for item in rest.split(","):
                if ":" in item:
                    k, v = item.split(":")

                    # %가 붙은 경우 제거
                    v = v.replace("%", "")

                    # float 변환 (여기가 핵심!)
                    try:
                        scores[k] = float(v)
                    except:
                        scores[k] = 0.0

            return part_name, scores
        except:
            return None, None

    # def process_measurement(self, detections):
    #     if self.measure_state in ["STANDBY", "DONE", "PROCESSING"]: return
    #     current_frame_data = {}; current_bboxes = {}; valid_parts_count = 0
    #     target_parts = ["chin", "lips", "right_cheek", "left_cheek", "right_eye", "left_eye", "forehead", "nose", "glabella"]
    #     for det in detections:
    #         label = det.get_label(); bbox = det.get_bbox()
    #         current_bboxes[label] = [bbox.xmin(), bbox.ymin(), bbox.width(), bbox.height()]
    #         if ":" in label:
    #             part_name, scores = self.parse_skin_label(label)
    #             if part_name and scores:
    #                 current_frame_data[part_name] = scores
    #                 if label in current_bboxes: current_bboxes[part_name] = current_bboxes.pop(label)
    #                 valid_parts_count += 1
    #         elif label in target_parts:
    #             valid_parts_count += 1
    #             current_frame_data[label] = {"Dry": random.randint(10,40),"Oil":random.randint(30,70),"Acne":random.randint(0,30),"Wrinkle":random.randint(0,50),"Pigment":random.randint(0,20)}
    #     if current_bboxes: self.last_bboxes = current_bboxes
    #     current_time = time.time()
    #     if self.measure_state == "IDLE":
    #         if valid_parts_count >= self.required_parts:
    #             self.measure_state = "READY"; self.start_time = current_time
    #             self.status_signal.emit("✅ 얼굴 인식됨! 5초간 유지하세요.")
    #         else: self.status_signal.emit(f"가까이 오세요 ({valid_parts_count}부위)")
    #     elif self.measure_state == "READY":
    #         if valid_parts_count < self.required_parts:
    #             print("self.measure_state = IDLE")
    #             self.measure_state = "IDLE"; self.status_signal.emit("얼굴을 놓쳤습니다.")
    #         elif current_time - self.start_time > 1.0:
    #             print("self.measure_state = MEASURING")
    #             self.measure_state = "MEASURING"; self.start_time = current_time
    #             self.collected_data.clear(); self.status_signal.emit("측정 중... 📸 (0%)")
    #     elif self.measure_state == "MEASURING":
    #         elapsed = current_time - self.start_time
    #         progress = min(100, int(elapsed / 5.0 * 100))
    #         self.status_signal.emit(f"분석 중... {progress}%")
    #         print(f"current_frame_data",current_frame_data)
    #         for part, scores in current_frame_data.items(): self.collected_data[part].append(scores)
    #         if elapsed >= 5.0: self.finalize_measurement()

    def process_measurement(self, detections):
        if self.measure_state in ["STANDBY", "DONE", "PROCESSING"]:
            return

        current_frame_data = {}
        current_bboxes = {}
        valid_parts_count = 0

        TARGET_PARTS = [
            "chin", "lips", "right_cheek", "left_cheek",
            "right_eye", "left_eye", "forehead", "nose", "glabella"
        ]

        # C++ → UI key 변환
        KEY_MAP = {
            "wrinkle": "Wrinkle",
            "pigmentation": "Pigment",
            "pore": "Pore",
            "dryness": "Dry",
            "sagging": "Sagging"
        }

        # 각 부위가 필요한 지표
        REGION_METRICS = {
            "forehead":     ["Wrinkle", "Pigment"],
            "glabella":     ["Wrinkle"],
            "left_eye":     ["Wrinkle"],
            "right_eye":    ["Wrinkle"],
            "left_cheek":   ["Pigment", "Pore"],
            "right_cheek":  ["Pigment", "Pore"],
            "lips":         ["Dry"],
            "chin":         ["Sagging"]
        }

        # -------------------------------
        # 🔥 1) Detection & Regression 파싱
        # -------------------------------
        for det in detections:

            label = det.get_label()           # 예: "right_cheek:3"
            base_label = label.split(":")[0]  # right_cheek

            bbox = det.get_bbox()

            cls = det.get_objects_typed(hailo.HAILO_CLASSIFICATION)

            # ===============================================
            # 🔥 회귀(Classification) 있는 경우 (핵심)
            # ===============================================
            if len(cls) > 0:
                raw = cls[0].get_label()   # 예: right_cheek:pigmentation:1.53,pore:2.14
                print("상태별 등급", raw)

                part_name, raw_scores = self.parse_skin_label(raw)

                if part_name and raw_scores:

                    # UI key로 변경 (wrinkle → Wrinkle)
                    fixed_scores = {}
                    for k, v in raw_scores.items():
                        ui_key = KEY_MAP.get(k)
                        if ui_key:
                            fixed_scores[ui_key] = float(v)

                    # 부위별 필요한 값만 저장
                    need = REGION_METRICS.get(part_name, [])
                    filtered = {k: fixed_scores[k] for k in need if k in fixed_scores}

                    current_frame_data[part_name] = filtered

                    # 🔥 bbox는 YOLO 라벨이 아니라 part_name으로 저장해야 함
                    current_bboxes[part_name] = [
                        bbox.xmin(), bbox.ymin(), bbox.width(), bbox.height()
                    ]

                    valid_parts_count += 1
                    continue

            # ===============================================
            # 🔹 회귀 없는 YOLO detection
            # ===============================================
            if base_label in TARGET_PARTS:
                current_frame_data[base_label] = {}
                current_bboxes[base_label] = [
                    bbox.xmin(), bbox.ymin(), bbox.width(), bbox.height()
                ]
                valid_parts_count += 1

        # -------------------------------
        # bbox 전역 저장
        # -------------------------------
        if current_bboxes:
            self.last_bboxes = current_bboxes

        # -------------------------------
        # 🔥 2) 상태 머신
        # -------------------------------
        now = time.time()

        if self.measure_state == "IDLE":
            if valid_parts_count >= self.required_parts:
                self.measure_state = "READY"
                self.start_time = now
                self.status_signal.emit("✅ 얼굴 인식됨! 5초간 유지하세요.")
            else:
                self.status_signal.emit(f"가까이 오세요 ({valid_parts_count}부위)")

        elif self.measure_state == "READY":
            if valid_parts_count < self.required_parts:
                self.measure_state = "IDLE"
                self.status_signal.emit("얼굴을 놓쳤습니다.")
            elif now - self.start_time > 1.0:
                self.measure_state = "MEASURING"
                self.collected_data.clear()
                self.start_time = now
                self.status_signal.emit("측정 중... 📸 (0%)")

        elif self.measure_state == "MEASURING":
            elapsed = now - self.start_time
            progress = min(100, int(elapsed / 5.0 * 100))
            self.status_signal.emit(f"분석 중... {progress}%")

            print("current_frame_data =", current_frame_data)

            # 🔥 빈 dict도 저장 (부위 존재 판정 위해)
            for part, scores in current_frame_data.items():
                rounded_scores = {k: round(v, 1) for k, v in scores.items()}
                self.collected_data[part].append(rounded_scores)

            if elapsed >= 5.0:
                self.finalize_measurement()


    # def finalize_measurement(self):
    #     self.measure_state = "PROCESSING"; print("📊 측정 완료!")
    #     final_result = {}
    #     if not self.collected_data:
    #         print("측정 실패",self.collected_data)
    #         self.status_signal.emit("실패"); self.request_mirror_mode(); return
        
    #     total_severity = 0; total_count = 0
    #     for part, data_list in self.collected_data.items():
    #         if not data_list: continue
    #         avg_scores = {}; keys = data_list[0].keys()
    #         for k in keys:
    #             vals = [d.get(k, 0) for d in data_list]
    #             avg_val = int(sum(vals) / len(vals))
    #             avg_scores[k] = avg_val
    #             total_severity += avg_val; total_count += 1
    #         final_result[part] = avg_scores
        
    #     avg_sev = int(total_severity / total_count) if total_count > 0 else 0
    #     summary_score = max(0, 100 - avg_sev)

        
    #     safe_snapshot = self.last_frame.copy() if self.last_frame else None
    #     result_pack = {"score":summary_score, "time":time.strftime("%Y-%m-%d %H:%M"), "details":final_result, "snapshot":safe_snapshot, "bboxes":self.last_bboxes}
    #     self.result_signal.emit(result_pack); self.status_signal.emit("분석 완료!"); self.request_mirror_mode()
    def finalize_measurement(self):
        self.measure_state = "PROCESSING"
        print("📊 측정 완료!")

        final_result = {}
        if not self.collected_data:
            print("측정 실패", self.collected_data)
            self.status_signal.emit("실패")
            self.request_mirror_mode()
            return

        MODEL_MAX = 3.0
        REAL_MAX = 5.0

        total_severity = 0.0
        total_count = 0

        for part, data_list in self.collected_data.items():
            if not data_list:
                continue

            avg_scores = {}
            keys = data_list[0].keys()

            for k in keys:
                raw_vals = [float(d.get(k, 0.0)) for d in data_list]
                raw_avg = sum(raw_vals) / len(raw_vals)

                # UI 표시는 원본 등급 그대로
                avg_scores[k] = round(raw_avg, 2)

                # 🔥 점수 계산 시에만 완화된 severity 사용
                # 기존 raw/3 → 이제 raw/5 로 완화 (점수 상승함)
                severity_for_score = raw_avg / REAL_MAX

                total_severity += severity_for_score
                total_count += 1

            final_result[part] = avg_scores

        # ------------------------------
        # 점수 계산
        # ------------------------------
        avg_sev = (total_severity / total_count) if total_count > 0 else 0
        summary_score = max(0, int(100 - avg_sev * 100))

        # ------------------------------
        # 결과 전달
        # ------------------------------
        safe_snapshot = self.last_frame.copy() if self.last_frame else None

        result_pack = {
            "score": summary_score,
            "time": time.strftime("%Y-%m-%d %H:%M"),
            "details": final_result,
            "snapshot": safe_snapshot,
            "bboxes": self.last_bboxes
        }

        self.result_signal.emit(result_pack)
        self.status_signal.emit("분석 완료!")
        self.request_mirror_mode()


    def run(self):
        print("🧠 스레드 루프 시작")
        while self.running:
            if self.requested_mode != self.active_mode:
                print(f"🔄 모드 변경: {self.active_mode} -> {self.requested_mode}")
                self.stop_pipeline()
                time.sleep(1.5)
                self.pipeline, self.appsink = self._build_pipeline(self.requested_mode)
                if self.pipeline:
                    self.pipeline.set_state(Gst.State.PLAYING)
                    self.active_mode = self.requested_mode
                    if self.active_mode == 'MIRROR': self.mirror_ready_signal.emit()
                else:
                    time.sleep(1); continue

            if self.pipeline and self.appsink:
                try:
                    sample = self.appsink.emit("pull-sample")
                    if sample:
                        buf = sample.get_buffer()
                        if buf.get_size() < 200000: continue
                        
                        caps = sample.get_caps()
                        h = caps.get_structure(0).get_value("height")
                        w = caps.get_structure(0).get_value("width")
                        buffer = buf.extract_dup(0, buf.get_size())
                        frame = np.ndarray((h, w, 3), buffer=buffer, dtype=np.uint8)
                        
                        if w != 640:
                            import cv2
                            frame = cv2.resize(frame, (640, 640))
                        
                        q_img = QImage(frame.data, 640, 640, 640*3, QImage.Format_RGB888).copy()
                        if self.active_mode != 'SKIN_TYPE': self.last_frame = q_img.copy()
                        self.change_pixmap_signal.emit(q_img)

                        roi = hailo.get_roi_from_buffer(buf)
                        if self.active_mode == 'SKIN_TYPE':
                            self.process_skin_type_from_tensor(roi)
                        elif self.active_mode == 'AI':
                            dets = roi.get_objects_typed(hailo.HAILO_DETECTION)
                            self.process_measurement(dets)
                    else: time.sleep(0.005)
                except Exception as e: pass
            else: time.sleep(0.1)
        self.stop_pipeline()

    def stop(self):
        self.running = False
        self.wait()
