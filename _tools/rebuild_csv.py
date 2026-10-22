#!/usr/bin/env python3
"""从各单元 md 重建 all.csv（unit,word,ipa,pos,meaning）。"""
import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
ROOT = next((os.path.join(PARENT, d) for d in ("output", "ourput")
             if os.path.isdir(os.path.join(PARENT, d))),
            os.path.join(PARENT, "output"))


def unit_sort(p):
    u = os.path.basename(p)[:-3]
    grade, rest = u.split("_U")
    return (grade, int(rest))


def main():
    rows = []
    files = [p for p in glob.glob(os.path.join(ROOT, "[0-9]*_U*.md"))
             if not p.endswith("_EXPLAIN.md")]
    for path in sorted(files, key=unit_sort):
        unit = os.path.basename(path)[:-3]
        for line in open(path, encoding="utf-8"):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 5 or not cells[0].isdigit():
                continue
            rows.append([unit] + cells[1:])
    out = os.path.join(ROOT, "all.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["unit", "word", "ipa", "pos", "meaning"])
        w.writerows(rows)
    print("all.csv:", len(rows), "rows,", len(files), "units")


if __name__ == "__main__":
    main()
