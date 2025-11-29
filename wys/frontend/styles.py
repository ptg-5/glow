# frontend/styles.py

# 고급스러운 다크 & 골드 테마
STYLESHEET = """
/* 전체 배경 및 기본 폰트 */
QMainWindow, QWidget#MainBackground {
    background-color: #121212;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}
QLabel { color: #E0E0E0; }

/* 웰컴 스크린 로고 */
QLabel#WelcomeLogo {
    color: #D4AF37; font-size: 60px; font-weight: 300; letter-spacing: 8px;
}

/* 상단 헤더바 */
QFrame#HeaderBar {
    background-color: #1E1E1E;
    border-bottom: 1px solid #333333;
}
QLabel#HeaderLogo {
    color: #D4AF37; font-size: 22px; font-weight: bold; letter-spacing: 2px;
}
QLabel#HeaderInfo { color: #AAAAAA; font-size: 14px; }
QLabel#HeaderSensor { color: #4DB6AC; font-size: 14px; font-weight: bold; }

/* 사이드바 네비게이션 */
QFrame#SideNav {
    background-color: #1E1E1E;
    border-right: 1px solid #333333;
    min-width: 80px; max-width: 80px;
}
QPushButton.NavBtn {
    background-color: transparent; border: none; color: #888888;
    font-size: 12px; padding: 15px 5px; margin: 5px; border-radius: 10px;
}
QPushButton.NavBtn:hover { background-color: #2A2A2A; color: #D4AF37; }
QPushButton.NavBtn:checked { background-color: #333333; color: #D4AF37; font-weight: bold;}

/* 메인 콘텐츠 패널 */
QFrame#ContentPanel {
    background-color: #181818;
    border-radius: 15px; margin: 10px;
}
QLabel#CameraView {
    background-color: #000000; border-radius: 12px;
    border: 2px solid #333333;
}

/* 우측 패널 및 채팅창 */
QFrame#RightPanel { background-color: transparent; }
QTextEdit#ChatHistory {
    background-color: #222222; border: none; border-radius: 10px;
    color: #E0E0E0; padding: 10px; font-size: 13px;
}
QLineEdit#ChatInput {
    background-color: #2A2A2A; border: 1px solid #333333;
    border-radius: 20px; color: white; padding: 10px 15px; font-size: 13px;
}

/* 버튼 스타일 */
QPushButton#BtnStart {
    background-color: #D4AF37; color: #121212; font-weight: bold;
    border-radius: 8px; padding: 12px; font-size: 14px; border: none;
}
QPushButton#BtnStop {
    background-color: #2A2A2A; color: #FF5555; font-weight: bold;
    border-radius: 8px; padding: 12px; font-size: 14px; border: 1px solid #FF5555;
}

/* 리포트 카드 스타일 */
QFrame.ReportCard {
    background-color: #222222; border-radius: 12px; padding: 15px; margin-bottom: 15px;
}
QLabel.CardTitle {
    color: #D4AF37; font-size: 16px; font-weight: bold; margin-bottom: 10px;
}
"""