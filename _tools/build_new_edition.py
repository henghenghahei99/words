#!/usr/bin/env python3
"""从「背诵版」词汇表原文解析出新教材单元词表（output/<UNIT>.md）。

原文形如（抓取时反斜杠被转义，需先去掉）：
    dinosaur / da n s (r)/ n.恐龙 p.4
    die out 灭绝 p.4

用法：
    python3 build_new_edition.py 8A_U1 /tmp/w_23248920.md "Look it up!"
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
ROOT = next((os.path.join(PARENT, d) for d in ("output", "ourput")
             if os.path.isdir(os.path.join(PARENT, d))),
            os.path.join(PARENT, "output"))

POS_TAGS = ("n", "v", "vt", "vi", "adj", "adv", "prep", "pron",
            "conj", "num", "art", "int", "aux", "modal")
POS_RE = r"(?:%s)\." % "|".join(POS_TAGS)
WORD_RE = r"[A-Za-z][A-Za-z'’\-\.,() ]*"

VERB_HEADS = {
    "be", "have", "do", "make", "take", "go", "get", "play", "look", "put",
    "give", "keep", "come", "bring", "turn", "set", "find", "run", "walk",
    "die", "cut", "blow", "pick", "grow", "learn", "study", "read", "write",
    "say", "speak", "tell", "ask", "answer", "help", "use", "work", "live",
    "agree", "allow", "arrive", "belong", "care", "carry", "catch", "change",
    "check", "choose", "clean", "climb", "close", "collect", "compare",
    "complete", "continue", "control", "cook", "count", "cover", "create",
    "deal", "decide", "deliver", "depend", "describe", "develop", "discover",
    "discuss", "draw", "drive", "drop", "eat", "enjoy", "enter", "explain",
    "fall", "feel", "fight", "fill", "finish", "fit", "fix", "fly", "follow",
    "forget", "forgive", "gain", "gather", "hand", "hang", "happen", "hate",
    "hear", "hold", "hope", "hurry", "hurt", "improve", "include", "increase",
    "introduce", "join", "jump", "kick", "know", "laugh", "lead", "leave",
    "let", "lie", "listen", "lose", "love", "mean", "meet", "move", "need",
    "notice", "offer", "open", "order", "pass", "pay", "plan", "plant",
    "point", "practise", "practice", "prepare", "prevent", "produce",
    "promise", "protect", "provide", "pull", "push", "reach", "realize",
    "receive", "record", "relax", "remember", "remind", "repeat", "reply",
    "report", "rest", "return", "ride", "ring", "rise", "save", "see",
    "seem", "sell", "send", "serve", "share", "shine", "show", "sing",
    "sit", "sleep", "smell", "solve", "sound", "spend", "stand", "start",
    "stay", "stop", "succeed", "suggest", "supply", "support", "suppose",
    "swim", "teach", "think", "throw", "touch", "train", "travel", "try",
    "turn", "understand", "visit", "wait", "wake", "want", "wash", "watch",
    "wear", "win", "wish", "wonder", "worry", "write",
    # 短语动词常见首词
    "suffer", "cheer", "tidy", "clean", "deal", "depend", "differ",
    "focus", "insist", "lean", "object", "refer", "rely", "result",
    "search", "stand", "stare", "stick", "succeed", "suffer", "vary",
    "wait", "warn", "waste", "wave", "wipe", "work", "worry",
}
PREP_HEADS = {"in", "on", "at", "of", "to", "with", "for", "by", "from",
              "about", "after", "before", "during", "into", "over", "under",
              "without", "as", "like", "through", "across", "against"}
ADJ_HEADS = {"be", "feel", "keep", "stay", "look", "sound", "get"}


def unescape(s):
    return s.replace("\\", "")


def guess_pos(word, chinese):
    first = re.split(r"[\s\.]+", word.strip().lower())[0]
    if first in PREP_HEADS and first not in ("to",):
        return "prep."
    if first in VERB_HEADS:
        return "v."
    return "n."


def parse_text(text):
    """返回 [(word, ipa, pos, zh)]，按原文顺序。"""
    rows = []
    for raw in text.splitlines():
        line = unescape(raw).strip()
        if not line or line.startswith("#") or line.startswith("序号"):
            continue
        if "p." not in line:
            continue
        m = re.match(r"^(%s?)\s+/([^/]+)/\s*(%s)\s*(.+?)\s+p\.\d+$"
                     % (WORD_RE, POS_RE), line)
        if m:
            word, ipa, pos, zh = m.groups()
            rows.append((word.strip(), "/%s/" % ipa.strip(), pos.strip(),
                         zh.strip()))
            continue
        m = re.match(r"^(%s?)\s+(%s)\s*(.+?)\s+p\.\d+$" % (WORD_RE, POS_RE),
                     line)
        if m:
            word, pos, zh = m.groups()
            rows.append((word.strip(), "", pos.strip(), zh.strip()))
            continue
        m = re.match(r"^(%s?)\s*([\u4e00-\u9fff].*?)\s+p\.\d+$" % WORD_RE, line)
        if m:
            word, zh = m.groups()
            word = word.strip()
            # 短语：无音标、词性按首词推断
            rows.append((word, "", guess_pos(word, zh), zh.strip()))
    return rows


def fix_ipa(rows):
    """源站音标丢失了变音符号（如 /da n s (r)/），用 eng_to_ipa 重算。"""
    try:
        import eng_to_ipa as ipa_mod
    except ImportError:
        return rows
    out = []
    for w, ipa, pos, zh in rows:
        if " " in w:
            out.append((w, "", pos, zh))
            continue
        # 单一单词一律用 eng_to_ipa 重算（源站音标普遍缺字符）
        got = ipa_mod.convert(w)
        if got and "*" not in got:
            ipa = "/%s/" % got
        out.append((w, ipa, pos, zh))
    return out


def write_unit(unit, title, rows):
    path = os.path.join(ROOT, unit + ".md")
    # 丢解析残留（词头不是英文开头、整行只是词性缩写、或词头不足两个字母）
    rows = [r for r in rows
            if re.match(r"^[A-Za-z][A-Za-z'’\-\. ]+$", r[0].strip())
            and not re.fullmatch(
                r"(n|v|vt|vi|adj|adv|prep|pron|conj|num|art|int|aux)\.?",
                r[0].strip())]
    lines = ["# %s · %s" % (unit, title), "",
             "> 沪教牛津版（2024/2025 修订）· 共 %d 条（含短语）" % len(rows),
             "", "| # | 英文 | 音标 | 词性 | 中文 |", "|---|---|---|---|---|"]
    for i, (w, ipa, pos, zh) in enumerate(rows, 1):
        lines.append("| %d | %s | %s | %s | %s |" % (i, w, ipa, pos, zh))
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    unit, src, title = sys.argv[1], sys.argv[2], sys.argv[3]
    text = open(src, encoding="utf-8").read()
    # 只取「背诵版」那段：到形如 “Unit N … 默写版” 的小标题为止
    # （文档标题里也含“背诵版+默写版”，要跳过）
    cut = len(text)
    for m in re.finditer(r"(?m)^\s*Unit\s*\d+[^\n]*默写版", text):
        if "背诵版" in m.group(0):
            continue
        cut = m.start()
        break
    body = text[:cut]
    # 兜底：遇到“默写版”字样（不管在不在标题行）也截断
    k = body.find("（默写版）")
    if k > 0:
        body = body[:k]
    rows = parse_text(body)
    seen, uniq = set(), []
    for r in rows:
        key = r[0].lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    uniq = fix_ipa(uniq)
    p = write_unit(unit, title, uniq)
    print("%s -> %d 条  %s" % (unit, len(uniq), p))
    for r in uniq:
        print("   ", r)


if __name__ == "__main__":
    main()
