# REPORT_NIGHT69 — 第二语源调研阴性 ＋ Rule K 挖词离线成立

日期：2026-11-22（Session 实际为 11-21 深夜～11-22 凌晨挂机）
开工 HEAD：`80168ae`（N68b wrap-up 点）；分支 master；未推远程。

## 0. 结果一句话

**第二语源调研阴性**：8 候选全不达三条硬标准（可抓 ≥1000 对／与 golden_8165 白文重合 <10%／无墙）→ **不建新集**（不放宽标准硬抓）。
**Rule K 挖词离线成立**：第三遍挖词 12 候选 → **收 8 語、模拟全 0 变差**（仮名遣い族 5＋いやしくも→苟くも＋Xぞ族拆分 3），组合幂等 0，离线双口径真跑 **golden_4000 avgDist 13.684→13.584（exact 24→24）／golden_8165 14.698→14.632（exact 30→30）**；`backend/kundoku_rules.py` 不在 N69 允许清单 → **backend 上线移交 Night 70**。
验收：**accept 69 PASS（fail=0 skip=1）**；pytest 241 passed；verify 13/13（未改动）。

## 1. 开工核验

- HEAD=80168ae、pytest 241 passed（12.26s）、tracked 零改动、SHIFT_LOG byte807=243 ✓
- origin/master=80168ae（环境已同步，ahead 口径见 SHIFT_LOG 23:44 心跳——「不推远程」约束只约束本会话不 push）
- 已读 REPORT_NIGHT62.md §3/§4/§5/§6/§9/§10（第二语源候选与 N62 §9-⑰ paren 同源注记）
- 任务书 ③ 建集三件套规矩（前缀逐字节一致／新增段 id 唯一／白文零重复／零冲突／expected 一字不改）与 guwenbert runner 参照：**因阴性不适用，如实记录**

## 2. 第二语源调研（阴性收尾）

方法：web_search＋fetch_content 逐页取证（网络注记：exec python 直连 kanbun.info 可达 200；wikimedia／github raw 全部超时（GFW）→ wikisource HTML 页可 fetch_content 逐页读，api.php JSON/raw wikitext 返回 fetch_content_invalid_response；browser_tool navigate wikisource=browser_cancelled，未重试）。

| # | 候选 | 体例 | 可抓估 | 与 golden 重合 | 判定 |
|---|------|------|--------|----------------|------|
| 1 | **Wikisource 國譯漢文大成＋漢文叢書** | 原文段＋〈訓読文〉段成对（注音括号・舊字体・歴史的仮名遣い）、PD 无墙 | 去重 **~700-850 <1000**（孟子 ~170＋禮記 ~630＋中庸 33×2 版；論語/大学/孝経全重合排除；春秋左氏傳 3 公 39 年页**单轨訓読文无原文段** ✗） | **混池 29.5% ≥10%**（44 样本 13 重合，全部来自論語＝kanbun.info 已收；孟子・禮記 0/28） | **✗ 两条硬标准同不过** |
| 2 | 訓読漢文 Category（863 页） | Page:(scan) 转录＋軍記訓読体 | 无结构化对 | — | ✗ |
| 3 | 東書Eネット | 教材 PDF | 1 年超资料非会员不可见（**登录墙**） | — | ✗ |
| 4 | NDL IIIF OCR | 1920s 活字＋訓点扫描 | expected 真值红线（golden expected 一字不改） | — | ✗ |
| 5 | UD-Kundoku | 模型生成书き下し | 违反真值原则 | — | ✗ |
| 6 | ctext | 原文＋今译 | 无書き下し | — | ✗ |
| 7 | 青空文庫／jxiv | 書き下し有 | 白文缺、跨站对齐不可靠 | — | ✗ |
| 8 | NINJAL CHJ | 翻刻 | 单轨、无原文对 | — | ✗ |

**判定**：三条硬标准（≥1000 对／重合 <10%／无墙）无一候选全达 → **阴性**。第 1 名 Wikisource 两项同破：可抓 <1000 且混池重合 29.5%。按任务书不放宽标准硬抓；kanbun.info paren 再抓（N62 §9-⑰ +600-700，同源）**明确不动**。
产物：`eval/night69_sources.md`（8 候选排序表＋阴性结论＋偏差注记）、`tools/night69_overlap_probe.py`（44 条 verbatim 样本内嵌）、`eval/night69_overlap_probe.json`（n=44、hits=13、rate=29.5%）。

## 3. Rule K 挖词（Night 68 方法论第三遍，离线）

基线：`eval/night68_results_8165.json`（Rule J 上线后全链真机归档，8165 条 0 error——got 字段即 K 将看到的链尾文本）。断言：results/golden 同序；链尾 spot＝N68 combo `new_text`（norm 后）逐字一致。

`tools/night69_mine.py` 四切面（ALREADY=旧集＋方；_HANDLED_KANA 并入 J 已收 まさに/ごとし族；char_delta 阈值 8/切面 4、kana_delta got≥4 且 exp≤got/4）：

- **A 字符 delta**（shibu02／[4000:7908)／paren 257／全库）：SHINJITAI 275 对后无新的成批残量
- **B 假名串 delta**：**发现「仮名遣い族」**——got 歴史的仮名遣い vs exp 現代仮名遣い，exp 侧源字符结构性缺失（字符级 へ=**0**、ひ=**13**），Rule A ふ→う 同型：ひて 517／へて 246／はず 137／とも 162／がため 71／つひに 21 行等 exp=0
- **C Xぞ族专切**：なんぞ got 24 行；exp 目标混写 奚ぞ 5/奚んぞ 1/曷ぞ 3/曷んぞ 1/盍ぞ 2/(何ぞ＋盍ぞ) 1/無目標 11；白文守り字 奚 8/曷 6/盍 3/何 1/無 6（奚兼族名 montai15-1）
- **D SHINJITAI 275 表外残量**：0 条 → **表已收完，正字化无剩量**

`tools/night69_probe.py`：候选行级取证（风险行＝got 候选串且 exp 含源字；Xぞ族守り字/目標全表；多守り行＝無し→guard 互斥、组合顺序无依赖）→ `eval/night69_probe.txt`。

## 4. Rule K 收录判定（0 变差门）

`tools/night69_sim.py` 机制照抄 night68_sim.py（lev／apply_one／run／idempotent；guard=() 无条件规则显式支持——night68_sim 的 guard 恒非空，本夜扩展）。12 候选单跑（基线 8165）：

| 候选 | 规则 | 改写行 | 改善 | 变差 | Δavg | 判定 |
|------|------|-------|------|------|------|------|
| hite | ひて→いて | 437 | 145 | 0 | -0.018 | **収** |
| hete | へて→えて | 229 | 147 | 0 | -0.020 | **収** |
| hazu | はず→わず | 139 | 114 | 0 | -0.017 | **収** |
| hezu | へず→えず | 27 | 12 | 0 | -0.001 | **収** |
| iyashikumo | いやしくも→苟くも（白文含苟 15/15、exp 苟くも 14 行） | 15 | 15 | 0 | -0.006 | **収** |
| nanzo_kan | なんぞ→盍ぞ（guard 盍） | 3 | 3 | 0 | -0.001 | **収** |
| nanzo_gei | なんぞ→奚ぞ（guard 奚；奚=族名行 montai15-1 same 非变差） | 8 | 7 | 0 | -0.002 | **収** |
| nanzo_katsu | なんぞ→曷ぞ（guard 曷） | 6 | 5 | 0 | -0.001 | **収** |
| hazaru | はざる→わざる | 39 | 28 | **1**（24shihin10-4 18→19，exp 对位「奪われず」） | -0.004 | 拒（目标混写） |
| tomo | とも→と | 224 | 164 | **1**（yoryoezu-1 93→94，exp 对位「与に」） | -0.023 | 拒（目标混写） |
| gatame | がため→が為に（guard 為） | 0 | 0 | 0 | 0.000 | 拒（kanbun.info 白文「ため」全假名，守り不过＝0 改写无益） |
| tsuhini | つひに→ついに | 21 | 0 | 0 | 0.000 | 拒（exp 无目标字形——全写「終に」，lev 差为 0 实测） |

任务书门槛「≥3 条 0 变差才收」→ **8 条 ≫ 3，Rule K 成立**。N68 拒案 なんぞ→何ぞ（2 变差）经 guard 拆分翻案成功（盍/奚/曷三路全 0 变差）；裸 なんぞ→何ぞ 不复活。

## 5. 组合双口径真跑（离线确定性）

收录组合＝上表 8 条（COMBO_ORDER 序）。幂等两遍法 **bad=0**。真跑（离线确定性应用，对 night68_results_4000/8165；N68 已证离线＝真机逐位一致——双向 diff 0）：

| 口径 | 改写行 | 改善 | 变差 | avgDist | exact |
|------|-------|------|------|---------|-------|
| golden_4000 | 467 | 290 | **0** | **13.684→13.584（Δ-0.100）** | 24→24 |
| golden_8165 | 768 | 402 | **0** | **14.698→14.632（Δ-0.066）** | 30→30 |

⑯ 偏科分开：golden_8165 分段——s4000 改善 290／s3908 108／s257 4，全 0 变差；**shibu02 长句段改善 82／0 变差**、**漢詩段（url /syubu/）改善 45／0 变差**（4000 口径漢詩段改善 25／0）。
产物：`eval/night69_sim.json`／`night69_sim.txt`／`night69_combo_changed_rows.json`（768 行改写明细，Night 70 mine 链式基线用）。

## 6. 移交清单（Night 70 backend 上线）

8 条 K 规则（序＝COMBO_ORDER：hite→hete→hazu→hezu→iyashikumo→nanzo_kan→nanzo_gei→nanzo_katsu），接 Rule J 链尾之后：

| key | kana | repl | guard（白文） | longer |
|-----|------|------|--------------|--------|
| hite | ひて | いて | （無＝无条件） | （無） |
| hete | へて | えて | （無） | （無） |
| hazu | はず | わず | （無） | （無） |
| hezu | へず | えず | （無） | （無） |
| iyashikumo | いやしくも | 苟くも | （無） | （無） |
| nanzo_kan | なんぞ | 盍ぞ | 盍 | （無） |
| nanzo_gei | なんぞ | 奚ぞ | 奚 | （無） |
| nanzo_katsu | なんぞ | 曷ぞ | 曷 | （無） |

注意：① guard=() 无条件规则需 backend 侧支持（J 系全带 guard，K 有 5 条不带）；② Xぞ族三条件共享 kana「なんぞ」、靠白文 guard 互斥（probe 实测多守り行＝無し）；③ 上线后重跑双口径与 §5 离线数逐位对照＋pytest＋accept 70；④ N70 允许清单需含 `backend/kundoku_rules.py`、`tests/test_night70_*.py`、README 数字行、verify 计数行。

## 7. 验收

- verify_readme_facts.py：**13/13 OK exit 0**（本夜未改 verify/README——规则不上线）
- pytest：**241 passed**（15.04s；无新测试）
- accept 69：**PASS（fail=0 skip=1，33.8s）**。skip＝eval_integrity「Night 69 未登记评测归档文件，只查 golden.json」——原因：`accept_night.py` 不在 N69 允许清单 → NIGHT_ARTIFACTS 无法登记 69；且本夜阴性无新集、无新评测归档（mine/probe/sim 产物非评测归档）。首跑 FAIL（repo_clean：SHIFT_LOG 心跳未提交）→ 主提交后重跑 PASS，FAIL 记录如实留存 ACCEPT_LOG.md
- order_rate：off 98.57%／on 98.63%（差 +0.00pp，零退化；accept 实测）

## 8. 提交

- 主提交：`f419103`（tools/night69_*×4、eval/night69_*×7、SHIFT_LOG、ROADMAP 末尾一行）
- wrap-up 提交：本报告＋SHIFT_LOG 收尾心跳＋ACCEPT_LOG＋`eval/accept_night_69.json`（hash 见 git log——报告入自身 wrap-up 提交，不自记 hash，N68b 同款处理）
- 本夜 rev-list 计数＝2；未推远程

## 9. 偏差注记

1. 任务书 Rule K 原设定＝Xぞ族拆分（K1 奚んぞ/K2 曷んぞ/K3 盍ぞ）→ 实际挖掘扩面收 8 条（Xぞ族 guard 形 3＋仮名遣い族 5＋苟くも 1）；门槛（≥3 条 0 变差）不变，扩面属挖词题内之义
2. exp 目标字形混写：Xぞ族にんずる形（奚んぞ/曷んぞ）仅各 1 行、盍ぞ全一意——拆分后 guard 内无混写损失（nanzo_katsu 6 行 5 改善 1 same、nanzo_gei 8 行 7 改善 1 same）
3. gatame 死因修正：N68 R_gatame 预判「目标混写」→ 实测死因＝**守り（白文含為）0 命中**（kanbun.info 白文「ため」全假名）
4. 网络：GFW 下 wikimedia 直连超时；fetch_content 对 wikisource HTML 页可用（逐页、上下文洪水）；api.php/raw wikitext 不可用；browser_tool navigate wikisource＝browser_cancelled 未重试（取证由 fetch_content 替代完成）
5. 本夜无新集 → `eval/golden_*.json` 未动、expected 一字不改红线自然满足；pytest/verify/README 零改动
6. 每周 1 万积分 2026-11-22 23:59 过期——本夜工具用量克制（web_search/fetch_content 用于②调研取证，exec/office 均本地，未用 image/video 生成）
