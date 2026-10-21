#!/usr/bin/env python3
"""Render the dictionary: output/dictionary.md + output/index.html (+ per-letter files)."""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
DATA = os.path.join(SEARCH, "data")
OUT = os.path.join(SEARCH, "output")
LEVELS = ["小学", "初中", "高中", "CET4", "CET6"]


def load():
    words = {w["word"].lower(): w for w in json.load(open(os.path.join(DATA, "words.json"), encoding="utf-8"))}
    entries = {}
    p = os.path.join(DATA, "entries.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if "\t" not in line:
                continue
            w, block = line.rstrip("\n").split("\t", 1)
            entries[w] = block.replace("\\n", "\n")
    return words, entries


def md_block(block):
    return block.strip().replace("/-／", "/—/").replace("//", "/—/")


def anchors(letter):
    return "letter-%s" % letter


def main():
    words, entries = load()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "letters"), exist_ok=True)

    keys = [w for w in sorted(entries, key=lambda w: (w, words.get(w, {}).get("rank", 9)))
            if w in words]
    by_letter = {}
    for w in keys:
        by_letter.setdefault(w[0].upper(), []).append(w)
    letters = sorted(by_letter)

    total = len(keys)
    level_count = {lv: sum(1 for w in keys if lv in words.get(w, {}).get("levels", []))
                   for lv in LEVELS}

    # ---------- markdown ----------
    md = ["# 英语词源词典 · 说文解字", "",
          "> 收录 小学 / 初中 / 高中 / 大学四级 / 大学六级 共 **%d** 词。" % total,
          "> 词源按 Oxford / Merriam-Webster / Online Etymology Dictionary 整理，非教材注释；有争议处标“存疑”。",
          "",
          "## 目录", ""]
    md.append("| 字母 | 词数 | 字母 | 词数 |")
    md.append("|---|---|---|---|")
    half = (len(letters) + 1) // 2
    for i in range(half):
        a = letters[i]
        b = letters[i + half] if i + half < len(letters) else ""
        md.append("| [%s](#%s) | %d | %s | %s |" % (
            a, anchors(a), len(by_letter[a]),
            ("[%s](#%s)" % (b, anchors(b))) if b else "", len(by_letter[b]) if b else ""))
    md += ["", "分级： " + " · ".join("%s %d" % (lv, level_count[lv]) for lv in LEVELS), ""]
    for L in letters:
        md += ["", '<a id="%s"></a>' % anchors(L), "", "## %s" % L, ""]
        for w in by_letter[L]:
            md.append(md_block(entries[w]))
            md.append("")
    open(os.path.join(OUT, "dictionary.md"), "w", encoding="utf-8").write("\n".join(md))

    # ---------- per-letter markdown ----------
    for L in letters:
        part = ["# %s" % L, ""]
        for w in by_letter[L]:
            part.append(md_block(entries[w]))
            part.append("")
        open(os.path.join(OUT, "letters", "%s.md" % L), "w", encoding="utf-8").write("\n".join(part))

    # ---------- per-level index ----------
    lv_dir = os.path.join(OUT, "levels")
    os.makedirs(lv_dir, exist_ok=True)
    for lv in LEVELS:
        ws = [w for w in keys if lv in words.get(w, {}).get("levels", [])]
        lines = ["# %s 词汇索引（%d 词）" % (lv, len(ws)), ""]
        for w in ws:
            first = ""
            for l in entries[w].splitlines():
                if l.startswith("- **释义**"):
                    first = l.split("：", 1)[-1].strip()
                    break
            lines.append("- **%s** %s" % (words[w]["word"], first))
        open(os.path.join(lv_dir, "%s.md" % lv), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ---------- html ----------
    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
        return s

    def entry_html(block):
        lines = block.strip().splitlines()
        head = lines[0][4:].strip() if lines[0].startswith("### ") else ""
        head = head.replace("/-／", "/—/").replace("//", "/—/")
        body = lines[1:]
        h = ['<article class="entry" data-w="%s">' % html.escape(head.split()[0].lower())]
        h.append('<h3 id="%s">%s</h3>' % (html.escape(head.split()[0].lower()), inline(head)))
        h.append("<ul>")
        for l in body:
            if l.startswith("- "):
                h.append("<li>%s</li>" % inline(l[2:]))
        h.append("</ul></article>")
        return "\n".join(h)

    toc_items = "".join('<a href="#%s">%s <small>%d</small></a>' % (anchors(L), L, len(by_letter[L]))
                        for L in letters)
    sections = []
    for L in letters:
        sections.append('<section class="letter" id="%s"><h2>%s</h2>' % (anchors(L), L))
        for w in by_letter[L]:
            sections.append(entry_html(entries[w]))
        sections.append("</section>")

    page = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>英语词源词典 · 说文解字</title>
<style>
:root{--ink:#1d232b;--muted:#6b7683;--line:#dfe4ea;--accent:#0d6c8a}
*{box-sizing:border-box}
body{margin:0;font:16px/1.75 "Noto Serif SC","Songti SC",Georgia,serif;color:var(--ink);background:#fff}
header{padding:28px 32px 12px;border-bottom:1px solid var(--line)}
header h1{margin:0 0 6px;font-size:30px}
header .sub{color:var(--muted);font-size:14px}
.tools{position:sticky;top:0;z-index:9;background:#fff;border-bottom:1px solid var(--line);padding:10px 32px}
.tools input{width:min(420px,60vw);padding:8px 12px;border:1px solid var(--line);border-radius:6px;font-size:15px}
.tools kbd{color:var(--muted);font-size:12px;margin-left:8px}
nav.toc{padding:18px 32px;border-bottom:1px solid var(--line)}
nav.toc h2,.levels h2{font-size:15px;color:var(--muted);margin:0 0 8px;font-weight:600;letter-spacing:.1em}
nav.toc .grid{display:flex;flex-wrap:wrap;gap:6px}
nav.toc a{min-width:56px;text-align:center;text-decoration:none;color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:4px 8px;font-size:14px}
nav.toc a small{color:var(--muted)}
.levels{padding:12px 32px 20px;border-bottom:1px solid var(--line);font-size:14px;color:var(--muted)}
main{padding:8px 32px 60px}
section.letter h2{font-size:26px;margin:34px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--accent)}
article.entry{margin:0 0 18px;padding:10px 0 6px;border-bottom:1px dashed var(--line);break-inside:avoid}
article.entry h3{margin:0 0 6px;font-size:19px;letter-spacing:.02em}
article.entry h3::before{content:"";}
article.entry ul{margin:0;padding-left:20px}
article.entry li{margin:2px 0}
article.entry strong{color:var(--accent)}
.hint{color:var(--muted);font-size:13px;margin:10px 0 0}
@media print{
  .tools,nav.toc .grid small{display:none}
  header{border:0}
  .tools{position:static}
  section.letter{break-before:page}
  article.entry{page-break-inside:avoid}
  body{font-size:11.5pt}
  a{color:inherit;text-decoration:none}
}
</style></head><body>
<header>
  <h1>英语词源词典 · 说文解字</h1>
  <div class="sub">小学 · 初中 · 高中 · CET4 · CET6 ｜ 共 %d 词 ｜ 词源按通行词源词典整理，非教材注释</div>
</header>
<div class="tools"><input id="q" placeholder="查词：输入英文（如 courage），回车跳到该词" autocomplete="off"><kbd>输入时即时过滤，Esc 清除；打印用 Ctrl/Cmd+P，按字母自动分页</kbd></div>
<nav class="toc"><h2>目录</h2><div class="grid">%s</div></nav>
<div class="levels"><h2>分级</h2>%s</div>
<main>%s</main>
<script>
const q=document.getElementById('q');
const entries=[...document.querySelectorAll('article.entry')];
function apply(){
  const v=q.value.trim().toLowerCase();
  if(!v){entries.forEach(e=>e.style.display='');return;}
  let first=null;
  entries.forEach(e=>{
    const hit=e.dataset.w.includes(v);
    e.style.display=hit?'':'none';
    if(hit&&!first)first=e;
  });
  if(first)first.scrollIntoView({block:'center'});
}
q.addEventListener('input',apply);
q.addEventListener('keydown',e=>{if(e.key==='Escape'){q.value='';apply();}});
</script>
</body></html>""" % (total, toc_items,
                      " · ".join("%s %d 词" % (lv, level_count[lv]) for lv in LEVELS),
                      "\n".join(sections))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)

    print("entries:", total, "letters:", len(letters))
    print("level counts:", level_count)
    print("files: dictionary.md, index.html, letters/*.md")


if __name__ == "__main__":
    main()
