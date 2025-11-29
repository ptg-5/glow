# frontend/welcome.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.lbl_logo = QLabel("GLOWFOREVER")
        self.lbl_logo.setObjectName("WelcomeLogo")
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        
        self.lbl_sub = QLabel("Tap or press SPACEBAR to begin")
        self.lbl_sub.setStyleSheet("color: #888888; font-size: 16px; margin-top: 30px; font-weight: 300;")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.lbl_logo)
        layout.addWidget(self.lbl_sub)
        layout.addStretch()
        self.setLayout(layout)