from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QLinearGradient, QFont
import qtawesome as qta
from backend.database import DBManager

# [부위 한글 변환]
PART_MAP = {
    "chin": "턱", "lips": "입술", 
    "right_cheek": "우측 볼", "left_cheek": "좌측 볼",
    "right_eye": "우측 눈가", "left_eye": "좌측 눈가",
    "forehead": "이마", "nose": "코", "glabella": "미간"
}

# [지표 한글 변환] - NEW
METRIC_MAP = {
    "Dry": "건조", "Oil": "유분", 
    "Acne": "트러블", "Wrinkle": "주름", "Pigment": "색소"
}

# --- 1. 그래프 위젯 (기존 유지) ---
class SkinGraphWidget(QWidget):
    def __init__(self, data_points):
        super().__init__()
        self.setFixedHeight(250)
        self.data = data_points 
        self.setStyleSheet("background-color: #1E1E1E; border-radius: 12px; border: 1px solid #333;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#1E1E1E"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

        if not self.data: 
            painter.setPen(QColor("#666"))
            painter.drawText(self.rect(), Qt.AlignCenter, "데이터 부족")
            return

        w = self.width()
        h = self.height()
        padding_x = 40; padding_y = 30
        count = len(self.data)
        step_x = (w - 2 * padding_x) / (count - 1) if count > 1 else 0

        points = []
        for i, score in enumerate(self.data):
            x = padding_x + i * step_x
            y = (h - padding_y) - (score / 100.0 * (h - 2 * padding_y))
            points.append(QPoint(int(x), int(y)))

        # 가이드라인
        painter.setPen(QPen(QColor("#333"), 1, Qt.DashLine))
        y_50 = (h - padding_y) - (0.5 * (h - 2 * padding_y))
        painter.drawLine(int(padding_x), int(y_50), int(w - padding_x), int(y_50))

        # 그래프 선
        if count > 1:
            pen = QPen(QColor("#FFD700")); pen.setWidth(3)
            painter.setPen(pen)
            for i in range(len(points) - 1): painter.drawLine(points[i], points[i+1])

        # 점 & 텍스트
        painter.setFont(QFont("Arial", 9))
        for i, p in enumerate(points):
            painter.setBrush(QColor("#FFD700")); painter.setPen(Qt.NoPen)
            painter.drawEllipse(p, 4, 4)
            painter.setPen(QColor("white"))
            painter.drawText(p.x() - 10, p.y() - 10, f"{self.data[i]}")

# --- 2. 제품 카드 (기존 유지) ---
class ProductCard(QFrame):
    def __init__(self, icon_name, name, desc):
        super().__init__()
        self.setFixedSize(140, 180)
        self.setStyleSheet("background-color: #2A2A2A; border-radius: 10px; border: 1px solid #444;")
        layout = QVBoxLayout(self)
        icon = qta.icon(icon_name, color="#D4AF37")
        lbl_icon = QLabel(); lbl_icon.setPixmap(icon.pixmap(64, 64)); lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_name = QLabel(name); lbl_name.setWordWrap(True); 
        lbl_name.setStyleSheet("color: white; font-weight: bold; font-size: 13px; border: none;")
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_desc = QLabel(desc); lbl_desc.setStyleSheet("color: #888; font-size: 11px; border: none;")
        lbl_desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_icon); layout.addWidget(lbl_name); layout.addWidget(lbl_desc)

# --- 3. 리포트 화면 (수정됨) ---
class ReportScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget()
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setSpacing(20)
        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll)
        self.refresh_data()

    def refresh_data(self):
        # 위젯 초기화
        for i in reversed(range(self.content_layout.count())): 
            item = self.content_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            elif item.spacerItem(): self.content_layout.removeItem(item)

        records = self.db.fetch_recent_records(limit=7)
        
        # 그래프 섹션
        lbl_chart = QLabel("📈 Skin Score Trend")
        lbl_chart.setStyleSheet("color: #D4AF37; font-size: 18px; font-weight: bold;")
        scores = [r['score'] for r in reversed(records)] if records else [0]
        if len(scores) < 2: scores = [0] + scores
        self.content_layout.addWidget(lbl_chart)
        self.content_layout.addWidget(SkinGraphWidget(scores))

        # 추천 제품 섹션
        lbl_rec = QLabel("🛍️ Recommended Products")
        lbl_rec.setStyleSheet("color: #D4AF37; font-size: 18px; font-weight: bold; margin-top: 10px;")
        prod_scroll = QScrollArea(); prod_scroll.setFixedHeight(210); prod_scroll.setStyleSheet("background: transparent; border: none;")
        prod_content = QWidget(); prod_layout = QHBoxLayout(prod_content)
        prod_layout.addWidget(ProductCard('fa5s.tint', 'Moisture Cream', 'Hydration'))
        prod_layout.addWidget(ProductCard('fa5s.sun', 'Sun Shield', 'Protection'))
        prod_layout.addWidget(ProductCard('fa5s.soap', 'Gentle Foam', 'Cleansing'))
        prod_layout.addStretch()
        prod_scroll.setWidget(prod_content)
        self.content_layout.addWidget(lbl_rec)
        self.content_layout.addWidget(prod_scroll)

        # 상세 기록 섹션
        lbl_hist = QLabel("📋 Recent History")
        lbl_hist.setStyleSheet("color: #D4AF37; font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.content_layout.addWidget(lbl_hist)

        if not records:
            lbl = QLabel("기록 없음"); lbl.setStyleSheet("color: #666; padding: 20px;"); lbl.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl)
        else:
            for rec in records:
                card = QFrame()
                card.setStyleSheet("background-color: #222; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #333;")
                card_layout = QVBoxLayout(card)
                
                # [헤더] 날짜 | 점수
                top_row = QHBoxLayout()
                date_str = str(rec['time']).split('.')[0]
                lbl_date = QLabel(date_str); lbl_date.setStyleSheet("color: #AAA; font-size: 14px; border: none;")
                lbl_score = QLabel(f"{rec['score']}점"); lbl_score.setStyleSheet("color: #FFD700; font-size: 18px; font-weight: bold; border: none;")
                top_row.addWidget(lbl_date); top_row.addStretch(); top_row.addWidget(lbl_score)
                card_layout.addLayout(top_row)
                
                # [본문] 모든 상세 내역 표시 (HTML)
                details = rec['details']
                if details:
                    detail_html = ""
                    for eng, scores in details.items():
                        kor_part = PART_MAP.get(eng, eng)
                        
                        # 각 부위별 모든 지표 나열
                        metrics_str = ""
                        if isinstance(scores, dict):
                            # scores = {'Oil': 50, 'Dry': 20, ...}
                            for m_key, m_val in scores.items():
                                m_kor = METRIC_MAP.get(m_key, m_key) # Dry -> 건조
                                # 수치가 높을수록 붉은색, 낮으면 회색 (간단 시각화)
                                color = "#FF6666" if m_val > 60 else "#AAAAAA"
                                metrics_str += f"<span style='color:{color};'>{m_kor} {m_val}</span>  "
                        
                        # 한 줄 생성: "턱: 건조 20 유분 50 ..."
                        detail_html += f"<p style='margin: 2px 0;'><b style='color:#DDD;'>{kor_part}</b> : {metrics_str}</p>"
                    
                    lbl_detail = QLabel(detail_html)
                    lbl_detail.setStyleSheet("font-size: 12px; border: none;")
                    card_layout.addWidget(lbl_detail)
                else:
                    card_layout.addWidget(QLabel("상세 데이터 없음"))
                
                self.content_layout.addWidget(card)

        self.content_layout.addStretch()