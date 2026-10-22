#!/usr/bin/env python3
"""解析「单词精讲」型文档（全册 6/8 份课件合集）。

段落形如：
    /k p re t/
    cooperate
    (动词)合作

用法：python3 build_from_jingjiang.py 9B /tmp/9b_all.md
"""
import re
import sys

from build_new_edition import fix_ipa, guess_pos, unescape, write_unit

POS_MAP = {
    "名词": "n.", "动词": "v.", "形容词": "adj.", "副词": "adv.",
    "介词": "prep.", "连词": "conj.", "代词": "pron.", "数词": "num.",
    "冠词": "art.", "感叹词": "int.", "情态动词": "modal v.",
    "短语": "phrase", "动词短语": "v.",
}

UNIT = re.compile(r"(?m)^Unit\s*(\d+)\s*(.+?)\s*$")
ENTRY = re.compile(
    r"/([^/\n]*)/\s*\n\s*([A-Za-z][A-Za-z'’\-\. ]*?)\s*\n\s*"
    r"\(([^)（）]{1,6})\)\s*([^\n]*)")


def main():
    book, src = sys.argv[1], sys.argv[2]
    text = unescape(open(src, encoding="utf-8").read())
    heads = [(m.start(), int(m.group(1)), m.group(2).strip())
             for m in UNIT.finditer(text)]
    for i, (pos, no, title) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        block = text[pos:end]
        rows = []
        for m in ENTRY.finditer(block):
            word = m.group(2).strip()
            cat = m.group(3).strip()
            zh = re.sub(r"^[（(]\s*", "", m.group(4).strip())
            zh = zh.split("（")[0].strip()
            p = POS_MAP.get(cat)
            if p == "phrase" or p is None:
                p = guess_pos(word, zh)
            if not zh:
                continue
            rows.append((word, "/%s/" % m.group(1).strip(), p, zh))
        seen, uniq = set(), []
        for r in rows:
            k = r[0].lower()
            if k in seen:
                continue
            seen.add(k)
            uniq.append(r)
        uniq = fix_ipa(uniq)
        unit = "%s_U%d" % (book, no)
        p = write_unit(unit, title, uniq)
        print("%-7s %-34s %3d 条  %s" % (unit, title[:34], len(uniq), p))


if __name__ == "__main__":
    main()
