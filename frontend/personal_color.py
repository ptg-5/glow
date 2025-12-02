import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QPushButton, QSizePolicy, QStackedLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage
from backend.personal_color_core import PersonalColorSystem

# =========================================================
# UI 클래스
# =========================================================
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
        self.analysis_result = None 
        
        # [중요] 카메라는 여기서 열지 않습니다! (Main이 보내줌)
        self.is_analyzing = False # 분석 모드 플래그
        
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #000000;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(0)
        
        # 좌측
        self.left_container = QFrame()
        self.left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_container.setStyleSheet("background-color: black; border: none;")
        left_stack = QStackedLayout(self.left_container)
        
        self.lbl_camera = ResizingLabel("Waiting for Camera...")
        self.lbl_camera.setStyleSheet("color: #555; font-size: 20px;")
        
        self.overlay_container = QWidget()
        self.overlay_container.setAttribute(Qt.WA_TranslucentBackground)
        overlay_layout = QVBoxLayout(self.overlay_container)
        
        self.lbl_result = QLabel("")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.hide()
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.lbl_result, alignment=Qt.AlignCenter)
        overlay_layout.addSpacing(40) 

        left_stack.addWidget(self.lbl_camera)
        left_stack.addWidget(self.overlay_container)
        layout.addWidget(self.left_container, stretch=7)

        # 우측
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(320)
        self.right_panel.setStyleSheet("background-color: transparent; border: none;")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(20, 30, 20, 30)
        
        lbl_title = QLabel("🎨 Personal Color")
        lbl_title.setAlignment(Qt.AlignRight)
        lbl_title.setStyleSheet("color: #AAA; font-size: 14px; margin-bottom: 10px;")
        
        self.btn_analyze = QPushButton(" ▶ 실시간 진단 시작")
        self.btn_analyze.setFixedHeight(60)
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.setStyleSheet("""
            QPushButton { 
                background-color: #D4AF37; color: black; 
                font-weight: bold; font-size: 16px; border-radius: 30px; border: none;
            }
            QPushButton:hover { background-color: #F4D03F; }
        """)
        self.btn_analyze.clicked.connect(self.toggle_analysis)

        self.lbl_detail = QLabel("버튼을 누르면\n실시간 분석을 시작합니다.")
        self.lbl_detail.setStyleSheet("""
            background-color: rgba(30, 30, 30, 0.6); 
            color: #EEE; font-size: 14px; padding: 20px; 
            border-radius: 15px; line-height: 1.4; font-family: sans-serif;
        """)
        self.lbl_detail.setWordWrap(True)
        self.lbl_detail.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        right_layout.addWidget(lbl_title)
        right_layout.addWidget(self.btn_analyze)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.lbl_detail, stretch=1)
        layout.addWidget(self.right_panel, stretch=3)

    # =========================================================================
    # [핵심] Main Window가 호출해주는 함수 (카메라 영상 수신)
    # =========================================================================
    def update_frame(self, q_img):
        """메인 윈도우가 보내주는 영상을 받아서 처리"""
        
        # 1. 분석 모드가 아니면 -> 그냥 화면에 띄우고 끝 (거울)
        if not self.is_analyzing:
            self.lbl_camera.setPixmap(QPixmap.fromImage(q_img))
            return

        # 2. 분석 모드면 -> 모델 로드 및 분석 수행
        if self.analyzer is None:
            self.analyzer = PersonalColorSystem() # 지연 로딩

        # QImage -> Numpy(BGR) 변환 (백엔드 분석용)
        # PyQt QImage는 포맷에 따라 다르지만 보통 ARGB32나 RGB888로 옴
        q_img = q_img.convertToFormat(QImage.Format_RGB888)
        w, h = q_img.width(), q_img.height()
        
        ptr = q_img.bits()
        ptr.setsize(q_img.byteCount())
        arr_rgb = np.array(ptr).reshape(h, w, 3)
        
        # OpenCV 백엔드는 BGR을 원하므로 변환
        frame_bgr = cv2.cvtColor(arr_rgb, cv2.COLOR_RGB2BGR)
        
        # 백엔드 분석 호출!
        data = self.analyzer.analyze_frame(frame_bgr)
        
        if data:
            # OpenCV 이미지를 복사해서 그리기 (원본 오염 방지)
            display_frame = arr_rgb.copy()
            
            x1, y1, x2, y2 = data['bbox']
            season = data['result']
            is_warm = data['is_warm']
            stats = data['stats']
            
            # 그리기 (RGB 기준 색상)
            color = (255, 165, 0) if is_warm else (180, 105, 255) # Orange vs Pink
            
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            # 텍스트 그리기 (영어만 가능)
            cv2.putText(display_frame, season, (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            for px, py in data['points']:
                cv2.circle(display_frame, (px, py), 4, (0, 255, 0), -1)

            # 분석된 이미지를 다시 QImage로 변환하여 표시
            final_h, final_w, _ = display_frame.shape
            final_qimg = QImage(display_frame.data, final_w, final_h, 
                                final_w * 3, QImage.Format_RGB888)
            
            self.lbl_camera.setPixmap(QPixmap.fromImage(final_qimg))
            
            # 텍스트 UI 업데이트
            self.update_result_ui(season, is_warm, stats)
        else:
            # 얼굴 못 찾으면 그냥 원본 표시
            self.lbl_camera.setPixmap(QPixmap.fromImage(q_img))

    def toggle_analysis(self):
        self.is_analyzing = not self.is_analyzing
        
        if self.is_analyzing:
            self.btn_analyze.setText("⏹ 분석 중지")
            self.btn_analyze.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold; font-size: 16px; border-radius: 30px;")
            self.lbl_result.show()
            self.lbl_result.setText("얼굴을 찾아주세요...")
        else:
            self.btn_analyze.setText(" ▶ 실시간 진단 시작")
            self.btn_analyze.setStyleSheet("background-color: #D4AF37; color: black; font-weight: bold; font-size: 16px; border-radius: 30px;")
            self.lbl_result.hide()
            self.lbl_detail.setText("버튼을 누르면\n실시간 분석을 시작합니다.")

    def update_result_ui(self, season, is_warm, stats):
        color_hex = "#FFA500" if is_warm else "#FF69B4"
        
        self.lbl_result.setText(season)
        self.lbl_result.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 150); 
            color: {color_hex}; font-size: 32px; font-weight: bold;
            border-radius: 15px; padding: 20px 40px; border: 3px solid {color_hex};
            font-family: sans-serif;
        """)
        
        type_str = "웜톤 (Warm)" if is_warm else "쿨톤 (Cool)"
        
        detail_html = f"""
        <h2 style='color:{color_hex}'>{season}</h2>
        <p style='font-size:16px; color:#DDD'>당신은 <b>{type_str}</b>입니다.</p>
        <hr style='border-color:#444'>
        <p style='color:#AAA; margin-bottom:5px'><b>Real-time Stats:</b></p>
        <p style='color:#DDD; margin:0'>- 밝기(L): {stats['L']:.1f}</p>
        <p style='color:#DDD; margin:0'>- 노란기(b): {stats['b']:.1f}</p>
        <p style='color:#DDD; margin:0'>- 채도(S): {stats['S']:.1f}</p>
        """
        self.lbl_detail.setText(detail_html)