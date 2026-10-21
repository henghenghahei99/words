#!/usr/bin/env python3
"""Generate <UNIT>_EXPLAIN.md (说文解字) for every unit word list.

Usage:
  python3 gen_explain.py 7B_U1            # one unit
  python3 gen_explain.py --all            # all units missing _EXPLAIN
  python3 gen_explain.py --force 7A_U2    # overwrite
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(HERE)
ROOT = next((os.path.join(_PARENT, d) for d in ("output", "ourput")
             if os.path.isdir(os.path.join(_PARENT, d))),
            os.path.join(_PARENT, "output"))
API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-chat"
CHUNK = 18

SYSTEM = (
    "你是资深英语词源与词汇教学专家，为初中生编写“说文解字”。"
    "要求词源准确、构词分析清楚、例词真实常用；不确定的词源标注“存疑”，不编造。"
)

RULES = """输出格式（严格遵守，不要输出任何解释性开场或结尾）：
### {idx}. {word} {ipa} {pos} {meaning}
- **词根·渊源**：词根（含义）+ 语源链（如 拉丁 xxx → 古法语 xxx → 英语）+ 本义如何引申为现义。
- **同根词**：每个同根词都要括注“怎么造出来的/为什么是这个意思”，格式如 record（**re-** 回 + cor 心 = 记在心里→记录）；不同词之间用、
- **前缀·后缀**：每个词缀后面必须跟“（例：词1, 词2）”；例词用该词以外的常用词；没有词缀写“无前后缀（单纯词）”。
- **同义·反义**：同义 词（中文）, 词（中文）；反义 词（中文）, 词（中文）。
  · 每个同义/反义词后面必须用括号跟中文释义，如：同义 brave（勇敢的）, bold（大胆的）；反义 cowardly（胆小的）。
  · 没有同义或反义时写“无”，不要编造。
- **变形**：形态变化 + 词性派生，按下面的小类别给全，用“；”分隔：
  · 动词 → 第三人称单数：X；过去式：X；过去分词：X；现在分词：X（不规则动词必须写对，如 go 的 went / gone / going）。
  · 名词 → 复数：X（不规则复数如 children / mice 必须写对；不可数名词写“不可数”）。
  · 形容词/副词 → 比较级：X；最高级：X（双音节及以上用 more / most；不作比较的写“无比较级”）。
  · 词性派生 → 名词派生 / 形容词派生 / 副词派生：词 + 词性 + 中文，如 courage n. → courageous adj. 勇敢的；bravely adv. 勇敢地。
  · 本词兼有多种词性时（如 adj. 兼 n.），每种词性的形态都要给。
  · 例：go → 动词 → 第三人称单数：goes；过去式：went；过去分词：gone；现在分词：going；名词派生 → going n. 去、进行。
  · 例：cotton → 名词 → 复数：cottons（作“棉花”义时不可数）；形容词 → 无比较级（物质/关系形容词，不作比较）；形容词派生 → cottony adj. 棉质的。

硬性要求：
1. 每条恰好 5 个 bullet，顺序不许变；编号、单词、音标、词性、中文必须与我给的完全一致。
2. 词源按 Oxford / Merriam-Webster / Online Etymology Dictionary 通行说法；有争议写“存疑”。
3. 不要用“略”“同上”之类省略，不要另加标题。
4. 中文释义简洁。
5. 严禁重复同一个词或短语来凑长度（如“staging staging staging…”），每个同根词只出现一次。
6. 若词条本身是搭配/短语（含空格、省略号），则打破上面的 5 条结构，只输出 2 个 bullet：
   - **同义搭配**：表达1 / 表达2
   - **反义搭配**：表达1（没有写“无”）
   其余（词根、同根词、前后缀、词性变化）一律不写，也不要写词源。

示例（仅示范格式与详略程度）：
### 6. courage /kərɪʤ/ n. 勇气；胆量
- **词根·渊源**：拉丁 **cor / cord-**（心）→ 古法语 *corage*，本义“由心而发的力量”，即“勇气”；与 heart 同出 PIE *kerd-*。
- **同根词**：courageous（courage + **-ous** …的：勇敢的）、encourage（**en-** 使 + corage 心 = 给心打气→鼓励）、discourage（**dis-** 去除 + courage = 夺心→使气馁）、cordial（cor 心 + **-ial** 出自内心的→衷心的）、record（**re-** 回 + cor 心 = 记在心里→记录）、cardiac（希腊 kardia 心 + **-ac** 心脏的）。
- **前缀·后缀**：名词后缀 **-age**（例：marriage, package）；动词化前缀 **en-**（例：enable）、**dis-**（例：disagree）。
- **同义·反义**：同义 bravery（勇气）, boldness（大胆）；反义 cowardice（怯懦）, timidity（胆小）。
- **变形**：名词 → 复数：courages（多用不可数）；形容词派生 → courageous adj. 勇敢的；副词派生 → courageously adv. 勇敢地；动词派生 → encourage v. 鼓励；discourage v. 使气馁。
"""

SUMMARY_RULES = """根据我给的单词表，输出三个 markdown 表格，用下面三个标记分隔，不要其他文字：
<<<MAP>>>
| 词根 | 含义 | 来源 | 本单元词 | 常见同根词 |
|---|---|---|---|---|
（8~16 行，选本单元最典型的词根；同根词只列 3~5 个，英文即可）

<<<AFFIX>>>
| 词缀 | 含义 | 本单元例词 | 扩展例词 |
|---|---|---|---|
（8~16 行；扩展例词用本单元以外的常用词）

<<<SYN>>>
| 词 | 同义（中文） | 反义（中文） |
|---|---|---|
（最多 20 行，只挑本单元核心词；同义/反义后面用括号给中文，如 brave（勇敢的））
"""


def post(payload, timeout=300, retries=4):
    if not KEY:
        sys.exit("DEEPSEEK_API_KEY not set")
    for attempt in range(retries):
        req = urllib.request.Request(
            API,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + KEY,
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError("HTTP %s: %s" % (e.code, body))
        except Exception:
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise


def chat(user, max_tokens=8000, temperature=0.3):
    return post({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    })


def clean_md(s):
    s = re.sub(r"[ \t]+（", "（", s)
    s = re.sub(r"（[ \t]+", "（", s)
    s = re.sub(r"[ \t]+）", "）", s)
    s = re.sub(r"\|[ \t]+", "| ", s)
    return s.strip()


def parse_unit(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or not cells[0].isdigit():
            continue
        rows.append({
            "idx": int(cells[0]), "word": cells[1], "ipa": cells[2],
            "pos": cells[3], "meaning": cells[4],
        })
    return rows


def fmt_row(r):
    ipa = r["ipa"] or ""
    pos = r["pos"] or ""
    return "%d. %s %s %s %s" % (r["idx"], r["word"], ipa, pos, r["meaning"])


def gen_entries(unit, rows):
    out = []
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i:i + CHUNK]
        body = "\n".join(fmt_row(r) for r in chunk)
        prompt = ("请为下面 %d 个词条写说文解字。\n\n%s\n\n词条：\n%s"
                  % (len(chunk), RULES, body))
        text = chat(prompt)
        text = text.strip()
        # keep only the "### " part
        idx = text.find("### ")
        if idx > 0:
            text = text[idx:]
        text = re.sub(r"(?m)^(### \d+\..*)\n\1\n", r"\1\n", text)
        out.append(text)
        # check coverage, retry missing ones once
        missing = [r for r in chunk if ("### %d." % r["idx"]) not in text]
        if missing:
            body2 = "\n".join(fmt_row(r) for r in missing)
            prompt2 = ("上一次输出漏了这些词条，请只补这些（格式同前）。\n\n%s\n\n词条：\n%s"
                       % (RULES, body2))
            text2 = chat(prompt2).strip()
            j = text2.find("### ")
            if j > 0:
                text2 = text2[j:]
            out.append(text2)
        print("  %s chunk %d/%d ok" % (unit, i // CHUNK + 1,
                                       (len(rows) + CHUNK - 1) // CHUNK))
    return "\n\n".join(out)


def gen_summary(rows):
    body = "\n".join(fmt_row(r) for r in rows)
    text = chat("本单元词表如下：\n%s\n\n%s" % (body, SUMMARY_RULES))
    parts = {"map": "", "affix": "", "syn": ""}
    for key, tag in (("map", "<<<MAP>>>"), ("affix", "<<<AFFIX>>>"),
                     ("syn", "<<<SYN>>>")):
        k = text.find(tag)
        if k >= 0:
            rest = text[k + len(tag):]
            nxt = min([rest.find(t) for t in ("<<<MAP>>>", "<<<AFFIX>>>", "<<<SYN>>>")
                       if rest.find(t) >= 0] or [len(rest)])
            parts[key] = rest[:nxt].strip()
    return parts


def build(unit, force=False):
    src = os.path.join(ROOT, unit + ".md")
    dst = os.path.join(ROOT, unit + "_EXPLAIN.md")
    if os.path.exists(dst) and not force:
        print("skip", unit)
        return
    rows = parse_unit(src)
    if not rows:
        print("EMPTY", unit)
        return
    title = ""
    for line in open(src, encoding="utf-8"):
        if line.startswith("# "):
            title = line[2:].strip()
            break
    entries = gen_entries(unit, rows)
    summ = gen_summary(rows)
    entries = clean_md(entries)
    summ = {k: clean_md(v) for k, v in summ.items()}
    head = [
        "# %s 说文解字%s" % (unit, (" · " + title.split(" · ")[-1]) if " · " in title else ""),
        "",
        "> 配套 `%s.md`（沪教牛津版 2024/2025 修订，%d 条）" % (unit, len(rows)),
        "> 说明：音标取自本单元词表；**词源为通用词典学信息，不是教材注释**，有争议处标注“存疑”。",
        "> 每条包含：词根与渊源 / 同根词 / 前缀·后缀 / 同义·反义（带中文）/ 变形（时态·复数·比较级·词性派生）。",
        "",
        "## 一、本单元词根地图",
        "",
        summ["map"] or "（略）",
        "",
        "## 二、逐词说文解字",
        "",
        entries,
        "",
        "## 三、本单元前缀 / 后缀小结",
        "",
        summ["affix"] or "（略）",
        "",
        "## 四、同义 / 反义速查（本单元核心词）",
        "",
        summ["syn"] or "（略）",
        "",
        "---",
        "",
        "### 制作说明",
        "- 词源按 Oxford / Merriam-Webster / Online Etymology Dictionary 整理，**不是教材原文**。",
        "- 同根词的括注给出构词路径，用于理解“为什么是这个意思”，不要求背诵。",
        "- “变形”里的时态、复数、比较级按《牛津高阶》通行形式给出；标“无比较级 / 不可数”的是本身不作变化的情况。",
        "- 若需增删（例如只保留高频词、加例句），在此文件上直接改即可。",
        "",
    ]
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(head))
    print("done", unit, len(rows), "entries")


def main():
    args = [a for a in sys.argv[1:]]
    force = "--force" in args
    args = [a for a in args if not a.startswith("--")]
    if "--all" in sys.argv:
        units = sorted(os.path.basename(p)[:-3] for p in
                       __import__("glob").glob(os.path.join(ROOT, "[0-9]*_U*.md"))
                       if not p.endswith("_EXPLAIN.md"))
        units = [u for u in units if not os.path.exists(
            os.path.join(ROOT, u + "_EXPLAIN.md"))]
    else:
        units = args
    if not units:
        sys.exit(__doc__)
    print("units:", units)
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda u: build(u, force), units))


if __name__ == "__main__":
    main()
