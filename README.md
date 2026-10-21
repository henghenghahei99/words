# 初中英语单词表 · 沪教牛津版（2024/2025 修订版 · 广州/深圳）

## 文件结构

```
words/
├── output/
│   ├── 7A_U1.md … 7A_U8.md      七年级上册，8 个单元
│   ├── 7B_U1.md … 7B_U8.md      七年级下册，8 个单元
│   ├── 8A_U1.md … 8A_U8.md      八年级上册，8 个单元
│   ├── 8B_U1.md … 8B_U8.md      八年级下册，8 个单元
│   ├── 9A_U1.md … 9A_U8.md      九年级上册，8 个单元
│   ├── 9B_U1.md … 9B_U6.md      九年级下册，6 个单元
│   ├── *_EXPLAIN.md             每单元一份“说文解字”（46 份）
│   ├── all.csv                  全部条目汇总（unit,word,ipa,pos,meaning）
│   └── source/                  原始抓取素材 + 来源说明（可删）
├── _tools/                      抓取 / 解析 / 生成脚本
└── README.md
```

每个 `output/xx_UN.md` 为一张表：序号 / **英文 / 音标 / 词性 / 中文**。
共 46 个单元、1537 条（含短语）；**词性 1537/1537**、音标 1511/1537。

## 单元标题

| 册 | U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|---|
| 7A | Friendship | School life | The seasons | The Earth | Off to space | Travelling around | Fun after school | Collecting as a hobby |
| 7B | People around us | Travelling around the world | Trees and us | Our animal friends | Water is life | Electricity everywhere | Role models of our time | Follow your interests |
| 8A | Encyclopaedias | Numbers | Computers | Inventions | Educational exchanges | Ancient stories | Memory | English week |
| 8B | Helping those in need | Body Language | Traditional skills | Cartoons and comic strips | Save the endangered animals | Pets | The unknown world | Life in the future |
| 9A | Wise men in history | Great minds | Family life | Problems and advice | Action! | Healthy diet | The Adventures of Tom Sawyer | Surprise endings |
| 9B | Great explorations | Culture shock | The environment | Natural disasters | Sport | Caring for your health | — | — |

## 数据来源（2026-10-21 抓取）

- 7A：`zy.21cnjy.com/20926785`《七年级英语上册单词表及单词默写表【牛津版（深圳·广州）（2024）】》
- 7B：`yy.suyang123.com/…/hjnjb_2025xiace_words1-8.html`（沪教牛津版七下，逐单元页）
- 8A / 8B / 9A / 9B：`yyld.51jiaoxi.com/{bashang,baxia,jiushang,jiuxia}/hjnjb_danci.html`

## 说文解字（*_EXPLAIN.md）

每个单元另配一份 `xx_UN_EXPLAIN.md`，结构：

1. 本单元词根地图（词根 / 含义 / 来源 / 本单元词 / 常见同根词）
2. 逐词说文解字
   - **单词**（恰好 5 行）：词根·渊源 / 同根词（每词带构词括注）/ 前缀·后缀（带“例：…”）/ 同义·反义（**每个词带中文释义**）/ **变形**
   - **搭配短语**（恰好 2 行）：只给 **同义搭配 / 反义搭配**
3. 前缀·后缀小结表
4. 同义·反义速查表（带中文释义）

“变形”一行包含：

| 词性 | 必给内容 |
|---|---|
| 动词 | 第三人称单数 / 过去式 / 过去分词 / 现在分词（不规则动词必须正确，如 go→went/gone/going） |
| 名词 | 复数（不规则复数、不可数词均需标明） |
| 形容词 / 副词 | 比较级 / 最高级（多音节用 more/most，不作比较标“无比较级”） |
| 全部 | 词性派生：名词/形容词/副词 + 中文，如 improvement n. 改进、improved adj. 改良的 |

例：

```
- **同义·反义**：同义 truthful（诚实的）, sincere（真诚的）；反义 dishonest（不诚实的）, deceitful（欺骗的）。
- **变形**：形容词 → 比较级：more honest；最高级：most honest；名词派生 → honesty n. 诚实；副词派生 → honestly adv. 诚实地。
```

生成脚本：`_tools/gen_explain.py`（全量）、`_tools/fix_phrases.py`（搭配条目收拢成 2 行）、
`_tools/check_explain.py`（校验）、`_tools/regen_colloc.py`（批量改搭配格式）、
`_tools/fix_entry.py`（单条重生成）、`_tools/repair_explain.py`（修复结构）。
词源为模型按通行词源词典整理，**非教材注释**，建议抽查后再给学生用。

### 校验结果（最近一次）

`python3 _tools/check_explain.py`：46 个单元、**缺词条 0**；
单词条目 1187 条全部 5 行、搭配条目 350 条全部 2 行；
同义·反义带中文 100%；动词时态 / 名词复数 / 形容词比较级缺失 0。

## 已知问题

1. **音标来源不一**：7B–9B 的音标取自“英语朗读宝”页面（教材配套）；7A 的源页面没有音标，
   由 `eng_to_ipa` 自动生成（偏美音，如 guitar `/gɪˈtɑr/`；教材标注为 `/gɪˈtɑː(r)/`）。
   短语（含 `...`、括号、生僻词）可能没有音标。
2. **词性为推断值**：7A、7B 与 8A 大部分来自教材配套资料；其余由 WordNet 义项占比 + 后缀规则
   + 少量人工表补齐（脚本 `_tools/fill_pos.py`，结果缓存在 `output/source/pos_cache.json`）。
   短语按首词功能标注（如 `take care of` → v.、`in fact` → prep.），个别可能不准。
3. **9B 只有 6 个单元**（教材本身如此）。
4. 已修正的源站错误：`add` → v.、`wisely` → adv.、`spred` → `spread`、`ded` → `dead`；
   源页中纯 ASCII 的“音标”（如 raise 写成 `rez`）已自动改用正确音标。
5. 已修正的词性（源站把名词义标成 v./adj.）：`pyramid`、`spelling`、`meaning`、`post`、
   `tool`、`thought`、`stranger`、`desert`、`present` → n.（`present` 作“现在的”为 adj.）、
   `mind`（介意）→ v.。
6. 抓取文本仍可能有个别错字/漏词，**以课本词汇表为准**；可直接改对应 md 与 all.csv。

## 重新生成

```bash
export DEEPSEEK_API_KEY=...            # 不写入任何文件
python3 _tools/ds.py search "查询词" out.json 10
python3 _tools/ds.py fetch "URL" page.md
python3 _tools/parse.py                # 重新生成 46 个 md + all.csv
python3 _tools/gen_explain.py --force 7A_U1   # 重做一个单元的说文解字
python3 _tools/fix_phrases.py          # 把搭配条目收拢成 2 行
python3 _tools/check_explain.py        # 全量校验（覆盖 / 行数 / 中文释义 / 变形标签）
```

依赖：`pip install eng-to-ipa nltk`（nltk 需 `wordnet` 语料，仅用于推断词性）。
填词性：先跑 `python3 _tools/fill_pos.py` 更新缓存，再跑 `parse.py`。

Search / Fetch 均为 `https://api.deepseek.com/v1/tools/{search,fetch}`，按次计费（5 元/1000 次）。
