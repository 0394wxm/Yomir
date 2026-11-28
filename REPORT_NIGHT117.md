# REPORT_NIGHT117 — N115＋N116 合并夜（ZCode 单会话・N108/N110/N112/N114 先例）

## 0. 结论

- **本夜＝合并夜**：night115-annotation-design（56cd695 主＋632f8c3 wrap-up＝剥夹注管線設計夜・報告-only）＋night116-annotation-impl（a1383e2 主＋a47e686 wrap-up＝剥夹注管線実施夜）を **--no-ff 2 回順次合流**（N115→N116・N108 先例）。master＝4e335ac ＋ N115 两提交 ＋ N116 两提交。
- **冲突実測＝m1 恰 1 处（SHIFT_LOG）＋m2 恰 3 处（SHIFT_LOG／ROADMAP／ACCEPT_LOG）**＝预期通り。接缝一律 byte-safe union（tools/night117_merge_log.py＝N112/N114 方法论克隆・assert-only・纯字节操作・禁整文件 decode）：
  - m1 SHIFT_LOG：base 162786＋ours 350＋theirs 2528＋接缝 0＝**merged 165664 B**（夜序 115＜117）。
  - m2 SHIFT_LOG：base 162786＋ours 2878（N115 群 2528＋N117 行 350）＋theirs 1232＋接缝 0＝**merged 166896 B**（夜序 115＜116＜117・N115 群＝ours 追加段前缀与 632f8c3 blob−base 逐位相等断言）。
  - m2 ROADMAP：base 65451＋ours 4198（Night 115 行）＋theirs 3750（Night 116 行）＋接缝 0＝**merged 73399 B**。
  - m2 ACCEPT_LOG：base 13641＋ours 170（115 试跑＋终跑 2 行）＋theirs 171（116 试跑＋终跑 2 行）＋接缝 0＝**merged 13982 B**。
- **夜序 115＜116＜117 成立**（机械并集会逆序＝N110/N112/N114 教训・心跳行锚定目视段行位置断言）。**canary 并集前后实测**＝LF blob [800]=243／[807]=63 ✓＋CRLF 虚拟形态 [807]=243 ✓（両 merge とも）。**哨兵守恒**＝N111…N117 全 token 计数 merged＝base＋两侧追加之和 ✓（最終 N111=8／N112=4／N113=3／N114=3／N115=6／N116=5／N117=1・N113/N114 計数は base 側の登記/收工行由来で N114 当時 2/1 から自然増）。
- **坑位①（N116 §4）クリア**：合后 `git show master:ROADMAP.md`＝**Night 115 行（「Night 115（…」・分支側のみだった行）＋Night 116 行（「- 状態: DONE - Night 116(…」）の两行实测**。
- **grep 防回滚全过**：backend/main.py 含 has_ruby_annotation（2）／strip_annotation（2）／hakubun_orig（2）＝N116 実施在 master 里・tools/verify_readme_facts.py:44 归档源＝night116_results_4000.json・README 含 13.455／13.454／511 passed・tools/accept_night.py:87 含 116 条目。
- **验证全绿**：pytest tests -q＝**511 passed**（503＋8・28.73s・0 新增）・実施 5 文件（backend/main.py・tests/test_night115_strip.py・tools/accept_night.py・tools/verify_readme_facts.py・README.md）＝**a47e686 侧 blob 级 diff 0 B**（合并零改动の直接証拠）・golden_4000＝**13.455／24／0・vs night116_results_4000.json 全行 byte-identical（diff 0 行・exit 0）**・golden_8165＝**13.454／30／0・sum 109852・vs night116_results_8165.json 全行 byte-identical（diff 0 行・exit 0）**・verify＝**26/26 exit 0**（归档源 night116）・词库＝**1531 不变**（base 500＋extra2 1031 実測＋pytest 词库断言維持）。
- **accept 117：试跑 FAIL＝repo_clean 1 項（設計行為・49.4s）＋终跑 PASS fail=0 skip=0・七门全绿（48.3s）**（两行留 ACCEPT_LOG＝N100/N104/N109/N113/N114/N116 先例）。NIGHT_ARTIFACTS 加 **117: ["night116_results_4000.json"]**（归档源维持 night116＝N112/N114 先例・**115 不登记＝設計夜 N98/N102/N103/N106/N109/N113 先例**）。
- **拍板表正文未動**（合并夜＝N114 先例）。本夜代码零改动（tools 3 本新規＝merge_log 1＋eval クロン 2・backend/词库/golden expected/tests 一字未改）。
- **本夜 5 提交**（心跳 77ed3fb・merge115 094b408・merge116 0557e59・登记 0d61d27・wrap-up）・**未推远程**（origin/master＝4e335ac・rev-list 超前＝**9**＝本夜 5＋N115 两＋N116 两・等你手推）。

## 1. 开工

- `git checkout master`：HEAD＝**4e335ac**（N114 wrap-up）✓・origin/master＝4e335ac（**rev-list=0 実測**）✓・已跟踪文件零改动 ✓・pytest tests -q＝**503 passed in 45.20s**（eval/night117_pytest_master.txt）✓。
- 分支核验：night115-annotation-design tip＝**632f8c3**（父 **56cd695**）・night116-annotation-impl tip＝**a47e686**（父 **a1383e2**）・merge-base 均为 **4e335ac** ✓。
- diffstat 実測（git diff --stat master...分支）：**N115＝22 文件＋5040**（ACCEPT_LOG＋2／REPORT_NIGHT115＋133／ROADMAP＋1／SHIFT_LOG＋6／tools/night115_ 3 本／eval/night115_ 15 個・**backend diff=0**＝report-only 与报告一致）；**N116＝26 文件＋127410−9**（backend/main.py 33（+32−1）／tests/test_night115_strip.py＋197（8 条）／tools/accept_night.py＋1（116 条目）／tools/verify_readme_facts.py 8（归档源切换）／README 8／ROADMAP＋1／SHIFT_LOG＋4／ACCEPT_LOG＋2／tools/night116_ 4 本／eval/night116_ 13 個）＝触碰范围与两报告逐项一致 ✓。
- 読済：REPORT_NIGHT115 **§0/§4/§5**（133 行全文）＋REPORT_NIGHT116 **§0/§2/§4**（80 行全文）（git show 分支侧落盘）。SHIFT_LOG blob canary 事前実測＝LF [800]=243／[807]=63・CRLF 虚拟 [807]=243・工作区 CRLF（163858 B）＋core.autocrlf=true（blob LF）確認。
- 心跳提交 **77ed3fb**（master 先落 1 行＝N100 坑位①・blob 163136 B＝162786＋350・canary 維持）。

## 2. 合并

### merge ①：night115-annotation-design → **094b408**

- `git merge --no-ff night115-annotation-design`：**冲突恰 1 处＝SHIFT_LOG.md**（ours＝心跳 1 行・theirs＝N115 6 行。ROADMAP/ACCEPT_LOG は ours 未触碰で無冲突・auto 带入）。
- byte-safe union（tools/night117_merge_log.py m1）：两侧纯追加断言 ✓・夜序 115＜117（N115 群 offset 162786–165049＜N117 行 offset 165314）・接缝 0（両側追加段 \n 终止）・canary 並集前後実測 ✓・哨兵守恒 ✓・字节账 162786＋350＋2528＋0＝165664 B。
- `git add SHIFT_LOG.md`＋commit（「Merge branch 'night115-annotation-design'」＝59ca4cd 先例の一行样式）。带入確認＝tools/night115_ 3 本・REPORT_NIGHT115・ROADMAP Night 115 行。

### merge ②：night116-annotation-impl → **0557e59**

- `git merge --no-ff night116-annotation-impl`：**冲突恰 3 处＝ACCEPT_LOG.md／ROADMAP.md／SHIFT_LOG.md**（预期通り・其余文件 clean 带入＝backend/main.py 等 blob 級同一）。
- byte-safe union（m2）：
  - **SHIFT_LOG**：ours 追加段＝N115 群＋N117 行の 2 段構成。N115 群＝`632f8c3:SHIFT_LOG.md`−base を再構成し ours 前缀逐位一致断言 ✓。並集＝base＋N115 群＋theirs（N116 4 行）＋N117 行＝**166896 B・夜序 115＜116＜117**（offset 162786–165049＜165314–166224＜166546）・接缝 0・canary ✓・哨兵守恒 ✓。
  - **ROADMAP**：ours 追加＝Night 115 行 4198 B・theirs 追加＝Night 116 行 3750 B・base 无 Night 115/116 断言 ✓・並集＝**73399 B・115＜116**（@65451＜@69666）。
  - **ACCEPT_LOG**：ours 追加＝115 两行 170 B・theirs 追加＝116 两行 171 B・**両分支各 2 行全数并入**・base 无「| 115 |／| 116 |」断言 ✓・並集＝**13982 B・115＜116**。
- `git add` 3 文件＋commit（「Merge branch 'night116-annotation-impl'」）。parents＝094b408＋a47e686 実測。
- **坑位① 実測**：合后 master:ROADMAP.md 含 **Night 115（**×1＋**Night 116(**×1（欠一行即停の门＝通過）。
- **grep 防回滚**（§0 記載の通り全过）。

## 3. 验证

- **pytest tests -q＝511 passed（503＋8・28.73s・exit 0）**（eval/night117_pytest_merged.txt）。
- **実施文件 blob 级同一**：`git diff a47e686 master -- backend/main.py tests/test_night115_strip.py tools/accept_night.py tools/verify_readme_facts.py README.md`＝**0 B**（合并が N116 実施を一字不改で带入＝黄金証拠）。
- **golden_4000 真跑**（tools/night117_eval_4000.py＝assert-only 克隆・基线 night116_results_4000.json・不写归档）：**13.455／24／0・diff 0 行＝全行 byte-identical**（exit 0）。
- **golden_8165 真跑**（tools/night117_eval_8165.py＝同款克隆）：**13.454／30／0・sum 109852・diff 0 行＝全行 byte-identical**（exit 0・stderr httpx 洪水は捨てて exit code 判定＝N110 教训）。
- **verify 26/26 対上・exit 0**（tools/verify_readme_facts.py・归档源＝night116 44 行実測）。
- **词库 1531 不变**（GLOSSARY_LEXICON 500＋LEXICON_EXTRA2 1031 実測・pytest 词库断言 N75/N80/N82/N89 維持）。
- **accept 117**：试跑 **FAIL fail=1（repo_clean 1 項＝tools/accept_night.py 登记改动中・其余 6 门 PASS・49.4s）**＝設計行為 → 登记 commit 後终跑 **PASS fail=0 skip=0・七门全绿（48.3s）**（ACCEPT_LOG 两行残置・eval/accept_night_117.json＝final）。

## 4. 坑位

1. **N115 SHIFT_LOG 行は変体形式**——N114 形式「… HH:MM N11n …」に対し N115 は「… HH:MM **Night 115** 开工心跳…」＋「… HH:MM **进度：N115** …」（夜 token が時刻直後にない）。N114 工具の锚定 regex（時刻直後 N11n）では 0 匹配で assert 停止（実際 m1 初跑で停止）→ night117_merge_log.py は**行首 datetime＋行内首个夜 token（`Night 11x`／`N11x` 両対応）**の行単位 extractor に汎化。N116 行は N114 形式のまま。
2. **N115 行内時刻は自夜の提交時刻と偏移**——SHIFT_LOG 行内 22:00–23:05 vs 同夜 ACCEPT_LOG タイムスタンプ 19:26–19:30／wrap-up 提交 19:30:10。**夜序規則（115＜116＜117）は夜号基準で時刻非依存**のため並集はこのままで正（接缝前後で時刻列が非単調に見える＝字节保存・内容不触・観察のみ）。N116 行内時刻（19:50–20:19）は提交時刻と一致。
3. **N115 ROADMAP 行は「- 状態: DONE - 」前置き無し**（「Night 115（2026-11-28, …」で始まる・N116 行は有り）。union は内容不触のため原样保存——在庫夜の ROADMAP 形式統一確認用に記録（本夜では直さない）。
4. **union 落盘後の SHIFT_LOG 工作区は LF 形态**——m2 工具が LF 原字节で書く（N114 先例）ため、その後の心跳追加は CRLF でなく **LF 追加**（本夜進度/收工心跳は LF 追加・blob は常に LF＝autocrlf=true）。開工心跳だけは CRLF 工作区時代の追加。
5. **継承坑位**（N113/N115/N116）：CJK console redirect は mojibake＝UTF-8 落盘＋exit code 判定・多行 python -c 禁・JSON dump に set/tuple 键禁・`_kundoku_result_for(use_cache=False)` は seg=defaultdict 必須（sim 層のみ・本夜は該当呼び出し無し）。

## 交付对照（任务书「交付」の数値欄）

- **Night 117 完成，全部验收通过。**
- 开工：HEAD＝4e335ac ✓・pytest 503 passed（45.20s）✓・目录 D:\kanbun-kakikudashi ✓・N115 tip 632f8c3（父 56cd695）＋N116 tip a47e686（父 a1383e2）・merge-base 4e335ac ✓・origin/master＝4e335ac（rev-list=0）✓。
- 合并：N115（--no-ff 094b408）＋N116（--no-ff 0557e59），冲突 m1 恰 1 处＋m2 恰 3 处（SHIFT_LOG×2／ROADMAP×1／ACCEPT_LOG×1・byte-safe union，字节账 m1 162786＋350＋2528＋0＝165664 B・m2 162786＋2878＋1232＋0＝166896 B／65451＋4198＋3750＋0＝73399 B／13641＋170＋171＋0＝13982 B；夜序 115＜116＜117；canary 并集前后实测＝LF blob [800]=243／[807]=63＋CRLF 虚拟 [807]=243 ✓・哨兵守恒 ✓）；ROADMAP 含 Night 115＋116 两行 ✓；grep 防回滚全过（has_ruby_annotation／strip_annotation／hakubun_orig 在 master 里・verify 源 night116・README 13.455/13.454/511・accept_night.py 116 条目）。
- 验证：pytest **511 passed**（0 新增）・golden_4000 **13.455／24／0**（全行 byte-identical vs night116・diff 0 行）✓・golden_8165 **13.454／30／0（sum 109852・全行 byte-identical vs night116・diff 0 行）**✓・verify **26/26 exit 0** ✓・词库 **1531 不动** ✓。
- 验收：accept 117 **PASS**（fail=0 skip=0・七门全绿・试跑 FAIL＝repo_clean 1 項設計行為・FAIL/PASS 两行留 ACCEPT_LOG）・本地提交 **77ed3fb＋094b408＋0557e59＋0d61d27＋wrap-up**（5 提交）・未推远程——origin/master＝4e335ac，rev-list 超前＝**9**（本夜 5 提交＋N115 两提交＋N116 两提交，等你手推）。报告见 REPORT_NIGHT117.md。
