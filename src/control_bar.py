"""悬浮控制栏 + 迷你模式顶栏"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSlider,
    QProgressBar, QMenu, QFileDialog, QComboBox, QColorDialog,
    QVBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont, QColor, QPalette


# ── 迷你模式顶栏 ────────────────────────────────────────────────

class MiniControlBar(QWidget):
    """摸鱼模式下的紧凑顶栏"""

    toggleScroll = Signal()
    speedChanged = Signal(int)
    pageUp = Signal()
    pageDown = Signal()
    fontChanged = Signal(str, int, float)  # 字号调整
    exitMini = Signal()                    # 退出摸鱼模式
    openFileRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setMouseTracking(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        # 左侧：阅读控制
        btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                padding: 2px;
            }
        """

        self.btn_open = QPushButton("📂")
        self.btn_open.setToolTip("打开文件")
        self.btn_open.setFixedSize(26, 26)
        self.btn_open.setStyleSheet(btn_style)
        self.btn_open.clicked.connect(self._on_open)
        layout.addWidget(self.btn_open)

        self.btn_page_up = QPushButton("◀")
        self.btn_page_up.setToolTip("上一页")
        self.btn_page_up.setFixedSize(26, 26)
        self.btn_page_up.setStyleSheet(btn_style)
        self.btn_page_up.clicked.connect(self.pageUp.emit)
        layout.addWidget(self.btn_page_up)

        self.btn_scroll = QPushButton("▶")
        self.btn_scroll.setToolTip("播放/暂停")
        self.btn_scroll.setFixedSize(30, 30)
        self.btn_scroll.setStyleSheet(btn_style + "font-size: 16px;")
        self.btn_scroll.clicked.connect(self.toggleScroll.emit)
        layout.addWidget(self.btn_scroll)

        self.btn_page_down = QPushButton("▶▶")
        self.btn_page_down.setToolTip("下一页")
        self.btn_page_down.setFixedSize(26, 26)
        self.btn_page_down.setStyleSheet(btn_style)
        self.btn_page_down.clicked.connect(self.pageDown.emit)
        layout.addWidget(self.btn_page_down)

        # 速度微调
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(5, 150)
        self.speed_slider.setValue(30)
        self.speed_slider.setFixedWidth(50)
        self.speed_slider.setToolTip("滚动速度")
        self.speed_slider.valueChanged.connect(self.speedChanged.emit)
        layout.addWidget(self.speed_slider)

        # 中间：当前行文本
        self.line_label = QLabel("")
        self.line_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.line_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.line_label.setStyleSheet("font-size: 11px; padding: 0 8px; background: transparent;")
        layout.addWidget(self.line_label, 1)

        # 右侧：工具按钮
        self.btn_font_small = QPushButton("A-")
        self.btn_font_small.setToolTip("缩小字号")
        self.btn_font_small.setFixedSize(26, 26)
        self.btn_font_small.setStyleSheet(btn_style)
        self.btn_font_small.clicked.connect(lambda: self.fontChanged.emit("", -1, 0))
        layout.addWidget(self.btn_font_small)

        self.btn_font_big = QPushButton("A+")
        self.btn_font_big.setToolTip("增大字号")
        self.btn_font_big.setFixedSize(26, 26)
        self.btn_font_big.setStyleSheet(btn_style)
        self.btn_font_big.clicked.connect(lambda: self.fontChanged.emit("", 1, 0))
        layout.addWidget(self.btn_font_big)

        self.btn_theme = QPushButton("🎨")
        self.btn_theme.setToolTip("主题")
        self.btn_theme.setFixedSize(26, 26)
        self.btn_theme.setStyleSheet(btn_style)
        self.btn_theme.clicked.connect(self._on_theme)
        layout.addWidget(self.btn_theme)

        self.btn_exit = QPushButton("📖")
        self.btn_exit.setToolTip("退出摸鱼模式")
        self.btn_exit.setFixedSize(26, 26)
        self.btn_exit.setStyleSheet(btn_style)
        self.btn_exit.clicked.connect(self.exitMini.emit)
        layout.addWidget(self.btn_exit)

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window(), "打开小说文件", "",
            "文本文件 (*.txt *.epub);;TXT (*.txt);;EPUB (*.epub)"
        )
        if path:
            self.openFileRequested.emit(path)

    def _on_theme(self):
        menu = QMenu(self)
        light = menu.addAction("☀  日间")
        dark = menu.addAction("🌙  夜间")
        green = menu.addAction("🌿  护眼绿")
        warm = menu.addAction("📜  护眼米黄")
        transparent = menu.addAction("👻  透明")
        action = menu.exec(self.btn_theme.mapToGlobal(self.btn_theme.rect().bottomLeft()))
        themes = {"☀  日间": "light", "🌙  夜间": "dark", "🌿  护眼绿": "eye_green",
                   "📜  护眼米黄": "eye_warm", "👻  透明": "transparent"}
        if action:
            theme_name = themes.get(action.text(), "")
            if theme_name and hasattr(self.window(), '_on_theme_change'):
                self.window()._on_theme_change(theme_name)

    def set_scroll_state(self, running: bool):
        self.btn_scroll.setText("⏸" if running else "▶")

    def set_current_line(self, text: str):
        self.line_label.setText(text)

    def set_speed(self, value: int):
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(value)
        self.speed_slider.blockSignals(False)

    def apply_theme(self, colors: dict):
        bg = colors.get("mini_bg", "rgba(20,20,25,0.9)")
        text_color = colors.get("mini_text", "#D0D0D0")
        hover = colors.get("mini_hover", "rgba(60,60,70,0.7)")
        btn_color = colors.get("mini_btn", "#A0A0A0")
        progress_bg = colors.get("progress_bg", "#444")
        progress_fg = colors.get("progress_fg", "#6CB4EE")

        self.setStyleSheet(f"""
            MiniControlBar {{
                background-color: {bg};
                border-radius: 10px;
            }}
            QPushButton {{
                background: transparent;
                color: {btn_color};
                border: none;
                border-radius: 13px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {hover};
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 11px;
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 3px;
                background: {progress_bg};
                border-radius: 1px;
            }}
            QSlider::handle:horizontal {{
                width: 10px;
                height: 10px;
                margin: -3px 0;
                background: {progress_fg};
                border-radius: 5px;
            }}
            QSlider::sub-page:horizontal {{
                background: {progress_fg};
                border-radius: 1px;
            }}
        """)


# ── 正常模式底部控制栏 ──────────────────────────────────────────

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
    miniModeToggled = Signal()           # 摸鱼模式切换
    textColorRequested = Signal(str)     # 请求更改文字颜色(颜色值)

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
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # ── 左侧：核心阅读控制 ──
        self.btn_open = QPushButton("📂")
        self.btn_open.setToolTip("打开文件")
        self.btn_open.setFixedSize(30, 30)
        self.btn_open.clicked.connect(self._on_open)
        layout.addWidget(self.btn_open)

        self.btn_scroll = QPushButton("▶")
        self.btn_scroll.setToolTip("自动滚动")
        self.btn_scroll.setFixedSize(30, 30)
        self.btn_scroll.clicked.connect(self._on_toggle_scroll)
        layout.addWidget(self.btn_scroll)

        self.btn_page_up = QPushButton("◀")
        self.btn_page_up.setToolTip("上一页")
        self.btn_page_up.setFixedSize(30, 30)
        self.btn_page_up.clicked.connect(self.pageUp.emit)
        layout.addWidget(self.btn_page_up)

        self.btn_page_down = QPushButton("▶▶")
        self.btn_page_down.setToolTip("下一页")
        self.btn_page_down.setFixedSize(30, 30)
        self.btn_page_down.clicked.connect(self.pageDown.emit)
        layout.addWidget(self.btn_page_down)

        # 速度滑块（紧凑）
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(5, 150)
        self.speed_slider.setValue(30)
        self.speed_slider.setFixedWidth(60)
        self.speed_slider.setToolTip("滚动速度")
        self.speed_slider.valueChanged.connect(self._on_speed)
        layout.addWidget(self.speed_slider)

        layout.addStretch()

        # ── 中间：进度 ──
        self.progress_label = QLabel("—")
        self.progress_label.setToolTip("阅读进度")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        layout.addStretch()

        # ── 右侧：常用工具 ──
        self.btn_font_small = QPushButton("A-")
        self.btn_font_small.setToolTip("缩小字号")
        self.btn_font_small.setFixedSize(30, 30)
        self.btn_font_small.clicked.connect(lambda: self._adj_font(-1))
        layout.addWidget(self.btn_font_small)

        self.btn_font_big = QPushButton("A+")
        self.btn_font_big.setToolTip("增大字号")
        self.btn_font_big.setFixedSize(30, 30)
        self.btn_font_big.clicked.connect(lambda: self._adj_font(1))
        layout.addWidget(self.btn_font_big)

        self.btn_theme = QPushButton("🎨")
        self.btn_theme.setToolTip("主题 / 文字颜色 / 窗口尺寸")
        self.btn_theme.setFixedSize(30, 30)
        self.btn_theme.clicked.connect(self._on_theme)
        layout.addWidget(self.btn_theme)

        # 溢出菜单（窗口尺寸、文字颜色）
        self.btn_more = QPushButton("⋯")
        self.btn_more.setToolTip("更多选项")
        self.btn_more.setFixedSize(30, 30)
        self.btn_more.clicked.connect(self._on_more_menu)
        layout.addWidget(self.btn_more)

        self.btn_mini = QPushButton("🐟")
        self.btn_mini.setToolTip("摸鱼模式")
        self.btn_mini.setFixedSize(30, 30)
        self.btn_mini.setCheckable(True)
        self.btn_mini.clicked.connect(self.miniModeToggled.emit)
        layout.addWidget(self.btn_mini)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("关闭")
        self.btn_close.setFixedSize(30, 30)
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
        """弹出主题 + 文字颜色选择菜单"""
        menu = QMenu(self)
        menu.addAction("☀  日间").triggered.connect(lambda: self.themeChanged.emit("light"))
        menu.addAction("🌙  夜间").triggered.connect(lambda: self.themeChanged.emit("dark"))
        menu.addAction("🌿  护眼绿").triggered.connect(lambda: self.themeChanged.emit("eye_green"))
        menu.addAction("📜  护眼米黄").triggered.connect(lambda: self.themeChanged.emit("eye_warm"))
        menu.addAction("👻  透明").triggered.connect(lambda: self.themeChanged.emit("transparent"))
        menu.addSeparator()
        menu.addAction("🖌  文字颜色…").triggered.connect(self._on_text_color)
        menu.exec(self.btn_theme.mapToGlobal(self.btn_theme.rect().bottomLeft()))

    def _on_more_menu(self):
        """溢出菜单：窗口尺寸调整"""
        menu = QMenu(self)
        menu.addAction("⬆  增高").triggered.connect(lambda: self.windowResizeRequested.emit(40))
        menu.addAction("⬇  降低").triggered.connect(lambda: self.windowResizeRequested.emit(-40))
        menu.addSeparator()
        menu.addAction("⬅  变窄").triggered.connect(lambda: self.windowWidthResizeRequested.emit(-80))
        menu.addAction("➡  变宽").triggered.connect(lambda: self.windowWidthResizeRequested.emit(80))
        menu.exec(self.btn_more.mapToGlobal(self.btn_more.rect().bottomLeft()))

    def _adj_font(self, delta: int):
        """调整字号"""
        self.fontChanged.emit("", delta, 0)

    def _on_text_color(self):
        """弹出颜色选择对话框"""
        color = QColorDialog.getColor(parent=self.window(), title="选择文字颜色")
        if color.isValid():
            self.textColorRequested.emit(color.name())

    def set_mini_state(self, active: bool):
        """更新摸鱼按钮状态"""
        self.btn_mini.setChecked(active)
        self.btn_mini.setText("🐠" if active else "🐟")

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
                border-top: 1px solid rgba(128,128,128,0.12);
                border-radius: 0 0 12px 12px;
            }}
            QPushButton {{
                background: transparent;
                color: {text};
                border: none;
                border-radius: 15px;
                font-size: 13px;
                min-width: 30px;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton#btn_close:hover {{
                background-color: rgba(220, 60, 60, 0.65);
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
                width: 12px;
                height: 12px;
                margin: -4px 0;
                background: {colors.get('progress_fg', '#88C')};
                border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{
                background: {colors.get('progress_fg', '#88C')};
                border-radius: 2px;
            }}
        """)
