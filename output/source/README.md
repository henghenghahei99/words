# 原始素材（source）

本目录是 `output/` 下词表与说文解字的**原始抓取素材**，由 `_tools/ds.py`（DeepSeek Search / Fetch API）在 **2026-10-21** 抓取，供 `_tools/parse.py` 复现结果。

> 版权归各原站所有，此处仅作构建缓存；不需要复现时可整目录删除。
> 页面内容可能随时变动，URL 也可能失效。

## 1. 词表来源

| 文件 | 内容 | 来源 |
|---|---|---|
| `r1.txt` | 7A（七上）单词表 + 默写表，含词性 | 21世纪教育网《七年级英语上册单词表及单词默写表【牛津版（深圳·广州）（2024）】》 `zy.21cnjy.com/20926785` |
| `r2.txt` | 7A 单词音频页（无音标） | 英语朗读宝 `yyld.51jiaoxi.com/qishang/hjnjb_danci.html` |
| `7B_u1.md` … `7B_u8.md` | 7B（七下）逐单元词表，含音标 | 英语朗读宝 `yy.suyang123.com/chuzhong/qinianji/hjnjb_2025xiace_wordsN.html` |
| `8A_r4.txt` | 8A（八上）全册词表，含音标 | 英语朗读宝 `yyld.51jiaoxi.com/bashang/hjnjb_danci.html` |
| `baxia.md` | 8B（八下）全册词表 | `yyld.51jiaoxi.com/baxia/hjnjb_danci.html` |
| `jiushang.md` | 9A（九上）全册词表 | `yyld.51jiaoxi.com/jiushang/hjnjb_danci.html` |
| `jiuxia.md` | 9B（九下，6 单元）全册词表 | `yyld.51jiaoxi.com/jiuxia/hjnjb_danci.html` |

## 2. 音标 / 词性辅助素材

| 文件 | 用途 |
|---|---|
| `7A_ipa_doc0.txt`、`7A_ipa_doc2.txt` | 7A 音标参考（仅覆盖部分单元，未采用） |
| `7A_kkabc.txt` | 旧版（2012）7A 词表，仅作对照，**未采用** |
| `8A_pos.txt` | 8A 单词笔记（含教材词性），用于 `pos_cache.json` |
| `8B_pos.json`、`9A_pos.json`、`9B_pos.json` | 词性相关搜索结果 |
| `8A_r1.txt`、`7B_r3.txt` | 知识点清单类页面，仅作交叉核对 |
| `pos_cache.json` | 由 `_tools/fill_pos.py` 生成的 词→词性 缓存（WordNet + 规则 + 少量人工） |

## 3. 检索记录

`s_*.json` 为 DeepSeek Search 的原始返回（含标题、URL、摘要），保留用于溯源，可删。

## 4. 已知偏差

- 抓取页存在个别错字，已在 `_tools/parse.py` 中用 `SPELL_FIX` 修正：`spred→spread`、`ded→dead`、`unitl→until`、`satisty→satisfy`。
- 7A 源页无音标，`output/7A_U*.md` 的音标由 `eng_to_ipa` 自动生成（偏美音）。
- 朗读宝页面的部分“音标”是纯 ASCII 残码（如 `rez`），已在生成时改用自动音标。
