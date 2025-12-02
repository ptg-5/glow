import sys
import time
import numpy as np
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QFrame, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# Hailo 라이브러리
import hailo

# ==========================================
# Hailo 파이프라인 스레드
# ==========================================
class HailoVideoThread(QThread):
    # 영상 전송 신호
    change_pixmap_signal = pyqtSignal(QImage)
    # Detection 결과 전송 신호
    detection_signal = pyqtSignal(str)
    
    def __init__(self, hef_path, labels_json):
        super().__init__()
        self._run_flag = True
        self.hef_path = hef_path
        self.labels_json = labels_json
        self.frame_count = 0

    def run(self):
        # GStreamer 초기화
        Gst.init(None)
        
        print("Hailo 파이프라인 시작...")
        
        # 파이프라인 문자열 (로그에서 복사 + appsink로 변경)
        pipeline_cmd = f"""
        v4l2src device=/dev/video0 name=source ! 
        video/x-raw, width=640, height=480 ! 
        videoflip name=videoflip_source video-direction=horiz ! 
        queue name=source_scale_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        videoscale name=source_videoscale n-threads=2 ! 
        queue name=source_convert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        videoconvert n-threads=3 name=source_convert qos=false ! 
        video/x-raw, pixel-aspect-ratio=1/1, format=RGB, width=640, height=640 ! 
        videorate name=source_videorate ! 
        capsfilter name=source_fps_caps caps="video/x-raw, framerate=30/1" ! 
        queue name=inference_scale_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        videoscale name=inference_videoscale n-threads=2 qos=false ! 
        queue name=inference_convert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        video/x-raw, pixel-aspect-ratio=1/1 ! 
        videoconvert name=inference_videoconvert n-threads=2 ! 
        queue name=inference_hailonet_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        hailonet name=inference_hailonet hef-path={self.hef_path} batch-size=2 vdevice-group-id=1 nms-score-threshold=0.3 nms-iou-threshold=0.45 output-format-type=HAILO_FORMAT_TYPE_FLOAT32 force-writable=true ! 
        queue name=inference_hailofilter_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        hailofilter name=inference_hailofilter so-path=/usr/local/hailo/resources/so/libyolo_hailortpp_postprocess.so config-path={self.labels_json} function-name=filter qos=false ! 
        queue name=inference_output_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        queue name=identity_callback_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        identity name=identity_callback ! 
        queue name=hailo_display_overlay_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        hailooverlay name=hailo_display_overlay ! 
        queue name=hailo_display_videoconvert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! 
        videoconvert name=hailo_display_videoconvert n-threads=2 qos=false ! 
        appsink name=qt_sink emit-signals=false sync=false max-buffers=1 drop=true
        """
        
        try:
            pipeline = Gst.parse_launch(pipeline_cmd)
            appsink = pipeline.get_by_name("qt_sink")
            identity = pipeline.get_by_name("identity_callback")
            
            # identity에 pad probe 콜백 등록 (detection 결과 수신)
            identity_pad = identity.get_static_pad("src")
            identity_pad.add_probe(Gst.PadProbeType.BUFFER, self.detection_callback)
            
            # 파이프라인 시작
            pipeline.set_state(Gst.State.PLAYING)
            print("✅ 파이프라인 PLAYING 상태")
            
            # 메인 루프
            while self._run_flag:
                sample = appsink.emit("pull-sample")
                
                if sample:
                    buf = sample.get_buffer()
                    caps = sample.get_caps()
                    
                    # 프레임 정보 가져오기
                    structure = caps.get_structure(0)
                    h = structure.get_value("height")
                    w = structure.get_value("width")
                    
                    # 버퍼를 numpy로 변환
                    buffer = buf.extract_dup(0, buf.get_size())
                    frame = np.ndarray((h, w, 3), buffer=buffer, dtype=np.uint8)
                    
                    # QImage로 변환
                    bytes_per_line = 3 * w
                    q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    
                    # 메인 스레드로 전송
                    self.change_pixmap_signal.emit(q_img)
                else:
                    time.sleep(0.01)
            
            # 종료 처리
            pipeline.set_state(Gst.State.NULL)
            print("파이프라인 종료")
            
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            import traceback
            traceback.print_exc()

    def detection_callback(self, pad, info):
        """Detection 결과를 파싱하는 콜백"""
        try:
            self.frame_count += 1
            buffer = info.get_buffer()
            
            if buffer is None:
                return Gst.PadProbeReturn.OK
            
            # Hailo ROI에서 detection 추출
            roi = hailo.get_roi_from_buffer(buffer)
            detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
            
            if detections:
                detection_text = f"Frame {self.frame_count}: {len(detections)}개 객체 감지\n"
                for det in detections:
                    label = det.get_label()
                    confidence = det.get_confidence()
                    bbox = det.get_bbox()
                    detection_text += f"  - {label}: {confidence:.2f} [{bbox.xmin():.0f},{bbox.ymin():.0f},{bbox.width():.0f},{bbox.height():.0f}]\n"
                
                # UI로 전송
                self.detection_signal.emit(detection_text)
        
        except Exception as e:
            print(f"콜백 에러: {e}")
        
        return Gst.PadProbeReturn.OK

    def stop(self):
        """스레드 종료"""
        self._run_flag = False
        self.wait()

# ==========================================
# 메인 GUI 윈도우
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Hailo AI Dashboard - PyQt6")
        self.setGeometry(100, 100, 1400, 800)
        
        # 메인 위젯
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        
        # 스레드 변수
        self.thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # --- [왼쪽] 제어 패널 ---
        left_panel = QFrame()
        left_panel.setFixedWidth(200)
        left_panel.setStyleSheet("background-color: #2c3e50;")
        left_layout = QVBoxLayout()
        
        title_label = QLabel("🤖 Hailo Control")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_start = QPushButton("🚀 분석 시작")
        self.btn_start.setFixedHeight(60)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white; 
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.btn_start.clicked.connect(self.start_analysis)
        
        self.btn_stop = QPushButton("⛔ 분석 종료")
        self.btn_stop.setFixedHeight(60)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_stop.clicked.connect(self.stop_analysis)
        self.btn_stop.setEnabled(False)
        
        self.status_label = QLabel("⚪ 대기 중")
        self.status_label.setStyleSheet("color: #ecf0f1; font-size: 14px; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(title_label)
        left_layout.addWidget(self.btn_start)
        left_layout.addWidget(self.btn_stop)
        left_layout.addWidget(self.status_label)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # --- [가운데] 영상 화면 ---
        center_panel = QFrame()
        center_panel.setStyleSheet("background-color: #34495e;")
        center_layout = QVBoxLayout()
        
        video_title = QLabel("📹 실시간 영상")
        video_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 5px;")
        
        self.video_label = QLabel("분석 시작을 눌러주세요")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("color: #95a5a6; font-size: 18px; background-color: #2c3e50; border: 2px solid #7f8c8d;")
        self.video_label.setMinimumSize(640, 640)
        
        center_layout.addWidget(video_title)
        center_layout.addWidget(self.video_label)
        center_panel.setLayout(center_layout)
        
        # --- [오른쪽] Detection 로그 ---
        right_panel = QFrame()
        right_panel.setFixedWidth(400)
        right_panel.setStyleSheet("background-color: #2c3e50;")
        right_layout = QVBoxLayout()
        
        log_title = QLabel("📊 Detection 로그")
        log_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 5px;")
        
        self.detection_log = QTextEdit()
        self.detection_log.setReadOnly(True)
        self.detection_log.setStyleSheet("""
            QTextEdit {
                background-color: #1c2833;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 2px solid #7f8c8d;
            }
        """)
        
        right_layout.addWidget(log_title)
        right_layout.addWidget(self.detection_log)
        right_panel.setLayout(right_layout)
        
        # 레이아웃 합치기
        self.main_layout.addWidget(left_panel)
        self.main_layout.addWidget(center_panel, stretch=1)
        self.main_layout.addWidget(right_panel)
    
    def start_analysis(self):
        """분석 시작"""
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("🟢 실행 중")
        self.detection_log.append("=== 시스템 시작 ===\n")
        
        # 스레드 시작
        self.thread = HailoVideoThread(
            hef_path="../best_yolov8_cdh.hef",
            labels_json="resources/json/cdh_labels.json"
        )
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.detection_signal.connect(self.update_detection_log)
        self.thread.start()
    
    def stop_analysis(self):
        """분석 종료"""
        if self.thread:
            self.thread.stop()
            self.thread = None
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("⚪ 대기 중")
        self.video_label.setText("분석 종료됨")
        self.detection_log.append("\n=== 시스템 종료 ===\n")
    
    def update_image(self, q_img):
        """영상 프레임 업데이트"""
        self.video_label.setPixmap(QPixmap.fromImage(q_img))
    
    def update_detection_log(self, text):
        """Detection 로그 업데이트"""
        self.detection_log.append(text)
        # 자동 스크롤
        self.detection_log.verticalScrollBar().setValue(
            self.detection_log.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """창 닫을 때 정리"""
        if self.thread:
            self.thread.stop()
        event.accept()

# ==========================================
# 실행
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 다크 테마 스타일
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
