# REPORT_MERGE_92 — night92-ruleq → master 合并带入清单（Night 93）

- 合并提交: **`3a64ff0`**（`git merge --no-ff night92-ruleq -m "Merge night92-ruleq"`）
- 合并前: master = 5a78d0b（N93 开工心跳）← b6a6248（N91 wrap-up＝merge-base）
- 被合并: night92-ruleq = a39e648（N92 wrap-up）← 22e4e9e（N92 主）
- 冲突: **1 文件**（SHIFT_LOG.md・追加-追加）＝字节安全并集；其余自动合并。
- master 侧合并前 delta＝开工心跳 1 行（224 B）のみ＝base 未落后（N91 の 3 冲突は
  base 落后の特例、本夜は該当せず）。

## 1. 冲突文件（字节安全并集）

| 文件 | base（b6a6248 blob） | ours（master 5a78d0b） | theirs（分支 a39e648） | union（theirs+d_ours） |
|------|----------------------|--------------------------|--------------------------|--------------------------|
| SHIFT_LOG.md | 137,389 B 纯 LF | 137,613 B（+224 B＝N93 开工心跳 1 行） | 138,684 B（+1,295 B＝N92 心跳 4 行） | **138,908 B**（工作副本 CRLF 化 139,917 B・byte807=243 写前后断言・暂存 blob 138,908 B 等价断言） |

夜序：theirs（N92 段）在前、d_ours（N93 心跳）在后。冲突标记 0。

## 2. 自动合并（M＝取分支值・master 侧未触碰）

- backend/kundoku_rules.py（Rule Q 2 条：Q_KANA_TO_KANJI＝ことなく→こと莫く〔guard 莫〕・
  すべからず→可からず〔guard 可〕＋Q_LONGER_WORDS 全空壳＋style_kana_to_kanji_q＋
  链尾 O→Q 调用）
- README.md（テスト行 **453 passed**・拡張評価行 **13.500**・規則エンジン行 N92 口径句・
  ルールチェーン Rule Q 句——header hash は合并後人工改 `3a64ff0`＝登记提交 852850d）
- tools/accept_night.py（NIGHT_ARTIFACTS[92]）
- tools/verify_readme_facts.py（20 项版＝归档源 night92 切换＋Rule Q 語数断言・
  master 旧版 19 项作废）
- ACCEPT_LOG.md（N92 验收行追加）

## 3. 分支新文件（A＝17）

REPORT_NIGHT92.md；eval/accept_night_92.json、eval/night92_combo_changed_rows.json、
eval/night92_mine.{json,txt}、eval/night92_probe.{json,txt}、eval/night92_results_4000.json、
eval/night92_results_8165.json、eval/night92_sim.{json,txt}；tests/test_night92_rule_q.py；
tools/night92_eval_4000.py、tools/night92_eval_8165.py、tools/night92_mine.py、
tools/night92_probe.py、tools/night92_sim.py。

## 4. 合并后状态（合后验证実数）

- pytest **453 passed**（443＋N92 的 10）✓
- golden_4000 **13.491/24/0**＝night92 归档逐位一致（diff 0 行・12 行 Rule Q 改写生效）✓
- golden_8165 **13.500/30/0**＝night92 归档逐位一致（diff 0 行・37 行改写生效・
  N91 13.502 から改善）✓
- 词库 **1531**（GLOSSARY_LEXICON 500〔_OLD_SIZE 209〕＋LEXICON_EXTRA2 1031・
  _ORDERED_ALL=1531）不动 ✓
- verify **20/20 exit 0** ✓
- accept 93 **PASS fail=0 skip=0**（31.1s 首跑即过・七门全绿）✓
