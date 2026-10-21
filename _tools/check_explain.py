#!/usr/bin/env python3
"""校验 output/*_EXPLAIN.md 的结构与「变形 / 同义·反义」字段质量。

检查项：
  1. 词表覆盖（每个单元词条都有对应 ### 段）
  2. bullet 数量（单词 5 条；搭配 2 条）
  3. 同义·反义是否带中文释义
  4. 变形是否含时态（动词）/ 复数（名词）/ 比较级（形容词）
  5. 超长行、重复标题

用法：python3 check_explain.py [UNIT ...]
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(HERE), "output")

CJK = re.compile(r"[\u4e00-\u9fff]")


def parse_unit(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or not cells[0].isdigit():
            continue
        rows.append({"idx": int(cells[0]), "word": cells[1],
                     "pos": cells[3], "meaning": cells[4]})
    return rows


def is_phrase(r):
    w = r["word"]
    return " " in w.strip() or "..." in w or "…" in w


def parse_entries(text):
    """### 12. word /ipa/ pos 中文  ->  {idx: (header, block)}"""
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^### (\d+)\.\s*(.+)$", line)
        if m:
            if cur:
                out[cur] = buf
            cur, buf = int(m.group(1)), []
        elif cur is not None:
            buf.append(line)
    if cur:
        out[cur] = buf
    return out


def check_unit(unit):
    src = os.path.join(ROOT, unit + ".md")
    exp = os.path.join(ROOT, unit + "_EXPLAIN.md")
    res = {"unit": unit, "missing": [], "bullets": [], "syn": [],
           "form": [], "long": [], "dup": []}
    if not os.path.exists(exp):
        res["missing"].append("*FILE*")
        return res
    rows = parse_unit(src)
    text = open(exp, encoding="utf-8").read()
    ent = parse_entries(text)
    for r in rows:
        if r["idx"] not in ent:
            res["missing"].append(r["word"])
            continue
        block = [l for l in ent[r["idx"]] if l.startswith("- **")]
        blk = "\n".join(block)
        form = next((l for l in block if l.startswith("- **变形**")), "")
        syn = next((l for l in block if l.startswith("- **同义")), "")
        pos = r["pos"]
        phrase_style = (len(block) == 2 and block[0].startswith("- **同义搭配")
                        and block[1].startswith("- **反义搭配"))
        want = 2 if (is_phrase(r) or phrase_style) else 5
        if len(block) != want:
            res["bullets"].append((r["word"], len(block)))
        if not is_phrase(r) and not phrase_style:
            if not syn:
                res["syn"].append(r["word"])
            else:
                # 同义/反义后面必须有中文
                body = syn.split("：", 1)[-1]
                if not CJK.search(body):
                    res["syn"].append(r["word"])
                else:
                    for seg in re.split(r"[；;]", body):
                        seg = seg.strip()
                        if not seg or seg.endswith("无") or "无" == seg:
                            continue
                        if re.search(r"[a-zA-Z]", seg) and not CJK.search(seg):
                            res["syn"].append(r["word"])
                            break
            bad = False
            if re.search(r"\b(vt|vi|v)\.", pos) and not all(
                    x in form for x in ("过去式", "过去分词", "现在分词")):
                bad = True
            if re.search(r"\b(n)\.", pos) and ("复数" not in form
                                               and "不可数" not in form):
                bad = True
            if re.search(r"\b(adj|a)\.", pos) and ("比较级" not in form
                                                   and "无比较级" not in form):
                bad = True
            if not form:
                bad = True
            if bad:
                res["form"].append(r["word"])
        _ = blk
    for line in text.splitlines():
        if len(line) > 600 and not line.startswith("|"):
            res["long"].append(line[:40])
    heads = re.findall(r"(?m)^### \d+\.\s*(.+)$", text)
    seen = set()
    for h in heads:
        if h in seen:
            res["dup"].append(h[:30])
        seen.add(h)
    return res


def main():
    units = sys.argv[1:]
    if not units:
        units = sorted(os.path.basename(p)[:-3] for p in
                       glob.glob(os.path.join(ROOT, "[0-9]*_U[0-9]*.md"))
                       if not p.endswith("_EXPLAIN.md"))
    tot = 0
    for u in units:
        r = check_unit(u)
        tot += len(r["missing"])
        flags = {k: v for k, v in r.items() if k != "unit" and v}
        if flags:
            print(u, json_like(flags))
    print("units:", len(units), "缺词条合计:", tot)


def json_like(d):
    return " ".join("%s=%s" % (k, v[:8] if isinstance(v, list) else v)
                    for k, v in d.items())


if __name__ == "__main__":
    main()
