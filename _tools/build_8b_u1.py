#!/usr/bin/env python3
"""生成 8B_U1：以「沪教新8下全册」的默写顺序为准，
中文来自朗读宝页（单词）+ 默写中译英段（短语）。

用法：python3 build_8b_u1.py /tmp/sy/8x_1.md /tmp/8b_all.md
"""
import sys

from build_from_beisong import parse_block, split_sections
from build_from_suyang import parse_suyang
from build_new_edition import fix_ipa, guess_pos, write_unit

MANUAL = {"joy": ("n.", "快乐；喜悦")}


def main():
    sy_src, bs_src = sys.argv[1], sys.argv[2]
    sy = {r[0].lower(): (r[2], r[3])
          for r in parse_suyang(open(sy_src, encoding="utf-8").read())}
    units = split_sections(open(bs_src, encoding="utf-8").read())
    u = units[1]
    order = [r[0] for r in parse_block(u["secs"]["默写：英译中"])]
    zh_list = [r[3] for r in parse_block(u["secs"]["默写：中译英"])]
    n_words = len(order) - len(zh_list)
    zh_map = dict(zip(order[n_words:], zh_list))
    rows = []
    for w in order:
        k = w.lower()
        if k in sy:
            pos, zh = sy[k]
        elif k in zh_map:
            pos, zh = guess_pos(w, zh_map[k]), zh_map[k]
        elif k in MANUAL:
            pos, zh = MANUAL[k]
        else:
            pos, zh = guess_pos(w, ""), "—"
        rows.append((w, "", pos, zh))
    rows = fix_ipa(rows)
    p = write_unit("8B_U1", "Helping those in need", rows)
    print(p, len(rows))


if __name__ == "__main__":
    main()
