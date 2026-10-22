#!/usr/bin/env python3
"""解析「序号 单词 音标 词性 中文 页码」型词汇表（如新版沪教牛津9上词汇汇总背诵版）。

行形如：
    1 outstanding /a t st nd / adj. 优秀的；杰出的 p.4
    7 * convinced /k n'v nst/ adj. 坚信的；确信的 p.5
    9 dramatist / dr m t st n. 剧作家 p.8      ← 偶尔少一个斜杠

用法：python3 build_from_numbered.py 9A /tmp/9a_all.md
"""
import re
import sys

from build_new_edition import (fix_ipa, guess_pos, parse_text, unescape,
                               write_unit)

HDR = re.compile(r"^Unit\s*(\d+)\s*(.*?)\s*$")
POS_ALT = r"(?:n|v|vt|vi|adj|adv|prep|pron|conj|num|art|int|aux)\."


def normalize(line):
    line = re.sub(r"^\d+\s+", "", line)          # 去掉序号
    line = re.sub(r"^\*\s*", "", line)           # 去掉 * 标记
    if line.count("/") == 1:                     # 补上缺失的结尾斜杠
        line = re.sub(r"/([^/]*?)\s+(%s)" % POS_ALT, r"/\1/ \2", line)
    return line


def main():
    book, src = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    # 只保留第一段（表格化重复段落之前）
    k = text.find("\\#\\# Unit 1")
    if k > 0:
        text = text[:k]
    cur, title = None, ""
    buf, titles = {}, {}
    for raw in text.splitlines():
        line = unescape(raw).strip()
        if not line:
            continue
        if line.startswith("序号") or line.startswith("|"):
            continue
        m = HDR.match(line)
        if m and not re.match(r"^\d", line):
            cur = int(m.group(1))
            title = m.group(2).strip()
            buf[cur] = []
            titles[cur] = title
            continue
        if cur is not None and "p." in line:
            buf[cur].append(normalize(line))
    for no in sorted(buf):
        rows = fix_ipa(parse_text("\n".join(buf[no])))
        unit = "%s_U%d" % (book, no)
        p = write_unit(unit, titles.get(no, ""), rows)
        print("%-7s %-26s %3d 条  %s" % (unit, titles.get(no, "")[:26],
                                        len(rows), p))


if __name__ == "__main__":
    main()
