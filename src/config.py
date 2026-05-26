"""配置持久化 — JSON 文件存储于 %APPDATA%/NovelReader/"""
import json
import os
from typing import Any
from dataclasses import dataclass, field, asdict


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NovelReader")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
BOOKMARKS_PATH = os.path.join(CONFIG_DIR, "bookmarks.json")


@dataclass
class ReaderConfig:
    """阅读器全局配置"""
    # 窗口
    window_width: int = 800
    window_height: int = 220
    window_x: int = -1  # -1 表示自动居中/底部
    window_y: int = -1

    # 摸鱼模式
    mini_mode: bool = False
    mini_width: int = 420
    mini_height: int = 80

    # 字体
    font_family: str = "Microsoft YaHei"
    font_size: int = 16
    line_spacing: float = 1.8

    # 自定义文字颜色（空字符串表示跟随主题）
    custom_text_color: str = ""

    # 主题: "light" / "dark" / "eye_green" / "eye_warm" / "transparent"
    theme: str = "dark"

    # 自动滚动
    auto_scroll_speed: int = 30  # 像素/秒
    auto_scroll_enabled: bool = False

    # 最近打开的文件列表
    recent_files: list[str] = field(default_factory=list)


@dataclass
class Bookmark:
    """单本书的阅读进度"""
    file_path: str = ""
    title: str = ""
    chapter_index: int = 0
    paragraph_index: int = 0
    scroll_position: int = 0  # 像素偏移


# ── 主题配色表 ─────────────────────────────────────────────────

THEMES = {
    "light": {
        "bg": "#F5F5F5",
        "text": "#1A1A1A",
        "control_bg": "rgba(235, 235, 235, 0.85)",
        "control_text": "#333333",
        "control_hover": "rgba(200, 200, 200, 0.9)",
        "progress_bg": "#DDDDDD",
        "progress_fg": "#4A90D9",
        "mini_bg": "rgba(245,245,245,0.92)",
        "mini_text": "#333333",
        "mini_hover": "rgba(210,210,210,0.8)",
        "mini_btn": "#555555",
    },
    "dark": {
        "bg": "transparent",
        "text": "#E8E8E8",
        "control_bg": "rgba(30, 30, 30, 0.75)",
        "control_text": "#CCCCCC",
        "control_hover": "rgba(60, 60, 60, 0.85)",
        "progress_bg": "#444444",
        "progress_fg": "#6CB4EE",
        "mini_bg": "rgba(20,20,25,0.9)",
        "mini_text": "#D0D0D0",
        "mini_hover": "rgba(60,60,70,0.7)",
        "mini_btn": "#A0A0A0",
    },
    "eye_green": {
        "bg": "#C8D9C0",
        "text": "#2C3E2D",
        "control_bg": "rgba(160, 190, 150, 0.85)",
        "control_text": "#1A2E1B",
        "control_hover": "rgba(140, 170, 130, 0.9)",
        "progress_bg": "#A0B898",
        "progress_fg": "#3D6B3E",
        "mini_bg": "rgba(180,210,175,0.92)",
        "mini_text": "#1A2E1B",
        "mini_hover": "rgba(150,180,145,0.8)",
        "mini_btn": "#3D6B3E",
    },
    "eye_warm": {
        "bg": "#F5E6C8",
        "text": "#4A3728",
        "control_bg": "rgba(220, 200, 160, 0.85)",
        "control_text": "#3D2E20",
        "control_hover": "rgba(200, 180, 140, 0.9)",
        "progress_bg": "#D4C4A8",
        "progress_fg": "#8B6B4A",
        "mini_bg": "rgba(240,225,195,0.92)",
        "mini_text": "#3D2E20",
        "mini_hover": "rgba(210,190,155,0.8)",
        "mini_btn": "#8B6B4A",
    },
    "transparent": {
        "bg": "transparent",
        "text": "#FFFFFF",
        "control_bg": "rgba(0, 0, 0, 0.45)",
        "control_text": "#E0E0E0",
        "control_hover": "rgba(60, 60, 60, 0.6)",
        "progress_bg": "rgba(255,255,255,0.2)",
        "progress_fg": "rgba(255,255,255,0.7)",
        "mini_bg": "rgba(0,0,0,0.6)",
        "mini_text": "#FFFFFF",
        "mini_hover": "rgba(80,80,80,0.5)",
        "mini_btn": "#CCCCCC",
    },
}


# ── 读写操作 ────────────────────────────────────────────────────

def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> ReaderConfig:
    """加载全局配置,不存在则返回默认值"""
    _ensure_dir()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ReaderConfig(**data)
        except Exception:
            pass
    return ReaderConfig()


def save_config(config: ReaderConfig):
    """保存全局配置"""
    _ensure_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, ensure_ascii=False, indent=2)


def load_bookmarks() -> dict[str, Bookmark]:
    """加载所有书签: {file_path: Bookmark}"""
    _ensure_dir()
    if os.path.exists(BOOKMARKS_PATH):
        try:
            with open(BOOKMARKS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: Bookmark(**v) for k, v in data.items()}
        except Exception:
            pass
    return {}


def save_bookmark(key: str, bookmark: Bookmark):
    """保存/更新一个书签"""
    _ensure_dir()
    bookmarks = load_bookmarks()
    bookmarks[key] = bookmark
    with open(BOOKMARKS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {k: asdict(v) for k, v in bookmarks.items()},
            f, ensure_ascii=False, indent=2,
        )


def get_theme_colors(theme_name: str) -> dict:
    """获取指定主题的配色字典"""
    return THEMES.get(theme_name, THEMES["dark"])
