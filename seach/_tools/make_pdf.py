#!/usr/bin/env python3
"""Build a printable PDF of the dictionary (A4, TOC with page numbers).

Layout: two columns, one page per letter, a clickable A-Z thumb index
(the letter navigation block on the outer edge) and PDF bookmarks.

Output: output/dictionary.pdf
"""
import html as htmlmod
import json
import os
import re
import tempfile

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

FONT_CACHE = os.environ.get("WORDS_FONT_DIR") or os.path.join(
    tempfile.gettempdir(), "words_fonts")


def _pick(*cands):
    for p in cands:
        if p and os.path.exists(p):
            return p
    return None


def _font(env, *cands):
    p = _pick(os.environ.get(env), *cands)
    if not p:
        raise SystemExit("font for %s not found; run _tools/prepare_fonts.py" % env)
    return p


FONT_CJK = _font("WORDS_FONT_CJK",
                 os.path.join(FONT_CACHE, "NotoSerifSC-Regular.ttf"),
                 "/tmp/NotoSerifSC-Regular.ttf")
FONT_CJK_B = _pick(os.environ.get("WORDS_FONT_CJK_BOLD"),
                   os.path.join(FONT_CACHE, "NotoSerifSC-Bold.ttf"),
                   "/tmp/NotoSerifSC-Bold.ttf")
if not FONT_CJK_B:
    print("bold TTF missing, falling back to regular")
    FONT_CJK_B = FONT_CJK
FONT_LAT = _font("WORDS_FONT_LAT",
                 os.path.join(FONT_CACHE, "DejaVuSans.ttf"),
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "C:/Windows/Fonts/segoeui.ttf",
                 "C:/Windows/Fonts/calibri.ttf",
                 "C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/Vera.ttf")
FONT_LAT_B = _pick(os.environ.get("WORDS_FONT_LAT_BOLD"),
                   os.path.join(FONT_CACHE, "DejaVuSans-Bold.ttf"),
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "C:/Windows/Fonts/segoeuib.ttf",
                   "C:/Windows/Fonts/calibrib.ttf",
                   "C:/Windows/Fonts/arialbd.ttf")
if not FONT_LAT_B:
    FONT_LAT_B = FONT_LAT
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

# ---- letter tab: one tab on the outer edge showing the page's letter ----
TAB_W = 15.0 * mm          # tab width (it runs off the page edge)
TAB_H = 15.0 * mm          # tab height
TAB_OVERHANG = 1.5 * mm    # part of the tab that sits outside the page
TAB_RADIUS = 3.0 * mm
TAB_EDGE = colors.HexColor("#0a5a73")
TAB_Y_FIRST = 250 * mm     # bottom edge of the A tab
TAB_Y_LAST = 30 * mm       # bottom edge of the Z tab
TAB_STEPS = 25             # A..Z spans 25 steps


def NAV_DEST(letter):
    return "letter-" + letter


class LetterHead(Paragraph):
    """Letter heading that also registers a named PDF destination."""

    def __init__(self, letter):
        Paragraph.__init__(self, markup(letter), STY["h1"])
        self.letter = letter

    def draw(self):
        self.canv.bookmarkPage(NAV_DEST(self.letter), fit="Fit")
        Paragraph.draw(self)


class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                         topMargin=20 * mm, bottomMargin=17 * mm,
                         title="英语词源词典 · 说文解字", author="words_local", **kw)
        self.letter_pages = {}     # letter -> page in the current pass
        self.prev_pages = {}       # letter -> page from the previous pass
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

    def build(self, flowables, **kw):
        # multiBuild runs several passes; reuse the previous layout so that the
        # thumb index can highlight the letter a page belongs to.
        self.prev_pages = dict(self.letter_pages)
        self.letter_pages = {}
        return super().build(flowables, **kw)

    def _letter_at(self, page):
        cur = None
        for letter, p in sorted(self.prev_pages.items(), key=lambda kv: kv[1]):
            if p <= page:
                cur = letter
            else:
                break
        return cur

    def _draw_nav(self, canv, doc):
        """Draw a single tab with the current letter, flush to the right edge.

        The tab slides down the edge as the alphabet progresses (A on top,
        Z at the bottom), like a real thumb index.
        """
        letter = self._letter_at(doc.page)
        if not letter:
            return
        idx = min(max(ord(letter.upper()) - ord("A"), 0), TAB_STEPS)
        w, h = TAB_W, TAB_H
        x = A4[0] - w + TAB_OVERHANG
        y = TAB_Y_FIRST - (TAB_Y_FIRST - TAB_Y_LAST) * idx / float(TAB_STEPS)
        visible_w = w - TAB_OVERHANG
        canv.saveState()
        canv.setFillColor(ACCENT)
        canv.setStrokeColor(TAB_EDGE)
        canv.setLineWidth(0.5)
        canv.roundRect(x, y, w, h, TAB_RADIUS, stroke=1, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("LAT-Bold", 19)
        canv.drawCentredString(x + visible_w / 2.0, y + h / 2.0 - 6.8, letter)
        canv.restoreState()

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
        if doc.page > 1:
            self._draw_nav(canv, doc)

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "LetterH":
            txt = flowable.getPlainText()
            letter = txt.strip()
            self.notify("TOCEntry", (0, txt, self.page))
            self.letter_pages[letter] = self.page
            try:
                self.canv.addOutlineEntry(txt, NAV_DEST(letter), level=0,
                                          closed=0)
            except Exception:  # noqa: BLE001 - outline is a nice-to-have
                pass


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
        story.append(LetterHead(L))
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

    target = os.path.join(OUT, "dictionary.pdf")
    tmp = os.path.join(OUT, "dictionary.tmp.pdf")
    doc = Doc(tmp)
    doc.multiBuild(story)
    try:
        os.replace(tmp, target)
    except PermissionError:
        print("locked:", target)
        print("built:", tmp)
        print("close the PDF viewer and rename it (or rerun this script)")
        return
    print("pdf:", target)
    print("entries:", len(keys))


if __name__ == "__main__":
    build()
