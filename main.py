"""小说阅读器入口"""
import sys
import os

# 确保能找到 src 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.app import NovelReader


def main():
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("NovelReader")
    app.setOrganizationName("NovelReader")

    reader = NovelReader()
    reader.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
