import json
<<<<<<< Updated upstream
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QLabel, QScrollArea, QSizePolicy, QPushButton,
                             QInputDialog, QMessageBox, QDialog, QFormLayout,
                             QSpinBox, QTextEdit, QDialogButtonBox,
=======
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QScrollArea, QSizePolicy, QPushButton, 
                             QInputDialog, QMessageBox, QDialog, QFormLayout, 
                             QSpinBox, QTextEdit, QDialogButtonBox, 
>>>>>>> Stashed changes
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QLinearGradient, QFont
import qtawesome as qta
from backend.database import DBManager

# [부위 한글 변환]
PART_MAP = {
<<<<<<< Updated upstream
    "chin": "턱", "lips": "입술",
=======
    "chin": "턱", "lips": "입술", 
>>>>>>> Stashed changes
    "right_cheek": "우측 볼", "left_cheek": "좌측 볼",
    "right_eye": "우측 눈가", "left_eye": "좌측 눈가",
    "forehead": "이마", "nose": "코", "glabella": "미간"
}

# [지표 한글 변환]
METRIC_MAP = {
<<<<<<< Updated upstream
    "Dry": "건조", "Oil": "유분",
=======
    "Dry": "건조", "Oil": "유분", 
>>>>>>> Stashed changes
    "Acne": "트러블", "Wrinkle": "주름", "Pigment": "색소"
}

# --- 1. 그래프 위젯 ---
<<<<<<< Updated upstream


=======
>>>>>>> Stashed changes
class SkinGraphWidget(QWidget):
    def __init__(self, data_points):
        super().__init__()
        self.setFixedHeight(250)
<<<<<<< Updated upstream
        self.data = data_points
        self.setStyleSheet(
            "background-color: #1E1E1E; border-radius: 12px; border: 1px solid #333;")
=======
        self.data = data_points 
        self.setStyleSheet("background-color: #1E1E1E; border-radius: 12px; border: 1px solid #333;")
>>>>>>> Stashed changes

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#1E1E1E"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

<<<<<<< Updated upstream
        if not self.data:
=======
        if not self.data: 
>>>>>>> Stashed changes
            painter.setPen(QColor("#666"))
            painter.drawText(self.rect(), Qt.AlignCenter, "데이터 부족")
            return

        w = self.width()
        h = self.height()
<<<<<<< Updated upstream
        padding_x = 40
        padding_y = 30
=======
        padding_x = 40; padding_y = 30
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        painter.drawLine(int(padding_x), int(
            y_50), int(w - padding_x), int(y_50))

        # 그래프 선
        if count > 1:
            pen = QPen(QColor("#FFD700"))
            pen.setWidth(3)
            painter.setPen(pen)
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i+1])
=======
        painter.drawLine(int(padding_x), int(y_50), int(w - padding_x), int(y_50))

        # 그래프 선
        if count > 1:
            pen = QPen(QColor("#FFD700")); pen.setWidth(3)
            painter.setPen(pen)
            for i in range(len(points) - 1): painter.drawLine(points[i], points[i+1])
>>>>>>> Stashed changes

        # 점 & 텍스트
        painter.setFont(QFont("Arial", 9))
        for i, p in enumerate(points):
<<<<<<< Updated upstream
            painter.setBrush(QColor("#FFD700"))
            painter.setPen(Qt.NoPen)
=======
            painter.setBrush(QColor("#FFD700")); painter.setPen(Qt.NoPen)
>>>>>>> Stashed changes
            painter.drawEllipse(p, 4, 4)
            painter.setPen(QColor("white"))
            painter.drawText(p.x() - 10, p.y() - 10, f"{self.data[i]}")

# --- 2. 제품 카드 ---
<<<<<<< Updated upstream


=======
>>>>>>> Stashed changes
class ProductCard(QFrame):
    def __init__(self, icon_name, name, desc):
        super().__init__()
        self.setFixedSize(140, 180)
<<<<<<< Updated upstream
        self.setStyleSheet(
            "background-color: #2A2A2A; border-radius: 10px; border: 1px solid #444;")
        layout = QVBoxLayout(self)
        icon = qta.icon(icon_name, color="#D4AF37")
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon.pixmap(64, 64))
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_name = QLabel(name)
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; border: none;")
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("color: #888; font-size: 11px; border: none;")
        lbl_desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_name)
        layout.addWidget(lbl_desc)

# --- 3. [NEW] 수정 팝업 다이얼로그 (다크 테마) ---


=======
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

# --- 3. [NEW] 수정 팝업 다이얼로그 ---
>>>>>>> Stashed changes
class EditRecordDialog(QDialog):
    def __init__(self, current_score, current_details, current_memo, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 700)
        self.old_pos = None

        self.setStyleSheet("""
            QWidget#MainFrame { background-color: #1E1E1E; border: 1px solid #444; border-radius: 15px; }
            QLabel { color: #E0E0E0; font-family: 'Segoe UI', sans-serif; }
            QLabel#Title { color: #FFD700; font-size: 18px; font-weight: bold; }
            QScrollBar:vertical { border: none; background: #2C2C2C; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #555; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QSpinBox { background-color: #2C2C2C; color: #FFD700; border: 1px solid #444; border-radius: 5px; padding: 8px; font-weight: bold; font-size: 14px; }
            QSpinBox::up-button, QSpinBox::down-button { width: 0px; }
            QTextEdit { background-color: #2C2C2C; color: #EEE; border: 1px solid #444; border-radius: 8px; padding: 10px; }
            QFrame.PartCard { background-color: #252525; border-radius: 10px; border: 1px solid #333; }
            QPushButton#BtnSave { background-color: #D4AF37; color: #121212; font-weight: bold; border-radius: 8px; font-size: 14px; }
            QPushButton#BtnSave:hover { background-color: #F4D03F; }
            QPushButton#BtnCancel { background-color: #333; color: #AAA; border: 1px solid #555; border-radius: 8px; font-size: 14px; }
            QPushButton#BtnCancel:hover { background-color: #444; color: white; }
            QPushButton#BtnClose { background-color: transparent; color: #888; border: none; font-size: 16px; font-weight: bold; }
            QPushButton#BtnClose:hover { color: #FF4444; }
        """)

<<<<<<< Updated upstream
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.main_frame.setGraphicsEffect(shadow)

        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)

        # 헤더
        header_layout = QHBoxLayout()
        lbl_title = QLabel("✨ 기록 수정하기")
        lbl_title.setObjectName("Title")
        btn_close_x = QPushButton("✕")
        btn_close_x.setObjectName("BtnClose")
        btn_close_x.clicked.connect(self.reject)
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_close_x)
        frame_layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #444;")
        frame_layout.addWidget(line)

        # 점수
        score_box = QFrame()
        score_box.setStyleSheet(
            "background-color: #2A2A2A; border-radius: 10px; padding: 10px;")
        score_layout = QHBoxLayout(score_box)
        lbl_s = QLabel("⭐ 종합 점수")
        lbl_s.setStyleSheet("font-size: 14px; color: #AAA;")
        self.spin_score = QSpinBox()
        self.spin_score.setRange(0, 100)
        self.spin_score.setValue(current_score)
        self.spin_score.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(lbl_s)
        score_layout.addStretch()
        score_layout.addWidget(self.spin_score)
        frame_layout.addWidget(score_box)

        # 상세
        lbl_detail_title = QLabel("상세 분석 데이터")
        lbl_detail_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        frame_layout.addWidget(lbl_detail_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll_content = QWidget()
        self.form_layout = QVBoxLayout(scroll_content)
        self.form_layout.setSpacing(10)
        self.form_layout.setContentsMargins(0, 0, 5, 0)
=======
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10)
        self.main_frame = QFrame(); self.main_frame.setObjectName("MainFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20); shadow.setXOffset(0); shadow.setYOffset(0); shadow.setColor(QColor(0, 0, 0, 150))
        self.main_frame.setGraphicsEffect(shadow)

        frame_layout = QVBoxLayout(self.main_frame); frame_layout.setContentsMargins(20, 20, 20, 20); frame_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        lbl_title = QLabel("✨ 기록 수정하기"); lbl_title.setObjectName("Title")
        btn_close_x = QPushButton("✕"); btn_close_x.setObjectName("BtnClose"); btn_close_x.clicked.connect(self.reject)
        header_layout.addWidget(lbl_title); header_layout.addStretch(); header_layout.addWidget(btn_close_x)
        frame_layout.addLayout(header_layout)

        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setStyleSheet("color: #444;"); frame_layout.addWidget(line)

        score_box = QFrame(); score_box.setStyleSheet("background-color: #2A2A2A; border-radius: 10px; padding: 10px;")
        score_layout = QHBoxLayout(score_box)
        lbl_s = QLabel("⭐ 종합 점수"); lbl_s.setStyleSheet("font-size: 14px; color: #AAA;")
        self.spin_score = QSpinBox(); self.spin_score.setRange(0, 100); self.spin_score.setValue(current_score); self.spin_score.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(lbl_s); score_layout.addStretch(); score_layout.addWidget(self.spin_score)
        frame_layout.addWidget(score_box)

        lbl_detail_title = QLabel("상세 분석 데이터"); lbl_detail_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        frame_layout.addWidget(lbl_detail_title)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("background: transparent; border: none;")
        scroll_content = QWidget(); self.form_layout = QVBoxLayout(scroll_content); self.form_layout.setSpacing(10); self.form_layout.setContentsMargins(0, 0, 5, 0)
>>>>>>> Stashed changes

        self.input_widgets = {}

        if not current_details:
<<<<<<< Updated upstream
            lbl_empty = QLabel("데이터가 없습니다.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #666; padding: 20px;")
=======
            lbl_empty = QLabel("데이터가 없습니다."); lbl_empty.setAlignment(Qt.AlignCenter); lbl_empty.setStyleSheet("color: #666; padding: 20px;")
>>>>>>> Stashed changes
            self.form_layout.addWidget(lbl_empty)
        else:
            for part_key, metrics in current_details.items():
                kor_part = PART_MAP.get(part_key, part_key)
<<<<<<< Updated upstream
                card = QFrame()
                card.setProperty("class", "PartCard")
                card_layout = QVBoxLayout(card)

                lbl_part = QLabel(f"{kor_part}")
                lbl_part.setStyleSheet(
                    "color: #D4AF37; font-weight: bold; font-size: 13px;")
                card_layout.addWidget(lbl_part)

                self.input_widgets[part_key] = {}

                if isinstance(metrics, dict):
                    grid = QHBoxLayout()
                    grid.setSpacing(10)
                    for i, (metric_key, value) in enumerate(metrics.items()):
                        kor_metric = METRIC_MAP.get(metric_key, metric_key)
                        item_layout = QVBoxLayout()
                        lbl_m = QLabel(kor_metric)
                        lbl_m.setStyleSheet("color: #888; font-size: 11px;")
                        spin = QSpinBox()
                        spin.setRange(0, 100)
                        spin.setValue(int(value))
                        item_layout.addWidget(lbl_m)
                        item_layout.addWidget(spin)
=======
                card = QFrame(); card.setProperty("class", "PartCard"); card_layout = QVBoxLayout(card)
                lbl_part = QLabel(f"{kor_part}"); lbl_part.setStyleSheet("color: #D4AF37; font-weight: bold; font-size: 13px;")
                card_layout.addWidget(lbl_part)
                self.input_widgets[part_key] = {}

                if isinstance(metrics, dict):
                    grid = QHBoxLayout(); grid.setSpacing(10)
                    for i, (metric_key, value) in enumerate(metrics.items()):
                        kor_metric = METRIC_MAP.get(metric_key, metric_key)
                        item_layout = QVBoxLayout()
                        lbl_m = QLabel(kor_metric); lbl_m.setStyleSheet("color: #888; font-size: 11px;")
                        spin = QSpinBox(); spin.setRange(0, 100); spin.setValue(int(value))
                        item_layout.addWidget(lbl_m); item_layout.addWidget(spin)
>>>>>>> Stashed changes
                        grid.addLayout(item_layout)
                        self.input_widgets[part_key][metric_key] = spin
                    card_layout.addLayout(grid)
                self.form_layout.addWidget(card)

<<<<<<< Updated upstream
        self.form_layout.addStretch()
        scroll.setWidget(scroll_content)
        frame_layout.addWidget(scroll)

        # 메모
        frame_layout.addWidget(QLabel("📝 메모"))
        self.text_memo = QTextEdit()
        self.text_memo.setPlainText(current_memo)
        self.text_memo.setFixedHeight(60)
        self.text_memo.setPlaceholderText("기록에 남길 메모를 입력하세요...")
        frame_layout.addWidget(self.text_memo)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("BtnCancel")
        btn_cancel.setFixedHeight(45)
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("저장하기")
        btn_save.setObjectName("BtnSave")
        btn_save.setFixedHeight(45)
        btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save, stretch=1)
        frame_layout.addLayout(btn_layout)
        layout.addWidget(self.main_frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

=======
        self.form_layout.addStretch(); scroll.setWidget(scroll_content); frame_layout.addWidget(scroll)

        frame_layout.addWidget(QLabel("📝 메모"))
        self.text_memo = QTextEdit(); self.text_memo.setPlainText(current_memo); self.text_memo.setFixedHeight(60); self.text_memo.setPlaceholderText("기록에 남길 메모를 입력하세요...")
        frame_layout.addWidget(self.text_memo)

        btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
        btn_cancel = QPushButton("취소"); btn_cancel.setObjectName("BtnCancel"); btn_cancel.setFixedHeight(45); btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("저장하기"); btn_save.setObjectName("BtnSave"); btn_save.setFixedHeight(45); btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cancel); btn_layout.addWidget(btn_save, stretch=1)
        frame_layout.addLayout(btn_layout); layout.addWidget(self.main_frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.old_pos = event.globalPos()
>>>>>>> Stashed changes
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
    def mouseReleaseEvent(self, event): self.old_pos = None

    def get_data(self):
        score = self.spin_score.value()
        memo = self.text_memo.toPlainText()
        details = {}
        for part_key, metrics_widgets in self.input_widgets.items():
            details[part_key] = {}
            for metric_key, spin_widget in metrics_widgets.items():
                details[part_key][metric_key] = spin_widget.value()
        return score, details, memo

# --- 4. 리포트 화면 ---
<<<<<<< Updated upstream


class ReportScreen(QWidget):
    def __init__(self):
        super().__init__()
        # self.db = DBManager() # [삭제] 충돌 방지를 위해 제거함
=======
class ReportScreen(QWidget):
    def __init__(self):
        super().__init__()
>>>>>>> Stashed changes
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
<<<<<<< Updated upstream
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
        # 화면 초기화
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.spacerItem():
                self.content_layout.removeItem(item)

        # [수정] self.db가 아니라 그냥 db를 씁니다!
        db = DBManager()
        try:
            records = db.fetch_recent_records(limit=10)  # <-- 여기! self.db 아님
        except Exception as e:
            print(f"DB Error: {e}")
            records = []
        finally:
            db.close()

        # 그래프
        lbl_chart = QLabel("📈 Skin Score Trend")
        lbl_chart.setStyleSheet(
            "color: #D4AF37; font-size: 18px; font-weight: bold;")
        scores = [r['score'] for r in reversed(records)] if records else [0]
        if len(scores) < 2:
            scores = [0] + scores
        self.content_layout.addWidget(lbl_chart)
        self.content_layout.addWidget(SkinGraphWidget(scores))

        # 제품
        lbl_rec = QLabel("🛍️ Recommended Products")
        lbl_rec.setStyleSheet(
            "color: #D4AF37; font-size: 18px; font-weight: bold; margin-top: 10px;")
        prod_scroll = QScrollArea()
        prod_scroll.setFixedHeight(210)
        prod_scroll.setStyleSheet("background: transparent; border: none;")
        prod_content = QWidget()
        prod_layout = QHBoxLayout(prod_content)
        prod_layout.addWidget(ProductCard(
            'fa5s.tint', 'Moisture Cream', 'Hydration'))
        prod_layout.addWidget(ProductCard(
            'fa5s.sun', 'Sun Shield', 'Protection'))
        prod_layout.addWidget(ProductCard(
            'fa5s.soap', 'Gentle Foam', 'Cleansing'))
        prod_layout.addStretch()
        prod_scroll.setWidget(prod_content)
        self.content_layout.addWidget(lbl_rec)
        self.content_layout.addWidget(prod_scroll)

        # 상세 기록
        lbl_hist = QLabel("📋 Recent History (Edit/Delete)")
        lbl_hist.setStyleSheet(
            "color: #D4AF37; font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.content_layout.addWidget(lbl_hist)

        if not records:
            lbl = QLabel("기록이 없습니다. 홈 화면에서 진단을 시작해보세요!")
            lbl.setStyleSheet("color: #666; padding: 20px; font-size: 14px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl)
        else:
            for rec in records:
                card = QFrame()
                card.setStyleSheet(
                    "background-color: #222; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #333;")
                card_layout = QVBoxLayout(card)

                # 헤더 Row
                top_row = QHBoxLayout()
                date_str = str(rec['time']).split('.')[0]
                lbl_date = QLabel(date_str)
                lbl_date.setStyleSheet(
                    "color: #AAA; font-size: 14px; border: none; background: transparent;")

                lbl_score = QLabel(f"{rec['score']}점")
                lbl_score.setStyleSheet(
                    "color: #FFD700; font-size: 18px; font-weight: bold; border: none; background: transparent;")

                # 수정 버튼
                btn_edit = QPushButton("✏️ Edit")
                btn_edit.setFixedSize(70, 30)
                btn_edit.setStyleSheet(
                    "QPushButton { background-color: #00a8ff; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #0097e6; }")
                btn_edit.clicked.connect(
                    lambda _, r=rec: self.edit_record_popup(r))

                # 삭제 버튼
                btn_delete = QPushButton("🗑️ Del")
                btn_delete.setFixedSize(70, 30)
                btn_delete.setStyleSheet(
                    "QPushButton { background-color: #e84118; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #c23616; }")
                btn_delete.clicked.connect(
                    lambda _, rid=rec['id']: self.delete_record(rid))

                top_row.addWidget(lbl_date)
                top_row.addStretch()
                top_row.addWidget(lbl_score)
                top_row.addSpacing(10)
                top_row.addWidget(btn_edit)
                top_row.addWidget(btn_delete)
                card_layout.addLayout(top_row)

                # 메모
                current_memo = rec.get('memo', '')
                if current_memo:
                    lbl_memo = QLabel(f"📝 {current_memo}")
                    lbl_memo.setStyleSheet(
                        "color: #00d2ff; font-size: 13px; margin: 5px 0; border: none; background: transparent;")
                    card_layout.addWidget(lbl_memo)

                # 상세 내용
                details = rec['details']
                if details:
                    detail_html = ""
                    for eng, scores in details.items():
                        kor_part = PART_MAP.get(eng, eng)
=======
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget(); self.content_layout = QVBoxLayout(self.scroll_content); self.content_layout.setSpacing(20)
        self.scroll.setWidget(self.scroll_content); self.main_layout.addWidget(self.scroll)
        self.refresh_data()

    # [수정] user_id 인자 받음 (기본값 0)
    def refresh_data(self, user_id=0):
        for i in reversed(range(self.content_layout.count())): 
            item = self.content_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            elif item.spacerItem(): self.content_layout.removeItem(item)

        db = DBManager()
        try:
            # [수정] user_id 전달
            records = db.fetch_recent_records(limit=10, user_id=user_id) 
        except Exception as e:
            print(f"DB Error: {e}"); records = []
        finally: db.close()

        lbl_chart = QLabel("📈 Skin Score Trend"); lbl_chart.setStyleSheet("color: #D4AF37; font-size: 18px; font-weight: bold;")
        scores = [r['score'] for r in reversed(records)] if records else [0]
        if len(scores) < 2: scores = [0] + scores
        self.content_layout.addWidget(lbl_chart); self.content_layout.addWidget(SkinGraphWidget(scores))

        lbl_rec = QLabel("🛍️ Recommended Products"); lbl_rec.setStyleSheet("color: #D4AF37; font-size: 18px; font-weight: bold; margin-top: 10px;")
        prod_scroll = QScrollArea(); prod_scroll.setFixedHeight(210); prod_scroll.setStyleSheet("background: transparent; border: none;")
        prod_content = QWidget(); prod_layout = QHBoxLayout(prod_content)
        prod_layout.addWidget(ProductCard('fa5s.tint', 'Moisture Cream', 'Hydration')); prod_layout.addWidget(ProductCard('fa5s.sun', 'Sun Shield', 'Protection')); prod_layout.addWidget(ProductCard('fa5s.soap', 'Gentle Foam', 'Cleansing')); prod_layout.addStretch()
        prod_scroll.setWidget(prod_content); self.content_layout.addWidget(lbl_rec); self.content_layout.addWidget(prod_scroll)

        lbl_hist = QLabel("📋 Recent History (Edit/Delete)"); lbl_hist.setStyleSheet("color: #D4AF37; font-size: 18px; font-weight: bold; margin-top: 10px;")
        self.content_layout.addWidget(lbl_hist)

        if not records:
            lbl = QLabel("기록이 없습니다. 홈 화면에서 진단을 시작해보세요!"); lbl.setStyleSheet("color: #666; padding: 20px; font-size: 14px;"); lbl.setAlignment(Qt.AlignCenter); self.content_layout.addWidget(lbl)
        else:
            for rec in records:
                card = QFrame(); card.setStyleSheet("background-color: #222; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #333;")
                card_layout = QVBoxLayout(card)

                top_row = QHBoxLayout()
                date_str = str(rec['time']).split('.')[0]
                lbl_date = QLabel(date_str); lbl_date.setStyleSheet("color: #AAA; font-size: 14px; border: none; background: transparent;")
                lbl_score = QLabel(f"{rec['score']}점"); lbl_score.setStyleSheet("color: #FFD700; font-size: 18px; font-weight: bold; border: none; background: transparent;")
                
                # 수정/삭제 버튼
                btn_edit = QPushButton("✏️ Edit"); btn_edit.setFixedSize(70, 30); btn_edit.setStyleSheet("QPushButton { background-color: #00a8ff; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #0097e6; }")
                btn_edit.clicked.connect(lambda _, r=rec: self.edit_record_popup(r))
                btn_delete = QPushButton("🗑️ Del"); btn_delete.setFixedSize(70, 30); btn_delete.setStyleSheet("QPushButton { background-color: #e84118; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #c23616; }")
                btn_delete.clicked.connect(lambda _, rid=rec['id']: self.delete_record(rid))

                top_row.addWidget(lbl_date); top_row.addStretch(); top_row.addWidget(lbl_score); top_row.addSpacing(10); top_row.addWidget(btn_edit); top_row.addWidget(btn_delete)
                card_layout.addLayout(top_row)

                current_memo = rec.get('memo', '')
                if current_memo:
                    lbl_memo = QLabel(f"📝 {current_memo}"); lbl_memo.setStyleSheet("color: #00d2ff; font-size: 13px; margin: 5px 0; border: none; background: transparent;")
                    card_layout.addWidget(lbl_memo)

                details = rec['details']
                if details:
                    detail_html = ""
                    for eng_part, scores in details.items():
                        kor_part = PART_MAP.get(eng_part, eng_part)
>>>>>>> Stashed changes
                        metrics_str = ""
                        if isinstance(scores, dict):
                            for m_key, m_val in scores.items():
                                m_kor = METRIC_MAP.get(m_key, m_key)
                                color = "#FF6666" if m_val > 60 else "#AAAAAA"
                                metrics_str += f"<span style='color:{color};'>{m_kor} {m_val}</span>  "
                        detail_html += f"<p style='margin: 2px 0;'><b style='color:#DDD;'>{kor_part}</b> : {metrics_str}</p>"
<<<<<<< Updated upstream
                    lbl_detail = QLabel(detail_html)
                    lbl_detail.setStyleSheet(
                        "font-size: 12px; border: none; background: transparent;")
=======
                    lbl_detail = QLabel(detail_html); lbl_detail.setStyleSheet("font-size: 12px; border: none; background: transparent;")
>>>>>>> Stashed changes
                    card_layout.addWidget(lbl_detail)

                self.content_layout.addWidget(card)
        self.content_layout.addStretch()

<<<<<<< Updated upstream
    # --- [팝업] 수정 핸들러 ---
=======
>>>>>>> Stashed changes
    def edit_record_popup(self, record_data):
        r_id = record_data['id']
        curr_score = record_data.get('score', 0)
        curr_details = record_data.get('details', {})
<<<<<<< Updated upstream
        curr_memo = record_data.get('memo', '')
=======
        curr_memo = record_data.get('memo', '') # 메모 가져오기
>>>>>>> Stashed changes

        dialog = EditRecordDialog(curr_score, curr_details, curr_memo, self)

        if dialog.exec_() == QDialog.Accepted:
            new_score, new_details, new_memo = dialog.get_data()
<<<<<<< Updated upstream

=======
>>>>>>> Stashed changes
            db = DBManager()
            try:
                db.update_skin_data(r_id, new_score, new_details)
                db.update_skin_memo(r_id, new_memo)
<<<<<<< Updated upstream
            finally:
                db.close()

            self.refresh_data()
            QMessageBox.information(self, "성공", "수정이 완료되었습니다!")

    # --- [팝업] 삭제 핸들러 ---
    def delete_record(self, record_id):
        reply = QMessageBox.question(self, '삭제 확인', '정말 삭제하시겠습니까?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            db = DBManager()
            try:
                db.delete_skin_record(record_id)
            finally:
                db.close()

            self.refresh_data()
=======
            finally: db.close()
            # [수정] refresh할 때 user_id 다시 넘기기 (여기선 UI 갱신만 하므로 인자 없이 호출하면 기본값 0 사용됨 -> Main Window에서 호출해줘야 정확)
            # 하지만 ReportScreen 안에는 current_user_id가 없으므로, 일단 기본 리프레시
            self.refresh_data() 
            QMessageBox.information(self, "성공", "수정이 완료되었습니다!")

    def delete_record(self, record_id):
        reply = QMessageBox.question(self, '삭제 확인', '정말 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            db = DBManager()
            try: db.delete_skin_record(record_id)
            finally: db.close()
            self.refresh_data()
>>>>>>> Stashed changes
