#!/usr/bin/env python3
"""Parse fetched word-list pages into per-unit files under words/.

Output columns: 序号 | 英文 | 音标 | 词性 | 中文
Sources (in output/source/):
  7A : r1.txt        (21cnjy 2024 七上 单词表, plain "word pos.meaning"; no IPA -> auto)
  7B : 7B_u1..8.md   (yy.suyang123, one unit per page, has IPA)
  8A : 8A_r4.txt     (yyld 八上, all units, has IPA)
  8B : baxia.md      (yyld 八下)
  9A : jiushang.md   (yyld 九上)
  9B : jiuxia.md     (yyld 九下)
"""
import csv
import json
import os
import re

import eng_to_ipa

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "source")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")

POS_RE = re.compile(
    r"^(n|v|adj|adv|prep|conj|pron|num|int|art|aux|vt|vi|abbr)\.\s*", re.I
)
IPA_RE = re.compile(r"[ˈˌːəɪʊæɑɒɔɜθðʃʒŋɡʌɛɐ]")
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 .'’()\-…]*$")

PLAIN_RE = re.compile(
    r"^\*?([A-Za-z][A-Za-z0-9 .'’()/\-…]*?)\s+"
    r"(?:(adv|adj|prep|conj|pron|num|int|art|aux|abbr|n|v)\.?,?\s*)?"
    r"([\u4e00-\u9fff（(].*)$"
)
PLAIN_RE_NO_SPACE = re.compile(
    r"^\*?([A-Za-z][A-Za-z0-9 .'’()/\-…]*?)\s*([\u4e00-\u9fff（(].*)$"
)

TITLES = {
    "7A": ["Friendship", "School life", "The seasons", "The Earth",
           "Off to space", "Travelling around", "Fun after school",
           "Collecting as a hobby"],
    "7B": ["People around us", "Travelling around the world", "Trees and us",
           "Our animal friends", "Water is life", "Electricity everywhere",
           "Role models of our time", "Follow your interests"],
}

# source typos: word -> corrected word (any unit)
SPELL_FIX = {
    "spred": "spread",
    "ded": "dead",
    "unitl": "until",
    "satisty": "satisfy",
}

# words neither WordNet nor the suffix rules cover
MANUAL_POS = {
    "since": "conj.", "anytime": "adv.", "whenever": "conj.",
    "else": "adv.", "role-play": "v.", "until": "prep.",
    "satisfy": "v.", "upon": "prep.", "onto": "prep.",
    "whether": "conj.", "understand": "v.",
}

# source typos: unit, word -> corrected POS
POS_FIX = {
    ("7A_U8", "add"): "v.",
    ("7B_U1", "wisely"): "adv.",
}


def clean(s):
    return s.replace("\\", "").replace("\u00a0", " ").strip()


def split_pos(meaning):
    m = POS_RE.match(meaning)
    if m:
        return m.group(1).lower() + ".", meaning[m.end():].strip()
    return "", meaning


VERB_HEADS = set("""be do does did have has had take make get go goes give put look turn
come keep find play use have let bring hold set run stand stay sit say see send show
spend start stop talk tell think try wait walk want work write read open close clear
clean cut blow burn pick fill grow hear help jump laugh learn leave lie live meet move
pay rain ring rise see sell speak swim teach throw wear win catch choose drive eat fall
feel fight fly forget hang happen hit hurt know lead lose mean""".split())
PREP_HEADS = set("""in on at of to for with by from as about after before under over
between among across through during without within into onto upon behind below above
near beside besides since until till despite except toward towards around against
along per via than""".split())
ADJ_HEADS = set("""full proud afraid good bad different similar ready interested famous
busy free angry happy sad sorry sure glad able busy worth""".split())


def phrase_pos(w):
    first = w.split()[0].lower()
    if first in VERB_HEADS:
        return "v."
    if first in PREP_HEADS:
        return "prep."
    if first in ADJ_HEADS:
        return "adj."
    return "n."


ADJ_LY = {
    "friendly", "lovely", "lonely", "likely", "lively", "daily", "weekly",
    "monthly", "yearly", "early", "silly", "ugly", "holy", "deadly",
    "costly", "curly", "elderly", "orderly", "scholarly", "kindly",
}


def rule_pos(w):
    lw = w.lower()
    if lw.endswith("ly") and lw not in ADJ_LY:
        return "adv."
    if lw.endswith(("tion", "sion", "ment", "ness", "ity", "ance", "ence",
                    "ship", "hood", "ism", "ist", "ics", "ery", "ure", "age")):
        return "n."
    if lw.endswith(("ous", "ful", "less", "able", "ible", "ive", "ical",
                    "ic", "ish", "ary", "al")):
        return "adj."
    if lw.endswith(("ize", "ise", "ify", "ate", "en")):
        return "v."
    return ""


def auto_ipa(word):
    w = word.replace("…", " ").strip()
    if not w or not re.fullmatch(r"[A-Za-z][A-Za-z'’\- ]*", w):
        return ""
    try:
        res = eng_to_ipa.convert(w)
    except Exception:
        return ""
    if not res or "*" in res:
        return ""
    return "/%s/" % res.strip()


def load_pos_cache():
    p = os.path.join(RAW, "pos_cache.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {}


def parse_yy_lines(lines):
    """Pages from 英语朗读宝: word / [ipa] / '翻译：meaning' (may echo the word)."""
    entries = []
    words, ipa = [], ""
    for raw in lines:
        s = clean(raw)
        if not s:
            continue
        if s.startswith("翻译："):
            if not words:
                continue
            prev = entries[-1][0].lower() if entries else None
            if len(words) >= 2 and prev and words[0].lower() == prev:
                words = words[1:]          # drop leading echo of previous word
            if len(words) >= 2:
                word, cur_ipa = words[-2], words[-1]
                cur_ipa = "/%s/" % cur_ipa.strip("/ ")
            else:
                word, cur_ipa = words[-1], "/%s/" % ipa.strip("/ ") if ipa else ""
            pos, zh = split_pos(clean(s[len("翻译："):]))
            if not (entries and entries[-1][0].lower() == word.lower()):
                entries.append([word, cur_ipa, pos, zh])
            words, ipa = [], ""
            continue
        if s.startswith("#") or s.startswith("- ") or s.startswith("点击") \
                or s.startswith("连续播放") or s.startswith("免费下载"):
            words, ipa = [], ""
            continue
        if IPA_RE.search(s) or (s.startswith("/") and s.endswith("/")):
            ipa = s.strip("/ ")
            continue
        if WORD_RE.match(s) and len(s) < 60:
            words.append(s)
            words = words[-3:]
        else:
            words, ipa = [], ""
    return entries


def split_yyl_units(text):
    lines = text.splitlines()
    units, cur = [], None
    for ln in lines:
        s = clean(ln)
        m = re.match(r"^#+\s*.*?Unit\s*(\d+)\s*(.*?)\s*单词表", s)
        if m:
            if cur:
                units.append(cur)
            cur = [int(m.group(1)), m.group(2).strip(), []]
            continue
        if cur is not None:
            cur[2].append(ln)
    if cur:
        units.append(cur)
    return units


def parse_plain_list(lines):
    """21cnjy style: 'guitar n.吉他' / 'be good at 擅长…' / bare 'Unit 1'."""
    units, cur = [], None
    in_quiz = False
    for ln in lines:
        s = clean(ln)
        if ("单词默写表" in s and s.startswith("2024年")) or "精品试卷" in s:
            in_quiz = True
        if in_quiz:
            continue
        if re.match(r"^Unit\s+\d+$", s):
            if cur:
                units.append(cur)
            cur = [int(s.split()[1]), "", []]
            continue
        if cur is None or not s:
            continue
        m = PLAIN_RE.match(s)
        if m:
            word = m.group(1).strip()
            pos = (m.group(2) or "").lower()
            pos = pos + "." if pos else ""
            zh = m.group(3).strip()
        else:
            m = PLAIN_RE_NO_SPACE.match(s)
            if not m:
                continue
            word, pos, zh = m.group(1).strip(), "", m.group(2).strip()
        if not WORD_RE.match(word) or any(w.lower() == word.lower() for w, *_ in cur[2]):
            continue
        cur[2].append([word, "", pos, zh])
    if cur:
        units.append(cur)
    return units


def md_escape(s):
    return s.replace("|", "\\|")


def write_unit(book, unit_no, title, entries):
    name = "%s_U%d" % (book, unit_no)
    path = os.path.join(OUT, name + ".md")
    lines = ["# %s%s" % (name, (" · " + title) if title else ""), ""]
    lines.append("> 沪教牛津版（2024/2025 修订）· 共 %d 条（含短语）" % len(entries))
    lines.append("")
    lines.append("| # | 英文 | 音标 | 词性 | 中文 |")
    lines.append("|---|---|---|---|---|")
    for i, (w, ipa, p, z) in enumerate(entries, 1):
        lines.append("| %d | %s | %s | %s | %s |" % (
            i, md_escape(w), md_escape(ipa), p, md_escape(z)))
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    books = {}

    with open(os.path.join(RAW, "r1.txt"), encoding="utf-8") as f:
        units = parse_plain_list(f.read().splitlines())
    for u in units:
        u[1] = TITLES["7A"][u[0] - 1]
    books["7A"] = units

    units = []
    for n in range(1, 9):
        p = os.path.join(RAW, "7B_u%d.md" % n)
        if not os.path.exists(p):
            print("missing", p)
            continue
        txt = open(p, encoding="utf-8").read()
        units.append([n, TITLES["7B"][n - 1], parse_yy_lines(txt.splitlines())])
    books["7B"] = units

    for book, fn in (("8A", "8A_r4.txt"), ("8B", "baxia.md"),
                     ("9A", "jiushang.md"), ("9B", "jiuxia.md")):
        txt = open(os.path.join(RAW, fn), encoding="utf-8").read()
        books[book] = [[no, title, parse_yy_lines(body)]
                       for no, title, body in split_yyl_units(txt)]

    rows, summary = [], []
    pos_cache = load_pos_cache()
    for book in ("7A", "7B", "8A", "8B", "9A", "9B"):
        for no, title, entries in books.get(book, []):
            if not entries:
                print("EMPTY", book, no)
                continue
            key = "%s_U%d" % (book, no)
            fixed = []
            for w, ipa, p, z in entries:
                w = SPELL_FIX.get(w.lower(), w)
                p = POS_FIX.get((key, w.lower()), p)
                if not p:
                    p = pos_cache.get(w.lower(), "")
                if not p:
                    p = MANUAL_POS.get(w.lower(), "")
                if not p:
                    base = re.sub(r"\(.*?\)", " ", w)
                    base = base.replace("......", " ").replace("...", " ") \
                               .replace("…", " ").strip()
                    if " " in base:
                        p = phrase_pos(base)
                    else:
                        p = pos_cache.get(base.lower(), "") \
                            or MANUAL_POS.get(base.lower(), "") \
                            or rule_pos(base)
                # ASCII-only "IPA" from the source is mangled (e.g. /rez/ for raise)
                if ipa and re.fullmatch(r"[A-Za-z'’()\-\s]+", ipa.strip("/")):
                    ipa = auto_ipa(w) or ipa
                if not ipa:
                    ipa = auto_ipa(w)
                fixed.append((w, ipa, p, z))
            write_unit(book, no, title, fixed)
            for w, ipa, p, z in fixed:
                rows.append([key, w, ipa, p, z])
            have = sum(1 for r in fixed if r[1])
            summary.append("%s: %d 条（音标 %d）%s" % (key, len(fixed), have, title))

    with open(os.path.join(OUT, "all.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["unit", "word", "ipa", "pos", "meaning"])
        wr.writerows(rows)

    print("\n".join(summary))
    print("total:", len(rows))


if __name__ == "__main__":
    main()
