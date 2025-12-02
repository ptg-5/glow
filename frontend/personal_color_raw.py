from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QPushButton, QSizePolicy, QStackedLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
import cv2
import numpy as np
from backend.personal_color_core import PersonalColorSystem 

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
        if self._pixmap: super().setPixmap(self.scaledPixmap())

    def scaledPixmap(self):
        return self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

class PersonalColorScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer = None 
        self.current_image = None 
        self.analysis_result = None 
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #000000;")
        layout = QHBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(0)
        
        # 좌측 카메라
        self.left_container = QFrame(); self.left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_container.setStyleSheet("background-color: black; border: none;")
        left_stack = QStackedLayout(self.left_container); left_stack.setStackingMode(QStackedLayout.StackAll)
        
        self.lbl_camera = ResizingLabel("Camera Loading...")
        self.lbl_camera.setStyleSheet("color: #333; font-size: 20px;")
        
        self.overlay_container = QWidget(); self.overlay_container.setAttribute(Qt.WA_TranslucentBackground)
        overlay_layout = QVBoxLayout(self.overlay_container)
        
        self.lbl_result = QLabel("")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet("background-color: rgba(0, 0, 0, 200); color: #D4AF37; font-size: 28px; font-weight: bold; border-radius: 15px; padding: 15px 30px; border: 2px solid #D4AF37; font-family: 'NanumGothic';")
        self.lbl_result.hide()
        
        overlay_layout.addStretch(); overlay_layout.addWidget(self.lbl_result, alignment=Qt.AlignCenter); overlay_layout.addSpacing(40) 
        left_stack.addWidget(self.lbl_camera); left_stack.addWidget(self.overlay_container)
        layout.addWidget(self.left_container, stretch=7)

        # 우측 패널
        self.right_panel = QFrame(); self.right_panel.setFixedWidth(320)
        self.right_panel.setStyleSheet("background-color: transparent; border: none;")
        right_layout = QVBoxLayout(self.right_panel); right_layout.setContentsMargins(20, 30, 20, 30)
        
        lbl_title = QLabel("🎨 Personal Color"); lbl_title.setAlignment(Qt.AlignRight); lbl_title.setStyleSheet("color: #AAA; font-size: 14px; margin-bottom: 10px;")
        self.btn_analyze = QPushButton(" 📸 촬영 및 진단"); self.btn_analyze.setFixedHeight(60)
        self.btn_analyze.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; font-weight: bold; font-size: 16px; border-radius: 30px; border: none; } QPushButton:hover { background-color: #F4D03F; }")
        self.btn_analyze.clicked.connect(self.run_analysis)

        self.lbl_detail = QLabel("정면을 응시하고\n촬영 버튼을 눌러주세요.")
        self.lbl_detail.setStyleSheet("background-color: rgba(30, 30, 30, 0.6); color: #EEE; font-size: 14px; padding: 20px; border-radius: 15px; font-family: 'NanumGothic';")
        self.lbl_detail.setWordWrap(True); self.lbl_detail.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        right_layout.addWidget(lbl_title); right_layout.addWidget(self.btn_analyze); right_layout.addSpacing(20); right_layout.addWidget(self.lbl_detail, stretch=1)
        layout.addWidget(self.right_panel, stretch=3)

    def load_analyzer(self):
        if self.analyzer is None:
            self.lbl_result.setText("AI 모델 로딩 중..."); self.lbl_result.show(); self.repaint() 
            try:
                self.analyzer = PersonalColorSystem(); self.lbl_result.setText("준비 완료"); QTimer.singleShot(2000, self.lbl_result.hide)
            except Exception as e: self.lbl_result.setText(f"로딩 실패: {e}")

    def update_frame(self, q_img):
        if self.analysis_result: return
        self.current_image = q_img.copy()
        self.lbl_camera.setPixmap(QPixmap.fromImage(q_img))

    def run_analysis(self):
        if not self.analyzer: self.load_analyzer(); return
        if self.current_image is None: self.lbl_result.setText("영상 없음"); self.lbl_result.show(); return

        q_img = self.current_image
        w, h = q_img.width(), q_img.height()
        ptr = q_img.bits(); ptr.setsize(q_img.byteCount())
        
        # PyQt (RGB) -> Numpy
        arr = np.array(ptr).reshape(h, w, 3) 
        
        # [수정] OpenCV는 BGR을 쓰므로 변환해서 넘김
        bgr_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        
        self.lbl_result.setText("분석 중..."); self.lbl_result.show(); self.repaint()
        
        # 분석 실행
        data = self.analyzer.analyze_frame(bgr_img)

        if not data: self.lbl_result.setText("얼굴을 찾을 수 없습니다"); self.analysis_result = None; return

        self.analysis_result = data
        self.draw_result(q_img, data)

    def draw_result(self, q_img, data):
        painter = QPainter(q_img); painter.setRenderHint(QPainter.Antialiasing)
        x1, y1, x2, y2 = data['bbox']; points = data['points']; season = data['result']; is_warm = data['is_warm']; stats = data['stats']
        color = QColor(255, 165, 0) if is_warm else QColor(255, 105, 180)
        
        pen = QPen(color, 4); painter.setPen(pen); painter.drawRect(x1, y1, x2-x1, y2-y1)
        painter.setBrush(QColor("#00FF00")); painter.setPen(Qt.NoPen)
        for px, py in points: painter.drawEllipse(px-5, py-5, 10, 10)
        painter.end()

        self.lbl_camera.setPixmap(QPixmap.fromImage(q_img))
        self.lbl_result.setText(f"{season}"); self.lbl_result.setStyleSheet(f"background-color: rgba(0, 0, 0, 200); color: {color.name()}; font-size: 32px; font-weight: bold; border-radius: 15px; padding: 20px 40px; border: 3px solid {color.name()}; font-family: 'NanumGothic';"); self.lbl_result.show()
        
        type_str = "웜톤 (Warm)" if is_warm else "쿨톤 (Cool)"; type_color = "#FFA500" if is_warm else "#FF69B4"
        detail_html = f"<h2 style='color:{type_color}'>{season}</h2><p style='font-size:16px; color:#DDD'>당신의 피부 타입은 <b>{type_str}</b>입니다.</p><hr style='border-color:#444'><p style='color:#AAA'><b>상세 분석:</b></p><p style='color:#DDD'>- 피부 밝기(L): {stats['L']:.1f}</p><p style='color:#DDD'>- 노란기(b): {stats['b']:.1f}</p><p style='color:#DDD'>- 채도(S): {stats['S']:.1f}</p>"
        self.lbl_detail.setText(detail_html)
        self.btn_analyze.setText("🔄 다시 하기"); self.btn_analyze.clicked.disconnect(); self.btn_analyze.clicked.connect(self.reset_view)

    def reset_view(self):
        self.analysis_result = None; self.lbl_result.hide(); self.btn_analyze.setText("📸 촬영 및 진단"); self.lbl_detail.setText("정면을 응시하고\n촬영 버튼을 눌러주세요."); self.btn_analyze.clicked.disconnect(); self.btn_analyze.clicked.connect(self.run_analysis)