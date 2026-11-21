# REPORT_NIGHT62.md — 评测扩到约束内上限 golden_7908（kanbun.info 枯竭实证）

日期: 2026-11-21（Night 62）
分支: night62-eval10000（本地提交，不合 master、不推远程）
任务书: 评测扩到 10000 条（golden_4000 + 6000 新对，kanbun.info 文本对，/syubu/ 剩约 270 页优先、其余栏目补，去重，expected 一字不改，新文件 eval/golden_10000.json；规则全跑分长度档×文体 breakdown；guwenbert 只跑新增段离线对比；pytest + accept 62 通过，写报告，本地提交）。
约束: 只做评测扩充，不碰规则和后端。

---

## 1. 结论摘要

- **golden_7908.json 落地**：4000 基座（逐条断言与 golden_4000 一致）+ **新增 3908**
  （N57/N60 池剩 330 + 全站剩页干净对 3579 − 跨源 id 冲突 1），id 全唯一、白文唯一 7883。
- **6000 新对 / 10000 总量在 kanbun.info 上不可达**——sitemap 全站 2696 页盘点 +
  1279 剩页全量抓取实证：干净文本对约束内上限 ≈3900。**用户拍板方案 A：扩到约束内
  上限、文件按实数命名、缺口与第二语源调研写进报告挂拍板**（本报告 §9）。
- 规则引擎全跑 7908 条：**avgDist 13.241、精确 25/7905、error 3**；**确定性对照
  前 4000 条 vs night60 归档 diff=0**（跨夜跨进程第五次）。
- guwenbert 新增段离线 3907 条：avgDist **12.466** vs 规则 12.577，逐条对决
  **规则更好 1366 / guwenbert 更好 1390 / 持平 1151**——五五开（差 0.9%），
  维持 D16「不接 guwenbert」的产品拍板。
- pytest **193→196**（+3 test_golden_7908）；accept 62：预跑 --no-pytest 如实
  FAIL（repo_clean：QA 会话 SHIFT_LOG 登记行未提交），提交后终跑 **PASS**
  （fail=0 skip=1，29.7s）。
- 本夜零规则/后端改动；消耗全部为本地脚本 + 会话推理（AutoClaw 积分内模型），
  无外部 API key。

## 2. 全站盘点（night62_inventory.py，sitemap 口径）

上一会话（QA 会话，见 §8）中断前留下独立盘点产物（night62_sitemap_*.json ×9、
night62_sitemap_inventory.*、night62_koji_*、night62_sample20.* 等），与本夜
night62_inventory 结果**交叉一致**（2696 URL / 已见 1415 页 / 已见白文 4305），
一并保留入档。本夜口径：

| 栏目 | 全站页数 | 剩页 | 抽样密度 | 推算新对 |
|---|---|---|---|---|
| syubu | 688 | 317 | 7.6-8.5 对/页 | ≈2400-2700 |
| shibu02（子部：老子/荘子/孫子/墨子/六韜/三略/司馬法等） | 216 | 216 | 2.6 对/页 | ≈560 |
| syubu02（廿四詩品/宋詩等） | 42 | 42 | 2.3 对/页 | ≈98 |
| shibu01（詩歸） | 10 | 10 | 1.0 对/页 | ≈10 |
| koji（故事名言） | 1151 | 501 | **0 新对/页** | 0 |
| keibu（経部，rongo 章余量） | 559 | 165 | **0 新对/页** | 0 |
| history / miscellaneous | 28 | 28 | 0 | 0 |

推算合计 ≈3100。**在手池子清点**（night62_reservoir.py）：day16_pool 1031 条、
golden.json 500、golden_rongo 117、golden_rongo_full 498、kanbun_parallel 1705
与 golden_4000 白文**全部重叠（0 新）**；仅 night57 池剩 127 + night60 池剩 203
= **330 条未入库**（全部 ≤20 字漢詩）。

→ 约束内上限 ≈3430，6000 新对不可达 → 提请用户拍板 → **方案 A**。

## 3. 全站剩页抓取（night62_scrape_10k.py）

N57 同款解析（genbun01 + yomi02/03 相邻对、剥 ruby/标签、expected 一字不改），
单线程限速 0.35s、断点续跑；去重基准 = golden_4000 白文 3975 唯一 + 批内重复；
**每条带 _quality 标记：ok / paren（白文含（），N57 起约定拒绝——本夜只标记
不启用）**。1279 页全量抓完（6237s）：

| 栏目 | 页数 | ok | paren |
|---|---|---|---|
| syubu | 317 | 2189 | 24 |
| shibu02 | 216 | 1142 | 168 |
| syubu02 | 42 | 225 | 23 |
| shibu01 | 10 | 22 | 31 |
| **koji** | **501** | **1** | 5 |
| **keibu** | **165** | **0** | 6 |
| history / miscellaneous | 28 | 0 | 0 |
| 合计 | 1279 | **3579** | 257 |

拒绝：dup_golden 668 / dup_batch 5 / empty 1。**koji 剩 501 页仅 1 条新对、
keibu 剩 165 页 0 条**——§2 盘点结论被全量抓取直接证实，「kanbun.info 干净
文本对已枯竭」从抽样推断升级为全量实证。

## 4. golden_7908 构建（night62_build_golden.py）

- 并入优先序：night57 池剩 → night60 池剩 → night62 剩页（syubu 优先，任务书口径）；
  paren 对不启用；硬断言**前 4000 条与 golden_4000 逐条相等且顺序一致**。
- 新增 3908 = 330（池剩）+ 3579（剩页）− 1（跨源 id 冲突，skip 并记录）；
  skipped：dup_hakubun 1974 / dup_id 1；paren 未启用 257。
- 构成（与 N60「清一色短句」相比显著改善）：
  - 分档：≤20字 6329 / 21-40字 903 / 41-60字 383 / >60字 293
    （**新增段**：3286 / 361 / 136 / 125）
  - 文体：漢詩 4385 / その他 1389 / 故事 1334 / 論語 362 / 大学 189 / 孝経 147 / 詩経 102
    （**新增段**：漢詩 2518 / その他 1389 / 故事 1）——「その他」为子部
    （老荘兵家）在历史文体口径下的归属，栏目级如实单列（§5 栏目补充表）。
- 双保险：tests/test_golden_7908.py 3 条（形状/前缀/新增行非空且无括号）。

## 5. 规则引擎全跑（night62_eval_10k.py，142s，TestClient 完整后端链）

**总量：OK 7905 / error 3 / 精确 25 / avgDist 13.241**（N60 口径 13.889 →
13.241，主因新增段构成，不能读成引擎变好）。

长度档 × 文体 avgDist（n）：

| 文体 | ≤20字 | 21-40字 | 41-60字 | >60字 |
|---|---|---|---|---|
| 漢詩 | 7.10(4382) | - | - | - |
| その他（子部） | 10.70(768) | 24.23(361) | 39.96(136) | 69.37(124) |
| 故事 | 9.55(700) | 22.87(344) | 38.26(183) | 61.90(107) |
| 論語 | 10.03(102) | 19.37(145) | 33.75(55) | 67.33(60) |
| 大学 | 10.11(134) | 21.70(44) | 35.67(9) | 61.50(2) |
| 孝経 | 8.78(138) | 17.00(9) | - | - |
| 詩経 | 5.17(102) | - | - | - |

栏目补充表（历史文体口径下 shibu02 等归「その他」）：
syubu 4484 条 avgDist 7.058（精确14）/ koji 1334 / 21.125（4）/ **shibu02 1142 /
24.691（2）** / keibu 698 / 19.837（5）/ syubu02 225 / 10.738（0）/ shibu01 22 / 17.409（0）。
**子部长文本（老荘兵家）首次成建制入评：21-60 字 avgDist 24-40，与故事同档，
是最值得后续攻规则的长文区。**

新增段（[4000:7908)，3908 条）：OK 3907 / error 1 / 精确 6 / **avgDist 12.577**；
分档 3285(8.005·6) / 361(24.227·0) / 136(39.956·0) / 125(69.296·0)。

**确定性对照：前 4000 条 vs night60_results_4000.json 输出文本 diff=0、归档缺行 0**
（跨夜跨进程第五次；规则与引擎确定性再证）。

**error 3 条全部是同一 KeyError（`應,v,助動詞,必要,*`）**：
toushisen135-12「應知黃綺心」、toushisen043-16「應照離人粧鏡臺」（皆已知）+
**新增 zasshi-2「應知故鄉事」——N59 ⑬「應必要型非孤例」论据再 +1**；
guwenbert 路径同行同败（kundoku 翻译层共享）。

## 6. guwenbert 新增段（night62_guwenbert_new.py，离线 ≈2750s）

HF_HUB_OFFLINE=1，只跑 [4000:] 3908 条（任务书：新增段离线对比）：
**OK 3907 / error 1 / 精确 3 / avgDist 12.466**；分档 3285(7.82·3) / 361(24.41·0) /
136(40.83·0) / 125(69.18·0)；文体 漢詩 2517(6.93·2) / その他 1389(22.47·1) / 故事 1(59.0·0)。

**h2h（night62_h2h.py，3907 可比）**：规则 avgDist 12.577/精确 6 vs guwenbert
12.466/精确 3；逐条 **规则更好 1366 / guwenbert 更好 1390 / 持平 1151**——
差距 0.111（0.9%），仍同量级，「接不接 guwenbert」**维持 D16 产品拍板**。
※ h2h 首版有 `gmap` 误用 `rdoc` 的复制粘贴 bug（规则自己比自己，全持平），
已修复重跑；归档为修复后结果（night62_h2h.txt）。

## 7. 测试与验收

- pytest **193→196**（+tests/test_golden_7908.py 3 条）；196 passed = collected。
- accept 62：
  - 预跑 `--no-pytest`：repo_clean 如实 FAIL（SHIFT_LOG.md 有 QA 会话未提交
    登记行，见 §8），其余 6 项 PASS/正常（rule_regression / engine_smoke /
    perf 16ms / order_rate 与基线差 +0.00pp）；ACCEPT_LOG 15:19:12 FAIL 行留痕。
  - 主提交 7da8fbb 后终跑：**PASS**（fail=0 skip=1，29.7s；pytest 196 = collected；
    perf 短句中位 1ms；order_rate 98.57%/98.63% 与基线持平）。

## 8. 与 QA 会话的协作（并行会话撞车 → 角色分工）

- 12:28-12:44 另一会话在本分支做 Night 62 开工盘点（产物 night62_sitemap_* 等），
  发现本会话（主会话）已拍板方案 A 并启动抓取后**立即停止、零抓取写入**；
- 12:55 用户拍板该会话转 **QA 角色**（SHIFT_LOG 12:55 登记行）：待主会话产出后
  做独立验证（golden 前缀逐条复核 / 白文去重复核 / 规则输出 vs night58/60 归档
  确定性复核 / expected 完整性抽查）+ pytest/accept 协调 + 审计报告。
- 主会话处理：QA 盘点产物**全部保留并随主提交入库**（交叉印证数据）；QA 会话
  的 3 个未跟踪探针脚本（tools/night62_koji_check.py / night62_sample_pages.py /
  night62_sitemap_inventory.py）**留给其审计提交**，主会话不代提交。
- QA 审计入口：eval/golden_7908.json（前缀断言可重放 tools/night62_build_golden.py）、
  eval/night62_results_7908.json（前 4000 diff=0 复算）、eval/night62_scraped_10k.json +
  night62_scrape_10k_state.json（1279 页覆盖与去重凭据）、eval/accept_night_62.json。

## 9. 待拍板事项（新增）

- **⑯ 第二语源**：kanbun.info 干净文本对已枯竭（§3 实证），10000 目标的唯一路径。
  候选与成本如实列出：
  1. ctext.org（原文全、无结构化書き下し）× 青空文庫（訓読文全、原文缺）——跨站
     对齐方案，对齐成本高、expected 一字不改难保证，需逐篇人工校验；
  2. 国語研/東洋文庫等漢文訓読コーパス——授权与结构待调研；
  3. OCR 自建 GT 线——repo 已有 OCR 管线（N36-50），白文侧 GT 是 N33 挂起的
     拍板项，書き下し侧仍需人工；
  4. LLM 生成書き下し——违反「expected 真值」原则，**不可作 golden**（仅可作对齐辅助）。
- **⑰ paren 对启用**：本夜标记未启用 257 条；如放宽 N57 约定，重抓已见 1415 页
  还可再收 ~600-700 条（合计 +~1000-1700），是约定内最便宜的增量（非第二语源）。

## 10. 产物清单

| 产物 | 说明 |
|---|---|
| eval/golden_7908.json / golden_7908_stats.json | 新评测集（前缀断言 + 构成统计） |
| eval/night62_inventory.json/.txt | sitemap 全站盘点（2696 URL） |
| eval/night62_reservoir.json | 在手池子清点（330） |
| eval/night62_scraped_10k.json / night62_scrape_10k.txt / _state.json | 全站剩页抓取（1279 页、3836 对、覆盖凭据） |
| eval/night62_results_7908.json / night62_eval.txt | 规则全跑（分档×文体×栏目、确定性对照） |
| eval/night62_guwenbert_new3908.json | guwenbert 新增段离线 |
| eval/night62_h2h.txt | 逐条对决 |
| tools/night62_inventory / _reservoir / _scrape_10k / _build_golden / _eval_10k / _guwenbert_new / _h2h / _append_shift .py | 本夜管线 |
| tests/test_golden_7908.py | 3 条完整性双保险 |
| eval/night62_sitemap_* 等 QA 会话盘点产物 | 交叉印证，保留入档 |

提交：7da8fbb（主提交，45 文件）+ wrap-up（本报告 + SHIFT_LOG + ACCEPT_LOG +
accept_night_62.json）。分支 night62-eval10000，不合 master、不推远程。
