#!/usr/bin/env python3
"""Build the merged headword list for the dictionary.

Levels: 小学(广州教科版) < 初中(沪教牛津+中考) < 高中 < CET4 < CET6
Output: data/words.json  [{word, ipa, levels, rank}]
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
SRC = os.path.join(SEARCH, "source")
OUT = os.path.join(SEARCH, "data")

sys.path.insert(0, "/workspace/alex/words/_tools")
import parse as P  # noqa: E402  (reuse the yy-page parser)

LEVELS = ["小学", "初中", "高中", "CET4", "CET6"]
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'’\-\. ]*$")


def add(bag, w, ipa="", level="", zh=""):
    w = (w or "").strip().strip(",.;:")
    if not w or not WORD_RE.match(w) or len(w) > 40:
        return
    # dictionary headwords only: no multi-word phrases / patterns
    if " " in w or "(" in w or ")" in w or "…" in w:
        return
    if w.lower() in {"a", "an", "the"} and " " in w:
        return
    key = w.lower()
    if len(key) > 2 and key.endswith("."):
        key = key.rstrip(".")
    it = bag.setdefault(key, {"word": w, "ipa": ipa, "levels": [], "zh": zh})
    # prefer the dotted abbreviation as display form (a.m. over a.m)
    if w.endswith(".") and not it["word"].endswith("."):
        it["word"] = w
    if ipa and not it["ipa"]:
        it["ipa"] = ipa
    if level and level not in it["levels"]:
        it["levels"].append(level)
    if zh and not it["zh"]:
        it["zh"] = zh


def parse_primary(bag):
    n = 0
    for p in sorted(glob.glob(os.path.join(SRC, "primary", "*.md"))):
        text = open(p, encoding="utf-8").read()
        for w, ipa, pos, zh in P.parse_yy_lines(text.splitlines()):
            add(bag, w, ipa.strip("/"), "小学", ("%s %s" % (pos, zh)).strip())
            n += 1
    return n


def parse_junior_csv(bag):
    p = "/workspace/alex/words/output/all.csv"
    n = 0
    if not os.path.exists(p):
        return 0
    for r in csv.DictReader(open(p, encoding="utf-8")):
        w = r["word"]
        if " " in w or "…" in w or "......" in w or "(" in w:
            continue
        add(bag, w, r["ipa"].strip("/"), "初中", ("%s %s" % (r["pos"], r["meaning"])).strip())
        n += 1
    return n


def parse_zhongkao(bag):
    p = os.path.join(SRC, "中考英语词汇表.txt")
    n = 0
    if not os.path.exists(p):
        return 0
    for line in open(p, encoding="utf-8", errors="ignore"):
        s = line.strip()
        if not s or re.fullmatch(r"[A-Z]", s) or not re.search(r"[\u4e00-\u9fff]", s):
            continue
        if "[" in s:
            i = s.index("[")
            word, ipa = s[:i].strip(), s[i + 1:s.find("]", i)]
            zh = s[s.find("]", i) + 1:].strip()
        else:
            j = re.search(r"[\u4e00-\u9fff]", s).start()
            head, zh = s[:j].strip(), s[j:].strip()
            m = re.search(r"\s+(?:n|v|a|ad|adv|adj|prep|conj|pron|num|art|int|aux|vt|vi)\.?$", head)
            word = head[:m.start()].strip() if m else head
            ipa = ""
        add(bag, word, ipa, "初中", zh)
        n += 1
    return n


def parse_plain(bag, fname, level, has_pos):
    p = os.path.join(SRC, fname)
    n = 0
    if not os.path.exists(p):
        return 0
    for line in open(p, encoding="utf-8", errors="ignore"):
        s = line.strip()
        if not s or re.fullmatch(r"[A-Z]", s) or not WORD_RE.match(s.split()[0]):
            continue
        if has_pos:
            m = re.match(r"^([A-Za-z][A-Za-z'’\-\. ]*?)\s+(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|num\.|art\.|a\.|ad\.).*$", s)
            w = m.group(1) if m else s.split()[0]
            zh = s[len(w):].strip()
        else:
            w, zh = s.split()[0], ""
        add(bag, w, "", level, zh)
        n += 1
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    bag = {}
    stats = {
        "小学": parse_primary(bag),
        "初中(textbook)": parse_junior_csv(bag),
        "初中(中考)": parse_zhongkao(bag),
        "高中": parse_plain(bag, "Highschool_edited.txt", "高中", False),
        "CET4": parse_plain(bag, "CET4_edited.txt", "CET4", True),
        "CET6": parse_plain(bag, "CET6_edited.txt", "CET6", True),
    }
    rank = {lv: i for i, lv in enumerate(LEVELS)}
    words = []
    for it in bag.values():
        if not it["levels"]:
            continue
        it["rank"] = min(rank[l] for l in it["levels"])
        it["levels"].sort(key=lambda x: rank[x])
        words.append(it)
    words.sort(key=lambda x: (x["word"].lower(), x["rank"]))
    with open(os.path.join(OUT, "words.json"), "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=0)
    print("原始行数:", stats)
    print("去重后词条:", len(words))
    for lv in LEVELS:
        print(" ", lv, sum(1 for w in words if w["levels"][0] == lv))
    from collections import Counter
    c = Counter(w["word"][0].upper() for w in words if w["word"][0].isalpha())
    print("字母分布:", dict(sorted(c.items())))


if __name__ == "__main__":
    main()
