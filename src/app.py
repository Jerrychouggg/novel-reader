"""主窗口 — 无边框置底窗口,集成模糊效果、阅读器、控制栏"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QFont, QColor, QCursor, QMouseEvent

from src.blur_effect import apply_blur
from src.config import (
    load_config, save_config, load_bookmarks, save_bookmark,
    get_theme_colors, ReaderConfig, Bookmark,
)
from src.book_manager import load_book, Book, Chapter
from src.auto_scroller import AutoScroller
from src.reader_widget import ReaderWidget
from src.control_bar import ControlBar


class NovelReader(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.bookmarks = load_bookmarks()
        self.book: Book | None = None
        self._current_chapter_idx = 0
        self._font_size = self.config.font_size
        self._theme = self.config.theme
        self._scrolling = False

        # 拖拽 / 调整大小 状态
        self._RESIZE_MARGIN = 8          # 边缘调整大小的感应区域(px)
        self._moving = False             # 是否正在拖动窗口
        self._resize_edge = 0            # 0=无, 1=顶, 2=左, 3=右, 4=左上, 5=右上
        self._drag_start_pos = QPoint()  # 拖动起始鼠标位置(全局坐标)
        self._drag_start_geom = None     # 拖动起始窗口几何

        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._apply_theme()
        self._apply_font()

        # 延迟应用模糊(窗口已显示后)
        QTimer.singleShot(100, self._apply_blur)
        # 尝试恢复上次阅读位置
        QTimer.singleShot(200, self._restore_last_book)

    # ── 窗口设置 ──────────────────────────────────────────────

    def _setup_window(self):
        """配置无边框置底窗口"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)       # 启用鼠标追踪(光标样式更新)
        self.setAcceptDrops(True)

        # 窗口标题
        self.setWindowTitle("小阅 — 桌面小说阅读器")

        # 尺寸与位置
        self._position_window()

        # 监听屏幕变化
        screen = self.screen()
        if screen:
            screen.geometryChanged.connect(self._position_window)

    def _position_window(self):
        """将窗口放在屏幕底部、任务栏上方"""
        screen = self.screen()
        if not screen:
            return

        avail = screen.availableGeometry()  # 不含任务栏的工作区
        full = screen.geometry()            # 全屏区域

        w = avail.width()
        h = self.config.window_height
        x = avail.x()
        y = avail.y() + avail.height() - h

        # 如果任务栏在底部,avail.height < full.height
        # 已由 availableGeometry 自动处理

        # 使用保存的位置(如果有)
        if self.config.window_x >= 0:
            x = self.config.window_x
        if self.config.window_y >= 0:
            y = self.config.window_y

        self.setGeometry(x, y, w, h)
        # 保证最小尺寸
        self.setMinimumSize(400, 100)

    def _on_window_resize(self, delta: int):
        """按钮调整窗口高度"""
        new_h = max(100, min(600, self.height() + delta))
        new_y = self.y() - (new_h - self.height())
        self.setGeometry(self.x(), new_y, self.width(), new_h)

    def _on_window_width_resize(self, delta: int):
        """按钮调整窗口宽度"""
        screen_w = self.screen().availableGeometry().width() if self.screen() else 1920
        new_w = max(400, min(screen_w, self.width() + delta))
        self.setGeometry(self.x(), self.y(), new_w, self.height())

    def showEvent(self, event):
        """窗口显示时应用模糊"""
        super().showEvent(event)
        QTimer.singleShot(50, self._apply_blur)

    def _apply_blur(self):
        """应用 Windows Acrylic/Mica 模糊"""
        hwnd = int(self.winId())
        result = apply_blur(hwnd)
        print(f"[模糊效果] 策略: {result}")

    # ── UI ────────────────────────────────────────────────────

    def _setup_ui(self):
        """构建界面"""
        central = QWidget()
        central.setObjectName("centralWidget")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 阅读区域
        self.reader = ReaderWidget()
        layout.addWidget(self.reader, 1)

        # 控制栏
        self.control_bar = ControlBar()
        layout.addWidget(self.control_bar)

        self.setCentralWidget(central)

        # 自动滚动器
        self.scroller = AutoScroller(self)
        self.scroller.set_scroll_callback(self.reader.scroll_by)
        self.scroller.speed = self.config.auto_scroll_speed

    # ── 信号连接 ──────────────────────────────────────────────

    def _setup_connections(self):
        """连接信号与槽"""
        # 控制栏信号
        self.control_bar.openFileRequested.connect(self._on_open_file)
        self.control_bar.toggleScroll.connect(self._on_toggle_scroll)
        self.control_bar.speedChanged.connect(self._on_speed_change)
        self.control_bar.themeChanged.connect(self._on_theme_change)
        self.control_bar.fontChanged.connect(self._on_font_change)
        self.control_bar.closeRequested.connect(self.close)
        self.control_bar.windowResizeRequested.connect(self._on_window_resize)
        self.control_bar.windowWidthResizeRequested.connect(self._on_window_width_resize)
        self.control_bar.pageUp.connect(self._on_page_up)
        self.control_bar.pageDown.connect(self._on_page_down)

        # 阅读区信号
        self.reader.clicked.connect(self.control_bar.show_bar)

        # 自动滚动同步按钮状态
        self.scroller._timer.timeout.connect(self._sync_scroll_state)

    # ── 文件操作 ──────────────────────────────────────────────

    def _on_open_file(self, path: str = None):
        """打开小说文件"""
        if not path:
            return
        try:
            self.book = load_book(path)
            self._current_chapter_idx = 0
            self._load_chapter(0)

            # 更新窗口标题
            self.setWindowTitle(f"小阅 — {self.book.title}")

            # 添加到最近文件
            if path not in self.config.recent_files:
                self.config.recent_files.insert(0, path)
                self.config.recent_files = self.config.recent_files[:10]
            save_config(self.config)

            # 恢复该书签
            bm = self.bookmarks.get(path)
            if bm:
                self._current_chapter_idx = bm.chapter_index
                self._load_chapter(bm.chapter_index)
                QTimer.singleShot(100, lambda: self.reader.scroll_to(bm.scroll_position))

            self.control_bar.show_bar()

        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def _load_chapter(self, idx: int):
        """加载指定章节到阅读区"""
        if not self.book or idx < 0 or idx >= len(self.book.chapters):
            return
        ch = self.book.chapters[idx]
        self._current_chapter_idx = idx
        self.reader.set_content(ch.paragraphs)
        self.reader.scroll_to(0)
        self.control_bar.set_progress(0, ch.title)

    # ── 自动滚动 ──────────────────────────────────────────────

    def _on_page_up(self):
        """手动上一页（向上翻 ~80% 可视区域）"""
        viewport_h = self.reader.viewport().height()
        self.reader.scroll_by(-viewport_h * 0.8)

    def _on_page_down(self):
        """手动下一页（向下翻 ~80% 可视区域）"""
        viewport_h = self.reader.viewport().height()
        self.reader.scroll_by(viewport_h * 0.8)

    def _on_toggle_scroll(self):
        self.scroller.toggle()
        self._scrolling = self.scroller.enabled
        self.control_bar.set_scroll_state(self._scrolling)

    def _on_speed_change(self, value: int):
        self.scroller.speed = value
        self.config.auto_scroll_speed = value
        save_config(self.config)

    def _sync_scroll_state(self):
        """定时同步滚动进度到控制栏"""
        if not self.book:
            return
        ratio = self.reader.scroll_ratio()
        if self.book.chapters:
            ch = self.book.chapters[self._current_chapter_idx]
            self.control_bar.set_progress(ratio, ch.title)

        # 到达底部时自动切下一章
        if ratio >= 0.99 and self._scrolling:
            self._next_chapter()

    def _next_chapter(self):
        """切换到下一章"""
        if not self.book:
            return
        nxt = self._current_chapter_idx + 1
        if nxt < len(self.book.chapters):
            self._current_chapter_idx = nxt
            self._load_chapter(nxt)
        else:
            self.scroller.stop()
            self.control_bar.set_scroll_state(False)

    # ── 主题 ──────────────────────────────────────────────────

    def _on_theme_change(self, name: str):
        self._theme = name
        self.config.theme = name
        save_config(self.config)
        self._apply_theme()

    def _apply_theme(self):
        colors = get_theme_colors(self._theme)
        self.control_bar.apply_theme(colors)
        self.reader.apply_theme(colors, QFont(self.config.font_family, self._font_size))

        # 中央容器背景
        style = f"""
            QWidget#centralWidget {{
                background-color: {colors['bg']};
            }}
        """
        self.centralWidget().setStyleSheet(style)

    # ── 字体 ──────────────────────────────────────────────────

    def _on_font_change(self, family: str, delta: int, spacing: float):
        """字号调整(+1/-1)"""
        self._font_size = max(10, min(40, self._font_size + delta))
        self.config.font_size = self._font_size
        save_config(self.config)
        self._apply_font()

    def _apply_font(self):
        """应用字体设置"""
        # 行距通过样式设置
        font = QFont(self.config.font_family, self._font_size)
        self.reader.text_label.setFont(font)

    # ── 拖拽支持 ──────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith((".txt", ".epub")):
                self._on_open_file(path)

    # ── 持久化 ────────────────────────────────────────────────

    def _restore_last_book(self):
        """启动时恢复上次打开的文件"""
        if self.config.recent_files:
            last = self.config.recent_files[0]
            if os.path.exists(last):
                self._on_open_file(last)

    def _save_bookmark(self):
        """保存当前阅读进度"""
        if not self.book:
            return
        bm = Bookmark(
            file_path=self.book.file_path,
            title=self.book.title,
            chapter_index=self._current_chapter_idx,
            paragraph_index=0,
            scroll_position=self.reader.scroll_position(),
        )
        save_bookmark(self.book.file_path, bm)

    # ── 窗口事件 ──────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        save_config(self.config)
        # 重设控制栏位置
        self.control_bar.setGeometry(
            0, self.height() - self.control_bar.height(),
            self.width(), self.control_bar.height()
        )

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config.window_x = self.x()
        self.config.window_y = self.y()
        save_config(self.config)

    def closeEvent(self, event):
        """关闭前保存书签和配置"""
        self._save_bookmark()
        save_config(self.config)
        super().closeEvent(event)

    # ── 窗口拖拽 & 调整大小 ──────────────────────────────────

    def _detect_edge(self, pos: QPoint) -> int:
        """检测鼠标靠近哪个边缘/角落: 0=无, 1=顶, 2=左, 3=右, 4=左上, 5=右上"""
        m = self._RESIZE_MARGIN
        w, h = self.width(), self.height()
        top = pos.y() <= m
        left = pos.x() <= m
        right = pos.x() >= w - m

        if top and left:
            return 4   # 左上角
        if top and right:
            return 5   # 右上角
        if top:
            return 1   # 顶边
        if left:
            return 2   # 左边
        if right:
            return 3   # 右边
        return 0

    def _edge_cursor(self, edge: int) -> Qt.CursorShape:
        """根据边缘类型返回光标样式"""
        if edge == 1:   # 顶边
            return Qt.CursorShape.SizeVerCursor
        if edge in (2, 3):  # 左/右边
            return Qt.CursorShape.SizeHorCursor
        if edge == 4:   # 左上角
            return Qt.CursorShape.SizeFDiagCursor
        if edge == 5:   # 右上角
            return Qt.CursorShape.SizeBDiagCursor
        return Qt.CursorShape.ArrowCursor

    def _update_cursor(self, pos: QPoint):
        """根据鼠标位置更新光标样式"""
        edge = self._detect_edge(pos)
        self.setCursor(self._edge_cursor(edge))

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下：判断是拖拽移动还是调整大小"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_start_geom = self.geometry()

            edge = self._detect_edge(pos)
            if edge:
                self._resize_edge = edge
                self._moving = False
            else:
                self._moving = True
                self._resize_edge = 0

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动：执行拖拽或调整大小"""
        global_pos = event.globalPosition().toPoint()
        g0 = self._drag_start_geom  # 起始几何

        if self._resize_edge and g0:
            delta = self._drag_start_pos - global_pos  # 注意: 反方向
            edge = self._resize_edge
            x, y, w, h = g0.x(), g0.y(), g0.width(), g0.height()
            screen_w = self.screen().availableGeometry().width() if self.screen() else 1920

            if edge == 1:  # 顶边 — 调整高度
                new_h = max(100, min(600, h + delta.y()))
                y = g0.y() - (new_h - h)
                h = new_h
            elif edge == 2:  # 左边 — 调整宽度
                new_w = max(400, min(screen_w, w + delta.x()))
                x = g0.x() - (new_w - w)
                w = new_w
            elif edge == 3:  # 右边 — 调整宽度
                w = max(400, min(screen_w, w - delta.x()))
            elif edge == 4:  # 左上角 — 同时调宽高
                new_w = max(400, min(screen_w, w + delta.x()))
                new_h = max(100, min(600, h + delta.y()))
                x = g0.x() - (new_w - w)
                y = g0.y() - (new_h - h)
                w, h = new_w, new_h
            elif edge == 5:  # 右上角 — 同时调宽高
                new_w = max(400, min(screen_w, w - delta.x()))
                new_h = max(100, min(600, h + delta.y()))
                y = g0.y() - (new_h - h)
                w, h = new_w, new_h

            self.setGeometry(x, y, w, h)

        elif self._moving:
            delta = global_pos - self._drag_start_pos
            self.move(g0.x() + delta.x(), g0.y() + delta.y())
        else:
            self._update_cursor(event.position().toPoint())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放：停止拖拽"""
        self._moving = False
        self._resize_edge = 0
        super().mouseReleaseEvent(event)

    # ── 键盘快捷键 ────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space:
            # 空格切换自动滚动
            self._on_toggle_scroll()
        elif key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_PageUp or key == Qt.Key.Key_Left:
            # 上一页
            self._on_page_up()
        elif key == Qt.Key.Key_PageDown or key == Qt.Key.Key_Right:
            # 下一页
            self._on_page_down()
        elif key == Qt.Key.Key_Up:
            self.reader.scroll_by(-50)
        elif key == Qt.Key.Key_Down:
            self.reader.scroll_by(50)
        else:
            super().keyPressEvent(event)
