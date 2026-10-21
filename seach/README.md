# 英语词源词典 · 说文解字（小学 → CET6）

一部可查、可打印的词源词典：**6319 个词头**，覆盖 小学 / 初中 / 高中 / 大学四级 / 大学六级。

## 收录统计

| 级别 | 词数（该级别累计） |
|---|---|
| 小学 | 708 |
| 初中 | 2216 |
| 高中 | 3444 |
| CET4 | 4534 |
| CET6 | 2219 |

> 一个词可同时属于多个级别，取“最低级别”作为主标签；上表为各级别包含的词数合计。
> 去重后总词头 **6319**，全部已生成词条（缺 0）。

## 目录

```
seach/
├── output/
│   ├── index.html          词典主页：字母目录 + 查词框 + 打印样式（推荐）
│   ├── dictionary.pdf      可打印 PDF（A4 双栏、1021 页，含目录页码）
│   ├── dictionary.md       全量 Markdown（6319 条，约 4.5 MB）
│   ├── letters/A.md … Z.md 按字母拆分，便于分册打印/阅读
│   └── levels/             分级索引：小学 / 初中 / 高中 / CET4 / CET6
├── data/
│   ├── words.json          合并后的词表（含音标、级别、中文提示）
│   └── entries.jsonl       词条缓存（断点续跑用）
├── source/                 原始词表（小学教材页、中考、高中、四六级） 
└── _tools/
    ├── fetch_primary.py    抓小学（广州教科版）逐单元词表
    ├── build_words.py      合并去重、打级别标签
    ├── gen_dict.py         生成词条（8 并发，缓存续跑）
    ├── render_dict.py      渲染 md / html / 分级索引
    └── check_dict.py       校验：覆盖率、六要素、超长行
```

## 怎么用

**查词（推荐）**
1. 打开 `output/index.html`（本地可直接双击；也可用任意静态服务器）。
2. 顶部输入框键入英文（如 `courage`），页面即时过滤并跳转；按 `Esc` 清空。
3. 顶部“目录”按 A–Z 跳转；“分级”显示各级词量。

**打印**
1. 最省事：直接打印 `output/dictionary.pdf`（A4、双栏、每字母另起一页、目录带页码）。
2. 或浏览器打开 `index.html` → `Ctrl/Cmd + P`。
2. 每个字母自动另起一页（`section.letter { break-before: page }`），词条 `break-inside: avoid`，不会跨页断开。
3. 需要 PDF：在打印对话框选择“另存为 PDF”。A4、单栏即可；正文 11.5pt。
4. 只想打印某一级：用 `output/levels/小学.md` 等分级索引，或 `output/letters/A.md` 分册。

## 词条字段

| 字段 | 说明 |
|---|---|
| 词头 / 音标 / 〔级别〕 | 级别取该词所属最低级别起，列出全部命中级别 |
| 释义 | 按常用度排序，最多 3 个义项 |
| 词源 | 词根（含义）+ 语源链 + 本义→今义 |
| 同根词 | 3–5 个，每个带构词/来源括注 |
| 词缀 | 前缀/后缀 + 含义 + “例：…”；无则“无（单纯词）” |
| 同义·反义 | 常用同义/反义，每条都带中文释义，如 `big（大的）` |
| 变形 | ① 动词：第三人称单数、过去式、过去分词、现在分词；② 名词：复数（不可数词标“不可数”）；③ 形容词：比较级/最高级（不作比较的标“无比较级”）；④ 词性派生：名词/形容词/副词等，附词性与中文义 |

## 数据来源

| 级别 | 来源 |
|---|---|
| 小学 | 广州教科版（3–6 年级）单词页，`yy.suyang123.com`（共 72 个单元页） |
| 初中 | 沪教牛津版（2024/2025）七上—九下词表 + 中考英语词汇表 |
| 高中 | `mahavivo/english-wordlists` 的 `Highschool_edited.txt` |
| CET4 | 同仓库 `CET4_edited.txt`（4615 词） |
| CET6 | 同仓库 `CET6_edited.txt`（2273 词） |

## 重新生成

```bash
export DEEPSEEK_API_KEY=...          # 搜索/抓取与词条生成共用
python3 _tools/build_words.py        # 合并词表 → data/words.json
python3 _tools/gen_dict.py --all     # 生成缺失词条（可反复运行，自动跳过已缓存）
python3 _tools/gen_dict.py --letter A --force   # 重做某个字母
python3 _tools/fix_labels.py         # 规则补标签（动词四态 / 名词复数 / 比较级）
python3 _tools/fix_edge.py           # 边界词补标签（情态动词、专有形容词、物质名词）
python3 _tools/normalize_entries.py  # 去重 + 折叠重复标签
python3 _tools/check_dict.py         # 校验
python3 _tools/render_dict.py        # 渲染 md / html / 分级索引
python3 _tools/prepare_fonts.py      # 首次生成 PDF 前：Noto CJK → TTF（需 otf2ttf）
python3 _tools/make_pdf.py           # 生成 output/dictionary.pdf
```

## 已知问题

1. **词源为模型生成**，依据通行词源词典，**非教材注释**；有争议处标“存疑”。用作学习参考前建议抽查。
2. 小学词表来自教材配套页面，个别单词（如极短代词）在源页缺失，已能以其他级别补齐的已合并。
3. 少数词头没有音标，显示为 `/—/`。
4. `index.html` 约 6.6 MB（单文件包含全部词条），低配设备首次打开可能稍慢；可改用 `letters/*.md` 分册。
5. 词典只收**单词**，不含短语（教材短语见另一个项目 `words/output/`）。
6. 音标统一用英式音标；个别源站为 ASCII 假音标（如 `rez`）的已用 `eng_to_ipa` 重算。“变形”中少数边界词（情态动词 `might/would`、屈折形词头 `bent/born`、专有形容词 `german/italian`）由规则补标签，非模型生成。

## 校验结果（最近一次）

`check_dict.py`：词表 6319 / 已生成 6319 / 缺 0；格式异常 0；超长行 0；同义反义无中文 0；动词时态标注不全 0；名词缺复数 0；形容词缺比较级 0。
