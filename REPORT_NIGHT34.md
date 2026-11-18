# REPORT_NIGHT34.md — Night 34：切分错挖掘 → 合并词典候选（负结果，已回退）（2026-11-19 凌晨）

切分错（89–100% 的最大错误类，Night 25 分类）的规则夜：1705 语料挖掘 count≥2 的
真实复合词候选 15 个 → MERGE_WORDS 引擎级实测 → **净负（+0.10，5 改善/25 变差，
净 +163 dist）→ 已回退，24.38 逐位恢复**。与 Night 21 merge_guard 失败同机制：
**全局合并语义下，长句树手术的连带效应吃掉全部短句收益**。

起点：`git log -1` = `1b01b92`。工具：`tools/mine_error_patterns.py`（Night 4 的，
一行未改）、`run_eval_parallel.py`。产物：`eval/night34_results_parallel.json`
（反例档案）、`eval/night34_revert_check.json`（回退确认）。

---

## 1. 挖掘（night30 归档 1705 条，Night 4 同一挖掘器）

切分类 top 候选（expected 整词、got 被假名拆开）：**忠信×9、辞気×5、疏食×3**、
門人/童子/多聞/佚遊/便辟/夜行/軍中/戦兢/大謀/門下/以上 各×2、**孟嘗君×2**（挖到的
是碎片 嘗君，正名是 3 字的 孟嘗君）。

**刻意排除 4 个**：色仁×5、爾舜×2、者有×2、天荒×2——expected 的"合并"是 kanbun.info
把并列概念连写不加假名的**排版约定**，不是词汇（色与仁、爾与舜是两个词），
对这种形态做树合并的语义风险不可控。

## 2. 引擎级实测（不是离线模拟——合并改分词，必须真跑）

15 词加入 MERGE_WORDS → pytest 33 passed → 1705 条引擎实测：

| 项 | night30（合并前） | night34（15 词） |
| --- | --- | --- |
| avgDist | 24.38 | 24.48（**+0.10**） |
| 改善/变差/持平 | — | 5 / **25** / 1675 |
| dist 总量 | — | 改善 -16 vs 变差 +179 |

典型变差：kanwomo-1 +17、itsumotte-1 +14、fushimichi-1 +14、ganenfuka-1 +13——
全是长句（与 Night 21 的 6 条长句变差同形态）。短句侧的目标案例（忠信/辞気 等）
确实改善了 5 条，但长句连带 25 条变差。

## 3. 处置：回退 + 证据留档

- MERGE_WORDS 已回退到 Night 4 的 21 条，注释里记明实验与数据；
- 回退后 1705 条复测 **24.38 逐位恢复**（night34_revert_check.json）+ pytest 33；
- night34_results_parallel.json 保留为反例档案（与 Night 21 的 v4 反例档案同一角色）；
- **未收**的 15 词候选清单完整保留在本报告——要启用必须先做「短句限定合并」的
  产品拍板（Night 21 的护栏实验是"长度护栏失败"，不是"短句合并不可行"；
  正确做法可能是行级隔离的 merge 开关，属产品形态决策，不在规则夜范围）。

## 4. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\mine_error_patterns.py eval/night30_results_parallel.json 30
:: 15 词加回 MERGE_WORDS 后：
python -I tools\run_eval_parallel.py night34_results_parallel.json   :: +0.10 / 5-25
:: 回退后：
python -I tools\run_eval_parallel.py night34_revert_check.json       :: 24.38 恢复
```

## 5. 禁止事项自查

实测净负就回退（没有为了"挖都挖了"硬上线）；排除的 4 个非词汇候选如实给出理由；
回退后逐位恢复验证在案；反例档案保留；旧归档（night30）未覆盖；无 key/token；
只本地提交。
