import re
import os
from typing import List, Dict
import fitz


def _extract_toc_chapters(doc: fitz.Document, text: str) -> List[Dict] | None:
    """Try to extract chapters from the PDF's Table of Contents (outline)."""
    toc = doc.get_toc()
    if not toc or len(toc) < 2:
        return None

    lines = text.split("\n")
    chapters = []
    pages_per_chapter = []
    for entry in toc:
        level, title, page_num = entry
        if level == 1 and title.strip():
            pages_per_chapter.append(page_num)

    if len(pages_per_chapter) < 2:
        return None

    for i, entry in enumerate(toc):
        level, title, page_num = entry
        if level != 1 or not title.strip():
            continue
        start_page = page_num - 1
        end_page = pages_per_chapter[i + 1] - 1 if i + 1 < len(pages_per_chapter) else doc.page_count
        content_parts = []
        for p in range(start_page, min(end_page, doc.page_count)):
            page_text = doc[p].get_text()
            if page_text.strip():
                content_parts.append(page_text)
        chapter_text = "\n".join(content_parts).strip()
        if chapter_text:
            chapters.append({
                "index": len(chapters) + 1,
                "title": title.strip(),
                "content": chapter_text,
            })

    if len(chapters) >= 2:
        return chapters
    return None


def _extract_text_with_fonts(doc: fitz.Document) -> tuple[str, List[Dict]]:
    """
    Extract text from PDF while recording font sizes.
    Returns (full_text, font_info) where font_info is a list of
    {text, font_size, line_index} for lines with notably large fonts.
    """
    all_lines = []
    font_info = []
    line_idx = 0

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        page_lines = []

        for block in blocks:
            if block["type"] != 0:
                continue
            for line_data in block.get("lines", []):
                spans = line_data.get("spans", [])
                if not spans:
                    continue
                fonts = [s["size"] for s in spans]
                avg_font = sum(fonts) / len(fonts)
                text = "".join(s["text"] for s in spans).strip()
                if not text:
                    continue
                all_lines.append(text)
                page_lines.append(text)
                font_info.append({
                    "text": text,
                    "font_size": avg_font,
                    "line_index": line_idx,
                })
                line_idx += 1

    full_text = "\n".join(all_lines)
    return full_text, font_info


def _detect_chapters_by_font(font_info: List[Dict], full_text: str) -> List[Dict] | None:
    """Detect chapter headings by font size (larger = heading)."""
    if len(font_info) < 5:
        return None

    sizes = [f["font_size"] for f in font_info]
    median_size = sorted(sizes)[len(sizes) // 2]
    headings = []

    for f in font_info:
        if f["font_size"] >= median_size * 1.3 and len(f["text"]) >= 3 and len(f["text"]) <= 80:
            headings.append({
                "line_index": f["line_index"],
                "title": f["text"],
            })

    if len(headings) < 2:
        return None

    lines = full_text.split("\n")
    chapters = []
    for idx, heading in enumerate(headings):
        start = heading["line_index"]
        end = headings[idx + 1]["line_index"] if idx + 1 < len(headings) else len(lines)
        content_lines = lines[start + 1:end]
        chapter_text = "\n".join(content_lines).strip()
        if len(chapter_text) > 50:
            chapters.append({
                "index": len(chapters) + 1,
                "title": heading["title"],
                "content": chapter_text,
            })

    if len(chapters) >= 2:
        return chapters
    return None


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            text_parts.append(text)
    doc.close()
    return "\n".join(text_parts)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


CHAPTER_PATTERNS = [
    re.compile(r"第[零一二三四五六七八九十百千万\d]+章\s*[^\n]*"),
    re.compile(r"第[零一二三四五六七八九十百千万\d]+节\s*[^\n]*"),
    re.compile(r"Chapter\s+\d+[^\n]*", re.IGNORECASE),
    re.compile(r"CHAPTER\s+\d+[^\n]*"),
    re.compile(r"PART\s+\d+[^\n]*", re.IGNORECASE),
]


def split_into_chapters(text: str) -> List[Dict]:
    if not text.strip():
        return [{"index": 1, "title": "全文", "content": "（无文本内容）"}]

    headings = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) > 80:
            continue
        for pattern in CHAPTER_PATTERNS:
            if pattern.match(line_stripped):
                headings.append({"index": i, "title": line_stripped})
                break

    if not headings:
        total = len(text)
        if total < 300:
            return [{"index": 1, "title": "全文", "content": text.strip()}]
        return _split_by_length(text)

    chapters = []
    for idx, heading in enumerate(headings):
        start = heading["index"]
        end = headings[idx + 1]["index"] if idx + 1 < len(headings) else len(lines)
        content_lines = lines[start + 1 : end]
        chapter_text = "\n".join(content_lines).strip()

        chapters.append({
            "index": idx + 1,
            "title": heading["title"],
            "content": chapter_text,
        })

    if not chapters:
        return _split_by_length(text)

    return chapters


def _split_by_length(text: str, max_chars: int = 3000) -> List[Dict]:
    chapters = []
    positions = []
    i = 0
    while i < len(text):
        end = min(i + max_chars, len(text))
        if end < len(text):
            for sep in ["\n\n", "\n", "。", ".", "；", ";"]:
                last = text.rfind(sep, i, end)
                if last > i + max_chars // 2:
                    end = last + len(sep)
                    break
        positions.append((i, end))
        i = end

    for idx, (start, end) in enumerate(positions):
        chapters.append({
            "index": idx + 1,
            "title": f"第{idx + 1}部分",
            "content": text[start:end].strip(),
        })

    return chapters


def parse_file(file_path: str, file_type: str) -> tuple:
    full_text = extract_text(file_path, file_type)

    if file_type == "pdf":
        doc = fitz.open(file_path)
        try:
            toc_chapters = _extract_toc_chapters(doc, full_text)
            if toc_chapters:
                chapter_name = os.path.splitext(os.path.basename(file_path))[0]
                return chapter_name, toc_chapters

            _, font_info = _extract_text_with_fonts(doc)
            font_chapters = _detect_chapters_by_font(font_info, full_text)
            if font_chapters:
                chapter_name = os.path.splitext(os.path.basename(file_path))[0]
                return chapter_name, font_chapters
        except Exception:
            raise
        finally:
            doc.close()

    chapter_name = os.path.splitext(os.path.basename(file_path))[0]
    chapters = split_into_chapters(full_text)
    return chapter_name, chapters
