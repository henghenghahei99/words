#!/usr/bin/env python3
"""把 46 个单元的 *_EXPLAIN.md 合成一本可打印 PDF。

输出：output/explain_all.pdf（A4、双栏、单元另起一页、目录带页码）

做法：先空目录跑一遍收集每个单元的起始页，再用该页码重建，重复到页码稳定；
目录用固定表格绘制，不用 ReportLab 的 TableOfContents（避免多出空条目）。

用法：python3 make_explain_pdf.py
"""
import html as htmlmod
import glob
import os
import re
import tempfile

from fontTools.ttLib import TTFont as _FTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
ROOT = next((os.path.join(PARENT, d) for d in ("output", "ourput")
             if os.path.isdir(os.path.join(PARENT, d))),
            os.path.join(PARENT, "output"))
OUT = os.path.join(ROOT, "explain_all.pdf")
FONT_CACHE = os.path.join(tempfile.gettempdir(), "words_fonts")

ACCENT = colors.HexColor("#0d6c8a")
MUTED = colors.HexColor("#6b7683")
INK = colors.HexColor("#1d232b")
RULE = colors.HexColor("#c9d3da")


def _pick(*cands):
    for p in cands:
        if p and os.path.exists(p):
            return p
    return None


FONT_CJK = _pick(os.path.join(FONT_CACHE, "NotoSerifSC-Regular.ttf"),
                 "/tmp/NotoSerifSC-Regular.ttf",
                 "/usr/share/fonts/truetype/noto/NotoSerifSC-Regular.ttf")
if not FONT_CJK:
    raise SystemExit("找不到中文字体；先跑 seach/_tools/prepare_fonts.py")
FONT_CJK_B = _pick(os.path.join(FONT_CACHE, "NotoSerifSC-Bold.ttf"),
                   "/tmp/NotoSerifSC-Bold.ttf") or FONT_CJK
FONT_LAT = _pick(os.path.join(FONT_CACHE, "DejaVuSans.ttf"),
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
if not FONT_LAT:
    raise SystemExit("找不到拉丁字体 DejaVuSans.ttf")

pdfmetrics.registerFont(TTFont("CJK", FONT_CJK))
pdfmetrics.registerFont(TTFont("CJK-Bold", FONT_CJK_B))
pdfmetrics.registerFont(TTFont("LAT", FONT_LAT))
pdfmetrics.registerFontFamily("CJK", normal="CJK", bold="CJK-Bold",
                              italic="CJK", boldItalic="CJK-Bold")

CJK_CMAP = set(_FTFont(FONT_CJK, lazy=True).getBestCmap() or {})


def _runs(s):
    """CJK 字体缺的字形（音标等）改用拉丁字体。"""
    out, buf, lat = [], "", None
    for ch in s:
        is_lat = (ord(ch) not in CJK_CMAP) and not ch.isspace()
        if is_lat != lat:
            if buf:
                out.append(('\x00L\x00' + buf + '\x00/\x00') if lat else buf)
            buf, lat = "", is_lat
        buf += htmlmod.escape(ch, quote=False)
    if buf:
        out.append(('\x00L\x00' + buf + '\x00/\x00') if lat else buf)
    return "".join(out).replace('\x00L\x00', '<font name="LAT">') \
        .replace('\x00/\x00', '</font>')


def markup(s):
    s = _runs(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", s)
    return s


STY = {
    "title": ParagraphStyle("cover_title", fontName="CJK-Bold", fontSize=27,
                            leading=36, textColor=INK, spaceAfter=10),
    "sub": ParagraphStyle("cover_sub", fontName="CJK", fontSize=12.5,
                          leading=20, textColor=MUTED),
    "note": ParagraphStyle("cover_note", fontName="CJK", fontSize=9.5,
                           leading=15, textColor=MUTED),
    "unith": ParagraphStyle("UnitH", fontName="CJK-Bold", fontSize=17,
                            leading=23, textColor=ACCENT, spaceAfter=6),
    "toch": ParagraphStyle("TOCHead", fontName="CJK-Bold", fontSize=17,
                           leading=23, textColor=ACCENT, spaceAfter=10),
    "sect": ParagraphStyle("SectH", fontName="CJK-Bold", fontSize=11.5,
                           leading=16, textColor=ACCENT, spaceBefore=8,
                           spaceAfter=3, keepWithNext=1),
    "entry": ParagraphStyle("EntryH", fontName="CJK-Bold", fontSize=10,
                            leading=14, textColor=INK, spaceBefore=6,
                            spaceAfter=1.5, keepWithNext=1),
    "bullet": ParagraphStyle("Bullet", fontName="CJK", fontSize=8.2,
                             leading=12, leftIndent=8, bulletIndent=0,
                             textColor=INK, spaceAfter=0.6),
    "quote": ParagraphStyle("Quote", fontName="CJK", fontSize=8,
                            leading=12, textColor=MUTED, spaceAfter=2),
    "cell": ParagraphStyle("Cell", fontName="CJK", fontSize=7,
                           leading=9.6, textColor=INK),
    "cellh": ParagraphStyle("CellH", fontName="CJK-Bold", fontSize=7,
                            leading=9.6, textColor=colors.white),
    "tocrow": ParagraphStyle("TOCRow", fontName="CJK", fontSize=8.6,
                             leading=12.2, textColor=INK),
    "tocpage": ParagraphStyle("TOCPage", fontName="CJK", fontSize=8.6,
                              leading=12.2, textColor=INK, alignment=2),
}


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        BaseDocTemplate.__init__(
            self, fn, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm,
            topMargin=17 * mm, bottomMargin=15 * mm,
            title="初中英语单词表 · 说文解字合集", author="words_local",
            **kw)
        gutter = 6.5 * mm
        col_w = (self.width - gutter) / 2
        frames = [
            Frame(self.leftMargin, self.bottomMargin, col_w, self.height,
                  id="c1", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0),
            Frame(self.leftMargin + col_w + gutter, self.bottomMargin, col_w,
                  self.height, id="c2", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0),
        ]
        self.addPageTemplates([PageTemplate(id="main", frames=frames,
                                            onPage=self._footer)])
        self.col_w = col_w
        self.unit_pages = {}

    def _footer(self, canv, doc):
        canv.saveState()
        canv.setFont("CJK", 7.5)
        canv.setFillColor(MUTED)
        canv.drawCentredString(A4[0] / 2, 9 * mm, "第 %d 页" % doc.page)
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.4)
        canv.line(17 * mm, 12.5 * mm, A4[0] - 17 * mm, 12.5 * mm)
        canv.restoreState()

    def afterFlowable(self, flowable):
        style = getattr(flowable, "style", None)
        if style is not None and style.name == "UnitH":
            self.unit_pages[flowable.getPlainText().strip()] = self.page


def unit_sort(p):
    u = os.path.basename(p)[:-len("_EXPLAIN.md")]
    grade, rest = u.split("_U")
    order = {"7A": 1, "7B": 2, "8A": 3, "8B": 4, "9A": 5, "9B": 6}
    return (order.get(grade, 9), int(rest))


def make_table(rows, width):
    head = rows[0]
    body = rows[1:]
    ncol = len(head)
    lens = []
    for i in range(ncol):
        col = [head[i]] + [r[i] if i < len(r) else "" for r in body]
        lens.append(max(len(c) for c in col))
    total = sum(lens) or 1
    widths = [max(width * 0.1, width * l / total) for l in lens]
    scale = width / sum(widths)
    widths = [w * scale for w in widths]
    data = [[Paragraph(markup(c), STY["cellh"]) for c in head]]
    for r in body:
        data.append([Paragraph(markup(c), STY["cell"])
                     for c in (r + [""] * (ncol - len(r)))[:ncol]])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
    ]))
    return t


def parse_md(path, col_w):
    story, table_buf = [], []

    def flush_table():
        if table_buf:
            story.append(Spacer(1, 2))
            story.append(make_table(table_buf, col_w))
            story.append(Spacer(1, 4))
            table_buf.clear()

    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            table_buf.append(cells)
            continue
        flush_table()
        if not line.strip() or line.strip() == "---":
            continue
        if line.startswith("# "):
            continue
        if line.startswith("### "):
            story.append(Paragraph(markup(line[4:]), STY["entry"]))
        elif line.startswith("## "):
            story.append(Paragraph(markup(line[3:]), STY["sect"]))
        elif line.startswith("> "):
            story.append(Paragraph(markup(line[2:]), STY["quote"]))
        elif line.startswith("- "):
            story.append(Paragraph(markup(line[2:]), STY["bullet"],
                                   bulletText="·"))
        else:
            story.append(Paragraph(markup(line), STY["bullet"]))
    flush_table()
    return story


def toc_block(titles, pages, col_w):
    rows = [[Paragraph(markup(t), STY["tocrow"]),
             Paragraph(str(pages.get(t, "")), STY["tocpage"])] for t in titles]
    half = (len(rows) + 1) // 2
    left, right = rows[:half], rows[half:]
    left += [["", ""]] * (half - len(left))
    right += [["", ""]] * (half - len(right))
    data = [list(l) + list(r) for l, r in zip(left, right)]
    w1 = (col_w - 2 * mm) * 0.86
    w2 = (col_w - 2 * mm) * 0.14
    t = Table(data, colWidths=[w1, w2, w1, w2], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
        ("LINEBELOW", (0, 0), (0, -1), 0.2, colors.HexColor("#e4eaee")),
        ("LINEBELOW", (2, 0), (2, -1), 0.2, colors.HexColor("#e4eaee")),
    ]))
    return t


def build(files, pages, out):
    doc = Doc(out)
    story = []
    story.append(Spacer(1, 45 * mm))
    story.append(Paragraph("初中英语单词表 · 说文解字", STY["title"]))
    story.append(Paragraph("沪教牛津版（2024/2025 修订）· 广州 / 深圳",
                           STY["sub"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("7A / 7B / 8A / 8B / 9A / 9B 共 %d 个单元" %
                           len(files), STY["sub"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "每条含：词根与渊源 / 同根词 / 前缀·后缀 / 同义·反义（带中文）/ "
        "变形（时态·复数·比较级·词性派生）；搭配条目只给同义·反义搭配两行。",
        STY["note"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "词源按 Oxford / Merriam-Webster / Online Etymology Dictionary 通行说法"
        "整理，<b>不是教材注释</b>，有争议处标“存疑”。", STY["note"]))
    story.append(PageBreak())

    titles = []
    for path in files:
        title = os.path.basename(path)[:-len("_EXPLAIN.md")]
        for line in open(path, encoding="utf-8"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
        titles.append(title)

    story.append(Paragraph("目　录", STY["toch"]))
    story.append(toc_block(titles, pages, doc.col_w))

    for path, title in zip(files, titles):
        story.append(PageBreak())
        story.append(Paragraph(markup(title), STY["unith"]))
        story.extend(parse_md(path, doc.col_w))

    doc.build(story)
    return doc.unit_pages


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "[0-9]*_U*_EXPLAIN.md")),
                   key=unit_sort)
    if not files:
        raise SystemExit("没有找到 *_EXPLAIN.md")
    pages = {}
    tmp = os.path.join(ROOT, ".explain_tmp.pdf")
    for _ in range(4):
        new = build(files, pages, tmp)
        if new == pages:
            break
        pages = new
    final = build(files, pages, OUT)
    if os.path.exists(tmp):
        os.remove(tmp)
    print("pdf:", OUT, "units:", len(files),
          "last unit starts p%s" % (max(final.values()) if final else "?"))


if __name__ == "__main__":
    main()
