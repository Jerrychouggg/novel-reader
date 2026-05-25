"""悬浮控制栏 — 半透明,鼠标悬停显示,移开半隐藏"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSlider,
    QProgressBar, QMenu, QFileDialog, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette


class ControlBar(QWidget):
    """底部控制栏"""

    # 信号
    openFileRequested = Signal(str)        # 请求打开文件
    toggleScroll = Signal()                # 切换自动滚动
    speedChanged = Signal(int)             # 速度变化
    themeChanged = Signal(str)             # 主题切换
    fontChanged = Signal(str, int, float)  # 字体/大小/行距变化
    closeRequested = Signal()              # 请求关闭窗口
    windowResizeRequested = Signal(int)    # 请求调整窗口高度(delta)
    windowWidthResizeRequested = Signal(int)  # 请求调整窗口宽度(delta)
    pageUp = Signal()                    # 上一页
    pageDown = Signal()                  # 下一页

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(1500)
        self._hide_timer.timeout.connect(self._collapse)

        self.setFixedHeight(48)
        self.setMouseTracking(True)
        self._setup_ui()
        self._setup_animations()

    # ── UI ────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # 打开文件按钮
        self.btn_open = QPushButton("📂")
        self.btn_open.setToolTip("打开文件")
        self.btn_open.setFixedSize(32, 32)
        self.btn_open.clicked.connect(self._on_open)
        layout.addWidget(self.btn_open)

        # 自动滚动按钮
        self.btn_scroll = QPushButton("▶")
        self.btn_scroll.setToolTip("自动滚动")
        self.btn_scroll.setFixedSize(32, 32)
        self.btn_scroll.clicked.connect(self._on_toggle_scroll)
        layout.addWidget(self.btn_scroll)

        # 上一页
        self.btn_page_up = QPushButton("◀")
        self.btn_page_up.setToolTip("上一页")
        self.btn_page_up.setFixedSize(32, 32)
        self.btn_page_up.clicked.connect(self.pageUp.emit)
        layout.addWidget(self.btn_page_up)

        # 下一页
        self.btn_page_down = QPushButton("▶▶")
        self.btn_page_down.setToolTip("下一页")
        self.btn_page_down.setFixedSize(32, 32)
        self.btn_page_down.clicked.connect(self.pageDown.emit)
        layout.addWidget(self.btn_page_down)

        # 速度滑块
        self.speed_label = QLabel("速度:")
        layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(5, 150)
        self.speed_slider.setValue(30)
        self.speed_slider.setFixedWidth(80)
        self.speed_slider.setToolTip("滚动速度")
        self.speed_slider.valueChanged.connect(self._on_speed)
        layout.addWidget(self.speed_slider)

        layout.addStretch()

        # 进度标签
        self.progress_label = QLabel("—")
        self.progress_label.setToolTip("阅读进度")
        layout.addWidget(self.progress_label)

        layout.addStretch()

        # 主题按钮
        self.btn_theme = QPushButton("🎨")
        self.btn_theme.setToolTip("主题")
        self.btn_theme.setFixedSize(32, 32)
        self.btn_theme.clicked.connect(self._on_theme)
        layout.addWidget(self.btn_theme)

        # 字号 -
        self.btn_font_small = QPushButton("A-")
        self.btn_font_small.setToolTip("缩小字号")
        self.btn_font_small.setFixedSize(32, 32)
        self.btn_font_small.clicked.connect(lambda: self._adj_font(-1))
        layout.addWidget(self.btn_font_small)

        # 字号 +
        self.btn_font_big = QPushButton("A+")
        self.btn_font_big.setToolTip("增大字号")
        self.btn_font_big.setFixedSize(32, 32)
        self.btn_font_big.clicked.connect(lambda: self._adj_font(1))
        layout.addWidget(self.btn_font_big)

        # 页面高度 -
        self.btn_height_down = QPushButton("─")
        self.btn_height_down.setToolTip("减小页面高度")
        self.btn_height_down.setFixedSize(32, 32)
        self.btn_height_down.clicked.connect(lambda: self.windowResizeRequested.emit(-40))
        layout.addWidget(self.btn_height_down)

        # 页面高度 +
        self.btn_height_up = QPushButton("█")
        self.btn_height_up.setToolTip("增大页面高度")
        self.btn_height_up.setFixedSize(32, 32)
        self.btn_height_up.clicked.connect(lambda: self.windowResizeRequested.emit(40))
        layout.addWidget(self.btn_height_up)

        # 页面宽度 -
        self.btn_width_down = QPushButton("⊲")
        self.btn_width_down.setToolTip("减小页面宽度")
        self.btn_width_down.setFixedSize(32, 32)
        self.btn_width_down.clicked.connect(lambda: self.windowWidthResizeRequested.emit(-80))
        layout.addWidget(self.btn_width_down)

        # 页面宽度 +
        self.btn_width_up = QPushButton("⊳")
        self.btn_width_up.setToolTip("增大页面宽度")
        self.btn_width_up.setFixedSize(32, 32)
        self.btn_width_up.clicked.connect(lambda: self.windowWidthResizeRequested.emit(80))
        layout.addWidget(self.btn_width_up)

        # 关闭按钮
        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("关闭")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setObjectName("btn_close")
        self.btn_close.clicked.connect(self.closeRequested.emit)
        layout.addWidget(self.btn_close)

    def _setup_animations(self):
        """展开/收起动画"""
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    # ── 展开/收起 ──────────────────────────────────────────────

    def show_bar(self):
        """展开控制栏"""
        if not self._collapsed:
            return
        self._collapsed = False
        parent = self.parent()
        if parent:
            pw, ph = parent.width(), parent.height()
            y = ph - self.height()
            self._anim.setStartValue(self.geometry())
            self._anim.setEndValue(self.geometry().translated(
                -self.x(), y - self.y()
            ))
            self._anim.start()
        self.setVisible(True)
        self._reset_hide_timer()

    def _collapse(self):
        """收起控制栏"""
        if self._collapsed:
            return
        self._collapsed = True
        parent = self.parent()
        if parent:
            pw, ph = parent.width(), parent.height()
            y = ph  # 藏到窗口下方,留一条边
            self._anim.setStartValue(self.geometry())
            self._anim.setEndValue(self.geometry().translated(
                -self.x(), y - self.y() - 4
            ))
            self._anim.start()

    def _reset_hide_timer(self):
        if not self._collapsed:
            self._hide_timer.start()

    # ── 事件 ──────────────────────────────────────────────────

    def enterEvent(self, event):
        """鼠标进入,展开"""
        self.show_bar()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开,开始计时收起"""
        self._reset_hide_timer()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动时重置计时器"""
        self._reset_hide_timer()
        super().mouseMoveEvent(event)

    # ── 交互 ──────────────────────────────────────────────────

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window(), "打开小说文件", "",
            "文本文件 (*.txt *.epub);;TXT (*.txt);;EPUB (*.epub)"
        )
        if path:
            self.openFileRequested.emit(path)

    def _on_toggle_scroll(self):
        self.toggleScroll.emit()

    def _on_speed(self, val):
        self.speedChanged.emit(val)

    def _on_theme(self):
        """弹出主题选择菜单"""
        menu = QMenu(self)
        light = menu.addAction("☀  日间")
        dark = menu.addAction("🌙  夜间")
        green = menu.addAction("🌿  护眼绿")
        warm = menu.addAction("📜  护眼米黄")
        transparent = menu.addAction("👻  透明")

        action = menu.exec(self.btn_theme.mapToGlobal(
            self.btn_theme.rect().bottomLeft()
        ))
        if action == light:
            self.themeChanged.emit("light")
        elif action == dark:
            self.themeChanged.emit("dark")
        elif action == green:
            self.themeChanged.emit("eye_green")
        elif action == warm:
            self.themeChanged.emit("eye_warm")
        elif action == transparent:
            self.themeChanged.emit("transparent")

    def _adj_font(self, delta: int):
        """调整字号"""
        self.fontChanged.emit("", delta, 0)

    # ── 状态更新 ──────────────────────────────────────────────

    def set_scroll_state(self, running: bool):
        """更新滚动按钮图标"""
        self.btn_scroll.setText("⏸" if running else "▶")

    def set_progress(self, ratio: float, chapter_title: str = ""):
        """更新进度显示"""
        pct = int(ratio * 100)
        self.progress_label.setText(f"{chapter_title} — {pct}%")

    def set_speed(self, value: int):
        """设置速度滑块值(不触发信号)"""
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(value)
        self.speed_slider.blockSignals(False)

    # ── 样式 ──────────────────────────────────────────────────

    def apply_theme(self, colors: dict):
        """应用主题配色"""
        bg = colors["control_bg"]
        text = colors["control_text"]
        hover = colors["control_hover"]

        self.setStyleSheet(f"""
            ControlBar {{
                background-color: {bg};
                border-top: 1px solid rgba(128,128,128,0.15);
            }}
            QPushButton {{
                background: transparent;
                color: {text};
                border: none;
                border-radius: 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton#btn_close:hover {{
                background-color: rgba(220, 60, 60, 0.7);
                color: white;
            }}
            QLabel {{
                color: {text};
                font-size: 12px;
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: {colors.get('progress_bg', '#555')};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: {colors.get('progress_fg', '#88C')};
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {colors.get('progress_fg', '#88C')};
                border-radius: 2px;
            }}
        """)
