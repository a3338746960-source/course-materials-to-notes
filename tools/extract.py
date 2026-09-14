#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程材料文本提取器
==================

把课程原始材料（PDF 课件 / .docx 大纲 / 老式 .ppt / 新版 .pptx）转成纯文本，
供后续整理成 Obsidian 笔记时核对与引用。

用法：
    python extract.py <源文件> <输出txt>

依赖：
    pip install pdfplumber python-docx olefile python-pptx

设计说明：
  - PDF 逐页输出并标注每页图片数，便于判断该页是否是扫描件 / 图表页。
  - .docx 保留 Heading 层级与表格——syllabus 的考核表常以表格形式给出。
  - 老式 .ppt 是二进制 OLE 复合文档，没有官方纯 Python 解析库，
    这里直接读 PowerPoint Document 流并递归下降（见 NOTES 一节）。
  - .pptx 是 zip + XML，走 python-pptx（可选依赖）。

NOTES —— .ppt 解析的两个坑：
  1) 必须递归进容器。该流是嵌套记录结构，文字块藏在 Slide(0x03E8) 等容器内部。
     判据：(rec_ver_inst & 0x000F) == 0x000F 即容器。
     若遇容器按 rec_len 整块跳过，会对所有 .ppt 输出 0 字符。
  2) 逐页分组不可靠。不同 deck 分出的 SLIDE 块数量差异极大（0 / 1 / 8 不等）。
     正文完整可靠，但不要依赖 SLIDE 编号定位页码。
"""

import os
import re
import struct
import sys

try:
    import olefile
except ImportError:
    olefile = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None


def clean(t):
    """统一换行与空白，压掉多余空行。"""
    t = t.replace("\x0b", "\n").replace("\x0c", "\n")
    t = t.replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def from_pdf(path):
    if pdfplumber is None:
        raise RuntimeError("缺少 pdfplumber，请先 pip install pdfplumber")
    out = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            imgs = len(page.images)
            out.append(f"\n===== PAGE {i} (images={imgs}) =====\n{clean(txt)}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# DOCX
# --------------------------------------------------------------------------
def from_docx(path):
    if docx is None:
        raise RuntimeError("缺少 python-docx，请先 pip install python-docx")
    d = docx.Document(path)
    out = []
    for p in d.paragraphs:
        s = p.text.strip()
        if not s:
            continue
        st = p.style.name if p.style else ""
        prefix = ""
        if st.startswith("Heading"):
            try:
                prefix = "#" * int(st.split()[-1]) + " "
            except ValueError:
                prefix = ""
        elif "List" in st:
            prefix = "- "
        out.append(prefix + s)
    for ti, tb in enumerate(d.tables, 1):
        out.append(f"\n===== TABLE {ti} =====")
        for row in tb.rows:
            out.append(" | ".join(c.text.strip().replace("\n", " ") for c in row.cells))
    return "\n".join(out)


# --------------------------------------------------------------------------
# 老式 .ppt（二进制 OLE）
# --------------------------------------------------------------------------
ATOM_CHARS = 0x0FA0        # TextCharsAtom  -> UTF-16LE
ATOM_BYTES = 0x0FA8        # TextBytesAtom  -> cp1252
SLIDE_CONTAINER = 0x03E8   # Slide
DOC_CONTAINER = 0x0FF0     # Document


def _is_container(rec_ver_inst):
    """记录头的低 4 位为 0xF 表示这是容器记录，必须递归进入。"""
    return (rec_ver_inst & 0x000F) == 0x000F


def _walk(data, start, end, out, depth=0, max_depth=16):
    """递归下降遍历记录树，收集所有文字块。"""
    i = start
    while i + 8 <= end:
        rec_ver_inst, rec_type, rec_len = struct.unpack_from("<HHI", data, i)
        body = i + 8
        if body + rec_len > end:
            i += 1
            continue
        if _is_container(rec_ver_inst):
            if depth < max_depth:
                _walk(data, body, body + rec_len, out, depth + 1, max_depth)
        elif rec_type == ATOM_CHARS:
            out.append(data[body:body + rec_len].decode("utf-16-le", "ignore"))
        elif rec_type == ATOM_BYTES:
            out.append(data[body:body + rec_len].decode("cp1252", "ignore"))
        i = body + rec_len


def _dedupe(chunks):
    seen, res = set(), []
    for t in chunks:
        t = clean(t)
        if t and t not in seen:
            seen.add(t)
            res.append(t)
    return res


def from_ppt(path):
    if olefile is None:
        raise RuntimeError("缺少 olefile，请先 pip install olefile")
    ole = olefile.OleFileIO(path)
    try:
        if not ole.exists("PowerPoint Document"):
            return "(no PowerPoint Document stream)"
        data = ole.openstream("PowerPoint Document").read()
    finally:
        ole.close()

    slides, i, n = [], 0, len(data)
    while i + 8 <= n:
        rec_ver_inst, rec_type, rec_len = struct.unpack_from("<HHI", data, i)
        body = i + 8
        if body + rec_len > n:
            i += 1
            continue
        if rec_type == SLIDE_CONTAINER:
            chunks = []
            _walk(data, body, body + rec_len, chunks)
            texts = _dedupe(chunks)
            if texts:
                slides.append(texts)
        i = body + rec_len

    if slides:
        blocks = []
        for idx, texts in enumerate(slides, 1):
            blocks.append(f"\n===== SLIDE {idx} =====\n" + "\n".join(texts))
        return "\n".join(blocks)

    # 退化路径：分不出 Slide 容器时，整棵树上收一遍
    all_chunks = []
    _walk(data, 0, n, all_chunks)
    texts = _dedupe(all_chunks)
    if not texts:
        return "(no text atoms found)"
    return "\n".join(texts)


# --------------------------------------------------------------------------
# .pptx（zip + XML）
# --------------------------------------------------------------------------
def from_pptx(path):
    try:
        from pptx import Presentation
    except ImportError:
        return ("(.pptx 需要 python-pptx：pip install python-pptx)\n"
                "也可先另存为 .pdf 再提取。")
    prs = Presentation(path)
    blocks = []
    for idx, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    s = "".join(run.text for run in para.runs).strip()
                    if s:
                        texts.append(s)
            if getattr(shape, "has_table", False) and shape.has_table:
                for row in shape.table.rows:
                    texts.append(" | ".join(c.text.strip() for c in row.cells))
        if texts:
            blocks.append(f"\n===== SLIDE {idx} =====\n" + "\n".join(texts))
    return "\n".join(blocks) or "(no text found)"


# --------------------------------------------------------------------------
def main(src, dst):
    ext = os.path.splitext(src)[1].lower()
    if ext == ".pdf":
        txt = from_pdf(src)
    elif ext == ".docx":
        txt = from_docx(src)
    elif ext == ".ppt":
        txt = from_ppt(src)
    elif ext == ".pptx":
        txt = from_pptx(src)
    else:
        txt = "(unsupported extension: %s)" % ext

    parent = os.path.dirname(dst)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"{dst}  <--  {len(txt)} chars")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
