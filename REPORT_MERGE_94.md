# REPORT_MERGE_94 — night94-ruler → master 合并带入清单（Night 95）

- 合并提交: **`22a4445`**（`git merge --no-ff night94-ruler -m "Merge night94-ruler"`）
- 合并前: master = 746adba（N95 开工心跳）← 07ff902（N93 wrap-up＝merge-base）
- 被合并: night94-ruler = f024951（N95 step0 报告修正）← efa818b（N94 wrap-up）← e820f83（N94 主）
- 冲突: **1 文件**（SHIFT_LOG.md・追加-追加）＝字节安全并集；其余自动合并。
- master 侧合并前 delta＝开工心跳 1 行（142 B）のみ＝base 未动（N93 常态）。
- step 0（合并前・分支提交 f024951）: REPORT_NIGHT94 §2 组合段别数修正——s3908 5 行
  better 4→**6 行 better 5**／s257 1 行 same→**0 行**（same 行 roushi51-2 は s3908
  golden idx 6974 在籍＝任务书の「s257 same 1 实为 better 1」假设不成立）。组合总数
  12 行／改善 10／変差 0 は初版から正确で不変。詳細＝REPORT_NIGHT95 §2。

## 1. 冲突文件（字节安全并集）

| 文件 | base（07ff902 blob） | ours（master 746adba） | theirs（分支 f024951） | union（theirs+d_ours） |
|------|----------------------|--------------------------|--------------------------|--------------------------|
| SHIFT_LOG.md | 139,655 B 纯 LF | 139,797 B（+142 B＝N95 开工心跳 1 行） | 141,622 B（+1,967 B＝N94 心跳 4 行） | **141,764 B**（工作副本 CRLF 化 142,780 B・byte807=243 写前后断言・暂存 blob 141,764 B 纯 LF 等价断言） |

夜序：theirs（N94 段）在前、d_ours（N95 心跳）在后。冲突标记 0。

## 2. 自动合并（M＝取分支值・master 侧未触碰）

- backend/kundoku_rules.py（Rule R 1 条：R_KANA_TO_KANJI＝ゆく→之く〔guard 之・
  (ゆ,之) 1 字块 3 行锚定 2 字长键〕＋R_LONGER_WORDS 全空壳＋style_kana_to_kanji_r＋
  链尾 Q→R 调用）
- README.md（テスト行 **462 passed**・規則エンジン行 **13.489**／拡張評価行 **13.498**・
  規則エンジン行 N94 口径句（eval/night94_results_4000.json）・ルールチェーン Rule R 句
  ——header hash は合并後人工改 `22a4445`＝登记提交 feffa7b）
- tools/accept_night.py（NIGHT_ARTIFACTS[94]・本夜登记提交で [95] 追加）
- tools/verify_readme_facts.py（21 项版＝归档源 night94 切换＋Rule R 語数断言・
  master 旧版 20 项作废）
- ACCEPT_LOG.md（N94 验收行追加）

## 3. 分支新文件（A＝17）

REPORT_NIGHT94.md；eval/accept_night_94.json、eval/night94_combo_changed_rows.json、
eval/night94_mine.{json,txt}、eval/night94_probe.{json,txt}、eval/night94_results_4000.json、
eval/night94_results_8165.json、eval/night94_sim.{json,txt}；tests/test_night94_rule_r.py；
tools/night94_eval_4000.py、tools/night94_eval_8165.py、tools/night94_mine.py、
tools/night94_probe.py、tools/night94_sim.py。

## 4. 合并后状态（合后验证実数）

- pytest **462 passed**（453＋N94 的 9）✓
- golden_4000 **13.489/24/0**＝night94 归档逐位一致（diff 0 行・6 行 Rule R 改写生效・
  N93 13.491 から改善）✓ — 归档 eval/night95_results_4000.json（NIGHT_ARTIFACTS[95] 登记）
- golden_8165 **13.498/30/0**＝night94 归档逐位一致（diff 0 行・12 行改写生效・
  N93 13.500 から改善）✓ — 归档 eval/night95_results_8165.json（扩充归档・非登记）
- 词库 **1531**（_OLD_SIZE 209＋extra 291＋LEXICON_EXTRA2 1031・_ORDERED_ALL=1531）不动 ✓
- verify **21/21 exit 0** ✓
- accept 95 **PASS fail=0 skip=0**（32.2s 登记后首跑即过・七门全绿）✓
