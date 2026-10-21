#!/usr/bin/env python3
"""Validate the generated dictionary: coverage, 6 bullets per entry, anomalies."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
DATA = os.path.join(SEARCH, "data")


def main():
    words = json.load(open(os.path.join(DATA, "words.json"), encoding="utf-8"))
    cache = {}
    for line in open(os.path.join(DATA, "entries.jsonl"), encoding="utf-8"):
        if "\t" in line:
            w, b = line.rstrip("\n").split("\t", 1)
            cache[w] = b.replace("\\n", "\n")
    keys = [w["word"].lower().rstrip(".") if len(w["word"]) > 2 else w["word"].lower()
            for w in words]
    missing = [w["word"] for w, k in zip(words, keys) if k not in cache]
    bad = []
    long_lines = []
    weak_syn = []
    bad_v = []
    bad_n = []
    bad_adj = []
    for k, b in cache.items():
        if k not in keys:
            continue
        lines = [l for l in b.splitlines() if l.startswith("- **")]
        if len(lines) != 6:
            bad.append((k, "bullets", len(lines)))
        if any(len(l) > 1200 for l in b.splitlines()):
            long_lines.append(k)
        if b.count("### ") != 1:
            bad.append((k, "heading", b.count("### ")))
        syn = next((l for l in lines if l.startswith("- **同义·反义**")), "")
        if syn and "无" not in syn and "（" not in syn:
            weak_syn.append(k)
        form = next((l for l in lines if l.startswith("- **变形**")), "")
        mean = next((l for l in lines if l.startswith("- **释义**")), "")
        if re.search(r"\b(vt|vi|v)\.", mean) and not all(
                x in form for x in ("过去式", "过去分词", "现在分词")):
            bad_v.append(k)
        if re.search(r"\b(n)\.", mean) and ("复数" not in form and "不可数" not in form):
            bad_n.append(k)
        if re.search(r"\b(adj|a)\.", mean) and ("比较级" not in form and "无比较级" not in form):
            bad_adj.append(k)
    print("词表:", len(words), "已生成:", len([k for k in keys if k in cache]),
          "缺:", len(missing))
    print("格式异常:", len(bad), bad[:5])
    print("超长行:", len(long_lines), long_lines[:5])
    print("同义反义无中文:", len(weak_syn), weak_syn[:5])
    print("动词时态标注不全:", len(bad_v), bad_v[:5])
    print("名词缺复数:", len(bad_n), bad_n[:5])
    print("形容词缺比较级:", len(bad_adj), bad_adj[:5])
    if missing:
        print("缺失示例:", missing[:10])


if __name__ == "__main__":
    main()
