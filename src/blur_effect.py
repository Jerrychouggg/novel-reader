"""Windows DWM API — Acrylic / Mica / BlurBehind 模糊背景效果"""
import ctypes
from ctypes import wintypes
import sys


# ── DWM API 常量 ──────────────────────────────────────────────

# DwmExtendFrameIntoClientArea
_DWM_EXTEND = 2

# DwmSetWindowAttribute 属性
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWA_MICA = 1029  # 旧版 Mica 属性（Win11 22000）

# SYSTEMBACKDROP_TYPE 枚举
DWMSBT_AUTO = 0
DWMSBT_NONE = 1
DWMSBT_MAINWINDOW = 2       # Mica
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
DWMSBT_TABBEDWINDOW = 4     # Mica Alt

# SetWindowCompositionAttribute — Win10 Acrylic
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

WCA_ACCENT_POLICY = 19


class AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class WindowCompositionAttribData(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(AccentPolicy)),
        ("SizeOfData", ctypes.c_size_t),
    ]


# ── 辅助 ───────────────────────────────────────────────────────

def _is_windows_11():
    """检测是否为 Windows 11（build >= 22000）"""
    ver = sys.getwindowsversion()
    return ver.major >= 10 and ver.build >= 22000


def _is_windows_10_1903():
    """检测是否为 Windows 10 1903+"""
    ver = sys.getwindowsversion()
    return ver.major == 10 and ver.build >= 18362


# ── 策略函数 ───────────────────────────────────────────────────

def _apply_mica(hwnd: int) -> bool:
    """Win11 Mica 效果"""
    try:
        # 深色模式（让 Mica 跟随系统主题）
        dark = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(dark),
            ctypes.sizeof(dark),
        )
        # SYSTEMBACKDROP_TYPE = MAINWINDOW (Mica)
        backdrop = ctypes.c_int(DWMSBT_MAINWINDOW)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(DWMWA_SYSTEMBACKDROP_TYPE),
            ctypes.byref(backdrop),
            ctypes.sizeof(backdrop),
        )
        return True
    except Exception:
        return False


def _apply_acrylic(hwnd: int) -> bool:
    """Win10 1903+ Acrylic 效果"""
    try:
        policy = AccentPolicy()
        policy.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
        policy.GradientColor = 0x99000000  # ARGB: 60% 透明度黑色

        data = WindowCompositionAttribData()
        data.Attribute = WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(policy)
        data.SizeOfData = ctypes.sizeof(data)

        ctypes.windll.user32.SetWindowCompositionAttribute(
            wintypes.HWND(hwnd),
            ctypes.pointer(data),
        )
        return True
    except Exception:
        return False


def _apply_blurbehind(hwnd: int) -> bool:
    """Win10 旧版 BlurBehind（模糊但不透明）"""
    try:
        policy = AccentPolicy()
        policy.AccentState = ACCENT_ENABLE_BLURBEHIND

        data = WindowCompositionAttribData()
        data.Attribute = WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(policy)
        data.SizeOfData = ctypes.sizeof(data)

        ctypes.windll.user32.SetWindowCompositionAttribute(
            wintypes.HWND(hwnd),
            ctypes.pointer(data),
        )
        return True
    except Exception:
        return False


def _extend_frame(hwnd: int):
    """将窗口框架延伸到客户区（让 DWM 管理整个窗口表面）"""
    margins = ctypes.c_int * 4
    m = margins(-1, -1, -1, -1)  # 全窗口
    try:
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
            wintypes.HWND(hwnd), m
        )
    except Exception:
        pass


# ── 公开接口 ───────────────────────────────────────────────────

def apply_blur(hwnd: int) -> str:
    """
    根据 Windows 版本自动选择最佳模糊策略。
    返回实际应用的策略名称: "mica" / "acrylic" / "blurbehind" / "none"
    """
    hwnd_int = int(hwnd)
    _extend_frame(hwnd_int)

    if _is_windows_11():
        if _apply_mica(hwnd_int):
            return "mica"

    if _is_windows_10_1903():
        if _apply_acrylic(hwnd_int):
            return "acrylic"

    if _apply_blurbehind(hwnd_int):
        return "blurbehind"

    return "none"


def refresh_blur(hwnd: int):
    """窗口尺寸/位置变化后刷新模糊（重新扩展框架即可）"""
    _extend_frame(int(hwnd))
