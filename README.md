# 小阅 — Windows 桌面小说阅读器

固定在 Windows 屏幕底部、任务栏上方的桌面小说阅读器，支持 Acrylic/Mica 毛玻璃模糊背景、自动滚动、手动翻页、主题切换。

> 摸鱼神器，阅读体验与工作界面融为一体。

## ✨ 特性

- 🪟 **屏幕底部贴合** — 窗口固定于任务栏上方，始终置顶
- 🔮 **Acrylic / Mica 模糊** — 自动适配 Win10/Win11 毛玻璃效果
- 👻 **透明主题** — 背景完全透明，桌面壁纸直接透出
- 📂 **拖拽打开** — 支持 `.txt` / `.epub`，自动检测编码
- 📖 **自动滚动** — 可调速，鼠标悬停自动暂停
- ⏩ **手动翻页** — 按钮 / ← → 方向键翻页
- 🎨 **多主题** — 日间 / 夜间 / 护眼绿 / 护眼米黄 / 透明
- 🔤 **字号可调** — A- / A+ 实时缩放
- 📐 **自由缩放** — 拖拽边缘 / 按钮调整窗口宽高
- 💾 **进度记忆** — 关闭后自动保存，下次启动恢复阅读位置

## 📋 环境要求

- Windows 10 / 11
- Python 3.10+

## 🚀 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Jerrychouggg/novel-reader.git
cd novel-reader

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# PowerShell:
venv\Scripts\Activate.ps1
# CMD:
venv\Scripts\activate.bat

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行
python main.py
```

## 🎮 操作说明

| 操作 | 方式 |
|------|------|
| 打开文件 | 拖拽 txt/epub 到窗口，或点击 📂 按钮 |
| 自动滚动 | 点击 ▶ 按钮，或按空格键 |
| 手动翻页 | ◀ ▶▶ 按钮，或 ← → / PageUp PageDown |
| 微调滚动 | ↑ ↓ 方向键 / 鼠标滚轮 |
| 调速 | 拖动速度滑块 |
| 切换主题 | 点击 🎨 → 选择主题 / 文字颜色 |
| 调字号 | 点击 A- / A+ |
| 调窗口大小 | 拖拽右边缘/右下角/底边，或 ⋯ 菜单中的尺寸选项 |
| 摸鱼模式 | 点击 🐟 按钮 / 双击窗口 / `Ctrl+M` |
| 拖拽移动 | 在阅读区按住左键拖拽 |
| 显示控制栏 | 鼠标移到底部 |
| 关闭 | ✕ 按钮 / `Esc`（迷你模式先退出迷你） |

## 📁 项目结构

```
novel-reader/
├── main.py              # 入口
├── requirements.txt     # 依赖
├── 启动.bat             # 双击启动（Windows）
├── .gitignore
├── README.md
└── src/
    ├── app.py           # 主窗口（无边框 + 模糊 + 拖拽 + 定位）
    ├── blur_effect.py   # Windows DWM API（Mica/Acrylic/BlurBehind）
    ├── reader_widget.py # 阅读区域组件
    ├── control_bar.py   # 悬浮控制栏（自动隐藏）
    ├── book_manager.py  # txt/epub 加载 + 编码检测
    ├── auto_scroller.py # QTimer 自动滚屏
    └── config.py        # JSON 配置/书签持久化（%APPDATA%/NovelReader/）
```

## 🛠 技术栈

- [PySide6](https://pypi.org/project/PySide6/) — Qt for Python
- [pywin32](https://pypi.org/project/pywin32/) — Windows API
- [chardet](https://pypi.org/project/chardet/) — 编码检测
- [ebooklib](https://pypi.org/project/ebooklib/) — EPUB 解析


## v1.2.0 — 摸鱼模式 & 交互优化

### 🆕 新功能

- **🐟 摸鱼模式**：一键切换为紧凑任务栏窗口（默认 420×80），仅显示单行文字与简化控制栏
  - 顶部迷你栏：播放/暂停、翻页、速度、字号、主题、退出
  - 双击窗口或 `Ctrl+M` 切换，`Esc` 退出迷你模式
- **🖱 鼠标拖拽调整窗口**：拖拽右边缘 / 右下角 / 底边直接改变窗口宽高
  - 感应区域扩大至 15px，新增可视拖拽手柄
- **🎨 自定义文字颜色**：通过系统取色器自由选择文字颜色，不受主题限制

### 🔧 改进

- **文字自适应窗口宽度**：左右边距按窗口宽度的 6% 自动计算（16~80px），拖拽缩放时文字即时自适应
- **控制栏精简**：尺寸调整按钮收入"⋯"溢出菜单，主题与文字颜色合并入口，整体节省约 40% 水平空间
- **UI 美化**：窗口圆角（16px / 迷你 12px）、按钮 hover 效果优化、5 套主题均新增迷你栏配色

### 🐛 修复

- 修复导入 epub 时 `No module named 'bs4'` 错误（补全 beautifulsoup4 依赖）
- 修复拖拽 resize 卡顿：边距更新与配置保存均加入防抖，去除冗余 `setGeometry` 调用
  
## 📝 License

MIT
