#!/usr/bin/env python3
"""解析「全册 U1~U8 单词背诵版/默写版合集」型文档（21世纪教育网）。

背诵版段落形如：
    Unit 2 Body language（背诵版）
    单词/短语 音标 中文意思
    shake / e k/ v. 摇动；抖动
    hold something up —— 举起；抬起

若某单元没有「背诵版」段（如 U1 只给了默写版），则把
「（默写：英译中）」（单词+音标）与「（默写：中译英）」（词性+中文）
按顺序配对。

用法：
    python3 build_from_beisong.py 8B /tmp/8b_all.md
"""
import os
import re
import sys

from build_new_edition import fix_ipa, guess_pos, unescape, write_unit

HDR = re.compile(r"^Unit\s*(\d+)\s*(.*?)（([^）]*)）\s*$")
WORD_IPA_POS = re.compile(
    r"^(.+?)\s+/([^/]+)/\s*"
    r"((?:n|v|vt|vi|adj|adv|prep|pron|conj|num|art|int|aux)\.)\s*(.+)$")
WORD_IPA = re.compile(r"^(.+?)\s+/([^/]+)/\s*$")
IPA_POS = re.compile(
    r"^/([^/]+)/\s*"
    r"((?:n|v|vt|vi|adj|adv|prep|pron|conj|num|art|int|aux)\.)\s*(.+)$")


def split_sections(text):
    """{unit_no: {kind: [lines]}, unit_no: {'title': str}}"""
    units, cur, kind = {}, None, None
    for raw in text.splitlines():
        line = unescape(raw).strip()
        m = HDR.match(line)
        if m:
            cur = int(m.group(1))
            units.setdefault(cur, {"title": m.group(2).strip(), "secs": {}})
            kind = m.group(3)
            units[cur]["secs"].setdefault(kind, [])
            continue
        if cur is not None and kind is not None:
            units[cur]["secs"][kind].append(line)
    return units


def parse_block(lines):
    rows = []
    for line in lines:
        if not line or line.startswith("单词/短语") or line.startswith("#"):
            continue
        if "——" in line:
            w, zh = line.split("——", 1)
            w, zh = w.strip(), zh.strip()
            rows.append((w, "", guess_pos(w, zh), zh))
            continue
        m = WORD_IPA_POS.match(line)
        if m:
            rows.append((m.group(1).strip(), "/%s/" % m.group(2).strip(),
                         m.group(3), m.group(4).strip()))
            continue
        m = WORD_IPA.match(line)
        if m:
            rows.append((m.group(1).strip(), "/%s/" % m.group(2).strip(),
                         "", ""))
            continue
    return rows


def build_book(book, path):
    text = open(path, encoding="utf-8").read()
    units = split_sections(text)
    out = []
    for no in sorted(units):
        info = units[no]
        secs = info["secs"]
        title = info["title"] or ("Unit %d" % no)
        if "背诵版" in secs:
            rows = parse_block(secs["背诵版"])
        else:
            # 用默写版配对：英译中（词+音标）/ 中译英（词性+中文）
            a = [r for r in parse_block(secs.get("默写：英译中", []))]
            b = [r for r in parse_block(secs.get("默写：中译英", []))]
            rows = []
            for i, (w, ipa, _, _) in enumerate(a):
                if i < len(b):
                    _, _, pos, zh = b[i]
                    rows.append((w, ipa, pos or guess_pos(w, zh), zh))
                else:
                    rows.append((w, ipa, guess_pos(w, ""), ""))
        # 去重
        seen, uniq = set(), []
        for r in rows:
            k = r[0].lower()
            if not k or k in seen:
                continue
            seen.add(k)
            uniq.append(r)
        uniq = fix_ipa(uniq)
        unit = "%s_U%d" % (book, no)
        p = write_unit(unit, title, uniq)
        print("%-7s %-32s %3d 条  %s" % (unit, title[:32], len(uniq), p))
        out.append(unit)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    build_book(sys.argv[1], sys.argv[2])
