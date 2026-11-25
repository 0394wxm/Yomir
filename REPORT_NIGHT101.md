# REPORT_NIGHT101 — 合 N98 进 master（主仓合并夜）

- 日期：2026-11-25（单会话・AutoClaw）
- 任务书：合 night98-report（Night 98 报告-only 全项目状态审计夜）进 master；N98 §3 决策表 3–9 项**原样带入——只带入、不执行、不重议**；不推远程；禁 OCR・禁 guwenbert・无网络
- 先例：N91 合 N88（base 落后＋3 冲突＋报告-only 夜不补登记）／N100 合 N99（同型・冲突仅 SHIFT_LOG 1 文件）

## 1. 开工核验

- HEAD＝`85fb05a`（N100 wrap-up）✓；`git checkout master` ✓
- `pytest tests -q`＝**476 passed**（15.51s）✓
- 分支 tip＝`42a8012`（0200be5 主＋42a8012 wrap-up）✓；`git merge-base master night98-report`＝**d7bd2ff** ✓（master +6／分支 +2・base 落后＝预期）
- 移交阅读：REPORT_NIGHT98 §3/§5（决策表 3–9 原文・下一阶段建议）＋REPORT_MERGE_88（N91 同型先例）＋REPORT_MERGE_62_64 §5（字节安全并集方法论）✓
- 工作树：仅 untracked 临时文件（eval/night98_check_*.tmp.json 等）＝不进合并・与分支 tracked 零碰撞 ✓

## 2. 合并（单次 --no-ff）

- 开工心跳 **02fb0b2**（SHIFT_LOG 1 行・byte807=243 写前后断言・blob canary=63・blob 147,005 B＝146,801＋204）→ `git merge --no-ff night98-report` → 冲突正好 3 文件（SHIFT_LOG／ACCEPT_LOG／ROADMAP・全部追加-追加）→ 合并提交 **b0fea38**。
- 字节安全并集明细（夜序 N98 段在前・N99/N100/N101 段在后）：SHIFT_LOG 144,576＋385＋2,429＝**147,390 B** LF（工作副本 CRLF 148,422 B・blob canary(807)=63／工作副本 canary=243 双形态写前后断言）；ACCEPT_LOG 11,520＋83＋253＝**11,856 B**（行序断言 98<99<100）；ROADMAP 41,748＋1,985＋1,381＝**45,114 B**（N98 行在 N99 行前）。暂存 blob＝union 逐字节等价断言三文件全过・冲突标记 0。
- 合并 stat：8 文件 +6,086 行＝冲突 3（M 并集）＋分支新文件 5（REPORT_NIGHT98.md・tools/night98_audit.py・eval/night98_audit.json・eval/night98_audit.txt・eval/accept_night_98.json）。

## 3. 合后验证（数字是死的，逐项对）

- pytest tests -q＝**476 passed**（15.59s）✓（报告-only・产品代码零改动）
- golden_4000 真跑＝**13.462／exact 24／error 0**・与 night100 归档 diff 0 行（tools/night101_eval_4000.py・92s・changed_ids_vs_n100=[]）→ eval/night101_results_4000.json ✓
- golden_8165 真跑＝**13.469／exact 30／error 0**・与 night100 归档 diff 0 行（tools/night101_eval_8165.py）→ eval/night101_results_8165.json（扩充归档不登记默认口径）✓
- 词库 **1531** 不动（import 实证：_OLD_SIZE 209＋extra as_dicts 291＋LEXICON_EXTRA2 1031＝_ORDERED_ALL 1531）✓
- verify_readme_facts＝**23/23 exit 0**（master 版 23 项・分支版 22 项作废）✓

## 4. 决策表 3–9 原样带入清单（REPORT_NIGHT98 §3 原文実数・每项＝「原样带入、未执行、不重议」）

| # | 拍板项 | N98 実測 | 下一执行夜入口 |
| --- | --- | --- | --- |
| 3 | なかれ→莫かれ post-N（guard 莫） | 17 改写 13 改善 **1 変差**（kokyo09-5 15→16）・Δ8165 −0.002（N94/N96 记录一致） | **変差許容拍板夜型**（「変差 1 行許容」拍板が下りれば収録可能・排除 guard は N86 実測否定済み） |
| 4 | がため／何のごとく 各 1 行 | rikutou37-2（rerun・tail 僅含「無」＝莫系字形外）・shiki050-4（rerun・tail＝「柰何續其後」守り字全無） | **機構设计夜**（guard 上下文機構変更＝rerun 行 tail 句型判別・规则引擎全体触及＝全量回帰必須・設計未定） |
| 5 | は系 1 字块構文判別機構 | は→将に 265 改写 27 改善 **207 変差**・は→未だ 172 改写 25 改善 **131 変差**（N92 一致・四夜実証） | **機構设计夜**（普通规则＋guard 解法不存在＝構文判別機構立项・潜在收益最大だが最重） |
| 6 | ことなき→こと莫き | 15 改写 12 改善 **2 変差**（rousShi46-2 34→35〔N96 报告 rousxi46-2＝笔误〕・rikutou26-5 53→54） | **数据侧字形统一**（exp 侧 莫く/莫し 混在の字形統一＝语料 expected 改訂を伴うデータ側拍板） |
| 7 | 嗟や→嗟乎 在庫 | 3 改写 3 改善 0 変差・Δ8165 **−0.000367**（収録線 −0.001 未達・歎詞语料無新增＝実質凍結） | **收录线撤废或新语料**（歎詞データ増強があれば一発収録級の在庫） |
| 8 | ことなく guard 外残量 | **5 行**（p-haigun-1 白文毋・toushisen080-8/koshi19_01-8/rikutou04-2/rikutou21-2 勿＝毋 1・勿 4・無 0・罔 0） | **sim 先验 guard 扩展**（guard 莫→勿/毋 併用拡張のデータ側拍板・勿 は Rule S/M 干渉＝拡張前に全域発火 sim 検証必須） |
| 9 | N84 遗留三项 | 夹注残渣 kanbun 分支 **2 行**（rikutou59-2・soji07-6〔N84 报告文字「8 行」＝口径混写・归档実測 2 行〕）・sonshi09-38 no_tail 空串 d0=13・echo 30 行（got==tail 14＋新字体化 16） | **剥夹注管线拍板**（detect_text_type 口径改訂＋全量回帰＝N84 先例の反対側・echo 升级は规则/词库层配合） |

## 5. 下一阶段建议（承接 N98 §5・只建议不擅自开工）

1. N98 §5 推荐①の「変差許容拍板夜」は N99 で実施済み（Rule T 3 条収録・Δ−0.028 実収）。残る収益は决策表 3–9：最軽は **8（sim 先验 guard 扩展）**・次いで **6（数据侧字形统一）**；4/5 は機構设计夜として別枠。拍板待ちのため本夜は着手せず。
2. 产品上线线：夹注残渣 2 行と echo 30 行の「新字体化骨架」表示が UX 課題として残存（9 の剥夹注管线拍板が先）。
3. 等用户手推 origin/master（本夜链 4 提交）。

## 6. 验收

- NIGHT_ARTIFACTS 照例加 **101: ["night101_results_4000.json"]**（只加 101・**98 不补登记**＝N91 先例）
- accept_night.py 101＝**PASS fail=0 skip=0**（34.9s・登记 26716d6 後首跑即过・七门全绿：repo_clean／pytest 476=476／eval_integrity 実查 night101_results_4000.json／rule_regression／engine_smoke／perf_envelope／order_rate 98.57/98.63 退化 0）
- 提交链：**02fb0b2**（心跳）→ **b0fea38**（merge --no-ff night98-report）→ **26716d6**（登记：NIGHT_ARTIFACTS[101]＋night101_eval_4000/8165＋双归档＋README header hash→b0fea38・数字行维持 master 值）→ 本 wrap-up；不合其他分支、未推远程（origin/master＝85fb05a）。

## 7. 禁止事项自查

- backend／词库（glossary_lexicon*）／golden expected／README 数字行（476・13.462・13.469・Rule T 维持）：**一字未改** ✓
- 冲突解决只涉及 SHIFT_LOG／ACCEPT_LOG／ROADMAP 的追加并集（夜序 theirs 在前・绝不文本三路合并）；分支文件只接受分支版本 ✓
- 允许清单内文件のみ：tools/accept_night.py（NIGHT_ARTIFACTS[101]のみ）・tools/night101_eval_4000.py／night101_eval_8165.py（新 2 个）・eval/night101_results_4000.json／night101_results_8165.json（新归档）・eval/accept_night_101.json・SHIFT_LOG.md（心跳）・ACCEPT_LOG.md・REPORT_NIGHT101.md・REPORT_MERGE_98.md・README.md（header hash のみ）✓
- `eval/night98_check_*.tmp.json` untracked 不进合并 ✓；禁 OCR・禁 guwenbert・无网络（web_search 0・ページ取得 0）✓

## 8. 本夜坑位记录

- eval 工具克隆的自检三连：①注释行 token「# ---- 与 night99 归档全行逐位对照 ----」漏替换＝残留 grep 逮到；②新文本自带「N99/N100」字样＝被自己的 N99 残留断言逮到（新文本措辞改「は既に master 生效済み」）；③night100_results_4000 残留计数预期 3→4（BIG 块新文本也含该 token）——「逐个替换带出现次数断言＋陈旧引用 grep 自检」的价值再次确认。
- 其余按 N100 坑位惯例执行（心跳提交 merge 前落位・exec 失败不链 ; 续跑・登记提交含全部 tracked 改动）——本夜首跑全过、无 amend 无重跑。
