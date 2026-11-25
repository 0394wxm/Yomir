# REPORT_NIGHT99 — 拍板夜：撤 0 变差硬门，收 Rule T 3 条

- 日期：2026-11-25（单会话・AutoClaw）
- 分支：`night99-rulet`（自 master `d7bd2ff` 分出）；**不合 master、未推远程**
- 拍板原文（任务书）：用户 2026-11-25 拍板（N98 报告 §3/§4 决策表 1a/1b/1c/2 为据）：撤 0 变差硬门，仅限本夜三条——べからず→可からず、べからざる→可からざる、べきなり→可きなり。变差行上限 6 行，ID 须与 N98 实测一致；超出即停下报数。
- 工具：`tools/night99_sim.py`（night98_audit 型 sim・基线＝night97 归档）＋`tools/night99_eval_4000.py` / `night99_eval_8165.py`（night96 型真跑回归・sim 逐位对照）
- 归档（全部已跟踪）：`eval/night99_sim.json`・`eval/night99_sim.txt`・`eval/night99_combo_changed_rows.json`（三条 combo 改写 178 行预测＝eval 对照源）・`eval/night99_results_4000.json`（默认口径登记）・`eval/night99_results_8165.json`（扩充归档）

## 1. 开工核验

- HEAD＝`d7bd2ff`（N97 wrap-up）＝origin/master ✓；`git checkout -b night99-rulet master` ✓
- `pytest tests -q`＝**469 passed**（15.7s）✓；已跟踪文件零改动 ✓
- 移交阅读：REPORT_NIGHT98 §3（决策表 1a/1b/1c/2・変差 ID 实测）＋§4（收益汇总）✓（N98 分支未合 master、报告经 `git show night98-report:REPORT_NIGHT98.md` 读得）

## 2. sim（tools/night99_sim.py・基线＝N97 归档・全部硬断言 PASS）

基线复核：行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）✓・night97 vs night96 归档 got diff 0 行 ✓・基线 avgDist 13.488/13.496・exact 24/30 ✓・词库 209+291+1031=1531 ✓・lev 纯 Python 回退（.night72_deps 不存在＝N86 先例）。

| 测定 | 改写 | 改善 | 変差 | Δ8165 | Δ4000 | vs N98 実測 |
|---|---|---|---|---|---|---|
| T1 べからず→可からず（guard 可） | 78 | 70 | **5**（shushu-4/shukateki-1/ryojo-3/saio-x13/toushisen216-7） | −0.011 | −0.008 | 78/70/5・変差 ID 级一致 |
| T2 べからざる→可からざる（guard 可） | 82 | 79 | **1**（shiseinishite-1 73→74） | −0.011 | −0.011 | 82/79/1・一致 |
| T1+T2 combo | 157 | 146 | **5**（shushu-4/shukateki-1/ryojo-3/**shiseinishite-1**/toushisen216-7） | −0.022 | −0.019 | 157/146/5・一致・幂等 bad 0 |
| T3 べきなり→可きなり（guard 可） | 31 | 29 | **1**（p-gekirin-1 8→9） | −0.006 | −0.006 | 31/29/1・一致 |
| 三条 combo | 178（4000 内 93） | 165 | **6**（combo 5＋p-gekirin-1） | −0.028 | −0.026 | 幂等 bad 0 |

- 任务书硬门：combo 5 行全部落在 N98 已知 6 行集合内 ✓・三条合计変差总数＝6 ✓・一行も超出集合なし ✓（exit 2 未触发）。
- **Δ4000 実測 −0.026 vs 任务书估算 −0.025**：三条同時適用では べからず族×べきなり の重複発火 10 行の交互作用があり、単純和（−0.019−0.006）より 0.001 多い改善。代表例 saio-x13：T1 単独では変差（13→14）だが T2（べからざる→可からざる・exp 側 可からざる 実在）の同発火改善と相殺し combo では 13→13 持平＝変差 6 行から外れる（N98 combo 実測「5 変差」の内訳と同じ現象）。実測为准。
- golden 预测：4000 **13.462**／8165 **13.469**（任务书估算 13.463/13.468 との ±0.001＝上記交互作用＋round 舍入）。exact 预测 24/30 不変（rewritten 行に exact 行なし＝誰も exact を壊さない・誰も exact に届かない）。

## 3. Rule T 实装

- `backend/kundoku_rules.py`：`T_KANA_TO_KANJI` 3 条（べからず→可からず／べからざる→可からざる／べきなり→可きなり・いずれも guard 可＝可は新旧変異なしで guard_forms 并查同形）＋`T_LONGER_WORDS` 空壳 3 键（三键互不重叠＝べからず は べからざる の部分文字列でない・順序非依存）＋`style_kana_to_kanji_t`（E〜S 同構・白文含字正条件＋长词护栏）＋pipeline 链尾 **Q→R→S→T**。
- `tests/test_night99_rule_t.py` 7 tests：正例 3 行型（tankako_soso-20/yamai-x12/gashin-x18 改善行）・変差 6 行の行動ロック（got→new 断言）＋sim JSON の ID 集合ロック・guard 反例（可 無し＝一字不動）＋空白文発火（E〜K 世代同语义）・禁区不复活（なかれ/ことなく/は系/がため/何のごとく/嗟や）・構造/链序 Q→R→S→T・幂等/现代句/echo 行型。
- `pytest tests -q`＝**476 passed**（469→476・15.2s・首跑全绿）。

## 4. 实跑双口径（TestClient 全量・sim 逐位一致）

- golden_4000：**13.462 / exact 24 / error 0**・真跑改写 93 行＝sim 预测 93 行 new_text 逐位一致・変差 5 行（p-gekirin-1/ryojo-3/shiseinishite-1/shukateki-1/shushu-4）＝sim 5 行一致・**計画外 0・欠落 0**（92s）
- golden_8165：**13.469 / exact 30 / error 0**・真跑改写 178 行＝sim 预测 178 行逐位一致・変差 6 行＝sim 6 行 **ID 一一对应**・**計画外 0・欠落 0**（196s）
- exact 24/30 不変（预测どおり）・词库 1531 不動（词库不进规则引擎）
- 変差 6 行明细（全 N98 実測 ID）：shushu-4 11→12・shukateki-1 36→39・ryojo-3 26→27・shiseinishite-1 73→74・toushisen216-7 7→8（4000 外＝8165 のみ）・p-gekirin-1 8→9

## 5. 验证

- `tools/verify_readme_facts.py`：Rule T 語数断言追加（**3 語**）＋归档源切换→**23/23 exit 0**（22→23・N78/N86/N92/N94/N96 先例。任务书表记「归档源 night97→night99」の实际现状は night96＝N96 切换後 N97/N98 未动分、本夜で night99 に统合＝意图一致）
- README 数字行同步：テスト **476 passed**・4000 **13.462**/24/4000・8165 **13.469**/30/8165・ルールチェーン Rule T 句追加・規則エンジン系列句「N99 で Rule T（かな→漢字第 15 系列・3 語＋拍板夜変差許容）を追加」
- `tools/accept_night.py`：NIGHT_ARTIFACTS[99] 登记後 **accept 99 PASS fail=0 skip=0（33.5s・主提交 b997349 後首跑即过・七门全绿：repo_clean/pytest 476=476/eval_integrity（night99_results_4000.json・id 唯一・expected 未改）/rule_regression/engine_smoke/perf_envelope 11ms/order_rate +0.00pp）**

## 6. 提交

- 主提交＝`b997349`（15 文件：kundoku_rules・tools/night99_sim＋eval_4000＋eval_8165・accept_night・verify_readme_facts・tests/test_night99_rule_t・eval 5 件・README・ROADMAP・SHIFT_LOG）
- wrap-up＝本提交（REPORT_NIGHT99.md＋ACCEPT_LOG＋eval/accept_night_99.json＋README header hash→主提交 `b997349`＝合并夜「header は夜の主 commit を指す」惯例の准用）
- **未合 master、未推远程** ✓

## 7. 禁止事项自查

- なかれ复活・は系・がため/何のごとく・ことなき・嗟や・ことなく guard 外・N84 遗留（夹注残渣/echo）：**一字未動** ✓（tests/test_night99_rule_t.py の禁区不复活断言で锁定）
- 词库 `glossary_lexicon*.py`：一字未動（1531 実証）✓・golden expected：一字未改 ✓
- 禁 OCR・禁 guwenbert・无网络（TestClient＝本地 127.0.0.1 testserver）✓
- 允许清单内文件のみ変更 ✓（backend/kundoku_rules.py は Rule T 3 条＋链尾调用のみ）

## 8. 坑位・移交

- 任务书の Δ4000 估算 −0.025／golden 13.463 に対し実測 −0.026／13.462（交互作用＋round 舍入・改善方向の偏差）——拍板数字（変差 6 行 ID・上限）は完全一致、收益側は実測为准で僅かに良い。
- verify 归档源は N96 以降「night96」のままだった（任务书「night97」表记は N97 登记归档との混考）——本夜で night99 に统合済み、次夜からは night99 が chain tail。
- 拍板事項の残り（N98 §3 决策表 3〜9）は原样未動で次拍板待ち：なかれ→莫かれ post-N（17/13/1 kokyo09-5）・がため/何のごとく rerun tail 機構変更・は系構文判別機構・ことなき字形統一（データ側）・嗟や在庫（歎詞データ増強）・ことなく guard 外 5 行（guard 勿/毋併用拡張＝Rule S/M 干渉要 sim 先検）・N84 夹注残渣（剥夹注管线）・echo 30 行。
- 次夜建议：合并夜（night99-rulet 未合・b997349＋wrap-up）か残り拍板項のデータ側/機構側着手。
