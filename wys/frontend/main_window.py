from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont

from frontend.styles import STYLESHEET
from frontend.welcome import WelcomeScreen
from frontend.dashboard import DashboardScreen
from frontend.report import ReportScreen
from frontend.personal_color import PersonalColorScreen
from frontend.mirror import MirrorScreen
from backend.voice_thread import VoiceWorker
# [중요] 센서 매니저 임포트 확인
from sensors.manager import SensorWorker 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLOWFOREVER - AI Smart Mirror")
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet(STYLESHEET)
        
        main_widget = QWidget()
        main_widget.setObjectName("MainBackground")
        main_widget.setStyleSheet("background-color: #000000;")
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderBar")
        self.header_frame.setFixedHeight(60)
        self.header_frame.setStyleSheet("background-color: rgba(20, 20, 20, 0.8); border-bottom: 1px solid #333;")
        h_layout = QHBoxLayout(self.header_frame)
        
        lbl_logo = QLabel("GLOWFOREVER")
        lbl_logo.setObjectName("HeaderLogo")
        self.lbl_datetime = QLabel("Loading...")
        self.lbl_datetime.setObjectName("HeaderInfo")
        self.lbl_sensor = QLabel("TEMP: --°C")
        self.lbl_sensor.setObjectName("HeaderSensor")
        
        h_layout.addWidget(lbl_logo)
        h_layout.addStretch()
        h_layout.addWidget(self.lbl_datetime)
        h_layout.addSpacing(20)
        h_layout.addWidget(self.lbl_sensor)
        
        main_layout.addWidget(self.header_frame)
        
        # --- Content ---
        content_box = QHBoxLayout()
        content_box.setSpacing(0)
        
        # Sidebar
        self.side_nav = QFrame()
        self.side_nav.setObjectName("SideNav")
        self.side_nav.setStyleSheet("background-color: rgba(20, 20, 20, 0.8); border-right: 1px solid #333;")
        nav_layout = QVBoxLayout(self.side_nav)
        
        self.btn_home = QPushButton("🏠\nHome")
        self.btn_report = QPushButton("📋\nReport")
        self.btn_color = QPushButton("🎨\nColor")
        self.btn_mirror = QPushButton("🪞\nMirror")
        
        self.nav_btns = [self.btn_home, self.btn_report, self.btn_color, self.btn_mirror]
        for btn in self.nav_btns:
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(70)
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        
        # Stack
        self.stack = QStackedWidget()
        self.page_welcome = WelcomeScreen()
        self.page_dashboard = DashboardScreen()
        self.page_report = ReportScreen()
        self.page_color = PersonalColorScreen()
        self.page_mirror = MirrorScreen()
        
        self.stack.addWidget(self.page_welcome)     
        self.stack.addWidget(self.page_dashboard)   
        self.stack.addWidget(self.page_report)      
        self.stack.addWidget(self.page_color)       
        self.stack.addWidget(self.page_mirror)      
        
        content_box.addWidget(self.side_nav)
        content_box.addWidget(self.stack)
        main_layout.addLayout(content_box)
        
        self.dashboard = self.page_dashboard
        
        # [1] 음성 스레드
        self.voice_thread = VoiceWorker()
        self.voice_thread.status_signal.connect(self.update_voice_status)
        self.voice_thread.user_text_signal.connect(self.add_user_message)
        self.voice_thread.ai_start_signal.connect(self.on_ai_response_start)
        self.voice_thread.ai_chunk_signal.connect(self.on_ai_response_chunk)
        self.voice_thread.finished_signal.connect(self.on_voice_finished)

        # [2] ★★★ 센서 스레드 (이 부분이 빠져 있었습니다!) ★★★
        self.sensor_thread = SensorWorker()
        self.sensor_thread.data_signal.connect(self.update_sensor)
        self.sensor_thread.start() 

        # 결과 화면 변수
        self.is_showing_result = False
        self.result_timer = QTimer(self)
        self.result_timer.setSingleShot(True)
        self.result_timer.timeout.connect(self.finish_result_view)

        self.PART_MAP = {
            "chin": "턱", "lips": "입술", "right_cheek": "우측 볼", "left_cheek": "좌측 볼",
            "right_eye": "우측 눈가", "left_eye": "좌측 눈가", "forehead": "이마", "nose": "코", "glabella": "미간"
        }

        # 초기화 실행
        self.setup_connections()
        self.start_clock()
        
        self.stack.setCurrentIndex(1)
        self.header_frame.show()
        self.side_nav.show()
        self.btn_home.setChecked(True)

    def setup_connections(self):
        self.btn_home.clicked.connect(lambda: self.change_page(1))
        self.btn_report.clicked.connect(lambda: self.change_page(2))
        self.btn_color.clicked.connect(lambda: self.change_page(3))
        self.btn_mirror.clicked.connect(lambda: self.change_page(4))
        self.page_mirror.wake_up_signal.connect(lambda: self.change_page(1))
        
        self.dashboard.btn_send.clicked.connect(self.send_text_message)
        self.dashboard.input_chat.returnPressed.connect(self.send_text_message)
        self.dashboard.btn_mic.clicked.connect(self.toggle_voice_chat)

    def start_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        self.lbl_datetime.setText(QDateTime.currentDateTime().toString("MM.dd (ddd) | hh:mm AP"))

    # [센서 업데이트 함수]
    def update_sensor(self, temp, hum, dist, is_seated):
        if temp > 0:
            self.lbl_sensor.setText(f"TEMP: {temp:.1f}°C  |  HUM: {hum:.1f}%")
        
    # ... (이하 기존 코드 동일: change_page, toggle_voice_chat 등) ...
    def change_page(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_home.setChecked(index==1)
        self.btn_report.setChecked(index==2)
        self.btn_color.setChecked(index==3)
        self.btn_mirror.setChecked(index==4)
        if index == 2: self.page_report.refresh_data()
        if index == 4:
            self.header_frame.hide()
            self.side_nav.hide()
        else:
            self.header_frame.show()
            self.side_nav.show()

    def toggle_fullscreen(self):
        if self.isFullScreen(): self.showNormal()
        else: self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11: self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self.isFullScreen(): self.showNormal()
        elif event.key() == Qt.Key_Space and self.stack.currentIndex() == 0: self.change_page(1)
    
    def mousePressEvent(self, event):
        if self.stack.currentIndex() == 0: self.change_page(1)
            
    def mouseDoubleClickEvent(self, event):
        self.toggle_fullscreen()

    def send_text_message(self):
        text = self.dashboard.input_chat.text().strip()
        if not text: return
        self.add_user_message(text)
        self.dashboard.input_chat.clear()
        self.dashboard.input_chat.setDisabled(True)
        if self.voice_thread.isRunning(): self.voice_thread.stop()
        saved_ctx = self.voice_thread.skin_context if hasattr(self.voice_thread, 'skin_context') else ""
        self.voice_thread = VoiceWorker(mode="TEXT", input_text=text)
        self.voice_thread.skin_context = saved_ctx
        self.voice_thread.status_signal.connect(self.update_voice_status)
        self.voice_thread.ai_start_signal.connect(self.on_ai_response_start)
        self.voice_thread.ai_chunk_signal.connect(self.on_ai_response_chunk)
        self.voice_thread.finished_signal.connect(self.on_voice_finished)
        self.voice_thread.start()

    def toggle_voice_chat(self):
        if self.dashboard.btn_mic.isChecked(): self.start_voice_chat()
        else: self.stop_voice_chat()

    def start_voice_chat(self):
        if self.voice_thread.isRunning(): return
        print("🎤 음성 비서 시작")
        self.dashboard.input_chat.setDisabled(True)
        saved_ctx = self.voice_thread.skin_context if hasattr(self.voice_thread, 'skin_context') else ""
        self.voice_thread = VoiceWorker(mode="VOICE")
        self.voice_thread.skin_context = saved_ctx
        self.voice_thread.status_signal.connect(self.update_voice_status)
        self.voice_thread.user_text_signal.connect(self.add_user_message)
        self.voice_thread.ai_start_signal.connect(self.on_ai_response_start)
        self.voice_thread.ai_chunk_signal.connect(self.on_ai_response_chunk)
        self.voice_thread.finished_signal.connect(self.on_voice_finished)
        self.voice_thread.start()
        self.dashboard.btn_mic.setText("⏹")

    def stop_voice_chat(self):
        if self.voice_thread.isRunning(): self.voice_thread.stop()
        self.dashboard.btn_mic.setText("🎤")
        self.dashboard.btn_mic.setChecked(False)
        self.dashboard.input_chat.setDisabled(False)
        self.dashboard.input_chat.setPlaceholderText("질문을 입력하세요...")

    def update_voice_status(self, msg):
        self.dashboard.input_chat.setPlaceholderText(msg)

    def add_user_message(self, text):
        self.dashboard.chat_history.append(f"<div style='text-align:right; color:#AAAAAA;'>🎤 나:<br>{text}</div>")
        self.dashboard.chat_history.append("")
        self.dashboard.chat_history.verticalScrollBar().setValue(self.dashboard.chat_history.verticalScrollBar().maximum())

    def on_ai_response_start(self):
        self.dashboard.chat_history.append(f"<font color='#D4AF37'>🤖 Dr.Glow:</font>")
        self.dashboard.chat_history.verticalScrollBar().setValue(self.dashboard.chat_history.verticalScrollBar().maximum())

    def on_ai_response_chunk(self, token):
        cursor = self.dashboard.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        self.dashboard.chat_history.setTextCursor(cursor)
        self.dashboard.chat_history.insertPlainText(token)
        self.dashboard.chat_history.verticalScrollBar().setValue(self.dashboard.chat_history.verticalScrollBar().maximum())

    def on_voice_finished(self):
        if self.dashboard.btn_mic.isChecked():
            self.dashboard.btn_mic.setChecked(False)
            self.dashboard.btn_mic.setText("🎤")
        self.dashboard.input_chat.setDisabled(False)
        self.dashboard.input_chat.setPlaceholderText("대기 중...")

    def update_image(self, q_img):
        if self.is_showing_result: return
        if self.stack.currentIndex() == 1:
            self.dashboard.video_label.setPixmap(QPixmap.fromImage(q_img))
        elif self.stack.currentIndex() == 3:
             self.page_color.update_frame(q_img)

    def update_ai_status(self, msg):
        if self.is_showing_result: return
        self.dashboard.lbl_instruction.setText(msg)
        self.dashboard.lbl_result.hide()

    def draw_face_analysis(self, q_img, bboxes, details):
        if q_img is None: return None
        painter = QPainter(q_img)
        painter.setRenderHint(QPainter.Antialiasing)
        img_w = q_img.width(); img_h = q_img.height()
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        for part, bbox in bboxes.items():
            x, y, w, h = bbox
            cx = int((x + w/2) * img_w); cy = int((y + h/2) * img_h)
            scores = details.get(part, {})
            oil_score = scores.get('Oil', 0)
            kor_name = self.PART_MAP.get(part, part)
            color = QColor("#00FF00")
            if oil_score > 60: color = QColor("#FF4444")
            elif oil_score < 20: color = QColor("#FFFF00")
            pen = QPen(color, 3); painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - 15, cy - 15, 30, 30)
            text_x = cx + 50 if cx < img_w/2 else cx - 120
            text_y = cy - 10
            painter.setPen(QPen(color, 2))
            painter.drawLine(cx + (15 if cx < img_w/2 else -15), cy, text_x, text_y + 15)
            text_str = f"{kor_name}\n유분 {oil_score}"
            painter.fillRect(text_x, text_y, 80, 40, QColor(0, 0, 0, 180))
            painter.setPen(QColor("white"))
            painter.drawText(text_x, text_y, 80, 40, Qt.AlignCenter, text_str)
        painter.end()
        return q_img

    def show_analysis_result(self, result_data):
        print("UI 결과 수신 완료 -> 결과 화면 고정")
        self.is_showing_result = True
        if isinstance(result_data, dict):
            details = result_data.get('details', {})
            if self.voice_thread: self.voice_thread.set_context(details)
            score = result_data.get('score', 0)
            timestamp = result_data.get('time', '')
            snapshot = result_data.get('snapshot', None)
            bboxes = result_data.get('bboxes', {})
            if snapshot and bboxes:
                final_img = self.draw_face_analysis(snapshot, bboxes, details)
                self.dashboard.video_label.setPixmap(QPixmap.fromImage(final_img))
            display_text = (
                f"<span style='font-size:14px; color:#AAAAAA;'>📅 {timestamp}</span><br>"
                f"⭐ 피부 점수: <font color='#FFD700' size='6'><b>{score}점</b></font><br>"
                f"<span style='font-size:14px; color:white;'>결과 확인 중 (5초 후 복귀)</span>"
            )
            self.dashboard.lbl_result.setText(display_text)
            self.dashboard.lbl_result.show()
            self.dashboard.scan_overlay.stop_scan()
            self.dashboard.lbl_instruction.hide()
            self.result_timer.start(5000) 
        else:
            self.dashboard.lbl_result.setText(str(result_data))
            self.dashboard.lbl_result.show()
            self.result_timer.start(5000)

    def finish_result_view(self):
        print(">>> 결과 화면 종료 -> 거울 모드 복귀")
        self.is_showing_result = False
        self.dashboard.lbl_result.hide()
        self.dashboard.lbl_instruction.setText("대기 모드 (버튼을 눌러 시작하세요)")
        self.dashboard.lbl_instruction.show()