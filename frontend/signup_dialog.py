from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from backend.database import DBManager

class SignupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("회원가입")
        
        # [수정] 창 크기를 더 넉넉하게 늘림 (높이 600)
        self.setFixedSize(400, 600)
        
        # [수정] 폰트 강제 지정 ('NanumGothic') 및 입력창 크기 확대
        self.setStyleSheet("""
            QDialog { 
                background-color: #1E1E1E; 
                border: 2px solid #444; 
                border-radius: 20px; 
            }
            QLabel { 
                color: #DDD; 
                font-size: 16px; 
                font-weight: bold;
                font-family: 'NanumGothic', 'Malgun Gothic', sans-serif; /* 한글 폰트 지정 */
                margin-top: 10px;
            }
            QLineEdit { 
                background-color: #333; 
                border: 1px solid #555; 
                border-radius: 10px; 
                color: white; 
                padding: 15px; /* [핵심] 위아래 여백을 늘려서 입력창을 키움 */
                font-size: 15px;
                font-family: 'NanumGothic', sans-serif;
                margin-bottom: 5px;
            }
            QLineEdit:focus { 
                border: 2px solid #D4AF37; 
                background-color: #222;
            }
            QPushButton { 
                background-color: #D4AF37; 
                color: black; 
                font-weight: bold; 
                border-radius: 10px; 
                font-size: 18px; 
                padding: 15px; /* 버튼도 키움 */
                margin-top: 20px;
                font-family: 'NanumGothic', sans-serif;
            }
            QPushButton:hover { background-color: #F4D03F; }
            QPushButton#CancelBtn {
                background-color: #444; color: #AAA; margin-top: 10px;
            }
            QPushButton#CancelBtn:hover { background-color: #555; color: white; }
        """)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 50, 40, 50) # 전체 여백 확보
        layout.setSpacing(5)

        # 타이틀
        lbl_title = QLabel("✨ 새 계정 만들기")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #D4AF37; font-size: 28px; font-weight: bold; margin-bottom: 30px; border: none;")
        layout.addWidget(lbl_title)

        # 입력 필드들 (라벨 + 입력창)
        # 이름
        layout.addWidget(QLabel("이름"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("이름을 입력하세요")
        layout.addWidget(self.input_name)
        
        # 아이디
        layout.addWidget(QLabel("아이디"))
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("아이디 (영문/숫자)")
        layout.addWidget(self.input_id)
        
        # 비밀번호
        layout.addWidget(QLabel("비밀번호"))
        self.input_pw = QLineEdit()
        self.input_pw.setPlaceholderText("비밀번호 (4자리 이상)")
        self.input_pw.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input_pw)
        
        # 비밀번호 확인
        layout.addWidget(QLabel("비밀번호 확인"))
        self.input_pw_confirm = QLineEdit()
        self.input_pw_confirm.setPlaceholderText("비밀번호를 다시 입력하세요")
        self.input_pw_confirm.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input_pw_confirm)

        layout.addStretch() # 빈 공간을 아래로 밀기

        # 버튼
        btn_signup = QPushButton("가입하기")
        btn_signup.setCursor(Qt.PointingHandCursor)
        btn_signup.clicked.connect(self.try_signup)
        layout.addWidget(btn_signup)
        
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("CancelBtn")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    def try_signup(self):
        name = self.input_name.text().strip()
        uid = self.input_id.text().strip()
        pw = self.input_pw.text().strip()
        pw_cf = self.input_pw_confirm.text().strip()

        # 유효성 검사
        if not name or not uid or not pw:
            self.show_msg("입력 오류", "모든 항목을 입력해주세요.")
            return
        
        if len(pw) < 4:
            self.show_msg("비밀번호 오류", "비밀번호는 4자리 이상이어야 합니다.")
            return
            
        if pw != pw_cf:
            self.show_msg("비밀번호 오류", "비밀번호가 일치하지 않습니다.")
            return

        # DB 저장
        db = DBManager()
        try:
            success, msg = db.register_user(uid, pw, name)
            if success:
                self.show_msg("성공", f"환영합니다, {name}님!\n이제 로그인해주세요.")
                self.accept()
            else:
                self.show_msg("실패", msg)
        except Exception as e:
            self.show_msg("오류", f"DB 오류: {e}")
        finally:
            db.close()

    def show_msg(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        # 메시지 박스도 한글 폰트 적용
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: black; font-size: 14px; font-family: 'NanumGothic'; }
            QPushButton { background-color: #D4AF37; color: white; padding: 5px 15px; }
        """)
        msg.exec_()