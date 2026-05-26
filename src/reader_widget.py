"""阅读区域 — QScrollArea + QLabel 渲染文本，自适应窗口宽度"""
from PySide6.QtWidgets import (
    QScrollArea, QLabel, QWidget, QVBoxLayout, QFrame,
)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QMouseEvent, QResizeEvent


class _ReaderContainer(QWidget):
    """内部容器：resize 时防抖更新边距，避免拖拽时频繁重排文字"""

    def __init__(self, reader: "ReaderWidget", parent=None):
        super().__init__(parent)
        self._reader = reader
        self.setObjectName("readerContainer")
        # 防抖：resize 停止 120ms 后才更新边距
        self._margin_timer = QTimer(self)
        self._margin_timer.setSingleShot(True)
        self._margin_timer.setInterval(120)
        self._margin_timer.timeout.connect(self._apply_pending_margin)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        # 记录待处理的宽度，重启防抖计时器
        self._pending_width = event.size().width()
        self._margin_timer.start()

    def _apply_pending_margin(self):
        """resize 停止后才真正更新边距"""
        w = getattr(self, '_pending_width', self.width())
        self._reader._sync_margins_to_width(w)


class ReaderWidget(QScrollArea):
    """核心阅读区域"""

    clicked = Signal()
    scrollChanged = Signal(float)
    bottomReached = Signal()

    _MARGIN_MIN = 16
    _MARGIN_MAX = 80
    _MARGIN_RATIO = 0.06

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chapters: list[str] = []
        self._custom_text_color = ""
        self._mini_mode = False
        self._setup_ui()
        self.viewport().installEventFilter(self)

    # ── UI ──────────────────────────────────────────────────

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self._container = _ReaderContainer(self)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(40, 20, 40, 20)

        self.text_label = QLabel("拖入 txt/epub 文件开始阅读\n\n— 或者点击控制栏 📂 打开 —")
        self.text_label.setObjectName("readerLabel")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.text_label.setTextFormat(Qt.TextFormat.PlainText)

        layout.addWidget(self.text_label)
        self.setWidget(self._container)

    # ── 自适应边距 ──────────────────────────────────────────

    def _calc_margin(self, width: int) -> int:
        return max(self._MARGIN_MIN, min(self._MARGIN_MAX, int(width * self._MARGIN_RATIO)))

    def _sync_margins_to_width(self, width: int):
        """根据容器宽度更新左右边距（仅在 resize 停止后调用）"""
        if self._mini_mode:
            return
        m = self._calc_margin(width)
        lay = self._container.layout()
        if lay:
            lay.setContentsMargins(m, 20, m, 20)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)

    # ── 迷你模式 ────────────────────────────────────────────

    def set_mini_mode(self, active: bool):
        self._mini_mode = active
        lay = self._container.layout()
        if not lay:
            return
        if active:
            lay.setContentsMargins(12, 4, 12, 4)
            self.text_label.setWordWrap(False)
            self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            font = self.text_label.font()
            font.setPointSize(10)
            self.text_label.setFont(font)
        else:
            m = self._calc_margin(self._container.width())
            lay.setContentsMargins(m, 20, m, 20)
            self.text_label.setWordWrap(True)
            self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        if self._chapters:
            self._refresh_content()

    def _refresh_content(self):
        if self._chapters:
            self.set_content(self._chapters)

    def get_current_line(self) -> str:
        if not self._chapters:
            return ""
        ratio = self.scroll_ratio()
        total = len(self._chapters)
        if total == 0:
            return ""
        idx = min(int(ratio * total), total - 1)
        line = self._chapters[idx]
        return line[:80] + ("…" if len(line) > 80 else "")

    # ── 滚动 ────────────────────────────────────────────────

    def scroll_by(self, delta_pixels: float):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + int(delta_pixels))

    def scroll_to(self, position: int):
        self.verticalScrollBar().setValue(position)

    def scroll_position(self) -> int:
        return self.verticalScrollBar().value()

    def scroll_ratio(self) -> float:
        bar = self.verticalScrollBar()
        return bar.value() / bar.maximum() if bar.maximum() > 0 else 0.0

    # ── 内容 ────────────────────────────────────────────────

    def set_content(self, paragraphs: list[str]):
        self._chapters = paragraphs
        self.text_label.setText("\n\n".join(paragraphs))

    def clear(self):
        self.text_label.clear()
        self._chapters = []

    # ── 样式 ────────────────────────────────────────────────

    def apply_theme(self, colors: dict, font: QFont):
        self.text_label.setFont(font)
        bg = colors["bg"]
        self._container.setStyleSheet(f"QWidget#readerContainer {{ background-color: {bg}; }}")
        text_color = self._custom_text_color or colors["text"]
        pal = self.text_label.palette()
        pal.setColor(QPalette.ColorRole.WindowText, QColor(text_color))
        self.text_label.setPalette(pal)
        self.text_label.setStyleSheet(f"color: {text_color}; padding: 10px;")

    def set_custom_text_color(self, color: str):
        self._custom_text_color = color

    # ── 事件 ────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        self.scrollChanged.emit(self.scroll_ratio())
