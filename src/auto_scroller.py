"""自动滚动 — QTimer 驱动,支持鼠标悬停暂停"""
from PySide6.QtCore import QTimer, QObject


class AutoScroller(QObject):
    """管理自动滚动的定时器和状态"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._speed = 30        # 像素/秒
        self._enabled = False
        self._paused = False    # 鼠标悬停暂停
        self._scroll_callback = None  # 回调: (delta_pixels)

        # 定时器间隔(ms),每 30ms tick 一次
        self._timer.setInterval(30)

    # ── 属性 ─────────────────────────────────────────────────

    @property
    def speed(self) -> int:
        return self._speed

    @speed.setter
    def speed(self, value: int):
        self._speed = max(1, min(value, 200))

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def paused(self) -> bool:
        return self._paused

    # ── 公开方法 ─────────────────────────────────────────────

    def set_scroll_callback(self, callback):
        """设置滚动回调: callback(delta_pixels)"""
        self._scroll_callback = callback

    def start(self):
        """开始自动滚动"""
        self._enabled = True
        self._paused = False
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        """停止自动滚动"""
        self._enabled = False
        self._paused = False
        if self._timer.isActive():
            self._timer.stop()

    def pause(self):
        """暂停（鼠标悬停时）"""
        if self._enabled:
            self._paused = True

    def resume(self):
        """恢复"""
        self._paused = False

    def toggle(self):
        """切换 开/关"""
        if self._enabled:
            self.stop()
        else:
            self.start()

    # ── 内部 ─────────────────────────────────────────────────

    def _tick(self):
        if not self._enabled or self._paused:
            return
        # 30ms 间隔,计算每次 tick 的像素增量
        delta = self._speed * (30 / 1000.0)
        if self._scroll_callback:
            self._scroll_callback(delta)
