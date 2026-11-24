# REPORT_NIGHT95 — 合 night94-ruler 进 master（kanbun-kakikudashi）

- 日期: 2026-11-24（单会话夜・合并夜）
- 分支: master（开工 07ff902＝N93 wrap-up）；合并 night94-ruler（tip f024951＝N94 wrap-up efa818b＋step0 报告修正）；**未推远程**
- 任务书: 合 N94 进 master（step 0 报告对数清零→单次 --no-ff；禁 OCR、禁 guwenbert、禁 eval 以外的网络；backend/main.py・词库一字不改）
- 结果一句话: **Merge night94-ruler 完成（合并提交 `22a4445`）**——step 0 先在分支清零 REPORT_NIGHT94 §2 组合段别 1 行差（分支提交 `f024951`）；冲突 **1 文件**（SHIFT_LOG.md 追加-追加・字节安全并集 1,967＋142 B）；合后 pytest **462 passed**（453＋N94 的 9）、golden_4000 **13.489/24/0** 与 night94 归档**逐位一致（diff 0 行・N93 13.491 から 6 行改写改善生效）**、golden_8165 **13.498/30/0** 与 night94 归档**逐位一致（diff 0 行・N93 13.500 から 12 行改写改善生效）**、词库 **1531**（209＋291＋1031）不动、verify **21/21 exit 0**（分支版 21 项为准）、accept 95 **PASS fail=0 skip=0**（32.2s 登记后首跑即过・七门全绿）。

## 1. 开工核验（①）

- `git checkout master` → HEAD = **07ff902**（N93 wrap-up・与 origin/master 一致）✓
- `pytest tests -q` = **453 passed** ✓（14.33s＝合并前 master 基线）
- `git log -1 night94-ruler` = **efa818b**（N94 wrap-up）✓
- `git merge-base master night94-ruler` = **07ff902**（N94 自 master 直分、无 clone 中转）✓
- `git rev-list --count master..night94-ruler` = **2**（主 e820f83＋wrap-up efa818b）→ step 0 后 **3**（＋f024951）✓
- 已跟踪文件零改动 ✓（untracked 历史缓存のみ）
- 前置阅读：REPORT_NIGHT94.md（§2 组合段・§5 验证数・§7 移交）与 REPORT_MERGE_92.md §1/§3（字节安全并集数字・合并带入清单惯例）確認済み。

## 2. step 0（②）：REPORT_NIGHT94 §2 组合段别 1 行差清零（分支上・合并前）

- 问题：§2 组合段「12 行改写／改善 10」vs 段别合计 s4000 better 5＋s3908 better 4＋s257 same 1＝改善 9，**差 1 行**。
- 以 JSON 为准重算：eval/night94_combo_changed_rows.json 12 行逐行 Δ（new_dist−old_dist）＋golden_8165.json 行序归段（idx<4000→s4000・<7908→s3908・≥7908→s257＝tools/night94_sim.py L157 同一口径）→ **s4000 6 行（better 5・same 1：menyu-1 idx=1199）／s3908 6 行（better 5・same 1：roushi51-2 idx=6974）／s257 0 行**、合计 better 10／worse 0／same 2。与 eval/night94_sim.json combo_reachable.segs（5/0/1・5/0/1・0/0/0）三方一致。
- 判定：**组合总数 12／改善 10／変差 0 正确、段别句错误**——初版把 s3908 的 same 行 roushi51-2（Δ0）误写到 s257。任务书备选假设「s257 的 same 1 实为 better 1」不成立（s257 該当 0 行・10 个改善行は全部 s4000/s3908 在籍）。
- 修正：REPORT_NIGHT94 §2 一处（「／s3908 5 行（better 4・same 1）／s257 1 行（same 1）。」→「／s3908 6 行（better 5・same 1）／s257 0 行。」）＝**只改数字文字**、eval 归档・代码・重跑零触碰。分支 night94-ruler 上单独提交 **`f024951`**（"Night 94 report fix: combo improved count"・1 file changed, 1 insertion(+), 1 deletion(-)）→ checkout master 走合并。

## 3. 合并（③）：心跳提交 → merge --no-ff → 冲突 1 文件字节安全并集

- 开工心跳先落提交 `746adba`（merge 拒绝脏树・N81 §5.3 惯例；byte807=243 写前后断言・+143 B CRLF）。
- `git merge --no-ff night94-ruler -m "Merge night94-ruler"` → **CONFLICT (content): SHIFT_LOG.md** 唯一冲突（预期どおり）——master 自分支点未动、master 侧 delta＝开工心跳 1 行（142 B blob）vs 分支侧 delta＝N94 心跳 4 行（1,967 B blob）（追加-追加）。
- **字节安全并集（REPORT_MERGE_92 §1 / N93 惯例）**：python subprocess 读 3 阶段 blob（:1: base=07ff902 blob **139,655 B** 纯 LF／:2: ours=746adba **139,797 B**＝base+**142 B**＝N95 开工心跳 1 行／:3: theirs=f024951 **141,622 B**＝base+**1,967 B**＝N94 心跳 4 行）、断言 ours/theirs とも startswith(base)（追加-追加のみ）、union＝**theirs+d_ours＝141,764 B**（夜序 theirs 在前＝N94 段在前・N95 心跳在后）、工作副本＝CRLF 化 union **142,780 B**、**byte807=243 写前后断言**（冲突标记 1/1/1→0）、git add 后**暂存 blob＝141,764 B 纯 LF（CR=0）等价断言**后 commit → 合并提交 **`22a4445`**。
- 其余全部自动合并：**A（分支新文件）17**（REPORT_NIGHT94.md、eval/accept_night_94.json、eval/night94_combo_changed_rows.json、eval/night94_mine.{json,txt}、eval/night94_probe.{json,txt}、eval/night94_results_4000.json、eval/night94_results_8165.json、eval/night94_sim.{json,txt}、tests/test_night94_rule_r.py、tools/night94_eval_4000.py、tools/night94_eval_8165.py、tools/night94_mine.py、tools/night94_probe.py、tools/night94_sim.py）＋**M（自动合并取分支值）5**（README.md＝テスト行 462・4000 行 13.489・8165 行 13.498・Rule R 句、backend/kundoku_rules.py＝Rule R 1 条、tools/accept_night.py＝NIGHT_ARTIFACTS[94]、tools/verify_readme_facts.py＝21 项版、ACCEPT_LOG.md＝N94 验收行）。
- `git log --oneline -3`＝22a4445（merge）←746adba（心跳）←f024951 ✓。

## 4. 合后验证（④・数字是死的逐项对）

- `pytest tests -q` = **462 passed** ✓（14.36s＝453＋N94 的 9）。
- **golden_4000 全量真跑（tools/night95_eval_4000.py・TestClient 完整链・89s）＝avgDist 13.489／exact 24/4000／error 0**——与 eval/night94_results_4000.json **逐位一致、diff 0 行**（6 行 Rule R 改写在 master 生效の证明；**不是 N93 的 13.491**——合并改善生效）。
- **golden_8165 全量真跑（tools/night95_eval_8165.py）＝avgDist 13.498／exact 30/8165／error 0**——与 eval/night94_results_8165.json **逐位一致、diff 0 行**（**不是 N93 的 13.500**——12 行改写随合并生效）。
- 归档：eval/night95_results_4000.json（默认口径登记用）・eval/night95_results_8165.json（扩充归档・非登记）。
- **词库 1531 条不动**（import 实证：GLOSSARY_LEXICON=500〔_OLD_SIZE=209〕＋extra as_dicts()=291＋LEXICON_EXTRA2=1031・_ORDERED_ALL=1531・unique word forms 1531・extra2 与本体零交集＝N94 未碰词库の確認）。
- `tools/verify_readme_facts.py` → **21/21 OK・exit 0**（N94 分支版 21 项为准＝Rule R 語数断言＋归档源 night94 切换随合并生效；master 旧版 20 项作废）。
- README 同步：数字行（462・13.489・13.498・Rule R 句）已由分支合入、**header hash 人工改**为「Night 95 合并：night94-ruler Rule R 1 条（主 e820f83＋wrap-up efa818b＋step0 报告修正 f024951）・合并提交 `22a4445`」——数字与 header 同在登记提交 `feffa7b` 内收口（header 改后 verify 21/21 复跑再確認）。

## 5. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `95: ["night95_results_4000.json"]`（仅此一条）。
- **accept 95：PASS（fail=0 skip=0、32.2s・登记 feffa7b 后首跑即 PASS）**——repo_clean ✓／pytest 462=462 ✓／eval_integrity（night95_results_4000.json 実查：id 唯一・自报数一致・expected 未改）✓／rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate（off 98.57%・on 98.63%、退化页 0）✓。

## 6. 移交

1. **master 链更新**：07ff902（N93 wrap-up）→ 746adba（N95 开工心跳）→ **22a4445（merge --no-ff night94-ruler）** → feffa7b（N95 登记）→ wrap-up（本报告）。origin/master=07ff902 未推（rev-list origin/master..master＝**7**＝N95 四提交 746adba/22a4445/feffa7b/2a2b933＋合并带入的 N94 分支三提交 e820f83/efa818b/f024951）。
2. **拍板事項（N86/N88/N92/N94 から原样带入 master・本夜一字未动）**：べからず族 89 行 79 改善 5 変差（発火残量 78）；べきなり→可きなり 31 行 29 改善 1 変差（p-gekirin-1・変差 1 行許容拍板なら一発収録級）；なかれ→莫かれ post-N 17 行（kokyo09-5）；がため/何のごとく 各 1 行（rerun 行 tail guard 機構変更待ち）；は系 1 字块構文判別機構（N94 §7 移交①・26 块実測裏付け）；嗟や→嗟乎 在庫化（Δ−0.000367・歎詞データ増強拍板待ち）；guard 外 ことなく 5 行（(な,莫) 5 残量同一行集・白文側字形対応データ拍板候補）；N84 §8 夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行。
3. **次夜建议**（N94 §7 移交⑤から）：1 字块 rows>=3 区带実質枯竭（56 块完掘）→次は rows 2 以下 micro 区带か 2 字块 B2 长键（(すべ,可) 型未試 prefix 分離）；scan 系 4 夜枯竭維持复核。

## 7. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查＋night95_eval 逐位一致）；backend/main.py・词库（glossary_lexicon*.py）一字未改 ✓；分支逻辑文件全部取分支版本（kundoku_rules.py・tests・night94_* 工具＝不手动改逻辑）✓；site-packages 一行未动 ✓
- 允许清单内文件のみ ✓：REPORT_NIGHT94.md（step 0・§2 段别句一处のみ・分支 f024951）、tools/accept_night.py（95 一条のみ）、tools/night95_eval_4000.py・night95_eval_8165.py、eval/night95_results_4000.json・night95_results_8165.json、SHIFT_LOG.md（心跳 3 行）、ACCEPT_LOG.md（accept 自動追加分）、eval/accept_night_95.json、REPORT_NIGHT95.md、REPORT_MERGE_94.md、README.md（header hash のみ・数字行は分支合入値のまま）✓；ROADMAP.md 本夜无追加行（N94 行已随合并带入＝N90/N91/N93 合并夜先例）✓
- 合并本身触碰的冲突文件 SHIFT_LOG.md＝字节安全并集（非文本三路合并）✓
- 临时脚本は AutoClaw ワークスペース（night95_step0_recount.py・night95_step0_fix.py・night95_union_shiftlog.py・night95_gen_evaltools.py・night95_lexicon_check.py・night95_reg_edits.py 6 本）で仓库外・仓库に持ち込まず ✓
- SHIFT_LOG 纯追加（.NET AppendAllText 絶対パス・UTF-8 無 BOM・byte807=243 写前后断言×3 回の追記）✓；无 OCR／guwenbert／eval 以外的网络 ✓（web_search 0・ページ取得 0）
- 本地提交（心跳 746adba＋merge 22a4445＋登记 feffa7b＋wrap-up）、**未推远程** ✓

## 8. 偏差注记

1. **step 0 的对数结果与任务书备选假设不同**：任务书猜测「s257 的 same 1 实为 better 1」，実測（combo JSON 逐行＋golden_8165 行序归段＋night94_sim 归档 segs 三方一致）は **s257 該当 0 行**、错误実体＝s3908 の same 行 roushi51-2（idx=6974・Δ0）被误记为 s257 1 行——修正は段别句のみ（s3908 5→6 行・better 4→5／s257 1→0 行）、组合总数 12／改善 10／変差 0 は初版から正确で不変。
2. 任务书④「verify 21/21」＝分支版 21 项为准、master 旧版 20 项作废——合并後 verify は night94 归档源・Rule R 語数断言で **21/21 exit 0**（README header 人工改后复跑も 21/21）。
3. step 0 修正提交で night94-ruler 分支 tip が efa818b→f024951 に前进（rev-list 2→3）——合并・验证数字に影响なし（报告文字のみ）。
4. accept 95 は登记提交後に 1 回のみ実施（N93 型・repo_clean FAIL 试跑なし＝登记后 tree clean のため）——ACCEPT_LOG には PASS 1 行のみ記録。
