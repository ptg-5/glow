from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
                             QLabel, QPushButton, QTextEdit, QLineEdit, 
                             QSizePolicy, QStackedLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
import qtawesome as qta

# [비율 유지 라벨]
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
        grad = QColor(0, 255, 0, 180)
        pen = QPen(grad); pen.setWidth(2)
        painter.setPen(pen); painter.drawLine(0, self.scan_y, self.width(), self.scan_y)

class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # [핵심] 전체 배경 완전 검정 (거울 효과)
        self.setStyleSheet("background-color: black;")
        
        # 메인 레이아웃 (좌우 분할)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0) # 패널 사이 간격 제거

        # === [좌측] 카메라 영역 (70%) ===
        self.left_container = QFrame()
        self.left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_container.setStyleSheet("background-color: black; border: none;") # 테두리 제거
        
        left_stack = QStackedLayout(self.left_container)
        left_stack.setStackingMode(QStackedLayout.StackAll)

        # Layer 0: 카메라
        self.video_label = ResizingLabel()
        self.video_label.setText("Camera Loading...")
        self.video_label.setStyleSheet("color: #333; font-size: 20px;")
        
        # Layer 1: 스캔 효과
        self.scan_overlay = ScanOverlay()
        self.scan_overlay.hide()
        
        # Layer 2: 중앙 오버레이 (안내 문구)
        self.overlay_container = QWidget()
        self.overlay_container.setAttribute(Qt.WA_TranslucentBackground)
        overlay_layout = QVBoxLayout(self.overlay_container)
        
        self.lbl_instruction = QLabel("시작 버튼을 눌러주세요")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0); /* 배경 투명 */
            color: #AAA; font-size: 18px; font-weight: bold;
            padding: 10px;
            font-family: 'NanumGothic';
        """)
        
        self.lbl_result = QLabel("")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet("""
            background-color: rgba(0, 0, 0, 220); 
            color: #FFF; font-size: 18px; font-weight: bold;
            border-radius: 15px; padding: 20px; border: 2px solid #D4AF37;
            font-family: 'NanumGothic';
        """)
        self.lbl_result.hide()
        
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.lbl_result, alignment=Qt.AlignCenter)
        overlay_layout.addWidget(self.lbl_instruction, alignment=Qt.AlignCenter)
        overlay_layout.addSpacing(50)

        left_stack.addWidget(self.video_label)
        left_stack.addWidget(self.scan_overlay)
        left_stack.addWidget(self.overlay_container)

        # === [우측] 제어 패널 (30%) ===
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(320)
        # [핵심] 배경 투명하게 해서 왼쪽과 이어지게 함
        self.right_panel.setStyleSheet("background-color: transparent; border: none;")
        
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 시스템 정보
        self.lbl_sys_info = QLabel("SYSTEM: HAILO-10 AI")
        self.lbl_sys_info.setAlignment(Qt.AlignRight)
        self.lbl_sys_info.setStyleSheet("color: #444; font-size: 11px; margin-bottom: 10px;")

        # 2. 버튼
        self.btn_start = QPushButton(" START")
        self.btn_start.setIcon(qta.icon('fa5s.play', color='#000'))
        self.btn_start.setFixedHeight(55)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #D4AF37; color: black; 
                font-weight: bold; border-radius: 27px; font-size: 16px;
            }
            QPushButton:hover { background-color: #F4D03F; }
        """)
        
        self.btn_stop = QPushButton(" STOP")
        self.btn_stop.setIcon(qta.icon('fa5s.stop', color='white'))
        self.btn_stop.setFixedHeight(55)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #333; color: #FF4444; 
                font-weight: bold; border-radius: 27px; font-size: 16px; border: 1px solid #444;
            }
            QPushButton:hover { background-color: #444; }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_start, 7)
        btn_layout.addWidget(self.btn_stop, 3)

        self.btn_start.clicked.connect(self.scan_overlay.start_scan)
        self.btn_stop.clicked.connect(self.scan_overlay.stop_scan)

        # 3. 채팅창
        lbl_chat = QLabel("💬 Dr.Glow AI")
        lbl_chat.setStyleSheet("color: #888; font-weight: bold; margin-top: 30px;")
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 20, 20, 0.5); /* 아주 옅은 배경 */
                border-radius: 15px; border: none;
                color: #E0E0E0; font-family: 'NanumGothic'; font-size: 14px; padding: 10px;
            }
        """)

        # 4. 입력창
        input_box = QFrame()
        input_box.setStyleSheet("background-color: rgba(30, 30, 30, 0.8); border-radius: 20px;")
        input_layout = QHBoxLayout(input_box)
        input_layout.setContentsMargins(5, 5, 5, 5)

        self.input_chat = QLineEdit()
        self.input_chat.setPlaceholderText("질문 입력...")
        self.input_chat.setStyleSheet("background: transparent; color: white; border: none; font-size: 14px; font-family: 'NanumGothic';")
        
        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(35, 35)
        self.btn_send.setStyleSheet("background-color: #D4AF37; border-radius: 17px; color: black;")
        
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedSize(35, 35)
        self.btn_mic.setCheckable(True)
        self.btn_mic.setStyleSheet("""
            QPushButton { background-color: transparent; border: 1px solid #555; border-radius: 17px; color: #888; }
            QPushButton:checked { background-color: #FF4444; border: none; color: white; }
        """)

        input_layout.addWidget(self.input_chat)
        input_layout.addWidget(self.btn_send)
        input_layout.addWidget(self.btn_mic)

        # 배치
        right_layout.addWidget(self.lbl_sys_info)
        right_layout.addLayout(btn_layout)
        right_layout.addWidget(lbl_chat)
        right_layout.addWidget(self.chat_history)
        right_layout.addSpacing(10)
        right_layout.addWidget(input_box)

        # 최종 조립 (비율 7:3)
        main_layout.addWidget(self.left_container, stretch=7)
        main_layout.addWidget(self.right_panel, stretch=3)