# REPORT_NIGHT23.md — Night 23：論語分文体评测落地（2026-11-19 凌晨）

按 ROADMAP 准确率深水区方向 + Night 21 §5 顺延项（「論語 genre：keibu 页是 rongo01.html
→ rongo0101-16.html 三级结构、正文用 honbun02 class——需独立解析器」）写细并执行：
**論語文体评测数据落地 + 与故事名言 500 条的同口径分文体对照**。

起点：`git log -1` = `c7d660a`（Night 22 收尾提交）；pytest 33 passed（本夜不改后端）。

结论先给数字（同一生产线、同一把尺子）：

| 文体 | n | 精确匹配 | avgDist | ≤20 字 | 20-40 字 | >40 字 |
| --- | --- | --- | --- | --- | --- | --- |
| 故事名言（golden.json） | 500 | 1/500 | **26.21** | 10.32（n=208） | 24.71（n=144） | 50.01（n=148） |
| 論語（golden_rongo.json） | 117 | 0/117 | **35.55** | **13.74**（n=19） | **20.33**（n=46） | **56.98**（n=52） |

---

## 1. 页面结构（实测，Night 21 记录有两处要修正）

探针：`tools/night23_probe_rongo.py` / `night23_probe_rongo_chapter.py` / `night23_probe_rongo_links.py`。

- 三级结构确认：篇索引 `rongo01.html`..`rongo20.html`（20 篇）→ 章节页 `rongo0101.html` 等
  （篇+章 4 位数编号），每页**一对** genbun01/yomi03。
- **修正 Night 21 的两处记录**：① 正文类名是 `yomi03`（不是 honbun02——honbun02 只出现在
  rongo00 书目页）；② 成对结构仍是 `genbun01` + `yomi03`（与故事部 genbun01/yomi02 同型），
  所以解析器不是全新写，是 build_golden.py 的参数化变体。
- 章节页 genbun01 带「001（01-01）」编号行，须剥掉；yomi03 的 ruby/rt/rp 剥法与 yomi02 相同。
- 篇章分布实测：篇 20（堯曰）只有 3 章；篇 14 有 47 章。

## 2. 数据落地（`tools/build_golden_rongo.py`）

- 每篇取前 6 章（RONGO_PER_PIAN 可调，篇 20 取全部 3 章）→ **117 条，抓取失败 0**。
- 与既有 golden.json 的 id 空间不冲突（rongo0201-1 vs mujun-2 等）。
- 白文混入注记括号（（…））的丢弃（与 build_golden.py 同一过滤，编号行先剥再滤）。
- 抽查核对：rongo0101-1「子曰、學而時習之…」→ expected「子は曰く、学びて時に之を習う、
  亦た説ばしからずや。…」——剥 ruby 后文本完整、含新字体（页面即用新字体，无需正字化
  映射介入 expected 侧）。
- **采样偏差（如实）**：每篇取前 6 章偏各篇开头；篇 20 只有 3 条。这是取样策略不是全量，
  分文体结论按"文体方向"理解，不按逐篇绝对值。

## 3. 論語评测（`tools/run_eval_rongo.py`，117 条 engine OK 117，error 0）

- 进程内 TestClient 走完整 HTTP 栈；**monkeypatch db.save_kundoku 不写库**（与 Day4 §3
  同一验证过的等价路径；写库只持久化不改变输出，省去 117 × ~0.7s 的 D: fsync）。
- 结果：**精确匹配 0/117，avgDist 35.55**；长度分档见开头表格；按篇 n=6 各篇 avgDist
  12.67（篇 07 子罕的短章）～ 50.50（篇 10 鄉党）。
- 最差 5 条全是长对话/叙事段：rongo1601-1（季氏將伐顓臾，dist 250）、rongo2002-1（174）、
  rongo2001-1（堯曰，136）、rongo1806-1（長沮桀溺，100）、rongo1303-1（98）。

## 4. 分文体对照的三个发现

1. **論語整体比故事名言难 9.3（35.55 vs 26.21）**，主因是**长度分布偏长**（>40 字占
   52/117=44%，故事名言只有 148/500=30%）——这与 Night 21 的长度分档洞察一致：
   长句是主要坏点，論語把这个坏点放大了。
2. **同长度档下文体差异真实存在**：≤20 字論語 13.74 vs 10.32（+3.4，对话体的短句里有
   「曰く/也/乎/矣」等文末约定，引擎的推定不合 kanbun.info 的論語页习惯）；但 **20-40 字
   論語反而更好（20.33 vs 24.71）**——这一档的論語多为「X問…。子曰、…」双句结构，
   引擎的引用句处理（は曰く→曰く 规则）与页面约定契合。
3. **精确匹配两文体都≈0**（1/500、0/117）， Rule C' 上线后的精确命中（kantanayu-3）
   仍是孤例——精确匹配的突破不在这条线，与前夜结论一致。

## 5. 没做的（顺延，理由）

- **漢詩（syubu）文体**：韵文训读路径（掲載形态、韵脚）与散文完全不同，Night 21 §5 已声明
  顺延；本夜没有触碰。
- 論語全量 512 章抓取：117 条已支撑文体方向结论；全量抓取是机械扩展，等需要按篇细分时再做。
- 20-40 档「論語更好」的机制解释（是引用句规则还是双句结构本身）需要错误分类审计，
  本夜只记现象不下结论。

## 6. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night23_probe_rongo.py          :: 页面结构探针（3 个）
python -I tools\build_golden_rongo.py           :: 抓取 → eval/golden_rongo.json（117 条）
python -I tools\run_eval_rongo.py               :: 评测 → eval/night23_results_rongo.json
python -I tools\night23_genre_compare.py        :: 分文体对照表
```

## 7. 禁止事项自查

expected（golden_rongo.json）逐字来自 kanbun.info 页面剥 ruby 后的事实文本，未做任何改写；
评测归档 night23_results_rongo.json 由脚本生成、无手工编辑；分档口径（≤20/20-40/>40、剥空白、
levenshtein）与 Night 21/22 完全同一把尺子；采样偏差如实声明；无 key/token；只本地提交。
