# REPORT_MERGE_96 — night96-rules → master 合并带入清单（Night 97）

## 1. 冲突文件（字节安全并集）

| 文件 | base（9d3b8a8 blob） | ours（master f80046e） | theirs（分支 642eb0d） | union（theirs+d_ours） |
|------|----------------------|--------------------------|--------------------------|--------------------------|
| SHIFT_LOG.md | 142,852 B 纯 LF（1018 行） | 142,982 B（+130 B＝N97 开工心跳 1 行） | 143,877 B（+1,025 B＝N96 心跳 4 行） | **144,007 B**（工作副本 CRLF 化 145,030 B・byte807=243 写前后断言・暂存 blob 144,007 B 纯 LF 等价断言） |

夜序：theirs（N96 段）在前、d_ours（N97 心跳）在后。冲突标记 0。
master 自分支点（9d3b8a8）未动＝本冲突仅此 1 文件，与 N95 合并夜同型常态。

## 2. 自动合并（M＝取分支值・master 侧未触碰）
- backend/kundoku_rules.py（Rule S 1 条：S_KANA_TO_KANJI＝なきなり→勿かれ〔guard 勿・ことなきなり→こと勿かれ 型
  B2 micro 新長键＝Rule M なかれ→勿かれ の活用形分割兄弟〕＋S_LONGER_WORDS 全空壳＋style_kana_to_kanji_s＋
  链尾 R→S 调用）
- README.md（テスト行 **469 passed**・規則エンジン行 **13.488**／拡張評価行 **13.496**・規則エンジン行 N96 口径句
  （eval/night96_results_4000.json）・ルールチェーン Rule S 句——header hash は合并後人工改 `9c4c308`＝登记提交 d5d22bd）
- tools/accept_night.py（NIGHT_ARTIFACTS[96]・本夜登记提交で [97] 追加）
- tools/verify_readme_facts.py（22 项版＝归档源 night96 切换＋Rule S 語数断言・master 旧版 21 项作废）
- ACCEPT_LOG.md（N96 验收行追加）
- ROADMAP.md（N96 行随分支带入・合并夜无追加行＝N90/N91/N95 先例）

## 3. 分支新文件（A＝17）
REPORT_NIGHT96.md；eval/accept_night_96.json、eval/night96_combo_changed_rows.json、eval/night96_mine.{json,txt}、
eval/night96_probe.{json,txt}、eval/night96_results_4000.json、eval/night96_results_8165.json、
eval/night96_sim.{json,txt}；tests/test_night96_rule_s.py；tools/night96_eval_4000.py、tools/night96_eval_8165.py、
tools/night96_mine.py、tools/night96_probe.py、tools/night96_sim.py。

## 4. 合并后状态（合后验证実数）
- pytest **469 passed**（462＋N96 的 7）
- golden_4000＝**13.488／24／0**（eval/night97_results_4000.json 与 night96 归档 diff 0 行・135s）
- golden_8165＝**13.496／30／0**（eval/night97_results_8165.json 与 night96 归档 diff 0 行・changed_ids_vs_n96＝[]）
- 词库 **1531**（209＋291＋1031・_ORDERED_ALL=1531）
- verify_readme_facts **22/22 exit 0**（header 改前後各一次）
- accept 97 **PASS fail=0 skip=0**（55.4s・登记 d5d22bd 後首跑・七门全绿・eval_integrity 実查 night97_results_4000.json）
- 合并提交 **9c4c308**；master 链 f80046e → 9c4c308 → d5d22bd → wrap-up；未推远程（origin/master＝9d3b8a8）。
