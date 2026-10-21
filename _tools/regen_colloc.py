#!/usr/bin/env python3
"""Rewrite collocation entries in <UNIT>_EXPLAIN.md to the 2-bullet format.

搭配/短语条目只保留：
- **同义搭配**：…
- **反义搭配**：…
其余（词根、同根词、前后缀、词性变化）删除；单词条目不动。

Usage: python3 regen_colloc.py [UNIT ...] / --all
"""
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import gen_explain as G

ROOT = G.ROOT
CHUNK = 20

SYSTEM = (
    "你是资深英语教师，为初中生整理固定搭配/短语的同义与反义表达。"
    "只给地道、常用、语义相当的搭配，不编造。"
)

RULES = """输出格式（严格遵守，不要开场白、不要总结）：
### {idx}. {word} {ipa} {pos} {meaning}
- **同义搭配**：表达1 / 表达2 / 表达3
- **反义搭配**：表达1 / 表达2（确实没有就写“无”）

要求：
1. 每条恰好 2 个 bullet：先是“同义搭配”，再是“反义搭配”。
2. 编号、短语、音标、词性、中文必须与我给的完全一致。
3. 同义搭配不要照抄原短语；要给出换一种说法的表达（可含单个动词/介词短语）。
4. 反义搭配只给真正语义相反的搭配；没有就写“无”。
5. 不要写词源、不要写例句、不要重复同一个表达。

示例：
### 28. be good at /bi gʊd æt/ v. 擅长…
- **同义搭配**：be skilled at / be expert in / do well in
- **反义搭配**：be poor at / be bad at

### 34. medium height /ˈmidiəm haɪt/ n. 中等身高
- **同义搭配**：average height / of medium build
- **反义搭配**：very tall / very short
"""


def is_colloc(w):
    return (" " in w) or ("…" in w) or ("......" in w) or ("..." in w)


def chat(user, max_tokens=4000):
    return G.post({
        "model": G.MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    })


def gen_chunk(unit, chunk):
    body = "\n".join(G.fmt_row(r) for r in chunk)
    text = chat("%s\n\n需要改写的搭配：\n%s" % (RULES, body)).strip()
    k = text.find("### ")
    if k > 0:
        text = text[k:]
    missing = [r for r in chunk if ("### %d." % r["idx"]) not in text]
    if missing:
        body2 = "\n".join(G.fmt_row(r) for r in missing)
        more = chat("%s\n\n上一次漏了这些，请只补这些（格式同前）：\n%s"
                    % (RULES, body2)).strip()
        j = more.find("### ")
        if j > 0:
            more = more[j:]
        text += "\n\n" + more
    return text


def splice(path, new_text):
    """Replace existing entry blocks by the regenerated ones (regex based)."""
    new_blocks = {}
    parts = re.split(r"(?m)^### (\d+)\. ", new_text)
    for i in range(1, len(parts), 2):
        idx = int(parts[i])
        block = "### %d. %s" % (idx, parts[i + 1].strip())
        block = re.sub(r"(?m)^### %d\. .*\n(?=### %d\. )" % (idx, idx), "", block)
        new_blocks[idx] = block.strip()

    txt = open(path, encoding="utf-8").read()
    for idx, block in new_blocks.items():
        pat = re.compile(r"(?ms)^### %d\. .*?(?=^### \d+\. |\n## |\Z)" % idx)
        if pat.search(txt):
            txt = pat.sub(lambda m: block + "\n\n", txt, count=1)
    open(path, "w", encoding="utf-8").write(txt)
    open(path, "w", encoding="utf-8").write("\n".join(lines))


def build(unit):
    src = os.path.join(ROOT, unit + ".md")
    dst = os.path.join(ROOT, unit + "_EXPLAIN.md")
    if not os.path.exists(dst):
        print("missing explain", unit)
        return
    rows = [r for r in G.parse_unit(src) if is_colloc(r["word"])]
    if not rows:
        print("no collocations", unit)
        return
    out = []
    for i in range(0, len(rows), CHUNK):
        out.append(gen_chunk(unit, rows[i:i + CHUNK]))
        print("  %s colloc %d/%d" % (unit, i // CHUNK + 1,
                                     (len(rows) + CHUNK - 1) // CHUNK))
    splice(dst, "\n\n".join(out))
    print("done", unit, len(rows), "collocations")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        import glob
        units = sorted(os.path.basename(p)[:-3] for p in
                       glob.glob(os.path.join(ROOT, "[0-9]*_U*.md"))
                       if not p.endswith("_EXPLAIN.md"))
    else:
        units = args
    if not units:
        sys.exit(__doc__)
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(build, units))


if __name__ == "__main__":
    main()
