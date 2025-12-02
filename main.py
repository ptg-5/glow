import sys
from PyQt5.QtWidgets import QApplication
from frontend.main_window import MainWindow
from backend.ai_thread import HailoWorker

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    ai_thread = HailoWorker("", "")
    
    ai_thread.change_pixmap_signal.connect(window.update_image)
    ai_thread.status_signal.connect(window.update_ai_status)
    ai_thread.result_signal.connect(window.show_analysis_result)
    
    # [필수] 버튼 상태 제어 신호 연결
    window.connect_ai_worker(ai_thread)
    
    ai_thread.start() 
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()