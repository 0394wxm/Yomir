# REPORT_NIGHT116 — 剥夹注管線实施夜（項 9・N115 Stage 0/1 落地・ZCode 单会话）

## 0. 结论

- **本夜＝項 9 剥夹注管線的实施夜**。N115 设计（Stage 0/1）按用户 2026-11-28 拍板三点落地：①剥下注记去向＝**丢弃**；②新信号命名＝**helper `has_ruby_annotation`**（API text_type 契約不変・`kanbun_ruby` 第三 type 値不採用）；③**hakubun 返原文**（N84 先例）。
- **backend/main.py 仅两处（+32−1・恰三块）**：①N84 ruby 块（158 行 `return tail`）直后追加 `RUBY_SPAN_RE`／`has_ruby_annotation`／`strip_annotation`（168/171/176 行）；②`kundoku()` engine 分支 `_kundoku_result_for` 调用点直前（446–450 行）插入 `hakubun_orig` 退避＋`if has_ruby_annotation(text): text = strip_annotation(text)`＋`strip_note`（＋response 挂钩 2 行＝`hakubun=hakubun_orig`＋`note=(strip_note + DISCLAIMER) if strip_note else ""`）。**detect_text_type 本体・kana 分支（N84 尾段路径）・tail rerun・echo/no_tail・规则链・词库・golden expected 一字未改**。
- **新测试 tests/test_night115_strip.py 8 条＝pytest 511 passed（503+8・18.62s）**。
- **双口径真跑（TestClient 完整链・写新归档・night111 归档不触碰）＝设计期待逐位命中**：
  - golden_4000＝**13.455／24／0・vs night111 全行 byte-identical（diff 0 行＝scope 4000 内 0 行）**（140s・exit 0）。
  - golden_8165＝**13.464→13.454／30／0・sum 109934→109852（Δ−82＝残渣 2 行分）・diff 恰 2 行＝rikutou59-2 224→155・soji07-6 36→23・其余 8163 行 byte-identical・exact 30 不変**（約340s・exit 0）。
- **冒烟不变量（8165 全行・sim 同口径重测）**：I1 非注记行 identity 7914/7914・I2 冪等 8165/8165・I3 注记行剥後無括号 251/251・I4 sonshi09-38 剥後 detect=kana（管線外維持）・剥後首尾空白 0 行・rongo 编号 6 行 `has_ruby_annotation`=False・dangling ） 6 行 identity。
- **verify 26/26 exit 0**（归档源 night111→night116 切换＝N107/N111 先例）。**词库 1531 不変**（pytest 词库断言維持）。README header（実施链・分支起点 4e335ac・未合 master）＋数字行（511 passed・13.455/24・13.454/30）与数字同提交。
- **accept 116：试跑 FAIL＝repo_clean 1 項（設計行為）＋终跑 PASS fail=0 skip=0 七门全绿**（两行留 ACCEPT_LOG＝N100/N104/N109/N113/N114 先例）。**NIGHT_ARTIFACTS 加 116: ["night116_results_4000.json"]**（归档源切 night116・**115 不登记＝設計夜 N98/N102/N103/N106/N109/N113 先例**）。
- **項 9 状態＝在庫→已実施（N116・実現値 Δ−82/8165 sum）**（§3）。拍板表正文未动（更新归在庫夜）。REPORT_NIGHT98/109/113/115 未动。分支 night116-annotation-impl 两提交**未合 master・未推远程**（待合并夜与 N115 一起合＝N108 先例）。

## 1. 开工

- `git checkout -b night116-annotation-impl master`：HEAD＝**4e335ac**（N114 wrap-up）✓・origin/master＝4e335ac（**rev-list 双向＝0 実測**）✓・已跟踪文件零改动 ✓・pytest tests -q＝**503 passed in 24.53s**（eval/night116_pytest_start.txt）✓。
- git identity：user.name=wang・user.email=wang@localhost（設定済み確認＝N115 同款）。
- 読済：**REPORT_NIGHT115 §0/§4/§5**（git show night115-annotation-design:REPORT_NIGHT115.md・133 行全文）＋**tools/night115_sim.py**（279 行＝設計関数 spec・Stage 0/1 の sim 層実装をそのまま backend に落とす）＋backend/main.py 読码（N84 块 142–158・kundoku() 339–465・KundokuResponse 97–113・DISCLAIMER 56 行）＋tools/night111_eval_4000/8165.py（真跑工具の雛形）＋tools/verify_readme_facts.py（归档源 44 行）＋tools/accept_night.py（NIGHT_ARTIFACTS 50–・7 门 601–）。
- tests 风险排查：api/kundoku を叩く既存 8 ファイル中、注记行を post するのは test_night84_empty_got.py のみ（RUBY_SHORT/RUBY_LONG＝いずれも detect=kana＝N84 分支・本夜触碰外）。其余の （ は全て注释/docstring・词库読み。**engine 分支注记行の既存断言＝0 件**（実装前に確認済み）。

## 2. 实施（backend/main.py 仅两处・落点以读码锚定）

### ① Stage 0/1 helpers（N84 块直后・実測 160–180 行＝diff +20）

- 任务书「142–166 行直后」の読码実測＝N84 块は **142–158**（142 `_RUBY_TAIL_ECHO_MAX`／143 `_RUBY_LEAD_JUNK`／146–158 `_ruby_tail_kanbun`）・161 が `ENGINE = None`。挿入点＝158 行直後（N84 ブロック直後・ENGINE 宣言の前）。
- `RUBY_SPAN_RE = re.compile(r"（[^（）]*[ぁ-ゖー][^（）]*）")`（168 行）＝**N115 sim の RUBY_SPAN と同一 regex・N98 B9 証拠式同口径**（含仮名の全角 （…） span・`[^（）]*` は括号非跨越＝span 対内完結）。
- `has_ruby_annotation(text)`（171）＝`bool(RUBY_SPAN_RE.search(text))`＝sim 逐字同型。**detect_text_type 本体・返り値・API text_type 字段は全部不変**（拍板②）。
- `strip_annotation(text)`（176）＝`RUBY_SPAN_RE.sub("", text)`＝含仮名 span 全剥・**剥下物捨て（拍板①）**・剥離により前後字符直接連結（十（じっ）勝（しょう）→十勝）・空白挿入なし・改行変換なし。

### ② engine 分支剥离（実測 445–450 行＋response 挂钩 490–497＝diff +12−1）

- `kundoku()` engine 分支、ENGINE None チェック後・`try: _kundoku_result_for(text, ...)`（423 行→実施後 453 行）直前に 1 か所挿入：
  - `hakubun_orig = text`（446）＝**拍板③ hakubun 返原文の退避**（text 再代入後も response が原文を返す・非注记行は同値＝出力不変）。
  - `if has_ruby_annotation(text): text = strip_annotation(text)`（448–449）＝**任务书 ② の 2 行そのもの**。
  - `strip_note = "白文含全角括号 ruby 夹注（N116）：已剥离夹注，对剥后白文重新訓読。"`（450）＝**N84 fallback_note 先例の同款文面**。
- response 挂钩：`hakubun=hakubun_orig`（原文返し・非注记行不変）＋`note=(strip_note + DISCLAIMER) if strip_note else ""`（**非注记行は note=""＝pydantic default と同値＝response byte-identical**・注记行のみ N84 先例どおり note 付与）。
- 剥後 text の流れ＝N115 Stage 3 設計どおり：`_kundoku_result_for`（规则链零改动・行级缓存键は剥後 text で自然分離）→ `llm.modern_translate/glossary`（剥後 text）→ `db.save_kundoku`（剥後 text）→ response `normalize_shinjitai`（response 層・现行通り）。kana 分支（355）・tail rerun（363）・echo 直出（390–394）・no_tail（404）＝**一字不改**。
- **scope 実証＝engine 分支注记行恰 2 行**：8165 全行で engine 分支 ∧ `has_ruby_annotation`＝rikutou59-2・soji07-6 のみ（N115 census 同値・golden_4000 内 0 行）。

### 新测试（tests/test_night115_strip.py・名取自 N115 §5・8 条＝pytest 503→511）

- ①単元（引擎不加载）：`has_ruby_annotation` 真/假样本（ruby 夹注 True・纯汉文/dangling ）/空 （）/無仮名 （）/無括号假名文 False・**rongo 编号 6 行（归档実測）全 False**）・`strip_annotation` 冪等＋剥後形状（太公（たいこう）曰（いわ）く→太公曰く）・非注记行恒等（rongo 6 行・真·假名行）・**dangling ）/空 （）/無仮名 （） 保留**（＋归档 dangling ） 6 行 identity）・`detect_text_type` 本体不変（ruby 夹注行の kana 误判機構そのまま維持＝N84 前提）。
- ②端到端（TestClient・module fixture＝N84 先例）：**两残渣行**（rikutou59-2/soji07-6・归档 hakubun を実送信）＝`text_type=="kanbun"`・**`hakubun`＝返原文**・**got 無注记 span（I6）**・note 带 N116・**d 224→155／36→23**（lev 純 Python・前提 d0＝归档実測値断言込み）。
- ③防退化：**scope 外 engine 行**（rongo1442-1・rikutou26-5〔4000 归档外＝8165 归档から〕）got 与 night111 归档逐位一致＋note 無 N116＝**新增变差 0**・**kana 分支 echo 行**（toushisen006-10）got 与归档逐位一致＝N84 尾段路径不変・真·假名文本空串維持。
- 开発中 2 回断言修正（両方ともテスト側・実装無関係）：sonshi09-38 は白文自体が ruby span 含むため剥非恒等（I4 は「剥後 kana」が正断言）・rikutou26-5 は 4000 归档外（N111 記録済み＝8165 归档から取得）。

## 3. 验证（顺序＝实施→双口径真跑写新归档→README＋verify 源切换→verify→登记）

- **pytest tests -q＝511 passed（503+8・18.62s・exit 0）**（eval/night116_pytest_full.txt）。
- **golden_4000 真跑**（tools/night116_eval_4000.py・TestClient 完整链・基线＝night111_results_4000.json）：**13.455／24／0・diff 0 行＝全行 byte-identical**（140s・exit 0）→ **eval/night116_results_4000.json** 写入（night111 归档不触碰）。
- **golden_8165 真跑**（tools/night116_eval_8165.py・基线＝night111_results_8165.json・sum 前提 109934 実測一致）：**13.454／30／0・sum 109852（Δ−82）・diff 恰 2 行（rikutou59-2 224→155・soji07-6 36→23）・其余 8163 行 byte-identical・exact 30 不変**（約340s・exit 0）→ **eval/night116_results_8165.json** 写入。**N115 sim 予測（155/23・Δ−82）と実跑逐位一致**＝設計→実装の検証完結。
- **冒烟補助**（tools/night116_smoke.py・tools/night116_wscheck.py）：8165 不变量 I1 7914/7914・I2 8165/8165・I3 251/251・I4 sonshi09-38 剥後 kana・rongo 6 行 False・dangling ） 6 行 identity・**剥後首尾空白 0/251 行**（engine 入力 hygiene）。
- **词库 1531 不変**（pytest 词库断言 N75/N80/N82/N89 維持・backend/glossary* 一字未改）。
- **README**：header→実施链（Night 116 実施夜・分支起点 4e335ac・未合 master）＋テスト行 **511 passed**＋規則エンジン行 13.455/24 維持・口径注記を N116 archive に切替＋拡張評価行 **13.454/30**・diff 恰残渣 2 行記載——**与数字同提交**（verify 不校验 header）。
- **verify**（tools/verify_readme_facts.py・归档源常量 night111→night116 のみ切换＝N107/N111 先例）：**26/26 対上・exit 0**（eval/night116_verify.txt）。
- **項 9 状態（N113 §3 拍板表の該当行に対する本夜の実績記録）＝在庫→已実施（N116）**：実現値＝8165 sum **109934→109852（Δ−82）**・avg **13.464→13.454**・改善 2 行（rikutou59-2 −69・soji07-6 −13）・変差 0・exact 30 不変。残差の主成分は内容対齐ずれ（rikutou59-2＝exp は白文第 2 段のみ・soji07-6＝exp は尾段のみ＋got 頭の余分）＝**剥夹注管線の救済域は注记残渣のみ・対齐ずれは语料整形の別課題（N115 §2(B) 判定のまま管線外）**。**拍板表正文自体は未動（更新归在庫夜）**。

## 4. 登记＋移交

- **NIGHT_ARTIFACTS 加 116: ["night116_results_4000.json"]**（tools/accept_night.py・归档源切 night116・**115 不登记**＝設計夜先例）。accept_night.py 116：
  - **试跑**（実施未提交のまま＝repo_clean FAIL が設計行為）：**FAIL fail=1**（repo_clean 1 項・他门緑）→ ACCEPT_LOG 試跑行残置（eval/night116_accept_trial.txt）。
  - **终跑**（提交後）：**PASS fail=0 skip=0・七门全绿**（eval/night116_accept_final.txt・eval/accept_night_116.json＝final 上書き）。**両行とも ACCEPT_LOG に残す**＝N100/N104/N109/N113/N114 先例。
- **提交＝2 本（主＋wrap-up）・未合 master・未推远程**（rev-list ahead of origin＝2・N115 と同じ待合并状態。**合并夜で N115・N116 を顺序合流**＝N108 先例）。
- **坑位（本夜発生分）**：
  1. **N115 提交メッセージの「ROADMAP Night 115 行」は night115-annotation-design 分支側のみ**（未合 master＝本夜分支の ROADMAP は Night 113 まで・`git show 56cd695 --stat` で 1 行追加を確認）。本夜の ROADMAP 行は本分支に追記＝合并時に N115 行と接缝（byte-safe union＝N114 先例の門）。
  2. **response の `hakubun=text` は text 再代入で剥後文になってしまう**——拍板③ 返原文のため `hakubun_orig` 退避が必須（任务書の 2 行插入だけだと hakubun が剥後 text を返す回帰バグ）。非注记行は同値なので response 不変。
  3. **JSON dump に set を入れない**（night116_eval_8165 の changed_d_vs_n111 を初版 set comprehension で書きかけ・N115 坑位 5「JSON に入れるものの键は最初から str」の値版）。sorted list に修正。
  4. **sonshi09-38 は「剥非恒等」行**——白文自体が ruby span 含む（N115 形態 3＝括号外混在との三重混在）。I4 の正断言は「剥後も detect=kana（管線外維持）」で「strip identity」ではない（テスト初版で誤断言・実装は無関係）。
  5. CJK console redirect・多行 python -c 禁・UTF-8 落盘（N113/N115 継承）・SHIFT_LOG は UTF-8 バイナリ追記（CRLF）。長跑は exit code 判定（4000 exit=0・8165 exit=0 実測）。
- **移交（次夜以降）**：合并夜＝night115-annotation-design（2 提交）＋night116-annotation-impl（2 提交）を --no-ff 順次合流（接缝候補＝ROADMAP・SHIFT_LOG・ACCEPT_LOG・NIGHT_ARTIFACTS コメント行）；N115 設計の残置＝sidecar／输出重贴（拍板① の他選択肢）は**不実施**（丢弃確定）；rikutou59-2/soji07-6 の対齐ずれ残差＝语料整形別工程；項 9 の拍板表正文更新＝在庫夜。

## 交付对照（任务书「交付」の数値欄）

- **Night 116 完成，全部验收通过。**
- 开工：HEAD＝4e335ac ✓・pytest 503 passed ✓・分支 night116-annotation-impl ✓（自 master 分出・rev-list=0）・REPORT_NIGHT115 §0/§4/§5 读过 ✓・用户拍板：注记丢弃＋has_ruby_annotation ✓（＋hakubun 返原文）。
- 实施：backend/main.py 两处 ✓（+32−1・helpers 168–178・engine 分支 445–450・response 挂钩 2 行）・detect_text_type 本体・kana 分支・规则链零改动 ✓・hakubun 返原文 ✓（hakubun_orig 退避）・新测试 **8** 条。
- 验证：pytest **511** passed（503+8）・golden_4000 **13.455／24／0**（全行 byte-identical・diff 0 行）✓・golden_8165 **13.454／30／0**（sum 109852・diff 恰 2 行：rikutou59-2 224→155・soji07-6 36→23）✓・verify **26/26** exit 0 ✓・词库 1531 不动 ✓。
- 验收：accept 116 **PASS**（试跑 FAIL＝repo_clean 1 項設計行為・final fail=0 skip=0 七门全绿）・項 9 状态记入 REPORT_NIGHT116 §3（在庫→已实施 N116・Δ−82）・分支 **night116-annotation-impl** ＋ **2 提交**（主＋wrap-up）・未合 master・未推远程（待与 N115 一起合，等你手推）。报告见 REPORT_NIGHT116.md。
