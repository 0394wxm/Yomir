# REPORT_NIGHT97 — 合并夜（night96-rules → master，AutoClaw 单会话）

## 0. 概要
Night 96（Rule S 1 条・分支 night96-rules＝5bbed94＋642eb0d）验收通过后，本夜把它合进 master。
单次 `git merge --no-ff`，冲突 1 文件（SHIFT_LOG.md 追加-追加）走字节安全并集，合后全部验证逐项通过，
accept 97 PASS（fail=0 skip=0・七门全绿）。不推远程。

## 1. 开工核验（对不上停下报数——全部对上）
- `git log -1`＝**9d3b8a8**（N95 wrap-up）✓
- `pytest tests -q`＝**462 passed**（14.43s）✓
- `git log -1 night96-rules`＝**642eb0d**（N96 wrap-up）✓
- `git merge-base master night96-rules`＝**9d3b8a8**（N96 自 master 直分，无 clone 中转、无需 fetch）✓
- `git rev-list master..night96-rules --count`＝2（5bbed94＋642eb0d）✓；树内只有历史 untracked 缓存
- 先读 REPORT_NIGHT96.md §5/§7（验证数・移交）与 REPORT_MERGE_94.md §1/§3（字节安全并集方法论・分支新文件清单）。
- 本夜无 step 0——N96 数字已在验收审计中全数对过，无待清零的报告差。

## 2. 合并（单次 --no-ff）
- 开工心跳 1 行（SHIFT_LOG.md，UTF-8 二进制追加・byte807=243 写前后断言・delta 131 B）先提交＝**f80046e**。
- `git merge --no-ff night96-rules -m "Merge night96-rules"` → 冲突 1 文件＝**SHIFT_LOG.md**（UU・预期唯一冲突）；
  其余 22 文件自动合并（M＝5 取分支值・A＝17 分支新文件）。
- 字节安全并集（git show :1:/​:2:/​:3: 三阶段 blob・绝不文本三路合并）：
  - base＝142,852 B（1018 行・纯 LF）／ours＝142,982 B（+130 B＝N97 开工心跳 1 行）／theirs＝143,877 B（+1,025 B＝N96 心跳 4 行）
  - union＝theirs＋d_ours＝**144,007 B**（1023 行・夜序 theirs（N96 段）在前）
  - 工作副本＝CRLF 化 union＝**145,030 B**、byte807=243 写前后断言、CRLF↔LF 往返等价断言
  - `git add` 后暂存 blob＝144,007 B 纯 LF 等价断言 → commit＝**9c4c308**；冲突标记 0。
- 合后 `git log --oneline -3`＝9c4c308（merge）← f80046e（心跳）✓

## 3. 合后验证（数字是死的，逐项对）
| 项 | 门 | 実数 | 判定 |
|---|---|---|---|
| pytest tests -q | 469 passed | **469 passed**（11.54s＝462＋N96 的 7） | ✓ |
| golden_4000 全量真跑 | 与 eval/night96_results_4000.json 逐位一致 13.488/24/0 | **13.488／24／0・diff 0 行**（135s・不是 N95 的 13.489——azamukuko-1 随合并生效） | ✓ |
| golden_8165 全量真跑 | 与 eval/night96_results_8165.json 逐位一致 13.496/30/0 | **13.496／30／0・diff 0 行**（changed_ids_vs_n96＝[]） | ✓ |
| 词库 | 1531 条不动 | **1531**（209＋291＋1031・_ORDERED_ALL=1531・N96 未碰词库） | ✓ |
| verify_readme_facts | 22/22 exit 0（分支版 22 项为准・master 旧版 21 项作废） | **22/22 exit 0**（header 改前・改后各跑一次） | ✓ |

工具＝tools/night97_eval_4000.py／night97_eval_8165.py（night96 型程序化克隆・N93/N95 合并夜型：基线换 night96 归档、
全行 diff=0 断言、逐个替换带出现次数断言＋残留 token grep 自检＋ast 检查・LF）；
归档 eval/night97_results_4000.json（默认口径登记用）＋eval/night97_results_8165.json（扩充归档，不登记默认口径）。

## 4. 登记＋验收
- README 数字行已随合并自动取分支值（テスト 469・4000 行 13.488・8165 行 13.496・Rule S 句）；
  人工仅改 header＝「Night 97 合并：night96-rules Rule S 1 条（主 5bbed94＋wrap-up 642eb0d）・合并提交 `9c4c308`」
  ＋日期 2026-11-25（CRLF 182 保持・与数字同登记提交收口）。
- tools/accept_night.py NIGHT_ARTIFACTS 照例加 `97: ["night97_results_4000.json"]`（CRLF 保持）。
- 登记提交＝**d5d22bd**（6 文件：accept_night.py・night97_eval×2・night97_results×2・README header）。
- `accept_night.py 97` 登记后首跑＝**PASS（fail=0 skip=0・55.4s・七门全绿）**：
  repo_clean PASS／pytest 469＝469／eval_integrity 実查 night97_results_4000.json／rule_regression／engine_smoke／
  perf_envelope／order_rate（右先率基线差 +0.00pp）。

## 5. 移交（N96 §7 原样带入・本夜一字未动）
1. micro 区带実質枯竭（1 字块 rows>=3＋rows<=2 計 714 块完掘）；
2. B2 (べ,可) prefix 分離完結（(すべ,可) 型已收規則吸収済み）；
3. 拍板事项（N86/N88/N92/N94 原样）：べからず族 89 行（可からず 78 発火 70 改善 5 変差・可からざる 82/79/1）・
   べきなり→可きなり 31 行 29 改善 1 変差（p-gekirin-1）・なかれ→莫かれ post-N 17 行（kokyo09-5）・
   がため/何のごとく 各 1 行（rerun 行 tail guard 機構変更待ち）・は系 1 字块構文判別機構（26＋278 块実測）・
   嗟や→嗟乎 在庫（Δ−0.000367）・guard 外ことなく 5 行・ことなき 字形統一（データ側）・N84 §8 夹注残渣 8 行等；
4. 長尾 scan 同名 3 件（してなる→使うや・なるをしむるの→令・はなる→少くして）＝自動拒扱い（N86 惯例）；
5. 次夜建议：規則側残り＝機構変更/データ側拍板 4 本に集約——報告-only 夜（N69/N74/N76/N88 先例）か
   2 字块 B2 rows<=3 快查・新语料依存在庫消化。

master 链：f80046e（心跳）→ 9c4c308（merge --no-ff）→ d5d22bd（登记）→ 本 wrap-up。origin/master＝9d3b8a8 未推。
