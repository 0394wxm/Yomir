# REPORT_NIGHT93 — 合 night92-ruleq 进 master（kanbun-kakikudashi）

- 日期: 2026-11-24（单会话夜・合并夜）
- 分支: master（开工 b6a6248＝N91 wrap-up）；合并 night92-ruleq（tip a39e648）；**未推远程**
- 任务书: 合 N92 进 master（单次 --no-ff；禁 OCR、禁 guwenbert、禁 eval 以外的网络；
  backend/main.py・词库一字不改）
- 结果一句话: **Merge night92-ruleq 完成（合并提交 `3a64ff0`）**——冲突 **1 文件**
  （SHIFT_LOG.md 追加-追加・字节安全并集）；合后 pytest **453 passed**（443＋N92 的 10）、
  golden_4000 **13.491/24/0** 与 night92 归档**逐位一致（diff 0 行）**、golden_8165
  **13.500/30/0** 与 night92 归档**逐位一致（diff 0 行・N91 13.502 から 37 行改写改善生效）**、
  词库 **1531**（500＋1031）不动、verify **20/20 exit 0**（分支版 20 项为准）、
  accept 93 **PASS fail=0 skip=0**（31.1s 首跑即过・七门全绿）。

## 1. 开工核验（①）

- `git checkout master` → HEAD = **b6a6248**（N91 wrap-up・与 origin/master 一致）✓
- `pytest tests -q` = **443 passed** ✓（20.08s＝合并前 master 基线）
- `git log -1 night92-ruleq` = **a39e648**（N92 wrap-up）✓
- `git merge-base master night92-ruleq` = **b6a6248**（N92 自 master 直分、无 clone 中转）✓
- 已跟踪文件零改动 ✓
- 前置阅读：REPORT_NIGHT92.md §0/§5/§7（Rule Q 2 条・验证数・移交）与 REPORT_MERGE_88.md
  §3（合并带入清单与字节安全并集方法论）确认済み。

## 2. 合并（②）：心跳提交 → merge --no-ff → 冲突 1 文件字节安全并集

- 开工心跳先落提交 `5a78d0b`（merge 拒绝脏树・N81 §5.3 惯例；byte807=243 写前后断言）。
- `git merge --no-ff night92-ruleq -m "Merge night92-ruleq"` → **CONFLICT (content): SHIFT_LOG.md**
  唯一冲突（预期どおり）——master 自分支点未动、master 侧 delta＝开工心跳 1 行 vs
  分支侧 delta＝N92 心跳 4 行（追加-追加）。
- **字节安全并集（REPORT_MERGE_88 §3 / N91 惯例）**：python subprocess 读 3 阶段 blob
  （:1: base=b6a6248 blob **137,389 B** 纯 LF／:2: ours=5a78d0b **137,613 B**＝base+**224 B**
  ＝N93 开工心跳 1 行／:3: theirs=a39e648 **138,684 B**＝base+**1,295 B**＝N92 心跳 4 行）、
  断言 ours/theirs とも startswith(base)（追加-追加のみ）、union＝**theirs+d_ours＝138,908 B**
  （夜序 theirs 在前＝N92 段在前・N93 心跳在后）、工作副本＝CRLF 化 union **139,917 B**、
  **byte807=243 写前后断言**、git add 后**暂存 blob＝138,908 B 纯 LF 等价断言**后
  commit → 合并提交 **`3a64ff0`**。冲突标记 0。
- 其余全部自动合并：**A（分支新文件）17**（REPORT_NIGHT92.md、eval/accept_night_92.json、
  eval/night92_combo_changed_rows.json、eval/night92_mine.{json,txt}、eval/night92_probe.{json,txt}、
  eval/night92_results_4000.json、eval/night92_results_8165.json、eval/night92_sim.{json,txt}、
  tests/test_night92_rule_q.py、tools/night92_eval_4000.py、tools/night92_eval_8165.py、
  tools/night92_mine.py、tools/night92_probe.py、tools/night92_sim.py）＋
  **M（自动合并取分支值）4**（README.md＝テスト行 453・8165 行 13.500・Rule Q 句・
  backend/kundoku_rules.py＝Rule Q 2 条・tools/accept_night.py＝NIGHT_ARTIFACTS[92]・
  tools/verify_readme_facts.py＝20 项版）＋ACCEPT_LOG.md／ROADMAP.md（N92 行随合并带入）。
- `git log --oneline -3`＝3a64ff0（merge）←5a78d0b（心跳）←a39e648 ✓。

## 3. 合后验证（③・数字是死的逐项对）

- `pytest tests -q` = **453 passed** ✓（13.37s＝443＋N92 的 10）。
- **golden_4000 全量真跑（tools/night93_eval_4000.py・TestClient 完整链・87s）＝
  avgDist 13.491／exact 24/4000／error 0**——与 eval/night92_results_4000.json
  **逐位一致、diff 0 行**（12 行 Rule Q 改写在 master 生效の证明；N91 也是 13.491＝
  Δ−0.001 四舍五入同值、持平是预期）。
- **golden_8165 全量真跑（tools/night93_eval_8165.py）＝avgDist 13.500／exact 30/8165／
  error 0**——与 eval/night92_results_8165.json **逐位一致、diff 0 行**
  （**不是 N91 的 13.502**——37 行改写随合并生效＝合并意义の确认）。
- 归档：eval/night93_results_4000.json（默认口径登记用）・eval/night93_results_8165.json
  （扩充归档）。
- **词库 1531 条不动**（import 实证：GLOSSARY_LEXICON=500〔内 _OLD_SIZE=209〕＋
  LEXICON_EXTRA2=1031・_ORDERED_ALL=1531＝N92 未碰词库の確認）。
- `tools/verify_readme_facts.py` → **20/20 OK・exit 0**（N92 分支版 20 项为准＝Rule Q 語数
  断言＋归档源 night92 切换随合并生效；master 旧版 19 项作废）。
- README 同步：数字行（453・13.500・Rule Q 句）已由分支合入、**header hash 人工改**为
  「Night 93 合并：night92-ruleq Rule Q 2 条（主 22e4e9e＋wrap-up a39e648）・合并提交
  `3a64ff0`」——数字与 header 同在登记提交 `852850d` 内收口。

## 4. 验收（④）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `93: ["night93_results_4000.json"]`（仅此一条）。
- **accept 93：PASS（fail=0 skip=0、31.1s・首跑即 PASS）**——repo_clean ✓／pytest 453=453 ✓／
  eval_integrity（night93_results_4000.json 実查：id 唯一・自报数一致・expected 未改）✓／
  rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate（off 98.57%・on 98.63%、
  退化页 0）✓。

## 5. 移交

1. **master 链更新**：b6a6248（N91 wrap-up）→ 5a78d0b（N93 开工心跳）→ **3a64ff0
   （merge --no-ff night92-ruleq）** → 852850d（N93 登记）→ wrap-up（本报告）。
   origin/master=b6a6248 未推（合并后 4 提交待用户手推）。
2. **拍板事項（N86/N88/N92 から原样带入 master・本夜一字未动）**：べからず族 89 行
   79 改善 5 変差（0 変差门撤廃なら収録可）；べきなり→可きなり 31 行 29 改善 1 変差
   （p-gekirin-1＝変差 1 行許容拍板なら一発収録級）；なかれ→莫かれ post-N 17 行
   （kokyo09-5 1 変差・排除 guard/kanji→kanji 机制拍板待ち）；がため/何のごとく 各 1 行
   （rerun 行 tail guard 機構変更待ち）；は系 1 字块（(は,将) 22・(は,未) 16）構文判別
   機構（N92 §7 移交①）；N84 §8 夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行。
3. **次夜建议**：Rule 链 Q 后、B2 主切面长键手測（1 字块锚定）已証有效性（N92 2 条収録）
   ——下一夜可继续 1 字块枚举的行数 3〜5 区带（(た,為) 9・(の,之) 9・(て,為) 7 等）
   与 新旧字体並查 2 字块查漏；scan 系已 3 夜枯竭確認、維持复核即可。

## 6. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查＋night93_eval 逐位一致）；
  backend/main.py・词库（glossary_lexicon*.py）一字未改 ✓；分支逻辑文件全部取分支版本
  （kundoku_rules.py・tests・night92_* 工具＝不手动改逻辑）✓；site-packages 一行未动 ✓
- 允许清单内文件のみ ✓：tools/accept_night.py（93 一条のみ）、tools/night93_eval_4000.py・
  night93_eval_8165.py、eval/night93_results_4000.json・night93_results_8165.json、
  SHIFT_LOG.md（心跳 4 行）、ACCEPT_LOG.md（accept 自動追加分）、eval/accept_night_93.json、
  REPORT_NIGHT93.md、REPORT_MERGE_92.md、README.md（header hash のみ・数字行は分支合入値のまま）✓；
  ROADMAP.md 本夜无追加行（N92 行已随合并带入＝N90/N91 合并夜先例）✓
- 合并本身触碰的冲突文件 SHIFT_LOG.md＝字节安全并集（非文本三路合并）✓
- 临时脚本は $env:TEMP（night92_shift_union.py）で仓库外・用完删除 ✓
- SHIFT_LOG 纯追加（.NET AppendAllText 絶対パス・UTF-8 無 BOM・byte807=243 写前后断言
  ×4 回）✓；无 OCR／guwenbert／eval 以外の网络 ✓（web_search 0・ページ取得 0）
- 本地提交（心跳 5a78d0b＋merge 3a64ff0＋登记 852850d＋wrap-up）、**未推远程** ✓

## 7. 偏差注记

1. 任务书②预期「至多 1 冲突（SHIFT_LOG.md）」＝実測どおり（master 侧 delta＝开工心跳
   1 行 224 B vs 分支侧 N92 心跳 4 行 1,295 B・追加-追加のみ）——README/ACCEPT_LOG/
   ROADMAP は N91 と異なり冲突せず自动合并（master 侧合并前未触碰＝base 未落后）。
2. 任务书③「verify 20/20」＝分支版 20 项为准、master 旧版 19 项作废——合并後 verify
   は night92 归档源・Rule Q 語数断言で **20/20 exit 0**（首跑）。
3. golden_4000 は N91/N92 同値 13.491（Δ−0.001 の round 持平）——「逐位一致」は
   行集合レベルで確認（diff 0 行・12 行改写含む）、数字の同値は预期どおり。
