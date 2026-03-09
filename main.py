#!/usr/bin/env python3
"""10 CHAMBERS AB — THE HEIST LEDGER v.1"""
import sys, os, random, math
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QScrollArea, QFrame,
    QGridLayout, QSizePolicy, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPixmap, QPainter, QPen, QBrush, QIcon,
    QRadialGradient, QFontDatabase)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as RC
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    HRFlowable)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

APP_NAME = "10 CHAMBERS AB — THE HEIST LEDGER v.1"
RED      = "#E8352A"
RED_DARK = "#C02A20"
BG       = "#272727"

def asset_path(name):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'assets', name)

def load_px(name, w=None, h=None):
    px = QPixmap(asset_path(name))
    if not px.isNull() and w and h:
        return px.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    return px

# ─── Stylesheet ───────────────────────────────────────────────────────────────
STYLE = """
* { font-family: Arial, sans-serif; }

/* ── Base ── */
QMainWindow          { background: #272727; }
QWidget#root         { background: #272727; }
QWidget#content_area { background: #272727; }
QWidget#setup_screen { background: #272727; }
QWidget#scroll_inner { background: #272727; }

/* ── Scroll ── */
QScrollArea          { background: #272727; border: none; }
QScrollArea > QWidget > QWidget { background: #272727; }
QScrollBar:vertical  { background: #2E2E2E; width: 7px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #505050; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── Inputs (inside white cards → dark text on light bg) ── */
QLineEdit {
    background: #F5F5F5; border: 1.5px solid #D8D8D8; border-radius: 5px;
    color: #1A1A1A; padding: 7px 10px; font-size: 13px;
    selection-background-color: #E8352A; selection-color: white;
}
QLineEdit:focus  { border-color: #E8352A; background: #FFFFFF; }
QLineEdit:disabled { background: #ECECEC; color: #999; border-color: #E0E0E0; }
QLineEdit#winner_field {
    background: #E6FFEE; color: #007030; border-color: #00AA44; font-weight: bold;
}
QLineEdit#elim_field { background: #FFF0F0; color: #BB4444; border-color: #FFCCCC; }

QSpinBox {
    background: #F5F5F5; border: 1.5px solid #D8D8D8; border-radius: 5px;
    color: #1A1A1A; padding: 5px 8px; font-size: 13px; min-width: 70px;
}
QSpinBox:focus   { border-color: #E8352A; }
QSpinBox:disabled { background: #ECECEC; color: #999; }
QSpinBox::up-button, QSpinBox::down-button {
    background: #E5E5E5; border: none; width: 20px; border-radius: 2px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #D5D5D5; }

/* ── Buttons ── */
QPushButton {
    background: #333333; border: 1px solid #444444; border-radius: 5px;
    color: #CCCCCC; padding: 7px 16px; font-size: 12px; font-weight: bold;
    letter-spacing: 1px;
}
QPushButton:hover   { background: #3D3D3D; border-color: #606060; color: #FFFFFF; }
QPushButton:pressed { background: #282828; }
QPushButton:disabled { background: #2A2A2A; color: #505050; border-color: #333333; }

QPushButton#btn_red {
    background: #E8352A; border: 2px solid #C02A20; color: white;
    padding: 8px 22px; font-size: 13px; letter-spacing: 2px;
}
QPushButton#btn_red:hover { background: #C02A20; }

QPushButton#btn_lock {
    background: #1A1A1A; border: 2px solid #E8352A; color: #E8352A;
    padding: 13px 40px; font-size: 15px; letter-spacing: 3px;
    min-width: 340px; border-radius: 5px; font-weight: bold;
}
QPushButton#btn_lock:hover { background: #221010; }
QPushButton#btn_lock[locked="true"] {
    background: #E8352A; border-color: #C02A20; color: white;
}
QPushButton#btn_lock[locked="true"]:hover { background: #C02A20; }

QPushButton#btn_draw {
    background: #242424; border: 1.5px solid #3A3A3A; color: #555;
    padding: 8px 18px; min-width: 200px; letter-spacing: 1px;
}
QPushButton#btn_draw_active {
    background: #E8352A; border: 2px solid #C02A20; color: white;
    padding: 8px 18px; min-width: 200px; font-size: 13px; font-weight: bold;
    letter-spacing: 1px;
}
QPushButton#btn_draw_active:hover { background: #C02A20; }
QPushButton#btn_draw_done {
    background: #1A2035; border: 1.5px solid #334; color: #5577CC;
    padding: 8px 18px; min-width: 200px; letter-spacing: 1px;
}

/* ── Topic cards (white on dark bg) ── */
QFrame#card {
    background: white; border: none; border-radius: 8px;
}
QFrame#card_done {
    background: #F0F3FF; border: 2px solid #AABBEE; border-radius: 8px;
}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# DRAW ANIMATION
# ═══════════════════════════════════════════════════════════════════════════════
_CODE_CHARS = list("01100101001011{}[];=></#!?%*+~^&|0110101::")


class CodeStream:
    def __init__(self, x, h):
        n = random.randint(6, 20)
        self.x = x; self.h = h
        self.chars = [random.choice(_CODE_CHARS) for _ in range(n)]
        self.y = random.uniform(-h * 0.9, h * 0.4)
        self.speed = random.uniform(1.8, 5.0)
        self.alpha = random.randint(55, 175)
        self.char_h = 20

    def update(self, mult=1.0):
        self.y += self.speed * mult
        if random.random() < 0.07:
            self.chars[random.randrange(len(self.chars))] = random.choice(_CODE_CHARS)
        if self.y > self.h + self.char_h * len(self.chars):
            self.y = random.uniform(-self.h * 0.8, -40)

    def draw(self, painter):
        font = QFont("Courier New", 13)
        font.setBold(True)
        painter.setFont(font)
        n = len(self.chars)
        for i, ch in enumerate(self.chars):
            cy = int(self.y) + i * self.char_h
            if cy < -20 or cy > self.h + 20:
                continue
            extra = 90 if i == n - 1 else (40 if i == n - 2 else 0)
            painter.setPen(QPen(QColor(255, 255, 255, min(255, self.alpha + extra))))
            painter.drawText(self.x, cy, ch)


class DrawAnimation(QWidget):
    CODE_RAIN, FAST, REVEAL = 0, 1, 2

    def __init__(self, topic_title, contestants, parent=None):
        super().__init__(parent)
        self.topic_title = topic_title
        self.contestants = contestants[:]
        random.shuffle(self.contestants)
        self.winner = random.choice(self.contestants)
        self.phase = self.CODE_RAIN
        self.elapsed = 0
        self.streams = []

        # Name pop (CODE_RAIN) — 1 name every 500ms at random position
        self.name_list = self.contestants[:]
        random.shuffle(self.name_list)
        self.name_idx = 0
        self.current_name = self.name_list[0] if self.name_list else ""
        self.name_x = 0.5; self.name_y = 0.5
        self.last_name_ms = 0

        # Fast phase
        self.fast_idx = 0
        self.fast_name = self.contestants[0] if self.contestants else ""
        self.last_fast_ms = 0
        self.fast_interval = 100

        # Reveal
        self.rev_alpha = 0; self.rev_scale = 0.2; self.shown_btns = False

        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

        self.btn_ok = QPushButton("✓  FINISHED", self)
        self.btn_ok.setFixedSize(190, 52)
        self.btn_ok.setVisible(False)
        self.btn_ok.setStyleSheet(
            "QPushButton{background:#007A30;border:2px solid #005A22;color:white;"
            "font-size:14px;font-weight:bold;border-radius:5px;letter-spacing:2px;}"
            "QPushButton:hover{background:#006226;}")

        self.btn_redo = QPushButton("↺  RE-SHUFFLE", self)
        self.btn_redo.setFixedSize(190, 52)
        self.btn_redo.setVisible(False)
        self.btn_redo.setStyleSheet(
            f"QPushButton{{background:white;border:2px solid {RED};color:{RED};"
            "font-size:14px;font-weight:bold;border-radius:5px;letter-spacing:2px;}}"
            "QPushButton:hover{background:#FFF5F5;}")

    def _init_streams(self, w, h):
        col_w = 22
        self.streams = [CodeStream(i * col_w + 6, h) for i in range(max(1, w // col_w))]

    def _rand_name_pos(self):
        self.name_x = random.uniform(0.12, 0.88)
        self.name_y = random.uniform(0.38, 0.72)

    def start(self):
        w, h = self.width(), self.height()
        self._init_streams(w, h)
        self.elapsed = 0; self.phase = self.CODE_RAIN
        self.last_name_ms = 0; self.name_idx = 0
        self.name_list = self.contestants[:]
        random.shuffle(self.name_list)
        self.current_name = self.name_list[0] if self.name_list else ""
        self._rand_name_pos()
        self.timer.start()

    def reshuffle(self):
        self.winner = random.choice(self.contestants)
        self.btn_ok.setVisible(False); self.btn_redo.setVisible(False)
        self.shown_btns = False; self.rev_alpha = 0; self.rev_scale = 0.2
        w, h = self.width(), self.height()
        self._init_streams(w, h)
        self.elapsed = 0; self.phase = self.CODE_RAIN
        self.last_name_ms = 0; self.name_idx = 0
        self.name_list = self.contestants[:]
        random.shuffle(self.name_list)
        self.current_name = self.name_list[0] if self.name_list else ""
        self._rand_name_pos()
        self.timer.start()

    def _tick(self):
        self.elapsed += 16
        if self.phase == self.CODE_RAIN:
            for s in self.streams: s.update(1.0)
            if self.elapsed - self.last_name_ms >= 500:
                self.name_idx = (self.name_idx + 1) % len(self.name_list)
                self.current_name = self.name_list[self.name_idx]
                self._rand_name_pos()
                self.last_name_ms = self.elapsed
            if self.elapsed >= 6000:
                self.phase = self.FAST; self.elapsed = 0
                self.fast_idx = 0; self.fast_name = self.contestants[0]
                self.last_fast_ms = 0; self.fast_interval = 100
        elif self.phase == self.FAST:
            t = min(1.0, self.elapsed / 1500.0)
            self.fast_interval = max(16, int(100 - t * 84))
            for s in self.streams: s.update(2.0 + t * 5)
            if self.elapsed - self.last_fast_ms >= self.fast_interval:
                self.fast_idx = (self.fast_idx + 1) % len(self.contestants)
                self.fast_name = self.contestants[self.fast_idx]
                self.last_fast_ms = self.elapsed
            if self.elapsed >= 1500:
                self.timer.stop(); self.phase = self.REVEAL
                QTimer.singleShot(16, self._rev_tick)
        self.update()

    def _rev_tick(self):
        self.rev_alpha = min(255, self.rev_alpha + 8)
        self.rev_scale = min(1.0, self.rev_scale + 0.04)
        self.update()
        if self.rev_alpha < 255 or self.rev_scale < 1.0:
            QTimer.singleShot(16, self._rev_tick)
        elif not self.shown_btns:
            self.shown_btns = True; self._place_btns()

    def _place_btns(self):
        cx, cy = self.width() // 2, self.height() // 2 + 140
        self.btn_ok.move(cx - 200, cy); self.btn_redo.move(cx + 10, cy)
        self.btn_ok.setVisible(True); self.btn_redo.setVisible(True)

    def _draw_topic_bar(self, p, w):
        bar_h = 58
        p.fillRect(0, 0, w, bar_h, QColor(0, 0, 0, 215))
        f_lbl = QFont("Arial", 9); f_lbl.setBold(True)
        f_lbl.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        p.setFont(f_lbl); p.setPen(QPen(QColor(255, 255, 255, 110)))
        lbl = "DRAWING NOW"; lw = p.fontMetrics().horizontalAdvance(lbl)
        p.drawText(w // 2 - lw // 2, 17, lbl)
        f_title = QFont("Impact", 19)
        f_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(f_title); p.setPen(QPen(QColor(255, 255, 255)))
        title = self.topic_title
        tw = p.fontMetrics().horizontalAdvance(title)
        while tw > w - 80 and len(title) > 4:
            title = title[:-1]
            tw = p.fontMetrics().horizontalAdvance(title + "…")
        if title != self.topic_title: title += "…"
        tw = p.fontMetrics().horizontalAdvance(title)
        p.drawText(w // 2 - tw // 2, 46, title)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor("#E8352A"))

        if self.phase in (self.CODE_RAIN, self.FAST):
            for s in self.streams: s.draw(p)

            if self.phase == self.CODE_RAIN:
                # Black bold name at random pos every 500ms
                f_name = QFont("Impact", 62)
                p.setFont(f_name); fm = p.fontMetrics()
                nw = fm.horizontalAdvance(self.current_name)
                nx = int(self.name_x * w); ny = int(self.name_y * h)
                nx = max(nw // 2 + 28, min(nx, w - nw // 2 - 28))
                ny = max(fm.ascent() + 70, min(ny, h - 30))
                p.setPen(QPen(QColor(0, 0, 0, 55)))
                p.drawText(nx - nw // 2 + 3, ny + 3, self.current_name)
                p.setPen(QPen(QColor(0, 0, 0)))
                p.drawText(nx - nw // 2, ny, self.current_name)

            else:  # FAST
                t = min(1.0, self.elapsed / 1500.0)
                f_fast = QFont("Impact", int(58 + t * 26))
                p.setFont(f_fast); fm = p.fontMetrics()
                nw = fm.horizontalAdvance(self.fast_name)
                cy = h // 2 + fm.ascent() // 3
                p.setPen(QPen(QColor(0, 0, 0, 50)))
                p.drawText(w // 2 - nw // 2 + 3, cy + 3, self.fast_name)
                p.setPen(QPen(QColor(0, 0, 0)))
                p.drawText(w // 2 - nw // 2, cy, self.fast_name)
                f_sub = QFont("Arial", 11)
                f_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
                p.setFont(f_sub); p.setPen(QPen(QColor(255, 255, 255, 160)))
                sub = "SELECTING WINNER..."; sw = p.fontMetrics().horizontalAdvance(sub)
                p.drawText(w // 2 - sw // 2, cy - 85, sub)

        elif self.phase == self.REVEAL:
            a = self.rev_alpha; s = self.rev_scale
            cx, cy = w // 2, h // 2
            g = QRadialGradient(QPointF(cx, cy), 320)
            g.setColorAt(0, QColor(255, 255, 255, int(a * 0.20)))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            p.fillRect(0, 0, w, h, g)
            fc = QFont("Impact", int(28 * s))
            fc.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
            p.setFont(fc); p.setPen(QPen(QColor(255, 255, 255, a)))
            fm = p.fontMetrics(); txt = "— CONGRATULATIONS —"
            tw = fm.horizontalAdvance(txt)
            p.drawText(cx - tw // 2, cy - 55, txt)
            fw = QFont("Impact", int(78 * s))
            p.setFont(fw); fm = p.fontMetrics()
            tw = fm.horizontalAdvance(self.winner)
            base_y = cy + fm.ascent() // 3 + 10
            p.setPen(QPen(QColor(0, 0, 0, int(a * 0.4))))
            p.drawText(cx - tw // 2 + 4, base_y + 4, self.winner)
            p.setPen(QPen(QColor(255, 255, 255, a)))
            p.drawText(cx - tw // 2, base_y, self.winner)
            if a > 160:
                fs = QFont("Arial", 13)
                fs.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
                p.setFont(fs)
                p.setPen(QPen(QColor(255, 255, 255, min(255, int((a - 160) * 3)))))
                sub = "IS THE WINNER"; tws = p.fontMetrics().horizontalAdvance(sub)
                p.drawText(cx - tws // 2, base_y + 55, sub)

        # Topic bar always on top
        self._draw_topic_bar(p, w)
        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.shown_btns: self._place_btns()
        if self.phase != self.REVEAL and self.streams:
            self._init_streams(self.width(), self.height())


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER  (solid red bar)
# ═══════════════════════════════════════════════════════════════════════════════
class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(78)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 0, 22, 0)

        logo = QLabel()
        px = load_px("logo_text.png", 130, 56)
        if not px.isNull(): logo.setPixmap(px)
        logo.setStyleSheet("background:transparent;")
        lay.addWidget(logo)
        lay.addSpacing(20)

        col = QVBoxLayout(); col.setSpacing(2)
        t1 = QLabel("10 CHAMBERS AB")
        t1.setStyleSheet("color:white;font-size:22px;font-weight:bold;"
                         "font-family:Impact,Arial Black,sans-serif;"
                         "letter-spacing:3px;background:transparent;")
        t2 = QLabel("THE HEIST LEDGER  v.1  —  RANDOM DRAW SYSTEM")
        t2.setStyleSheet("color:rgba(255,255,255,0.60);font-size:10px;"
                         "letter-spacing:4px;background:transparent;")
        col.addWidget(t1); col.addWidget(t2)
        lay.addLayout(col)
        lay.addStretch()

        # Est badge
        b1 = QLabel()
        px2 = load_px("est2015_red.png", 90, 50)
        if not px2.isNull(): b1.setPixmap(px2)
        b1.setStyleSheet("background:transparent;")
        lay.addWidget(b1)
        lay.addSpacing(14)

        b2 = QLabel()
        px3 = load_px("logo_badge.png", 60, 60)
        if not px3.isNull(): b2.setPixmap(px3)
        b2.setStyleSheet("background:transparent;")
        lay.addWidget(b2)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), self.height(), QColor("#E8352A"))
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
# TOPIC CARD  (solid white card on dark bg)
# ═══════════════════════════════════════════════════════════════════════════════
class TopicWidget(QFrame):
    draw_requested = pyqtSignal(object)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.locked = False
        self.done = False
        self.winner_name = ""
        self.contestant_inputs = []

        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("white"))
        self.setPalette(pal)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # Number + title row
        hdr = QHBoxLayout()
        self.num_lbl = QLabel(f"TOPIC {index+1}")
        self.num_lbl.setStyleSheet(
            f"color:{RED};font-size:13px;font-weight:900;letter-spacing:3px;"
            "background:transparent;font-family:Arial Black,sans-serif;")
        hdr.addWidget(self.num_lbl)
        hdr.addStretch()
        lay.addLayout(hdr)

        # Title input
        tr = QHBoxLayout()
        lbl = QLabel("Title:")
        lbl.setFixedWidth(65)
        lbl.setStyleSheet("color:#FFFFFF;font-size:13px;font-weight:bold;background:transparent;")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g. Who wins the PS5 raffle?")
        self.title_edit.setStyleSheet(
            "QLineEdit{background:#F5F5F5;color:#1A1A1A;border:1.5px solid #D0D0D0;"
            "border-radius:5px;padding:7px 10px;font-size:13px;}"
            "QLineEdit:focus{border-color:#E8352A;background:#FFFFFF;}"
            "QLineEdit:disabled{background:#E8E8E8;color:#888;}")
        tr.addWidget(lbl); tr.addWidget(self.title_edit)
        lay.addLayout(tr)

        # Contestant count
        cr = QHBoxLayout()
        lbl2 = QLabel("Contestants:")
        lbl2.setStyleSheet("color:#FFFFFF;font-size:13px;font-weight:bold;background:transparent;")
        self.count_spin = QSpinBox()
        self.count_spin.setRange(2, 50); self.count_spin.setValue(4)
        self.count_spin.setStyleSheet(
            "QSpinBox{background:#F5F5F5;color:#1A1A1A;border:1.5px solid #D0D0D0;"
            "border-radius:5px;padding:5px 8px;font-size:13px;min-width:70px;}"
            "QSpinBox:focus{border-color:#E8352A;}"
            "QSpinBox::up-button,QSpinBox::down-button{background:#E0E0E0;border:none;width:20px;}"
            "QSpinBox::up-button:hover,QSpinBox::down-button:hover{background:#CCCCCC;}")
        self.btn_add = QPushButton("ADD CONTESTANTS")
        self.btn_add.setStyleSheet(
            f"QPushButton{{background:{RED};border:1px solid {RED_DARK};color:white;"
            "padding:5px 12px;font-size:11px;font-weight:bold;letter-spacing:1px;"
            "border-radius:4px;}}"
            f"QPushButton:hover{{background:{RED_DARK};}}")
        self.btn_add.clicked.connect(self._gen_fields)
        cr.addWidget(lbl2); cr.addWidget(self.count_spin)
        cr.addSpacing(8); cr.addWidget(self.btn_add); cr.addStretch()
        lay.addLayout(cr)

        # Contestant grid
        self.grid = QGridLayout(); self.grid.setSpacing(6)
        lay.addLayout(self.grid)

        # Draw button
        br = QHBoxLayout(); br.addStretch()
        self.btn_draw = QPushButton("⚅  GENERATE THE WINNER")
        self.btn_draw.setObjectName("btn_draw")
        self.btn_draw.setEnabled(False)
        self.btn_draw.clicked.connect(lambda: self.draw_requested.emit(self))
        br.addWidget(self.btn_draw)
        lay.addLayout(br)

        self._gen_fields()

    def _gen_fields(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.deleteLater()
        self.contestant_inputs.clear()
        n = self.count_spin.value()
        for i in range(n):
            row, col = divmod(i, 3)
            cell = QWidget(); cell.setStyleSheet("background:transparent;")
            cl = QHBoxLayout(cell); cl.setContentsMargins(0,0,0,0); cl.setSpacing(4)
            num = QLabel(f"{i+1}.")
            num.setFixedWidth(28)
            num.setStyleSheet(f"color:{RED};font-size:14px;font-weight:900;background:transparent;")
            edit = QLineEdit(); edit.setPlaceholderText(f"Contestant {i+1}")
            edit.setStyleSheet(
                "QLineEdit{background:#F5F5F5;color:#1A1A1A;border:1.5px solid #D0D0D0;"
                "border-radius:5px;padding:6px 9px;font-size:12px;}"
                "QLineEdit:focus{border-color:#E8352A;background:#FFFFFF;}"
                "QLineEdit:disabled{background:#E8E8E8;color:#888;}")
            cl.addWidget(num); cl.addWidget(edit)
            self.grid.addWidget(cell, row, col)
            self.contestant_inputs.append(edit)

    def set_locked(self, locked):
        self.locked = locked
        self.title_edit.setEnabled(not locked)
        self.count_spin.setEnabled(not locked)
        self.btn_add.setEnabled(not locked)
        for e in self.contestant_inputs: e.setEnabled(not locked)
        if locked and not self.done:
            self.btn_draw.setObjectName("btn_draw_active")
            self.btn_draw.setEnabled(True)
        elif not locked and not self.done:
            self.btn_draw.setObjectName("btn_draw")
            self.btn_draw.setEnabled(False)
        self.btn_draw.style().unpolish(self.btn_draw)
        self.btn_draw.style().polish(self.btn_draw)

    def mark_done(self, winner):
        self.done = True; self.winner_name = winner
        self.num_lbl.setStyleSheet(
            "color:#4466BB;font-size:11px;font-weight:bold;letter-spacing:3px;background:transparent;")
        self.title_edit.setStyleSheet(
            "background:#F0F4FF;color:#3355BB;border-color:#AABBEE;font-weight:bold;font-size:14px;")
        self.title_edit.setEnabled(False)
        for e in self.contestant_inputs:
            name = e.text().strip()
            if name == winner:
                e.setObjectName("winner_field")
                e.style().unpolish(e); e.style().polish(e)
                tg = QLabel("🏆 WINNER!")
                tg.setStyleSheet("color:#007030;font-weight:bold;font-size:11px;background:transparent;")
                e.parent().layout().addWidget(tg)
            else:
                e.setObjectName("elim_field")
                e.style().unpolish(e); e.style().polish(e)
            e.setEnabled(False)
        self.btn_draw.setObjectName("btn_draw_done")
        self.btn_draw.setText("✓  DRAW COMPLETE"); self.btn_draw.setEnabled(False)
        self.btn_draw.style().unpolish(self.btn_draw); self.btn_draw.style().polish(self.btn_draw)
        # Change card background to light blue
        pal = self.palette(); pal.setColor(self.backgroundRole(), QColor("#F0F3FF"))
        self.setPalette(pal)

    def get_contestants(self):
        return [e.text().strip() for e in self.contestant_inputs if e.text().strip()]

    def get_title(self):
        return self.title_edit.text().strip() or f"Topic {self.index+1}"

    def is_valid(self):
        if not self.title_edit.text().strip():
            return False, "Please fill in the topic title."
        if len(self.get_contestants()) < 2:
            return False, f"'{self.get_title()}' needs at least 2 contestants."
        for e in self.contestant_inputs:
            if not e.text().strip():
                return False, f"All fields in '{self.get_title()}' must be filled in."
        return True, ""


# ═══════════════════════════════════════════════════════════════════════════════
# SETUP SCREEN  (dark bg + building watermark)
# ═══════════════════════════════════════════════════════════════════════════════
class SetupScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("setup_screen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Building watermark (bottom right, subtle)
        self._building = load_px("building.png")
        if not self._building.isNull():
            self._building = self._building.scaled(
                460, 460, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(BG))
        # Building bottom-right, very subtle
        if not self._building.isNull():
            bw = self._building.width(); bh = self._building.height()
            p.setOpacity(0.07)
            p.drawPixmap(w - bw - 10, h - bh - 10, self._building)
            p.setOpacity(1.0)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
class SummaryScreen(QWidget):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._building = load_px("building.png", 400, 400)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(60, 30, 60, 30)
        lay.setSpacing(0)

        # Logo
        lr = QHBoxLayout(); lr.addStretch()
        ll = QLabel(); px = load_px("logo_text.png", 150, 65)
        if not px.isNull(): ll.setPixmap(px)
        ll.setStyleSheet("background:transparent;")
        lr.addWidget(ll); lr.addStretch()
        lay.addLayout(lr); lay.addSpacing(10)

        title = QLabel("FINAL RESULTS — THE HEIST LEDGER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:white;font-size:18px;font-weight:bold;"
                            "letter-spacing:4px;font-family:Impact,sans-serif;")
        lay.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(255,255,255,0.2);max-height:1px;margin:14px 0;")
        lay.addWidget(sep)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent;border:none;")
        inner = QWidget(); inner.setObjectName("scroll_inner")
        inner.setStyleSheet("background:transparent;")
        il = QVBoxLayout(inner); il.setSpacing(10); il.setContentsMargins(0,0,0,0)

        for i, (topic, winner) in enumerate(results):
            row = QFrame()
            row.setStyleSheet("QFrame{background:#2E2E2E;border-radius:7px;}")
            rl = QHBoxLayout(row); rl.setContentsMargins(20, 16, 20, 16); rl.setSpacing(14)
            num = QLabel(f"#{i+1}")
            num.setFixedWidth(48)
            num.setStyleSheet(
                f"color:{RED};font-size:20px;font-weight:bold;"
                "font-family:Impact,sans-serif;background:transparent;")
            tl = QLabel(topic)
            tl.setStyleSheet(
                "color:white;font-size:18px;font-weight:bold;background:transparent;")
            tl.setWordWrap(True)
            wl = QLabel(winner)
            wl.setStyleSheet(
                "color:white;font-size:22px;font-weight:bold;"
                "font-family:Impact,sans-serif;background:transparent;")
            wl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rl.addWidget(num); rl.addWidget(tl, 1); rl.addWidget(wl)
            il.addWidget(row)

        # Attention Winners
        il.addSpacing(14)
        attn = QFrame()
        attn.setStyleSheet(f"QFrame{{background:{RED};border-radius:7px;}}")
        al = QVBoxLayout(attn); al.setContentsMargins(28, 22, 28, 22); al.setSpacing(8)
        a_title = QLabel("⚠  ATTENTION WINNERS!")
        a_title.setStyleSheet(
            "color:white;font-size:22px;font-weight:bold;"
            "font-family:Impact,sans-serif;letter-spacing:2px;background:transparent;")
        a_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        a_body = QLabel(
            "CONGRATULATIONS  ❤\n\n"
            "CONTACT YOUR LOCAL SALES REP. & FIGURE OUT A TIME TO FINALIZE THE DEAL,\n"
            "RECEIVE YOUR INVOICE AND COLLECT YOUR GOODS!")
        a_body.setStyleSheet(
            "color:white;font-size:13px;font-weight:bold;"
            "letter-spacing:1px;background:transparent;")
        a_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        a_body.setWordWrap(True)
        al.addWidget(a_title); al.addSpacing(4); al.addWidget(a_body)
        il.addWidget(attn)

        il.addStretch()
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)
        lay.addSpacing(20)

        br = QHBoxLayout(); br.addStretch()
        self.btn_pdf = QPushButton("📄  GENERATE REPORT (PDF)")
        self.btn_pdf.setStyleSheet(
            "QPushButton{background:white;border:2px solid #E8352A;color:#E8352A;"
            "padding:12px 28px;font-size:14px;font-weight:bold;letter-spacing:2px;border-radius:5px;}"
            "QPushButton:hover{background:#FFF5F5;}")
        self.btn_pdf.setEnabled(HAS_PDF)

        self.btn_new = QPushButton("↺  NEW DRAW")
        self.btn_new.setStyleSheet(
            "QPushButton{background:#E8352A;border:2px solid #C02A20;color:white;"
            "padding:12px 28px;font-size:14px;font-weight:bold;letter-spacing:2px;border-radius:5px;}"
            "QPushButton:hover{background:#C02A20;}")

        br.addWidget(self.btn_pdf); br.addSpacing(16); br.addWidget(self.btn_new)
        br.addStretch(); lay.addLayout(br)

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(BG))
        if not self._building.isNull():
            bw = self._building.width(); bh = self._building.height()
            p.setOpacity(0.06)
            p.drawPixmap(w-bw, h-bh, self._building)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class HeistLedger(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1150, 840); self.setMinimumSize(800, 600)
        icon_px = load_px("logo_badge.png")
        if not icon_px.isNull(): self.setWindowIcon(QIcon(icon_px))

        self.topic_widgets = []
        self.locked = False
        self.results = []
        self.active_anim = None
        self.current_topic = None

        # Root widget
        self.root = QWidget(); self.root.setObjectName("root")
        self.setCentralWidget(self.root)
        self.root_lay = QVBoxLayout(self.root)
        self.root_lay.setContentsMargins(0,0,0,0); self.root_lay.setSpacing(0)

        # Header
        self.header = HeaderWidget()
        self.root_lay.addWidget(self.header)

        # Content area
        self.content = QWidget(); self.content.setObjectName("content_area")
        self.content_lay = QVBoxLayout(self.content)
        self.content_lay.setContentsMargins(0,0,0,0)
        self.root_lay.addWidget(self.content, 1)

        self._build_setup()

    def _build_setup(self):
        self.setup = SetupScreen()
        setup_lay = QVBoxLayout(self.setup)
        setup_lay.setContentsMargins(24,18,24,18); setup_lay.setSpacing(14)

        # Top row: topic count + generate
        tr = QHBoxLayout()
        lbl = QLabel("NUMBER OF TOPICS:")
        lbl.setStyleSheet("color:#AAA;font-size:12px;font-weight:bold;letter-spacing:3px;")
        self.topic_count = QSpinBox()
        self.topic_count.setRange(1, 20); self.topic_count.setValue(2)
        self.topic_count.setStyleSheet(
            "QSpinBox{background:#F5F5F5;color:#1A1A1A;border:1.5px solid #D0D0D0;"
            "border-radius:5px;padding:5px 8px;font-size:13px;min-width:70px;}"
            "QSpinBox:focus{border-color:#E8352A;}"
            "QSpinBox::up-button,QSpinBox::down-button{background:#E0E0E0;border:none;width:20px;}"
            "QSpinBox::up-button:hover,QSpinBox::down-button:hover{background:#CCCCCC;}")
        self.btn_gen = QPushButton("GENERATE TOPICS")
        self.btn_gen.setObjectName("btn_red")
        self.btn_gen.clicked.connect(self._gen_topics)
        tr.addWidget(lbl); tr.addWidget(self.topic_count)
        tr.addSpacing(12); tr.addWidget(self.btn_gen); tr.addStretch()
        setup_lay.addLayout(tr)

        # Scroll area for cards
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.si = QWidget(); self.si.setObjectName("scroll_inner")
        self.si.setStyleSheet(f"background:{BG};")
        self.tl = QVBoxLayout(self.si)
        self.tl.setSpacing(12); self.tl.setContentsMargins(0,4,4,4)
        self.tl.addStretch()
        self.scroll.setWidget(self.si)
        setup_lay.addWidget(self.scroll, 1)

        # Add topic button
        self.btn_add_topic = QPushButton("+  ADD TOPIC")
        self.btn_add_topic.setFixedHeight(42)
        self.btn_add_topic.setStyleSheet(
            f"QPushButton{{background:transparent;border:2px dashed #555;border-radius:6px;"
            f"color:#888;font-size:13px;font-weight:bold;letter-spacing:2px;margin:0 4px;}}"
            f"QPushButton:hover{{border-color:{RED};color:{RED};}}")
        self.btn_add_topic.clicked.connect(self._add_one_topic)
        setup_lay.addWidget(self.btn_add_topic)

        # Lock button
        lr = QHBoxLayout(); lr.addStretch()
        self.btn_lock = QPushButton("🔓  LOCK DOWN THE DRAW")
        self.btn_lock.setObjectName("btn_lock")
        self.btn_lock.clicked.connect(self._toggle_lock)
        lr.addWidget(self.btn_lock); lr.addStretch()
        setup_lay.addLayout(lr)

        self.content_lay.addWidget(self.setup)
        self._gen_topics()

    def _gen_topics(self):
        for tw in self.topic_widgets:
            self.tl.removeWidget(tw); tw.deleteLater()
        self.topic_widgets.clear()
        if self.tl.count():
            self.tl.takeAt(self.tl.count() - 1)  # remove old stretch
        for i in range(self.topic_count.value()):
            tw = TopicWidget(i)
            tw.draw_requested.connect(self._start_draw)
            self.topic_widgets.append(tw)
            self.tl.addWidget(tw)
        self.tl.addStretch()

    def _add_one_topic(self):
        i = len(self.topic_widgets)
        tw = TopicWidget(i)
        tw.draw_requested.connect(self._start_draw)
        self.topic_widgets.append(tw)
        # Insert before the stretch at end
        self.tl.insertWidget(self.tl.count() - 1, tw)
        self.topic_count.setValue(i + 1)
        # Scroll to bottom so new card is visible
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _toggle_lock(self):
        if not self.locked:
            for tw in self.topic_widgets:
                if tw.done: continue
                ok, msg = tw.is_valid()
                if not ok:
                    QMessageBox.warning(self, "Not Ready", msg); return
            self.locked = True
            self.btn_lock.setText("🔒  LOCKED — CLICK TO UNLOCK")
            self.btn_lock.setProperty("locked","true")
            self.topic_count.setEnabled(False); self.btn_gen.setEnabled(False)
        else:
            self.locked = False
            self.btn_lock.setText("🔓  LOCK DOWN THE DRAW")
            self.btn_lock.setProperty("locked","false")
            self.topic_count.setEnabled(True); self.btn_gen.setEnabled(True)
        self.btn_lock.style().unpolish(self.btn_lock)
        self.btn_lock.style().polish(self.btn_lock)
        for tw in self.topic_widgets:
            if not tw.done: tw.set_locked(self.locked)

    def _start_draw(self, tw):
        cs = tw.get_contestants()
        if len(cs) < 2:
            QMessageBox.warning(self,"Not Enough","Add at least 2 contestants."); return
        self.current_topic = tw
        anim = DrawAnimation(tw.get_title(), cs, self.root)
        anim.setGeometry(self.root.rect()); anim.show(); anim.raise_()
        self.active_anim = anim
        anim.btn_ok.clicked.connect(self._on_done)
        anim.btn_redo.clicked.connect(lambda: self.active_anim and self.active_anim.reshuffle())
        anim.start()

    def _on_done(self):
        if not self.active_anim or not self.current_topic: return
        winner = self.active_anim.winner; tw = self.current_topic
        self.active_anim.hide(); self.active_anim.deleteLater(); self.active_anim = None
        tw.mark_done(winner)
        self.results.append((tw.get_title(), winner))
        if all(t.done for t in self.topic_widgets):
            self._show_summary()

    def _show_summary(self):
        self.setup.hide()
        self.summary = SummaryScreen(self.results)
        self.summary.btn_pdf.clicked.connect(self._gen_pdf)
        self.summary.btn_new.clicked.connect(self._new_draw)
        self.content_lay.addWidget(self.summary)

    def _new_draw(self):
        if hasattr(self,'summary'): self.summary.hide(); self.summary.deleteLater()
        self.results.clear(); self.locked = False
        self.btn_lock.setText("🔓  LOCK DOWN THE DRAW")
        self.btn_lock.setProperty("locked","false")
        self.topic_count.setEnabled(True); self.btn_gen.setEnabled(True)
        self._gen_topics(); self.setup.show()

    def _gen_pdf(self):
        if not HAS_PDF:
            QMessageBox.warning(self,"No PDF","pip install reportlab"); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF",
            f"HeistLedger_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "PDF Files (*.pdf)")
        if not path: return
        try:
            doc = SimpleDocTemplate(path, pagesize=A4,
                                    topMargin=20*mm,bottomMargin=20*mm,
                                    leftMargin=20*mm,rightMargin=20*mm)
            def S(**kw): return ParagraphStyle('x', **kw)
            story = [
                Paragraph("10 CHAMBERS AB",
                    S(fontSize=26, textColor=RC.HexColor(RED),
                      fontName='Helvetica-Bold', alignment=TA_CENTER,
                      spaceAfter=4)),
                Paragraph("THE HEIST LEDGER v.1  —  OFFICIAL DRAW REPORT",
                    S(fontSize=10, textColor=RC.HexColor('#666'),
                      fontName='Helvetica', alignment=TA_CENTER, spaceAfter=4)),
                Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
                    S(fontSize=8, textColor=RC.HexColor('#999'),
                      fontName='Helvetica', alignment=TA_CENTER, spaceAfter=16)),
                HRFlowable(width="100%", thickness=2, color=RC.HexColor(RED), spaceAfter=18),
            ]
            for i, (topic, winner) in enumerate(self.results):
                story += [
                    Paragraph(f"DRAW #{i+1}  —  {topic.upper()}",
                        S(fontSize=12, textColor=RC.HexColor('#222'),
                          fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=4)),
                    Paragraph(winner,
                        S(fontSize=22, textColor=RC.HexColor(RED),
                          fontName='Helvetica-Bold', spaceAfter=6)),
                ]
                if i < len(self.results) - 1:
                    story.append(HRFlowable(width="100%", thickness=0.5,
                                            color=RC.HexColor('#DDDDDD'), spaceAfter=10))
            story += [
                Spacer(1, 16*mm),
                HRFlowable(width="100%", thickness=2, color=RC.HexColor(RED), spaceAfter=12),
                Paragraph("ATTENTION WINNERS!",
                    S(fontSize=16, textColor=RC.HexColor(RED),
                      fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=6)),
                Paragraph("CONGRATULATIONS",
                    S(fontSize=12, textColor=RC.HexColor('#222'),
                      fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=8)),
                Paragraph(
                    "CONTACT YOUR LOCAL SALES REP. &amp; FIGURE OUT A TIME TO FINALIZE "
                    "THE DEAL, RECEIVE YOUR INVOICE AND COLLECT YOUR GOODS!",
                    S(fontSize=10, textColor=RC.HexColor('#444'),
                      fontName='Helvetica', alignment=TA_CENTER, spaceAfter=20)),
                HRFlowable(width="100%", thickness=1, color=RC.HexColor('#DDD'), spaceAfter=8),
                Paragraph("10 CHAMBERS AB — ESTABLISHED 2015",
                    S(fontSize=8, textColor=RC.HexColor('#999'),
                      fontName='Helvetica', alignment=TA_CENTER)),
            ]
            doc.build(story)
            QMessageBox.information(self,"Report Saved",f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self,"PDF Error",str(e))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.active_anim:
            self.active_anim.setGeometry(self.root.rect())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("10 Chambers AB")
    app.setStyleSheet(STYLE)
    win = HeistLedger()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
