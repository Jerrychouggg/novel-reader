"""阅读区域 — QScrollArea + QLabel 渲染文本"""
from PySide6.QtWidgets import (
    QScrollArea, QLabel, QWidget, QVBoxLayout, QFrame,
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QColor, QPalette, QMouseEvent


class ReaderWidget(QScrollArea):
    """核心阅读区域"""

    # 信号
    clicked = Signal()               # 点击切换控制栏
    scrollChanged = Signal(float)    # 滚动比例 0.0~1.0
    bottomReached = Signal()         # 到达底部

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._current_chapter_index = -1
        self._chapters = []

        # 安装事件过滤器,检测鼠标进入/离开
        self.viewport().installEventFilter(self)

    # ── UI 初始化 ────────────────────────────────────────────

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        # 内部容器
        container = QWidget()
        container.setObjectName("readerContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 20, 40, 20)

        # 文本标签
        self.text_label = QLabel("拖入 txt/epub 文件开始阅读\n\n— 或者点击控制栏 📂 打开 —")
        self.text_label.setObjectName("readerLabel")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.text_label.setTextFormat(Qt.TextFormat.PlainText)

        layout.addWidget(self.text_label)
        self.setWidget(container)

    # ── 滚动控制 ──────────────────────────────────────────────

    def scroll_by(self, delta_pixels: float):
        """滚动指定像素(用于自动滚动)"""
        bar = self.verticalScrollBar()
        new_val = bar.value() + int(delta_pixels)
        bar.setValue(new_val)

    def scroll_to(self, position: int):
        """滚动到指定像素位置"""
        self.verticalScrollBar().setValue(position)

    def scroll_position(self) -> int:
        """当前滚动位置(像素)"""
        return self.verticalScrollBar().value()

    def scroll_max(self) -> int:
        """最大滚动位置"""
        return self.verticalScrollBar().maximum()

    def scroll_ratio(self) -> float:
        """当前滚动比例 0.0~1.0"""
        bar = self.verticalScrollBar()
        if bar.maximum() == 0:
            return 0.0
        return bar.value() / bar.maximum()

    # ── 内容设置 ──────────────────────────────────────────────

    def set_content(self, paragraphs: list[str]):
        """设置当前要显示的段落列表"""
        text = "\n\n".join(paragraphs)
        self.text_label.setText(text)

    def clear(self):
        """清空内容"""
        self.text_label.clear()
        self._chapters = []
        self._current_chapter_index = -1

    # ── 样式应用 ──────────────────────────────────────────────

    def apply_theme(self, colors: dict, font: QFont):
        """应用主题配色和字体"""
        # 字体
        self.text_label.setFont(font)

        # 阅读区容器背景
        container = self.widget()
        if container:
            bg = colors["bg"]
            style = f"""
                QWidget#readerContainer {{
                    background-color: {bg};
                }}
            """
            container.setStyleSheet(style)

        # 文字颜色
        pal = self.text_label.palette()
        pal.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
        self.text_label.setPalette(pal)

        # 同时也设样式确保生效
        self.text_label.setStyleSheet(
            f"color: {colors['text']}; padding: 10px;"
        )

    # ── 事件 ──────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        """点击发出信号"""
        self.clicked.emit()
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        """检测滚动条变化"""
        if obj == self.viewport():
            if event.type() == QEvent.Type.Wheel:
                # 滚轮后检查是否到底
                ...

        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        """滚轮事件"""
        super().wheelEvent(event)
        ratio = self.scroll_ratio()
        self.scrollChanged.emit(ratio)
