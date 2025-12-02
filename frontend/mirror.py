# frontend/mirror.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class MirrorScreen(QWidget):
    # 화면을 터치했을 때 메인으로 돌아가라는 신호
    wake_up_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 완전 검정 배경
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout(self)
        
        # 은은하게 보이는 안내 문구 (거슬리지 않게 아주 어둡게)
        self.lbl_guide = QLabel("Tap screen to wake up")
        self.lbl_guide.setStyleSheet("color: #333333; font-size: 14px;")
        self.lbl_guide.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.lbl_guide)
        layout.addSpacing(50) # 하단에서 약간 띄움
        self.setLayout(layout)

    # 화면 어디든 클릭하면 깨어남
    def mousePressEvent(self, event):
        self.wake_up_signal.emit()