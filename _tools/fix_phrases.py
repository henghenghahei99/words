#!/usr/bin/env python3
"""把 *_EXPLAIN.md 里「搭配/短语」条目的 5 条 bullet 收拢成 2 条。

约定（与 7A 系列的原始规范一致）：词条本身含空格或省略号（即搭配/短语）时，
只保留
  - **同义搭配**：…
  - **反义搭配**：…
所以这里把模型多写的词源/同根词/词缀/变形合并丢弃，仅从「同义·反义」行
提取搭配对照，保证 46 个单元格式统一。

用法：python3 fix_phrases.py [UNIT ...]
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(HERE), "output")


def parse_unit_words(path):
    """返回 {序号: (word, pos)}，用于判断是否存在空格/省略号。"""
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or not cells[0].isdigit():
            continue
        out[int(cells[0])] = (cells[1], cells[3])
    return out


def is_phrase(word):
    w = word.strip()
    return " " in w or "…" in w or "..." in w


def split_blocks(text):
    """切成 [(prefix, idx, header, block_lines)]，prefix 为第一个块之前的文本。"""
    lines = text.splitlines()
    blocks, cur, pre = [], None, []
    for line in lines:
        m = re.match(r"^### (\d+)\.\s*(.+)$", line)
        if m:
            if cur is None:
                pre = blocks_start = None
            if cur:
                blocks.append(cur)
            cur = [int(m.group(1)), m.group(2), []]
        elif cur is not None:
            cur[2].append(line)
    if cur:
        blocks.append(cur)
    return blocks


def collapse(block_lines):
    """从 5 条 bullet 里抽出同义/反义，返回 2 条 bullet。"""
    syn_line = ""
    for l in block_lines:
        if l.startswith("- **同义"):
            syn_line = l
            break
    syn, anti = "无", "无"
    if syn_line:
        body = syn_line.split("：", 1)[-1]
        m = re.split(r"[；;]\s*反义", body, maxsplit=1)
        syn = re.sub(r"^同义\s*", "", m[0]).strip().strip("；;。 ")
        if len(m) > 1:
            anti = m[1].strip().strip("。 ")
    syn = syn or "无"
    anti = anti or "无"
    return ["- **同义搭配**：%s" % syn, "- **反义搭配**：%s" % anti]


def process(unit):
    src = os.path.join(ROOT, unit + ".md")
    exp = os.path.join(ROOT, unit + "_EXPLAIN.md")
    if not os.path.exists(exp):
        return 0
    words = parse_unit_words(src)
    text = open(exp, encoding="utf-8").read()
    lines = text.splitlines()
    out, i, changed = [], 0, 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^### (\d+)\.\s*(.+)$", line)
        if not m:
            out.append(line)
            i += 1
            continue
        idx = int(m.group(1))
        j = i + 1
        while j < len(lines) and not re.match(r"^### \d+\.", lines[j]):
            j += 1
        block = lines[i + 1:j]
        word = words.get(idx, ("", ""))[0]
        bullets = [l for l in block if l.startswith("- **")]
        if is_phrase(word) and len(bullets) != 2:
            new = collapse(bullets)
            out.append(line)
            out.extend(new)
            out.append("")
            changed += 1
        else:
            out.append(line)
            out.extend(block)
        i = j
    if changed:
        open(exp, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return changed


def main():
    units = sys.argv[1:]
    if not units:
        units = sorted(os.path.basename(p)[:-3] for p in
                       glob.glob(os.path.join(ROOT, "[0-9]*_U*.md"))
                       if not p.endswith("_EXPLAIN.md"))
    total = 0
    for u in units:
        n = process(u)
        if n:
            print(u, "collapsed", n)
        total += n
    print("units", len(units), "collapsed", total)


if __name__ == "__main__":
    main()
