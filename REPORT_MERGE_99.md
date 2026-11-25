# REPORT_MERGE_99 — night99-rulet → master 合并带入清单（Night 100）

## 1. 冲突文件（字节安全并集）

| 文件 | base（d7bd2ff blob） | ours（master a4a22e6） | theirs（分支 6329010） | union（theirs+d_ours） |
|------|----------------------|--------------------------|--------------------------|--------------------------|
| SHIFT_LOG.md | 144,576 B 纯 LF | 144,734 B（+158 B＝N100 开工心跳 1 行） | 145,717 B（+1,141 B＝N99 心跳 3 行） | **145,875 B**（工作副本 CRLF 化 146,903 B・blob canary(807)=63／工作副本 canary=243 双形态断言・写前后断言・暂存 blob 145,875 B＝union 纯 LF 等价断言） |

夜序：theirs（N99 段）在前、d_ours（N100 心跳）在后。冲突标记 0。
master 自分支点（d7bd2ff）未动＝本冲突仅此 1 文件，与 N95/N97 合并夜同型常态。

## 2. 自动合并（M＝取分支值・master 侧未触碰）

- backend/kundoku_rules.py（Rule T 3 条：T_KANA_TO_KANJI＝べからず→可からず／べからざる→可からざる／
  べきなり→可きなり〔いずれも guard 可・可は新旧変異なし〕＋T_LONGER_WORDS 空壳 3 键
  〔三键互不重叠＝べからず非べからざる子串〕＋style_kana_to_kanji_t＋链尾 S→T 调用＝拍板夜変差 6 行許容）
- README.md（テスト行 **476 passed**・規則エンジン行 **13.462**／拡張評価行 **13.469**・N99 系列句＋
  ルールチェーン Rule T 句——header hash は合并後人工改 `0d71cb3`＝登记提交 88f4b78）
- tools/accept_night.py（NIGHT_ARTIFACTS[99]・本夜登记提交で [100] 追加）
- tools/verify_readme_facts.py（**23 项版**＝Rule T 語数断言追加＋归档源 night99 切换・master 旧版 22 项作废）
- tests/test_night99_rule_t.py（7 tests・pytest 469→476）
- ACCEPT_LOG.md（N99 验收行追加）・ROADMAP.md（N99 行随分支带入・合并夜无追加行＝N90/N91/N95/N97 先例）

## 3. 分支新文件（A＝10）

REPORT_NIGHT99.md；eval/accept_night_99.json、eval/night99_combo_changed_rows.json、
eval/night99_results_4000.json、eval/night99_results_8165.json、eval/night99_sim.json、eval/night99_sim.txt；
tests/test_night99_rule_t.py；tools/night99_eval_4000.py、tools/night99_eval_8165.py、tools/night99_sim.py。

## 4. 合并后状态（合后验证実数）

- pytest **476 passed**（469＋N99 的 7）
- golden_4000＝**13.462／24／0**（eval/night100_results_4000.json 与 night99 归档 diff 0 行・92s・93 行改写随合并生效・変差 5 行在 4000 内）
- golden_8165＝**13.469／30／0**（eval/night100_results_8165.json 与 night99 归档 diff 0 行・changed_ids_vs_n99＝[]・178 行改写・変差 6 行）
- 词库 **1531**（209＋291＋1031・_ORDERED_ALL=1531・N99 未碰词库）
- verify_readme_facts **23/23 exit 0**（header 改前実测）
- accept 100 **PASS fail=0 skip=0**（34.5s・登记 88f4b78 後重跑 PASS・首跑 FAIL＝repo_clean 1 项＝心跳行未提交の設計行為・FAIL/PASS 両行留 ACCEPT_LOG・七门全绿・eval_integrity 実查 night100_results_4000.json）
- 合并提交 **0d71cb3**；master 链 d7bd2ff → a4a22e6（心跳）→ 0d71cb3（merge）→ 88f4b78（登记）→ wrap-up；未推远程（origin/master＝d7bd2ff）。
