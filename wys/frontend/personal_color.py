from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
import cv2
import numpy as np
from backend.personal_color_core import PersonalColorSystem 

# [NEW] 비율 유지하며 크기 조절되는 라벨
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
        # 비율 유지하면서 꽉 채우기 (KeepAspectRatio)
        # 꽉 채우고 싶으면 KeepAspectRatioByExpanding 사용
        return self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

class PersonalColorScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer = None 
        self.current_image = None 
        self.analysis_result = None 
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # [왼쪽] 카메라/분석 영역
        center_panel = QFrame()
        center_panel.setStyleSheet("background-color: #181818; border-radius: 15px;")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0,0,0,0) # 여백 제거
        
        # [수정] 커스텀 라벨 사용
        self.lbl_camera = ResizingLabel("카메라 준비 중...")
        self.lbl_camera.setStyleSheet("background-color: #000; border-radius: 12px;")
        
        self.lbl_result = QLabel("준비 완료 (버튼을 눌러주세요)")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet("color: #D4AF37; font-size: 24px; font-weight: bold; margin: 20px;")
        self.lbl_result.setFixedHeight(50) # 높이 고정해서 레이아웃 흔들림 방지
        
        center_layout.addWidget(self.lbl_camera, stretch=1) # stretch=1로 남은 공간 다 차지
        center_layout.addWidget(self.lbl_result)

        # [오른쪽] 제어 패널
        right_panel = QFrame()
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        
        lbl_title = QLabel("🎨 Personal Color")
        lbl_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        self.btn_analyze = QPushButton("📸 촬영 및 진단")
        self.btn_analyze.setFixedHeight(60)
        self.btn_analyze.setStyleSheet("""
            QPushButton { background-color: #D4AF37; color: black; font-weight: bold; font-size: 18px; border-radius: 10px; }
            QPushButton:hover { background-color: #F4D03F; }
        """)
        self.btn_analyze.clicked.connect(self.run_analysis)

        self.lbl_detail = QLabel("")
        self.lbl_detail.setStyleSheet("color: #AAA; font-size: 14px; padding: 10px; background-color: #222; border-radius: 10px;")
        self.lbl_detail.setWordWrap(True)
        self.lbl_detail.setAlignment(Qt.AlignTop) # 위쪽 정렬

        right_layout.addWidget(lbl_title)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.btn_analyze)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.lbl_detail, stretch=1) # 남은 공간 차지

        layout.addWidget(center_panel, stretch=1)
        layout.addWidget(right_panel)

    def load_analyzer(self):
        if self.analyzer is None:
            self.lbl_result.setText("AI 모델 로딩 중...")
            self.repaint() 
            try:
                self.analyzer = PersonalColorSystem()
                self.lbl_result.setText("준비 완료! 다시 버튼을 누르세요.")
            except Exception as e:
                self.lbl_result.setText(f"모델 로드 실패: {e}")

    def update_frame(self, q_img):
        if self.analysis_result: return
        self.current_image = q_img.copy()
        self.lbl_camera.setPixmap(QPixmap.fromImage(q_img))

    def run_analysis(self):
        if not self.analyzer:
            self.load_analyzer()
            return

        if self.current_image is None:
            self.lbl_result.setText("카메라 영상이 없습니다.")
            return

        q_img = self.current_image
        w, h = q_img.width(), q_img.height()
        ptr = q_img.bits()
        ptr.setsize(q_img.byteCount())
        arr = np.array(ptr).reshape(h, w, 3) 
        
        self.lbl_result.setText("분석 중...")
        self.repaint()
        
        data = self.analyzer.analyze_frame(arr)

        if not data:
            self.lbl_result.setText("얼굴을 찾을 수 없습니다.")
            self.analysis_result = None
            return

        self.analysis_result = data
        self.draw_result(q_img, data)

    def draw_result(self, q_img, data):
        painter = QPainter(q_img)
        painter.setRenderHint(QPainter.Antialiasing)
        
        x1, y1, x2, y2 = data['bbox']
        points = data['points']
        season = data['result']
        is_warm = data['is_warm']
        stats = data['stats']

        color = QColor(255, 165, 0) if is_warm else QColor(255, 105, 180)
        
        pen = QPen(color, 5) # 선 굵게
        painter.setPen(pen)
        painter.drawRect(x1, y1, x2-x1, y2-y1)

        painter.setBrush(QColor("#00FF00"))
        painter.setPen(Qt.NoPen)
        for px, py in points:
            painter.drawEllipse(px-5, py-5, 10, 10) # 점 크게

        painter.end()

        self.lbl_camera.setPixmap(QPixmap.fromImage(q_img))
        self.lbl_result.setText(f"진단 결과: {season}")
        self.lbl_result.setStyleSheet(f"color: {color.name()}; font-size: 28px; font-weight: bold; margin: 20px;")
        
        detail = f"타입: {'웜톤 (Warm)' if is_warm else '쿨톤 (Cool)'}\n\n"
        detail += f"피부 밝기(L): {stats['L']:.1f}\n"
        detail += f"노란기(b): {stats['b']:.1f}\n"
        detail += f"채도(S): {stats['S']:.1f}\n"
        
        self.lbl_detail.setText(detail)
        self.btn_analyze.setText("🔄 다시 하기")
        self.btn_analyze.clicked.disconnect()
        self.btn_analyze.clicked.connect(self.reset_view)

    def reset_view(self):
        self.analysis_result = None
        self.btn_analyze.setText("📸 촬영 및 진단")
        self.lbl_result.setText("준비 완료")
        self.lbl_result.setStyleSheet("color: #D4AF37; font-size: 24px; font-weight: bold; margin: 20px;")
        self.lbl_detail.clear()
        self.btn_analyze.clicked.disconnect()
        self.btn_analyze.clicked.connect(self.run_analysis)