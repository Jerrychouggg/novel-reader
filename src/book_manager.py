"""文件加载 — txt / epub 解析,编码检测"""
import os
from dataclasses import dataclass, field

import chardet


@dataclass
class Chapter:
    title: str = ""
    paragraphs: list[str] = field(default_factory=list)


@dataclass
class Book:
    file_path: str = ""
    title: str = "未命名"
    author: str = "未知作者"
    chapters: list[Chapter] = field(default_factory=list)


# ── TXT ─────────────────────────────────────────────────────────

def _detect_encoding(file_path: str) -> str:
    """使用 chardet 检测文件编码"""
    with open(file_path, "rb") as f:
        raw = f.read(50000)
    result = chardet.detect(raw)
    encoding = result.get("encoding", "utf-8")
    # 常用编码映射
    if encoding and "gb" in encoding.lower():
        encoding = "gbk"
    elif encoding and "big5" in encoding.lower():
        encoding = "big5"
    return encoding or "utf-8"


def load_txt(file_path: str) -> Book:
    """加载 txt 文件,按空行分章节"""
    encoding = _detect_encoding(file_path)
    title = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        content = f.read()

    # 按连续空行分割章节
    lines = content.splitlines()
    chapters: list[Chapter] = []
    current_title = ""
    current_paras: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            # 空行可作为段落分隔,累积到一定量则分章
            if current_paras:
                # 看看是否是章节标题模式
                pass
            continue

        # 简单章节检测: 以"第x章"、"Chapter"、"卷"等开头
        is_chapter_title = False
        markers = ["第", "Chapter", "CHAPTER", "卷", "part", "Part", "序", "楔子", "前言", "后记"]
        for m in markers:
            if stripped.startswith(m) and len(stripped) < 60:
                is_chapter_title = True
                break

        if is_chapter_title:
            # 保存上一章
            if current_paras or current_title:
                chapters.append(Chapter(title=current_title or f"第{len(chapters)+1}章",
                                        paragraphs=list(current_paras)))
            current_title = stripped
            current_paras = []
        else:
            # 跳过太短的无意义行
            if len(stripped) >= 1:
                current_paras.append(stripped)

    # 最后一批
    if current_paras or current_title:
        chapters.append(Chapter(title=current_title or f"第{len(chapters)+1}章",
                                paragraphs=list(current_paras)))

    # 如果没有检测到章节,整个文本作为一个章节
    if not chapters:
        all_paras = [l.strip() for l in lines if l.strip()]
        chapters.append(Chapter(title="全文", paragraphs=all_paras))

    return Book(file_path=file_path, title=title, chapters=chapters)


# ── EPUB ────────────────────────────────────────────────────────

def load_epub(file_path: str) -> Book:
    """加载 epub 文件"""
    try:
        from ebooklib import epub
    except ImportError:
        raise ImportError("请安装 ebooklib: pip install ebooklib")

    book = epub.read_epub(file_path)
    title = "未命名"
    author = "未知作者"

    # 元数据
    titles = book.get_metadata("DC", "title")
    if titles:
        title = titles[0][0]
    creators = book.get_metadata("DC", "creator")
    if creators:
        author = creators[0][0]

    chapters: list[Chapter] = []
    from bs4 import BeautifulSoup

    for item in book.get_items_of_type(9):  # ITEM_DOCUMENT = 9
        try:
            content = item.get_content().decode("utf-8", errors="replace")
        except Exception:
            continue
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()
        lines = text.splitlines()
        paragraphs = [l.strip() for l in lines if l.strip()]
        if paragraphs:
            chapter_title = paragraphs[0] if len(paragraphs[0]) < 80 else f"第{len(chapters)+1}章"
            chapters.append(Chapter(title=chapter_title, paragraphs=paragraphs))

    if not chapters:
        chapters.append(Chapter(title="全文", paragraphs=["（无法解析内容）"]))

    return Book(file_path=file_path, title=title, author=author, chapters=chapters)


# ── 统一接口 ────────────────────────────────────────────────────

def load_book(file_path: str) -> Book:
    """根据扩展名自动选择加载器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return load_txt(file_path)
    elif ext == ".epub":
        return load_epub(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")
