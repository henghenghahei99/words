#!/usr/bin/env python3
"""Deterministically add labels to inflection forms that the model left unlabeled.

Examples:
  动词 → abandons, abandoned, abandoned, abandoning
    -> 动词 → 第三人称单数：abandons；过去式：abandoned；过去分词：abandoned；现在分词：abandoning
  名词 → abilities            -> 名词 → 复数：abilities
  形容词 → abler, ablest      -> 形容词 → 比较级：abler；最高级：ablest

Only rewrites the 变形 bullet; leaves everything else untouched.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
CACHE = os.path.join(DATA, "entries.jsonl")

VERB_LABELS = ["第三人称单数", "过去式", "过去分词", "现在分词"]


def split_forms(s):
    s = s.strip().rstrip("。；;")
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
    elif "→" in s:
        parts = [p.strip() for p in s.split("→")]
    elif "、" in s:
        parts = [p.strip() for p in s.split("、")]
    else:
        parts = [s]
    return [p for p in parts if p]


def relabel(form):
    """Return a possibly relabeled 变形 line."""
    body = form.split("：", 1)[1] if "：" in form else ""
    if not body:
        return form
    # split sections by ；
    sections = [x.strip() for x in re.split(r"[；;]", body) if x.strip()]
    out = []
    for sec in sections:
        if re.match(r"^(第三人称单数|过去式|过去分词|现在分词|复数|比较级|最高级|"
                    r"不可数|无比较级)", sec):
            out.append(sec)
            continue
        m = re.match(r"^(名词|动词|形容词|副词)\s*(?:→|:)\s*(.+)$", sec)
        if not m:
            out.append(sec)
            continue
        kind, forms = m.group(1), m.group(2)
        parts = split_forms(forms)
        if kind == "动词" and len(parts) >= 4:
            out.append("动词 → " + "；".join(
                "%s：%s" % (VERB_LABELS[i], parts[i]) for i in range(4))
                + ("；" + "；".join(parts[4:]) if len(parts) > 4 else ""))
        elif kind == "名词" and len(parts) >= 1:
            out.append("名词 → 复数：%s" % "、".join(parts))
        elif kind == "形容词" and len(parts) >= 2:
            out.append("形容词 → 比较级：%s；最高级：%s" % (parts[0], parts[1]))
        else:
            out.append(sec)
    return "- **变形**：" + "；".join(out)


def main():
    changed = 0
    tmp = CACHE + ".tmp"
    with open(CACHE, encoding="utf-8") as fin, open(tmp, "w", encoding="utf-8") as fout:
        for line in fin:
            if "\t" not in line:
                continue
            w, block = line.rstrip("\n").split("\t", 1)
            text = block.replace("\\n", "\n")
            lines = text.split("\n")
            for i, l in enumerate(lines):
                if l.startswith("- **变形**"):
                    new = relabel(l)
                    if new != l:
                        lines[i] = new
                        changed += 1
                    break
            fout.write("%s\t%s\n" % (w, "\n".join(lines).replace("\n", "\\n")))
    os.replace(tmp, CACHE)
    print("relabeled:", changed)


if __name__ == "__main__":
    main()
