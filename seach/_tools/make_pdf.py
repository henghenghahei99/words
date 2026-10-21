#!/usr/bin/env python3
"""Build a printable PDF of the dictionary (A4, TOC with page numbers).

Output: output/dictionary.pdf
"""
import html as htmlmod
import json
import os
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, PageBreak,
                                Paragraph, Spacer, KeepTogether, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
DATA = os.path.join(SEARCH, "data")
OUT = os.path.join(SEARCH, "output")
LEVELS = ["小学", "初中", "高中", "CET4", "CET6"]
ACCENT = colors.HexColor("#0d6c8a")
MUTED = colors.HexColor("#6b7683")
INK = colors.HexColor("#1d232b")

FONT_CJK = "/tmp/NotoSerifSC-Regular.ttf"
FONT_CJK_B = "/tmp/NotoSerifSC-Bold.ttf"
if not os.path.exists(FONT_CJK_B):
    print("bold TTF missing, falling back to regular")
    FONT_CJK_B = FONT_CJK
FONT_LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_CJK))
pdfmetrics.registerFont(TTFont("CJK-Bold", FONT_CJK_B))
pdfmetrics.registerFont(TTFont("LAT", FONT_LAT))
pdfmetrics.registerFont(TTFont("LAT-Bold", FONT_LAT_B))
pdfmetrics.registerFontFamily("CJK", normal="CJK", bold="CJK-Bold",
                              italic="CJK", boldItalic="CJK-Bold")
pdfmetrics.registerFontFamily("LAT", normal="LAT", bold="LAT-Bold",
                              italic="LAT", boldItalic="LAT-Bold")

from fontTools.ttLib import TTFont as _FTFont  # noqa: E402
CJK_CMAP = set(_FTFont(FONT_CJK, lazy=True).getBestCmap() or {})


def _runs(s):
    """Wrap characters not in the CJK font with the Latin fallback font."""
    out, buf, lat = [], "", None
    for ch in s:
        is_lat = (ord(ch) not in CJK_CMAP) and not ch.isspace()
        if is_lat != lat:
            if buf:
                out.append(('\x00LAT\x00' + buf + '\x00/\x00') if lat else buf)
            buf, lat = "", is_lat
        buf += htmlmod.escape(ch, quote=False)
    if buf:
        out.append(('\x00LAT\x00' + buf + '\x00/\x00') if lat else buf)
    return "".join(out).replace('\x00LAT\x00', '<font name="LAT">') \
        .replace('\x00/\x00', '</font>')


def load():
    words = {w["word"].lower(): w for w in
             json.load(open(os.path.join(DATA, "words.json"), encoding="utf-8"))}
    entries = {}
    for line in open(os.path.join(DATA, "entries.jsonl"), encoding="utf-8"):
        if "\t" not in line:
            continue
        w, b = line.rstrip("\n").split("\t", 1)
        entries[w] = b.replace("\\n", "\n")
    keys = [w for w in sorted(entries) if w in words]
    return words, entries, keys


def markup(s):
    s = _runs(s.replace("/-／", "/—/"))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", s)
    return s


STY = {
    "cover_title": ParagraphStyle("cover_title", fontName="CJK-Bold", fontSize=28,
                                  leading=36, textColor=INK, spaceAfter=10),
    "cover_sub": ParagraphStyle("cover_sub", fontName="CJK", fontSize=12,
                                leading=18, textColor=MUTED),
    "cover_note": ParagraphStyle("cover_note", fontName="CJK", fontSize=9.5,
                                 leading=15, textColor=MUTED),
    "h1": ParagraphStyle("LetterH", fontName="CJK-Bold", fontSize=20, leading=26,
                         textColor=ACCENT, spaceBefore=0, spaceAfter=8),
    "h1plain": ParagraphStyle("H1Plain", fontName="CJK-Bold", fontSize=20,
                              leading=26, textColor=ACCENT, spaceBefore=0,
                              spaceAfter=8),
    "entry": ParagraphStyle("entry", fontName="CJK-Bold", fontSize=10.5, leading=14,
                            textColor=INK, spaceBefore=5, spaceAfter=2,
                            keepWithNext=1),
    "bullet": ParagraphStyle("bullet", fontName="CJK", fontSize=8.5, leading=12.4,
                             leftIndent=10, bulletIndent=0, textColor=INK,
                             spaceAfter=0.5),
    "toc": ParagraphStyle("toc", fontName="CJK", fontSize=10.5, leading=17,
                          textColor=INK),
    "toc0": ParagraphStyle("toc0", fontName="CJK", fontSize=10.5, leading=17,
                           textColor=INK),
}


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                         topMargin=20 * mm, bottomMargin=17 * mm,
                         title="英语词源词典 · 说文解字", author="words_local", **kw)
        gutter = 7 * mm
        col_w = (self.width - gutter) / 2
        frames = [Frame(self.leftMargin, self.bottomMargin, col_w, self.height,
                        id="c1", leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0),
                  Frame(self.leftMargin + col_w + gutter, self.bottomMargin, col_w,
                        self.height, id="c2", leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)]
        self.addPageTemplates([PageTemplate(id="main", frames=frames,
                                            onPage=self._deco)])

    def _deco(self, canv, doc):
        canv.saveState()
        canv.setFont("CJK", 8)
        canv.setFillColor(MUTED)
        if doc.page > 1:
            canv.drawCentredString(A4[0] / 2, 10 * mm, "%d" % doc.page)
        if doc.page > 1:
            canv.setStrokeColor(colors.HexColor("#dfe4ea"))
            canv.setLineWidth(0.4)
            canv.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
            canv.drawRightString(A4[0] - 18 * mm, A4[1] - 11.5 * mm,
                                 "英语词源词典 · 说文解字")
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "LetterH":
            txt = flowable.getPlainText()
            self.notify("TOCEntry", (0, txt, self.page))


def build():
    words, entries, keys = load()
    by_letter = {}
    for w in keys:
        by_letter.setdefault(w[0].upper(), []).append(w)
    letters = sorted(by_letter)
    level_count = {lv: sum(1 for w in keys if lv in words.get(w, {}).get("levels", []))
                   for lv in LEVELS}

    story = []
    # ---- cover ----
    story += [Spacer(1, 42 * mm),
              Paragraph("英语词源词典 · 说文解字", STY["cover_title"]),
              Paragraph("小学 · 初中 · 高中 · CET4 · CET6 ｜ 共 %d 词" % len(keys),
                        STY["cover_sub"]),
              Spacer(1, 10 * mm)]
    data = [["级别", "收录词数"]] + [[lv, str(level_count[lv])] for lv in LEVELS]
    t = Table(data, colWidths=[42 * mm, 32 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "CJK", 10.5),
        ("FONT", (0, 0), (-1, 0), "CJK-Bold", 10.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#dfe4ea")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [t, Spacer(1, 14 * mm),
              Paragraph("词源按 Oxford / Merriam-Webster / Online Etymology Dictionary "
                        "通行说法整理，非教材注释；有争议处标注“存疑”。", STY["cover_note"]),
              Paragraph("查词：先看目录定位字母，再在字母内按拼写顺序查找。", STY["cover_note"]),
              PageBreak()]

    # ---- TOC ----
    story.append(Paragraph("目录", STY["h1plain"]))
    toc = TableOfContents()
    toc.levelStyles = [STY["toc0"]]
    toc.dotsMinLevel = 0
    story += [toc, PageBreak()]

    # ---- entries ----
    for L in letters:
        story.append(Paragraph(L, STY["h1"]))
        for w in by_letter[L]:
            block = entries[w].strip().splitlines()
            head = block[0][4:].strip() if block[0].startswith("### ") else w
            m = re.match(r"^(\S+)\s*", head)
            word = m.group(1) if m else head
            rest = head[len(word):].strip()
            head_par = Paragraph("%s <font size=9 color='#6b7683'>%s</font>"
                                 % (markup(word), markup(rest)), STY["entry"])
            parts = [head_par]
            for line in block[1:]:
                if line.startswith("- "):
                    parts.append(Paragraph(markup(line[2:]), STY["bullet"],
                                           bulletText="•"))
            story.append(KeepTogether(parts))
        story.append(PageBreak())

    doc = Doc(os.path.join(OUT, "dictionary.pdf"))
    doc.multiBuild(story)
    print("pdf:", os.path.join(OUT, "dictionary.pdf"))
    print("entries:", len(keys))


if __name__ == "__main__":
    build()
