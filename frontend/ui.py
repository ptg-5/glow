from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QFrame, 
                             QStackedWidget, QLineEdit, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette

# ==========================================
# 1. 스타일 시트 (고급스러운 다크 & 골드 테마)
# ==========================================
STYLESHEET = """
QMainWindow {
    background-color: #121212;
}
QLabel {
    color: #E0E0E0;
    font-family: 'Segoe UI', sans-serif;
}
/* 로고 스타일 */
QLabel#LogoTitle {
    color: #FFD700; /* Gold */
    font-size: 48px;
    font-weight: bold;
    letter-spacing: 4px;
}
QLabel#HeaderTitle {
    color: #FFD700;
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 2px;
}
/* 버튼 스타일 */
QPushButton {
    background-color: #333333;
    color: white;
    border: 1px solid #555555;
    border-radius: 5px;
    padding: 10px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #444444;
    border: 1px solid #FFD700;
}
QPushButton:pressed {
    background-color: #FFD700;
    color: black;
}
/* 그룹박스 (패널) 스타일 */
QGroupBox {
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 20px;
    color: #AAAAAA;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
}
/* 텍스트 입력창 */
QLineEdit {
    background-color: #222222;
    border: 1px solid #444444;
    color: white;
    border-radius: 4px;
    padding: 5px;
}
QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    color: #00FF00; /* 터미널 느낌 */
    font-family: 'Consolas', monospace;
    border-radius: 4px;
}
"""

# ==========================================
# 2. 대기 화면 (Welcome Screen)
# ==========================================
class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.lbl_logo = QLabel("GLOWFOREVER")
        self.lbl_logo.setObjectName("LogoTitle") # 스타일 적용용 ID
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        
        self.lbl_sub = QLabel("Press SPACEBAR to Start Analysis")
        self.lbl_sub.setStyleSheet("color: #888888; font-size: 16px; margin-top: 20px;")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.lbl_logo)
        layout.addWidget(self.lbl_sub)
        layout.addStretch()
        self.setLayout(layout)

# ==========================================
# 3. 메인 대시보드 (Dashboard)
# ==========================================
class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # --- [상단] 헤더 (로고) ---
        header_layout = QHBoxLayout()
        lbl_header = QLabel("GLOWFOREVER")
        lbl_header.setObjectName("HeaderTitle")
        header_layout.addWidget(lbl_header)
        header_layout.addStretch() # 로고를 왼쪽에 고정
        main_layout.addLayout(header_layout)

        # --- [중단] 콘텐츠 영역 (좌:정보 / 중:카메라 / 우:제어&챗) ---
        content_layout = QHBoxLayout()
        
        # 1. [좌측] 환경 및 상태 패널 (추천 구성)
        left_panel = QFrame()
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # 1-1. 환경 센서 그룹
        grp_env = QGroupBox("ENVIRONMENT")
        env_layout = QVBoxLayout()
        self.lbl_temp = QLabel("TEMP : -- °C")
        self.lbl_hum = QLabel("HUM  : -- %")
        self.lbl_dist = QLabel("DIST : -- cm")
        for lbl in [self.lbl_temp, self.lbl_hum, self.lbl_dist]:
            lbl.setStyleSheet("font-size: 16px; color: #00d2ff; padding: 5px;")
            env_layout.addWidget(lbl)
        grp_env.setLayout(env_layout)
        
        # 1-2. 시스템 상태 그룹
        grp_sys = QGroupBox("SYSTEM STATUS")
        sys_layout = QVBoxLayout()
        self.lbl_fps = QLabel("FPS: 30.0")
        self.lbl_chip = QLabel("AI CHIP: HAILO-8L")
        self.lbl_status = QLabel("User: Not Detected")
        self.lbl_status.setStyleSheet("color: #FF4444; font-weight: bold;")
        
        sys_layout.addWidget(self.lbl_fps)
        sys_layout.addWidget(self.lbl_chip)
        sys_layout.addWidget(self.lbl_status)
        grp_sys.setLayout(sys_layout)

        left_layout.addWidget(grp_env)
        left_layout.addWidget(grp_sys)
        left_layout.addStretch()
        
        # 2. [중앙] 카메라 뷰
        center_panel = QFrame()
        center_layout = QVBoxLayout(center_panel)
        
        self.video_label = QLabel("CAMERA INITIALIZING...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; border: 2px solid #FFD700; border-radius: 10px;")
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        center_layout.addWidget(self.video_label)
        
        # 3. [우측] 제어 및 LLM 챗
        right_panel = QFrame()
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        
        # 3-1. 제어 버튼
        btn_layout = QVBoxLayout()
        self.btn_start = QPushButton("▶ START ANALYSIS")
        self.btn_start.setStyleSheet("background-color: #27ae60; font-weight: bold;")
        self.btn_stop = QPushButton("⏹ STOP ANALYSIS")
        self.btn_stop.setStyleSheet("background-color: #c0392b; font-weight: bold;")
        self.btn_stop.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        
        # 3-2. LLM 채팅 영역
        lbl_chat = QLabel("💬 AI ASSISTANT")
        lbl_chat.setStyleSheet("margin-top: 20px; font-weight: bold; color: #FFD700;")
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("AI와의 대화 내용이 여기에 표시됩니다...")
        
        self.input_chat = QLineEdit()
        self.input_chat.setPlaceholderText("질문을 입력하세요...")
        self.input_chat.setStyleSheet("padding: 10px;")

        right_layout.addLayout(btn_layout)
        right_layout.addWidget(lbl_chat)
        right_layout.addWidget(self.chat_history)
        right_layout.addWidget(self.input_chat)
        
        # 레이아웃 배치
        content_layout.addWidget(left_panel)
        content_layout.addWidget(center_panel, stretch=1) # 중앙이 남은 공간 다 씀
        content_layout.addWidget(right_panel)
        
        main_layout.addLayout(content_layout)

# ==========================================
# 4. 메인 윈도우 (화면 전환 관리)
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLOWFOREVER - Smart Mirror")
        self.setGeometry(100, 100, 1400, 900) # 넓게 시작
        
        # 스타일 적용
        self.setStyleSheet(STYLESHEET)
        
        # 스택 위젯 (페이지 넘기기용)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 페이지 생성
        self.page_welcome = WelcomeScreen()
        self.page_dashboard = DashboardScreen()
        
        self.stack.addWidget(self.page_welcome)   # Index 0
        self.stack.addWidget(self.page_dashboard) # Index 1
        
        # 편의를 위해 버튼/라벨 등을 외부에서 접근하기 쉽게 연결
        self.dashboard = self.page_dashboard
        self.btn_start = self.dashboard.btn_start
        self.btn_stop = self.dashboard.btn_stop
        self.video_label = self.dashboard.video_label
        
        # LLM 채팅 엔터키 연결 (더미 기능)
        self.dashboard.input_chat.returnPressed.connect(self.send_message)

    # --- Spacebar 이벤트 처리 ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.stack.currentIndex() == 0:
                print("🚀 사용자 감지(시뮬레이션): 대시보드로 이동")
                self.stack.setCurrentIndex(1)
        else:
            super().keyPressEvent(event)

    # --- 데이터 업데이트 메서드들 ---
    def update_image(self, q_img):
        # 현재 대시보드 화면일 때만 업데이트
        if self.stack.currentIndex() == 1:
            self.dashboard.video_label.setPixmap(QPixmap.fromImage(q_img))

    def update_log(self, text):
        # 로그는 채팅창에 시스템 메시지처럼 띄울 수도 있음
        if self.stack.currentIndex() == 1:
            # self.dashboard.chat_history.append(f"[SYSTEM] {text}") # 너무 시끄러우면 주석
            pass

    def update_sensor(self, temp, hum, dist, is_seated):
        if self.stack.currentIndex() == 1:
            self.dashboard.lbl_temp.setText(f"TEMP : {temp:.1f} °C")
            self.dashboard.lbl_hum.setText(f"HUM  : {hum:.1f} %")
            self.dashboard.lbl_dist.setText(f"DIST : {dist:.0f} cm")
            
            if is_seated:
                self.dashboard.lbl_status.setText("User: ACTIVE")
                self.dashboard.lbl_status.setStyleSheet("color: #00FF00; font-weight: bold;")
            else:
                self.dashboard.lbl_status.setText("User: AWAY")
                self.dashboard.lbl_status.setStyleSheet("color: #FF4444; font-weight: bold;")

    def send_message(self):
        user_text = self.dashboard.input_chat.text()
        if user_text:
            self.dashboard.chat_history.append(f"👤 나: {user_text}")
            self.dashboard.input_chat.clear()
            # 여기에 추후 Qwen LLM 연동 코드 작성
            self.dashboard.chat_history.append("🤖 GLOWFOREVER: (아직 LLM이 연결되지 않았습니다)")