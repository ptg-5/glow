from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
                             QLabel, QPushButton, QTextEdit, QLineEdit, 
                             QSizePolicy, QStackedLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
import qtawesome as qta

# [비율 유지 라벨] - 여백 없이 꽉 차게 보이려면 Expanding 사용 (선택 사항)
class ResizingLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(self.scaledPixmap())

    def resizeEvent(self, event):
        if self._pixmap:
            super().setPixmap(self.scaledPixmap())

    def scaledPixmap(self):
        # KeepAspectRatio: 원본 비율 유지 (검은 여백 생길 수 있음 -> 거울 느낌에 좋음)
        return self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

# [스캔 오버레이]
class ScanOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.scan_y = 0
        self.direction = 5
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.is_scanning = False

    def start_scan(self):
        self.is_scanning = True; self.timer.start(20); self.show()
    def stop_scan(self):
        self.is_scanning = False; self.timer.stop(); self.hide()
    def animate(self):
        self.scan_y += self.direction
        if self.scan_y > self.height() or self.scan_y < 0: self.direction *= -1
        self.update()
    def paintEvent(self, event):
        if not self.is_scanning: return
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        grad = QColor(0, 255, 0, 150) # 조금 더 은은하게
        pen = QPen(grad); pen.setWidth(2)
        painter.setPen(pen); painter.drawLine(0, self.scan_y, self.width(), self.scan_y)

class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #050505;") # 완전 검정보다 살짝 밝은 딥 블랙
        
        # 메인 레이아웃 (좌우 여백 제거)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === [좌측] 카메라 영역 (80%) ===
        self.left_container = QFrame()
        self.left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_container.setStyleSheet("background-color: black; border: none;")
        
        left_stack = QStackedLayout(self.left_container)
        left_stack.setStackingMode(QStackedLayout.StackAll)

        # Layer 0: 카메라
        self.video_label = ResizingLabel()
        self.video_label.setText("Camera Loading...")
        self.video_label.setStyleSheet("color: #444; font-size: 24px; font-weight: bold;")
        
        # Layer 1: 스캔 효과
        self.scan_overlay = ScanOverlay()
        self.scan_overlay.hide()
        
        # Layer 2: 오버레이 정보 (타이머, 결과 등)
        self.overlay_container = QWidget()
        self.overlay_container.setAttribute(Qt.WA_TranslucentBackground)
        overlay_layout = QVBoxLayout(self.overlay_container)
        overlay_layout.setContentsMargins(30, 30, 30, 50)

        # 상단 타이머
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.lbl_timer = QLabel("7")
        self.lbl_timer.setFixedSize(80, 80)
        self.lbl_timer.setAlignment(Qt.AlignCenter)
        self.lbl_timer.setStyleSheet("""
            background-color: rgba(220, 20, 60, 0.8); 
            color: white; font-size: 40px; font-weight: bold;
            border-radius: 40px; border: 3px solid rgba(255,255,255,0.5);
        """)
        self.lbl_timer.hide()
        top_layout.addWidget(self.lbl_timer)

        # 하단 결과 텍스트
        center_layout = QVBoxLayout()
        self.lbl_result = QLabel("")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        # 결과창 디자인 개선
        self.lbl_result.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7); 
            color: #FFD700; font-size: 22px; font-weight: bold;
            border-radius: 20px; padding: 25px; 
            border: 1px solid rgba(255, 215, 0, 0.3);
        """)
        self.lbl_result.hide()
        
        self.lbl_instruction = QLabel("시작 버튼을 눌러주세요")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setStyleSheet("color: #888; font-size: 16px; font-weight: bold; background: transparent;")

        center_layout.addStretch()
        center_layout.addWidget(self.lbl_result, alignment=Qt.AlignCenter)
        center_layout.addSpacing(10)
        center_layout.addWidget(self.lbl_instruction, alignment=Qt.AlignCenter)
        center_layout.addSpacing(20)

        overlay_layout.addLayout(top_layout)
        overlay_layout.addLayout(center_layout)

        left_stack.addWidget(self.video_label)
        left_stack.addWidget(self.scan_overlay)
        left_stack.addWidget(self.overlay_container)

        # === [우측] 제어 패널 (20% ~ 30%) ===
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(360) # 너비를 조금 넓혀서 여유 확보
        # 글래스모피즘 효과 (반투명 배경 + 블러 느낌)
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 20, 0.85);
                border-left: 1px solid #333;
            }
        """)
        
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(25, 40, 25, 40) # 내부 여백 넉넉하게
        right_layout.setSpacing(20) # 요소 간 간격

        # 1. 시스템 정보
        self.lbl_sys_info = QLabel("SYSTEM: HAILO-10 AI")
        self.lbl_sys_info.setAlignment(Qt.AlignRight)
        self.lbl_sys_info.setStyleSheet("color: #666; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        right_layout.addWidget(self.lbl_sys_info)

        # 2. 메인 버튼 그룹
        btn_container = QFrame()
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0,0,0,0)
        btn_layout.setSpacing(15)

        self.btn_start = QPushButton(" START")
        self.btn_start.setIcon(qta.icon('fa5s.play', color='black'))
        self.btn_start.setFixedHeight(60)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #FFD700; color: #121212; 
                font-weight: bold; border-radius: 15px; font-size: 16px;
            }
            QPushButton:hover { background-color: #FFC107; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        
        self.btn_stop = QPushButton("")
        self.btn_stop.setIcon(qta.icon('fa5s.stop', color='white'))
        self.btn_stop.setFixedSize(60, 60)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #333; border-radius: 30px; border: 2px solid #FF5555;
            }
            QPushButton:hover { background-color: #FF5555; }
            QPushButton:disabled { border-color: #555; background-color: #222; }
        """)
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start, 1)
        btn_layout.addWidget(self.btn_stop, 0)
        right_layout.addWidget(btn_container)

        self.btn_start.clicked.connect(self.scan_overlay.start_scan)
        self.btn_stop.clicked.connect(self.scan_overlay.stop_scan)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #444;")
        right_layout.addWidget(line)

        # 3. AI 채팅 영역
        lbl_chat = QLabel("💬 AI ASSISTANT")
        lbl_chat.setStyleSheet("color: #888; font-size: 14px; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(lbl_chat)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid #333; border-radius: 12px;
                color: #EEE; font-family: 'NanumGothic'; font-size: 14px; padding: 12px;
            }
        """)
        right_layout.addWidget(self.chat_history)

        # 4. 입력 영역
        input_box = QFrame()
        input_box.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border-radius: 25px;")
        input_box.setFixedHeight(50)
        input_layout = QHBoxLayout(input_box)
        input_layout.setContentsMargins(15, 5, 5, 5)

        self.input_chat = QLineEdit()
        self.input_chat.setPlaceholderText("AI에게 물어보세요...")
        self.input_chat.setStyleSheet("background: transparent; color: white; border: none; font-size: 14px;")
        
        self.btn_mic = QPushButton()
        self.btn_mic.setIcon(qta.icon('fa5s.microphone', color='white'))
        self.btn_mic.setFixedSize(40, 40)
        self.btn_mic.setCheckable(True)
        self.btn_mic.setCursor(Qt.PointingHandCursor)
        self.btn_mic.setStyleSheet("""
            QPushButton { background-color: transparent; border-radius: 20px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
            QPushButton:checked { background-color: #FF4444; }
        """)
        
        self.btn_send = QPushButton()
        self.btn_send.setIcon(qta.icon('fa5s.paper-plane', color='#121212'))
        self.btn_send.setFixedSize(40, 40)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton { background-color: #D4AF37; border-radius: 20px; }
            QPushButton:hover { background-color: #F4D03F; }
        """)

        input_layout.addWidget(self.input_chat)
        input_layout.addWidget(self.btn_mic)
        input_layout.addWidget(self.btn_send)
        right_layout.addWidget(input_box)

        # 전체 레이아웃 조립
        main_layout.addWidget(self.left_container, stretch=8) # 카메라를 더 넓게 (80%)
        main_layout.addWidget(self.right_panel, stretch=2)    # 패널을 더 좁게 (20%)

    def set_analyzing_state(self, is_running):
        if is_running:
            self.btn_start.setEnabled(False)
            self.btn_start.setText(" 분석 중...")
            self.btn_stop.setEnabled(True)
            self.scan_overlay.start_scan()
        else:
            self.btn_start.setEnabled(True)
            self.btn_start.setText(" START")
            self.btn_stop.setEnabled(False)
            self.scan_overlay.stop_scan()