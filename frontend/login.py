from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from backend.database import DBManager
from frontend.signup_dialog import SignupDialog # [NEW] 임포트

class LoginScreen(QWidget):
    login_success_signal = pyqtSignal(dict) 

    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #000000;")
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        login_box = QFrame()
        login_box.setFixedSize(400, 520) # 높이 살짝 늘림
        login_box.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 20px;
                border: 1px solid #333;
            }
        """)
        box_layout = QVBoxLayout(login_box)
        box_layout.setContentsMargins(40, 50, 40, 50)
        box_layout.setSpacing(20)

        lbl_logo = QLabel("GLOWFOREVER")
        lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet("color: #D4AF37; font-size: 32px; font-weight: bold; margin-bottom: 20px; border: none;")
        
        input_style = """
            QLineEdit {
                background-color: #333; border: 1px solid #555; border-radius: 10px;
                color: white; padding: 12px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #D4AF37; }
        """

        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("아이디")
        self.input_id.setStyleSheet(input_style)

        self.input_pw = QLineEdit()
        self.input_pw.setPlaceholderText("비밀번호")
        self.input_pw.setEchoMode(QLineEdit.Password)
        self.input_pw.setStyleSheet(input_style)
        self.input_pw.returnPressed.connect(self.try_login)

        btn_login = QPushButton("로그인")
        btn_login.setFixedHeight(50)
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: #D4AF37; color: black; font-weight: bold; font-size: 16px; border-radius: 10px;
            }
            QPushButton:hover { background-color: #F4D03F; }
        """)
        btn_login.clicked.connect(self.try_login)

        bottom_layout = QHBoxLayout()
        
        # [수정] 회원가입 버튼
        btn_signup = QPushButton("회원가입")
        btn_signup.setCursor(Qt.PointingHandCursor)
        btn_signup.setStyleSheet("color: #AAA; border: none; font-size: 13px; font-weight: bold;")
        btn_signup.clicked.connect(self.open_signup_popup) # 팝업 연결
        
        btn_guest = QPushButton("비회원 시작 >")
        btn_guest.setCursor(Qt.PointingHandCursor)
        btn_guest.setStyleSheet("color: white; border: none; font-size: 13px; font-weight: bold;")
        btn_guest.clicked.connect(self.guest_login)

        bottom_layout.addWidget(btn_signup)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_guest)

        box_layout.addWidget(lbl_logo)
        box_layout.addWidget(self.input_id)
        box_layout.addWidget(self.input_pw)
        box_layout.addSpacing(10)
        box_layout.addWidget(btn_login)
        box_layout.addLayout(bottom_layout)
        box_layout.addStretch()

        main_layout.addWidget(login_box)

    def try_login(self):
        uid = self.input_id.text().strip()
        upw = self.input_pw.text().strip()
        
        if not uid or not upw:
            self.show_msg("알림", "아이디와 비밀번호를 입력해주세요.")
            return

        user_info = self.db.login_user(uid, upw)
        if user_info:
            self.login_success_signal.emit(user_info)
        else:
            self.show_msg("로그인 실패", "아이디 또는 비밀번호가 일치하지 않습니다.")

    def guest_login(self):
        # 비회원 (ID: 0, 이름: Guest)
        self.login_success_signal.emit({"id": 0, "name": "Guest"})

    # [NEW] 회원가입 팝업 열기
    def open_signup_popup(self):
        dialog = SignupDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 가입 성공 시 아이디 칸으로 포커스 이동
            self.input_id.setFocus()

    def show_msg(self, title, text):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet("QLabel{color: black;}")
        msg.exec_()