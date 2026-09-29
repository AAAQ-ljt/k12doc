#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k12doc 统一提取器：教材原件 → 纯文本缓存。

用法:
  python 工具/extract.py [选项] <输入...> <输出.txt>

输入可以是 PDF/pptx/docx 文件，也可以是目录；目录会被递归展开为其中全部
可提取文件，按文件名自然排序（活动2 排在活动10 前）合并成一份 txt。
--filter 按文件名子串筛选目录展开结果（如按年级提取一批课件）。

示例:
  # PDF 单文件
  python 工具/extract.py "doc/小学/数学/[人教版] 义务教育教科书·数学五年级下册.pdf" "提取缓存/小学-数学-五年级下册.txt"
  # 信息科技教学指南：一个年级一册、每课一个 pptx，按年级合并提取
  python 工具/extract.py --filter 一年级 "doc/小学/信息科技" "提取缓存/小学-信息科技-一年级全一册.txt"

提取路径（按扩展名自动选择，依赖缺失时自动 pip 安装）:
  .pdf   → 系统 pdftotext（首选）；不可用或输出为空时 pypdf 兜底
  .pptx  → python-pptx（文本框/表格/演讲者备注；SmartArt、图表与图片内文字取不到）
  .docx  → python-docx（段落/表格；旧版 .doc 请先另存为 .docx）

提取损失与编改对策见 AGENTS.md 第八节。缓存中的「文件: / 幻灯片 N / 第 N 页」
标记仅用于定位，编改去噪时必须删除。
"""
import os
import re
import shutil
import subprocess
import sys

SUPPORTED = {".pdf", ".pptx", ".docx"}
FILE_MARK = "\n\n============ 文件: {} ============\n"


def ensure_module(pip_name, mod_name):
    """确保可导入 mod_name，缺失则自动 pip 安装 pip_name（每台机器只需一次）。"""
    try:
        __import__(mod_name)
        return
    except ImportError:
        pass
    print(f"[extract] 缺少依赖 {pip_name}，自动安装中（仅需一次）…", file=sys.stderr)
    r = subprocess.run([sys.executable, "-m", "pip", "install", pip_name])
    if r.returncode != 0:
        sys.exit(f"[extract] 自动安装失败，请手动执行：{sys.executable} -m pip install {pip_name}")
    __import__(mod_name)


def natural_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def expand_inputs(inputs, filt):
    files = []
    for p in inputs:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                for n in names:
                    if os.path.splitext(n)[1].lower() not in SUPPORTED:
                        continue
                    if filt is not None and filt not in n:
                        continue
                    files.append(os.path.join(root, n))
        elif os.path.isfile(p):
            ext = os.path.splitext(p)[1].lower()
            if ext not in SUPPORTED:
                sys.exit(f"[extract] 不支持的文件类型: {p}（支持 {', '.join(sorted(SUPPORTED))}）")
            if filt is None or filt in os.path.basename(p):
                files.append(p)
        else:
            sys.exit(f"[extract] 路径不存在: {p}")
    return sorted(set(files), key=lambda s: (natural_key(os.path.dirname(s)), natural_key(os.path.basename(s))))


def extract_pdf(path):
    """首选 pdftotext（stdout 模式），CMap 报错走 stderr 不影响正文；空输出时 pypdf 兜底。"""
    exe = shutil.which("pdftotext")
    if exe:
        r = subprocess.run([exe, "-enc", "UTF-8", path, "-"],
                           capture_output=True, encoding="utf-8", errors="replace")
        if r.stdout and r.stdout.strip():
            if "SimSun" in (r.stderr or "") or "Adobe-GB1" in (r.stderr or ""):
                print("[extract] ⚠ CMap 报错：部分宋体内容可能缺失，编改前必须通读全文", file=sys.stderr)
            return r.stdout
    ensure_module("pypdf", "pypdf")
    from pypdf import PdfReader
    pages = []
    for i, page in enumerate(PdfReader(path).pages, 1):
        t = (page.extract_text() or "").strip()
        if t:
            pages.append(f"--- 第 {i} 页 ---\n{t}")
    return "\n".join(pages)


def extract_pptx(path):
    ensure_module("python-pptx", "pptx")
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    def shape_text(sh):
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            return [t for s in sh.shapes for t in shape_text(s)]
        parts = []
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t:
                parts.append(t)
        if getattr(sh, "has_table", False) and sh.has_table:
            rows = [" | ".join(c.text.strip().replace("\n", " ") for c in row.cells)
                    for row in sh.table.rows]
            if rows:
                parts.append("\n".join(rows))
        return parts

    out = []
    for i, slide in enumerate(Presentation(path).slides, 1):
        lines = [f"--- 幻灯片 {i} ---"]
        for sh in slide.shapes:
            lines.extend(shape_text(sh))
        if slide.has_notes_slide:
            nt = slide.notes_slide.notes_text_frame.text.strip()
            if nt:
                lines.append("〔备注〕" + nt)
        out.append("\n".join(lines))
    return "\n".join(out)


def extract_docx(path):
    ensure_module("python-docx", "docx")
    import docx
    d = docx.Document(path)
    parts = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    for tbl in d.tables:
        for row in tbl.rows:
            parts.append(" | ".join(c.text.strip().replace("\n", " ") for c in row.cells))
    return "\n".join(parts)


EXTRACTORS = {".pdf": extract_pdf, ".pptx": extract_pptx, ".docx": extract_docx}


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = sys.argv[1:]
    filt = None
    pos = []
    i = 0
    while i < len(args):
        if args[i] == "--filter":
            i += 1
            if i >= len(args):
                sys.exit("[extract] --filter 需要一个文件名子串参数")
            filt = args[i]
        else:
            pos.append(args[i])
        i += 1
    if len(pos) < 2:
        sys.exit("用法: python 工具/extract.py [--filter 子串] <输入文件或目录...> <输出.txt>")

    inputs, out = pos[:-1], pos[-1]
    files = expand_inputs(inputs, filt)
    if not files:
        sys.exit("[extract] 没有找到可提取的文件" + (f"（filter={filt}）" if filt else ""))

    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    chunks, report = [], []
    for f in files:
        name = os.path.basename(f)
        try:
            text = EXTRACTORS[os.path.splitext(f)[1].lower()](f)
        except Exception as e:
            report.append(f"  失败 {name}: {e}")
            continue
        if text.strip():
            if len(files) > 1:
                chunks.append(FILE_MARK.format(name) + text)
            else:
                chunks.append(text)
            report.append(f"  完成 {name} ({len(text)} 字符)")
        else:
            report.append(f"  空 {name}（可能是扫描版/图片型，需 OCR，勿硬提）")

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(chunks))

    print(f"[extract] 共 {len(files)} 个输入 → {out}（{os.path.getsize(out)} 字符）")
    for line in report:
        print(line)
    print("[extract] 自查提醒: ①PDF 有大量 Adobe-GB1/SimSun 报错时部分宋体内容可能缺失，编改前通读全文；"
          "②输出异常小可能是扫描版，需 OCR；③pptx 取不到 SmartArt/图表/图片内文字，编改时按语义补全并标注。"
          "详见 AGENTS.md 第八节。")


if __name__ == "__main__":
    main()
