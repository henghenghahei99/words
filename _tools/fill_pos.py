#!/usr/bin/env python3
"""Build _raw/pos_cache.json : word -> "n."/"v."/"adj."/"adv." ...

Sources, in priority order:
  1. _raw/8A_pos.txt  (21cnjy 新沪教牛津英语八上单词笔记, textbook tags)
  2. https://api.dictionaryapi.dev  (Wiktionary, cached)
  3. suffix rules (see rule_pos)
"""
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "_raw")
CACHE = os.path.join(RAW, "pos_cache.json")

POS_RE = re.compile(
    r"([A-Za-z][A-Za-z'’\- ]{0,30}?)\s+(n|v|adj|adv|prep|conj|pron|num|int|art|aux)\.",
)
API_MAP = {
    "noun": "n.", "verb": "v.", "adjective": "adj.", "adverb": "adv.",
    "preposition": "prep.", "conjunction": "conj.", "pronoun": "pron.",
    "numeral": "num.", "interjection": "int.", "article": "art.",
    "determiner": "det.", "exclamation": "int.",
}
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


def load_glossary():
    out = {}
    path = os.path.join(RAW, "8A_pos.txt")
    if not os.path.exists(path):
        return out
    text = open(path, encoding="utf-8").read()
    for m in POS_RE.finditer(text):
        word = m.group(1).strip().lower()
        pos = m.group(2).lower() + "."
        if 0 < len(word) <= 30 and word not in out:
            out[word] = pos
    return out


def wn_pos(word):
    """Dominant POS from WordNet sense counts."""
    try:
        from nltk.corpus import wordnet as wn
        syns = wn.synsets(word)
    except Exception:
        return ""
    if not syns:
        return ""
    c = Counter()
    for s in syns:
        c[s.pos()] += 1
    score = {
        "n.": c.get("n", 0),
        "v.": c.get("v", 0),
        "adj.": c.get("a", 0) + c.get("s", 0),
        "adv.": c.get("r", 0),
    }
    best = max(score.values())
    if not best:
        return ""
    for k in ("adj.", "v.", "n.", "adv."):
        if score[k] == best:
            return k
    return ""


def api_pos(word):
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + urllib.parse.quote(word)
    try:
        with urllib.request.urlopen(url, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return ""
    if not isinstance(data, list) or not data:
        return ""
    kinds = []
    for entry in data:
        for mean in entry.get("meanings", []):
            k = API_MAP.get(mean.get("partOfSpeech", ""), "")
            if k and k not in kinds:
                kinds.append(k)
    return choose(kinds, "")


def choose(kinds, meaning):
    if not kinds:
        return ""
    if meaning.endswith("地") and "adv." in kinds:
        return "adv."
    if meaning.endswith("的") and "adj." in kinds:
        return "adj."
    for pref in ("v.", "n.", "adj.", "adv.", "prep.", "conj.", "pron.", "num."):
        if pref in kinds:
            return pref
    return kinds[0]


def main():
    glossary = load_glossary()
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    for k, v in glossary.items():
        cache.setdefault(k, v)

    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "all.csv"), encoding="utf-8")))
    todo = {}
    for r in rows:
        if r["pos"]:
            continue
        w = r["word"]
        if " " in w or "…" in w or not re.fullmatch(r"[A-Za-z][A-Za-z'’\-]*", w):
            continue
        lw = w.lower()
        if lw in cache:
            continue
        todo[lw] = r["meaning"]

    print("to look up:", len(todo))
    results = {}

    def work(item):
        w, meaning = item
        p = wn_pos(w) or api_pos(w) or rule_pos(w)
        return w, p

    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, (w, p) in enumerate(ex.map(work, todo.items()), 1):
            results[w] = p
            if i % 100 == 0:
                print(" ...", i)

    cache.update(results)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    got = sum(1 for v in results.values() if v)
    print("cached:", len(cache), "| newly resolved:", got, "/", len(results))


if __name__ == "__main__":
    main()
