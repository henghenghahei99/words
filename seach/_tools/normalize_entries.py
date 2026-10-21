#!/usr/bin/env python3
"""Deduplicate entries.jsonl (last wins) and normalize duplicated labels in 变形."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(HERE), "data", "entries.jsonl")

PATTERNS = [
    (r"(第三人称单数：)\s*三单\s*", r"\1"),
    (r"(过去式：)\s*过去式\s*", r"\1"),
    (r"(过去分词：)\s*过去分词\s*", r"\1"),
    (r"(现在分词：)\s*现在分词\s*", r"\1"),
    (r"(复数：)\s*复数：\s*", r"\1"),
    (r"(比较级：)\s*比较级：\s*", r"\1"),
    (r"(最高级：)\s*最高级：\s*", r"\1"),
    (r"\s+：", "："),
    (r"：\s+", "："),
]


def normalize(line):
    for pat, rep in PATTERNS:
        line = re.sub(pat, rep, line)
    return line


def main():
    entries = {}
    order = []
    for line in open(CACHE, encoding="utf-8"):
        if "\t" not in line:
            continue
        w, b = line.rstrip("\n").split("\t", 1)
        if w not in entries:
            order.append(w)
        entries[w] = b
    n_fix = 0
    with open(CACHE, "w", encoding="utf-8") as f:
        for w in order:
            text = entries[w].replace("\\n", "\n")
            lines = text.split("\n")
            for i, l in enumerate(lines):
                if l.startswith("- **变形**"):
                    new = normalize(l)
                    if new != l:
                        lines[i] = new
                        n_fix += 1
                    break
            f.write("%s\t%s\n" % (w, "\n".join(lines).replace("\n", "\\n")))
    print("unique:", len(order), "normalized:", n_fix)


if __name__ == "__main__":
    main()
