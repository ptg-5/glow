import sys
import os

os.environ["QT_PLUGIN_PATH"] = "/usr/lib/aarch64-linux-gnu/qt5/plugins"
os.environ["QT_IM_MODULE"] = "fcitx"
os.environ["GTK_IM_MODULE"] = "fcitx"
os.environ["XMODIFIERS"] = "@im=fcitx"
from PyQt5.QtWidgets import QApplication
from frontend.main_window import MainWindow
from backend.ai_thread import HailoWorker

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # 1. AI 스레드 생성
    ai_thread = HailoWorker("", "")
    
    # 2. 시그널 연결 (영상, 상태, 결과)
    ai_thread.change_pixmap_signal.connect(window.update_image)
    ai_thread.status_signal.connect(window.update_ai_status)
    ai_thread.result_signal.connect(window.show_analysis_result)
    
    # 3. 초기 거울 모드 시작 (중요: 이걸 해야 앱 켜자마자 얼굴이 보임)
    ai_thread.start() 
    
    # 4. 버튼 이벤트 연결
    # [수정됨] start_session -> request_start_session
    window.dashboard.btn_start.clicked.connect(ai_thread.request_start_session)
    
    # 정지 버튼 누르면 거울 모드로 복귀
    window.dashboard.btn_stop.clicked.connect(ai_thread.request_mirror_mode)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()