#!/usr/bin/env python3
"""从「英语朗读宝」单元单词页解析词表（按课本顺序，含词性+中文，无音标）。

原文形如：
    attack

    翻译：v.袭击；攻击
    翻译：v.袭击；攻击

用法：
    python3 build_from_suyang.py 8A_U8 /tmp/sy8.md "Pets and us"
    python3 build_from_suyang.py --batch books.json
"""
import json
import os
import re
import sys

from build_new_edition import ROOT, fix_ipa, guess_pos, unescape, write_unit

WORD_LINE = re.compile(r"^[A-Za-z][A-Za-z'’\-\.\(\) ]*(?:\.\.\.)?$")
TRANS = re.compile(r"^翻译[：:]\s*(%s)\s*(.*)$"
                   % r"(?:n|v|vt|vi|adj|adv|prep|pron|conj|num|art|int|aux)\.")


def parse_suyang(text):
    lines = [unescape(l).strip() for l in text.splitlines()]
    rows = []
    i = 0
    while i < len(lines) - 1:
        cur = lines[i]
        if not WORD_LINE.match(cur):
            i += 1
            continue
        # 后面可能隔一行音标（如 ˈeldəli），再是 “翻译：…”
        j, ipa_line, trans_line = i + 1, "", ""
        while j < len(lines):
            if lines[j]:
                if not ipa_line and not TRANS.match(lines[j]) and \
                        not re.search(r"[\u4e00-\u9fff]", lines[j]):
                    ipa_line = lines[j]
                elif TRANS.match(lines[j]):
                    trans_line = lines[j]
                    break
                else:
                    break
            j += 1
        if trans_line:
            m = TRANS.match(trans_line)
            pos, zh = m.group(1).strip(), m.group(2).strip()
            if zh.startswith("："):
                zh = zh[1:].strip()
            rows.append((cur.strip(), "", pos, zh))
            i = j + 1
            continue
        i += 1
    # 去重（保持首次出现顺序），并补上短语的词性 / 去掉 “phrase” 标记
    seen, uniq = set(), []
    for w, ipa, pos, zh in rows:
        k = w.lower()
        if k in seen:
            continue
        seen.add(k)
        zh = re.sub(r"^(phrase|phr\.)\s*", "", zh).strip() or "—"
        if not pos:
            pos = guess_pos(w, zh)
        uniq.append((w, ipa, pos, zh))
    return uniq


def build(unit, src, title):
    text = open(src, encoding="utf-8").read()
    rows = fix_ipa(parse_suyang(text))
    return write_unit(unit, title, rows), rows


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    unit, src, title = sys.argv[1], sys.argv[2], sys.argv[3]
    path, rows = build(unit, src, title)
    print("%s -> %d 条  %s" % (unit, len(rows), path))
    for r in rows[:3]:
        print("   ", r)
    print("    ...")
    for r in rows[-3:]:
        print("   ", r)


if __name__ == "__main__":
    main()
