#!/usr/bin/env python3
"""Generate dictionary-style 说文解字 entries for the merged word list.

Usage:
  python3 gen_dict.py --letter A      # only headwords starting with A
  python3 gen_dict.py --all           # everything still missing
  python3 gen_dict.py --force --letter A
Cache: data/entries.jsonl  (word<TAB>markdown block, appended per batch)
"""
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
DATA = os.path.join(SEARCH, "data")
WORDS = os.path.join(DATA, "words.json")
CACHE = os.path.join(DATA, "entries.jsonl")
API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-chat"
BATCH = 16
LOCK = threading.Lock()

SYSTEM = ("你是资深英语词源词典编纂者。为中学生与大学生编写简明可信的词源词条；"
          "词源按 Oxford / Merriam-Webster / Online Etymology Dictionary 通行说法，"
          "不确定的写“存疑”，绝不编造。")

RULES = """每个词条严格按下面格式输出（不要开场白、不要总结、不要编号外的内容）：

### {word}  /{ipa}/  〔{levels}〕
- **释义**：{pos} 中文；{pos} 中文（按常用度排序，最多 3 个义项）
- **词源**：词根（含义）+ 语源链（如 拉丁 xxx → 古法语 xxx → 英语）+ 本义如何引申为今义（1–2 句）
- **同根词**：3–5 个，每个都带构词/来源括注，如 record（**re-** 回 + cor 心 = 记在心里→记录）
- **词缀**：前缀/后缀 + 含义，并给“例：…”；没有词缀写“无（单纯词）”
- **同义·反义**：同义 word（中文）, word（中文）；反义 word（中文）（没有就写“无”）
- **变形**：必须带标签，按词性给全：
  名词 → 复数：children（不可数写“不可数”）；
  动词 → 第三人称单数：goes；过去式：went；过去分词：gone；现在分词：going；
  形容词/副词 → 比较级：better；最高级：best（无则写“无比较级”）；
  词性派生 → 名词/形容词/副词/动词形式，各带中文（如 improvement n. 改进）。
  本词不具备的项省略，不要编造。

硬性要求：
1. 每词恰好 6 个 bullet，顺序不变；`###` 行只出现一次，格式为 `### 单词  /音标/  〔级别〕`。
2. 词源准确；有争议标“存疑”；不要写与词源无关的故事。
3. 同根词、词缀例词必须是真实常用词，且不要用本词自身当例词。
4. 释义紧扣我给的中文提示，不要漏掉核心义项。
5. 严禁重复同一词语凑长度。
6. 同义/反义词必须逐个附中文释义，如 bravery（勇敢）, valor（英勇）。
7. 变形必须覆盖：名词复数、动词四态（三单/过去式/过去分词/现在分词）、形容词副词三级、以及各词性派生词；不能只写一两个。
"""


def chat(user, max_tokens=8000, temperature=0.3, retries=4):
    import time
    import urllib.error
    import urllib.request
    if not KEY:
        sys.exit("DEEPSEEK_API_KEY not set")
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    for attempt in range(retries):
        req = urllib.request.Request(
            API, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + KEY,
                     "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception:
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise


def load_cache():
    cache = {}
    if os.path.exists(CACHE):
        for line in open(CACHE, encoding="utf-8"):
            if "\t" in line:
                w, block = line.rstrip("\n").split("\t", 1)
                cache[w.lower()] = block
    return cache


def append_cache(items):
    with LOCK, open(CACHE, "a", encoding="utf-8") as f:
        for w, block in items:
            f.write("%s\t%s\n" % (w.lower(), block.replace("\n", "\\n")))


def fmt_word(it):
    return "%s  /%s/  〔%s〕｜提示义：%s" % (
        it["word"], it["ipa"] or "—", "·".join(it["levels"]),
        it.get("zh") or "—")


def gen_batch(batch):
    body = "\n".join(fmt_word(it) for it in batch)
    prompt = ("请为下面 %d 个词写词条。\n\n%s\n\n词条清单：\n%s"
              % (len(batch), RULES, body))
    text = chat(prompt)
    k = text.find("### ")
    if k > 0:
        text = text[k:]
    text = re.sub(r"(?m)^(### .*)\n\1\n", r"\1\n", text)
    blocks = {}
    parts = re.split(r"(?m)^### ", text)
    for p in parts[1:]:
        head = p.split("\n", 1)[0]
        m = re.match(r"([A-Za-z][A-Za-z'’\-\. ]*)", head)
        if not m:
            continue
        w = m.group(1).strip().lower()
        blocks[w] = "### " + p.strip()
    items = [(w, b) for w, b in blocks.items()]
    missing = [it for it in batch if it["word"].lower() not in blocks]
    return items, missing, text


def run(words, force=False):
    cache = load_cache()
    todo = [w for w in words if force or w["word"].lower() not in cache]
    print("total %d, todo %d" % (len(words), len(todo)))
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    done = 0

    def work(b):
        nonlocal done
        items, missing, _ = gen_batch(b)
        append_cache(items)
        done += len(items)
        print("  batch %d/%d ok (%d)" % (batches.index(b) + 1, len(batches), len(items)))
        if missing:
            print("   missing:", [m["word"] for m in missing])

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(work, batches))
    print("generated", done)


def main():
    args = sys.argv[1:]
    force = "--force" in args
    words = json.load(open(WORDS, encoding="utf-8"))
    if "--letter" in args:
        L = args[args.index("--letter") + 1].upper()
        words = [w for w in words if w["word"][0].upper() == L]
    if "--words" in args:
        want = {x.strip().lower() for x in args[args.index("--words") + 1].split(",")}
        words = [w for w in words if w["word"].lower().rstrip(".") in want
                 or w["word"].lower() in want]
    if "--words-file" in args:
        want = {x.strip().lower() for x in
                open(args[args.index("--words-file") + 1], encoding="utf-8") if x.strip()}
        words = [w for w in words if w["word"].lower().rstrip(".") in want
                 or w["word"].lower() in want]
    run(words, force)


if __name__ == "__main__":
    main()
