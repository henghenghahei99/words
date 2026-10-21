#!/usr/bin/env python3
"""Repair *_EXPLAIN.md entry sections: remove duplicated headings and sort by index."""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = "## 二、逐词说文解字"
END = "## 三、本单元前缀 / 后缀小结"
HEAD = re.compile(r"(?m)^### (\d+)\. ")


def rebuild(path):
    txt = open(path, encoding="utf-8").read()
    a = txt.find(START)
    b = txt.find(END)
    if a < 0 or b < 0 or b < a:
        return None
    head = txt[:a + len(START)]
    tail = txt[b:]
    body = txt[a + len(START):b]
    parts = HEAD.split(body)
    blocks = {}
    for i in range(1, len(parts), 2):
        idx = int(parts[i])
        content = "### %d. %s" % (idx, parts[i + 1].strip())
        # drop duplicated heading lines inside the block
        content = re.sub(r"(?m)^### %d\. .*\n(?=### %d\. )" % (idx, idx), "", content)
        blocks[idx] = content.strip()
    if not blocks:
        return None
    ordered = "\n\n".join(blocks[k] for k in sorted(blocks))
    new = head + "\n\n" + ordered + "\n\n" + tail
    if new != txt:
        open(path, "w", encoding="utf-8").write(new)
        return len(blocks)
    return 0


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "*_EXPLAIN.md")))
    for f in files:
        n = rebuild(f)
        print(os.path.basename(f), "blocks" if n is None else n)


if __name__ == "__main__":
    main()
