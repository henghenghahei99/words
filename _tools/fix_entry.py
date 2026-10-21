#!/usr/bin/env python3
"""Regenerate a single entry in <UNIT>_EXPLAIN.md (fixes repetition glitches).

Usage: python3 fix_entry.py 7A_U3 24
"""
import os
import re
import sys

import gen_explain as G

ROOT = G.ROOT


def main():
    unit, idx = sys.argv[1], int(sys.argv[2])
    src = os.path.join(ROOT, unit + ".md")
    dst = os.path.join(ROOT, unit + "_EXPLAIN.md")
    rows = G.parse_unit(src)
    row = next(r for r in rows if r["idx"] == idx)
    is_col = (" " in row["word"]) or ("…" in row["word"])
    rules = G.RULES
    if is_col:
        rules = rules.split("5. 严禁")[0] + (
            "5. 本条是搭配，只输出 2 个 bullet：**同义搭配** / **反义搭配**。")
    prompt = "请为下面这个词条写说文解字。\n\n%s\n\n词条：\n%s" % (
        rules, G.fmt_row(row))
    text = G.chat(prompt).strip()
    k = text.find("### ")
    if k > 0:
        text = text[k:]
    block = text.split("\n\n### ")[0].rstrip()

    txt = open(dst, encoding="utf-8").read()
    pat = re.compile(r"(?ms)^### %d\. .*?(?=^### \d+\. |\n## |\Z)" % idx)
    new = pat.sub(lambda m: block + "\n\n", txt, count=1)
    open(dst, "w", encoding="utf-8").write(new)
    print("fixed", unit, idx, row["word"], "->", len(block), "chars")


if __name__ == "__main__":
    main()
