# REPORT_NIGHT73 — Rule M 挖词＋上线（ZCode 并行线，night72-rulel 单会话续）

日期：2026-11-22（Night 73）；开工 HEAD：`5e54265`（= N72 wrap-up 点）；分支 `night73-rulem`（独立目录 `D:\kanbun-rulel` 续用，AutoClaw 的 N71 仍在主仓跑整本 OCR＋guwenbert——本夜与其零接触）；未合 master、未推远程。

## 0. 结果一句话

**Rule M 8 条收录（禁止族 guard 分割＋J/K 分工补完）＋模拟全 0 变差＋组合 167 行改写／改善 139／变差 0／幂等坏 0**；TestClient 双口径真跑与离线模拟**逐位一致**——golden_4000 **avgDist 13.544→13.517／exact 24／改写 65（双向 0 差）**、golden_8165 **14.583→14.546／exact 30／改写 167（双向 0 差）**；pytest **283→307**；accept 73 **PASS（fail=0 skip=0）**；verify **17/17 exit 0（テスト行 pytest 計数断言を新設＝N72 移交⑥対応）**。单条模拟 18 候选＝収 8（全 0 変差）＋拒 10（変差拒 8：陳→陣 30・べき 6・莫かれ 1・若し 1・莫 10・莫し 14・勿 21・勿し 25；過門不採用 2：はある→或・はそれ→も其れ）＋B2 候補不成立（ことな/るべ＝opcode 人工物）。备选②＝第二语源第二轮 8 候选**阴性**（最强新线索 Kanbun-LM 3421 句対死在同源：数据源＝kanbun.info 唐詩選）。

## 1. 开工核对与隔离

- `cd D:\kanbun-rulel`（N72 建立的 clone 续用，未进主仓）→ `checkout -b night73-rulem night72-rulel` → HEAD=`5e54265` ✓、tracked 零改动 ✓（仅未跟踪 `.night72_deps/`＝N72 遗留隔离依赖目录）
- git 身份 zwork/zwork@local 在 clone 内持久（N72 配置残留 .git/config，无需重配）
- pytest 首跑 **283 passed**（83.3s）✓；SHIFT_LOG 全程 `'ab'` 追加（heartbeat 工具 byte 计数打印 size 98580→99120 前缀零改动）
- 方法论输入：REPORT_NIGHT72.md（方法＋移交 7 项）＋REPORT_NIGHT70.md §2（K 世代 guard 空语义）＋eval/night69_sources.md（备选②第一轮）

## 2. 挖词（②）

- 基线 = `eval/night72_results_8165.json`（L 后链尾真机归档）。链尾断言：results/golden 同序；L combo 行 got==night72_combo.new_text；非 combo 行 got==night70 归档（L 只改 combo 行的再验证，全部通过）
- `tools/night73_mine.py` → `eval/night73_mine.json/.txt`：
  - **A 字符 delta**：L 后的巨型残量＝不(Δ163)・莫(Δ156)・勿(Δ81)・奈(Δ65)・陣(Δ77)・将(Δ248)——got 侧几乎为 0 的 4 字（不/莫/勿/奈）指向「禁止・反问」构文层
  - **B 假名串 delta**：顶部仍为 N24/25 定性结构差（して/なりて/するを…，全部标【结构】）；词形级＝とも 162（拒案维持）・さず/へる（活用结构）
  - **B2 opcode 词级挖（本夜新切面）**：SequenceMatcher replace 块、got 侧纯假名（≥2）×exp 侧汉字头 → (kana, 汉字头) 对计数＋守り字新旧两形命中実測——直接命中 そく→即、はある→或、ゆき→之、はそ→其、ことなかれ→莫、なかれ→莫/勿、もし→若、るべ→可 等 17 组
  - **C 拒案・移交复查**：とも 残量 224（拒案維持）／**がため 残量 0 行（L 収録後残量検証 ✓）**／べからず 残量 83（gap 收口済）／**はざる者＝恰 2 行（roushi33-2/utsuryo06-2）計数核实（本夜不収、移交維持）**
  - **D SHINJITAI 1:1 残量＝0 対（N69/N72 结论維持）**
- `tools/night73_probe.py` → `eval/night73_probe.json/.txt`（11 词形×守り字新旧两形＋禁止族 莫/毋/勿/無 4 字并查＋奈/陣/将/不 4 字逆向探查）；候选清单 `eval/night73_candidates.txt`（収 8／拒 9／不作为候选 5 组）
- **守り字新旧字体并查（N72 移交①）成文执行**：そく→即ち の守り＝即 9＋卽 3——卽 は SHINJITAI_MAP 逆引きで自動展開、単查 即 なら 3 行取り逃す
- **禁止族 4 字并查的发现**：なかれ 残量 115 行の白文守り字＝莫 84／勿 32／毋 0（毋 行は I が全部処理済）——I 毋かれ と同構の guard 分割で莫/勿が取れる
- **链不变式（本夜新确认）**：got に残る仮名 は E〜L の guard 未命中行のみ——M の guard 分割は早期系列と構造的に衝突しない（もし∧如／なかれ∧毋／はそれ∧夫/只／ごとし∧如/若 の重複は 0 行を実測再確認）；sim 入力＝真机链尾出力なので真跑一致性は構造的に保証

## 3. 模拟门（③）

- `tools/night73_sim.py`（night72_sim 机制照抄：lev/apply_one/run/idempotent，基线 = night72 真机 8165；C 库＋d0 缓存沿用，200 对等价抽查）
- **性能注记**：d0 缓存 6s（N72 加速机制そのまま、45 分钟问题不在）；实跑对照（④）的 TestClient 全量真跑因 N71 满负荷 600s 超时一次（324s/4000＋~470s/8165）→ 自动转后台继续跑完，未跳步未加速重写
- **收录 8 条（单条全 0 变差）**：

| 规则 | 护栏（白文） | 改写 | 改善/变差 | Δ |
|---|---|---|---|---|
| なかれ→勿かれ | 勿 32/32 | 32 | 32/0 | −0.007 |
| そく→即ち | 即/卽 12/12 | 12 | 12/0 | −0.004 |
| はあるいは→或いは | 或 12/12 | 12 | 12/0 | −0.004 |
| ゆき→之 | 之 5/5 | 5 | 5/0 | −0.001 |
| はそれ→其れ | 其 10/10 | 10 | 9/0 | −0.002 |
| 何のごとし→奈何 | 奈 45/45 | 45 | 45/0 | −0.015 |
| 何のごとく→奈何ぞ | 奈 3/3 | 3 | 2/0 | −0.001 |
| もし→若 | 若 55/55 | 55 | 28/0 | −0.004 |

- **拒案（0 变差门／字形死／不採用，逐行证据 eval/night73_sim.txt）**：なかれ→莫かれ（**1 変差 kokyo09-5 15→16**——白文 莫 は「莫大於」構文、exp 莫し と got こと余計で正 guard 不可達；莫 白文行は exp 莫かれ/莫し 混在で guard 分割不能）、なかれ→莫（10 変差）／莫し（14）／勿（21）／勿し（25）＝落选字形 4 条（同一 kana 一条のみ＝N68 ことごと死条目教训）、はある→或（**過門同数 12/12/0**——短 key の誤発火リスク上位で不採用、長 key 或いは を採用）、はそれ→も其れ（過門 9/0——其れ repl の delta −0.002 ＞ も其れ −0.001 で不採用）、もし→若し（**1 変差 kyugyu-2 66→67**——got もし ↔ exp 冒頭 仮令 の前置構文；裸形 若 は共有字論証で過門）、べき→可き（**6 変差 omoi-1 等**——exp 自写仮名 べし/べき、N55/N72 §8-3 gap 再確認）、**陳→陣（30 変差**——kanbun.info 通假歸一の疑いを exp/got 実数で検証：got 陳 100／exp 陳 39＝exp 側自書有りで無条件文字置換不可；guard 機構は kana 規則のみで kanji→kanji は表現不可→SHINJITAI 拒案）
- 多守り行 rinkiohen-2（莫∧勿・白文内両 なかれ）＝勿-first で全体改善（莫側も lev は 1 改善）→ 0 変差；もしの長詞 もしも/もしや/もしか＝I 同款で本夜语料 0 行（未来安全弁）
- 组合幂等 bad=0；双口径离线真算：**4000 改写 65／改善 55／变差 0、13.544→13.517；8165 改写 167／改善 139／变差 0、14.583→14.546**；s4000 55／s3908 83／s257 1；shibu02 78／漢詩 4
- repl 终字形断言：`normalize_shinjitai(repl)==repl` 8/8（＋拒案 4 repl も同検証）
- **guard=() 無条件規則は本系列なし**（陳→陣 のような文字置換は候補段階で拒案成立——K 世代の空 guard 設計とは別問題として README/test に明記）

## 4. 上线＋真跑对照（④）

- `backend/kundoku_rules.py`：`M_KANA_TO_KANJI` 8 条（序=COMBO_ORDER）＋`M_LONGER_WORDS`（もし＝I 同款、他 7 条 probe/sim 實測无更长词冲突）＋`style_kana_to_kanji_m`（K 世代同款 `if guard and hb and not any(...)`）；`style_fix_with_hakubun` 链尾接 M（L 之后）。拒案死因（莫かれ 1 変差行・字形落选・陣 30 変差・若し 1 変差・べき 6 変差）写入 M 块注释存档
- `tests/test_night73_rule_m.py` **24 项全过**：每条正例（実語料行型 moshisono-1/katsumoku-4/keimei-4（旧字体卽）/rongo0223-1/daigaku08-2/rongo0604-1/goshi02-1/kiyu-7/enou-1/enjaku-2）＋無護栏反例（一字不動）＋**莫 白文行不触锁**（kokyo09-5 型＋莫∧勿多守り行勿-first）＋長語マスク（もしも/もしや/もしか）＋空白文発火（E〜L 世代同语义）＋表整形性（8 条・repl 終字形・guard=() なしの明示）＋拒案不复活（べき/るべ/ことな/はある/陳・なかれ repl 勿かれのみ・もし repl 若のみ・はそれ repl 其れのみ）＋**链不変式ロック**（もし+如 は I 先勝／はそれ+夫 は I 先勝）＋链序 L→M＋幂等＋现代句探针＋经典句回帰。全量 pytest **307 passed**（283＋24，89.1s）
- **TestClient 真跑**（`tools/night73_eval.py`：期望值从 `night73_sim.json` **读入不手抄**；基线自检 night72 归档 avgDist==sim avg_old ✓；monkeypatch save_kundoku）：
  - golden_4000：**avgDist 13.517／exact 24／error 0**；改写 **65＝预测 65（双向 0 差）**／改善 55／变差 0／持平 10
  - golden_8165：**avgDist 14.546／exact 30／error 0**；改写 **167＝预测 167（双向 0 差）**／改善 139／变差 0／持平 28
  - 进程内确定性：8165 前 4000 行与 4000 单跑**逐位一致**；error→恢复 0／仍 error 0
  - ⑯ 分段：漢詩 6.986・孝経 8.986・詩経 5.108・論語 26.367；本夜 8 条の改写は禁止族・奈何族が論語/故事/漢詩に散布（s4000 55／s3908 83）
- **GT CER 逐位不变**（结构性证明，N63 §4/N70 §3/N72 §4 同款论证链）：OCR/GT 链全部输入文件（eval/night68_gt_cer.json、eval/night49_gt_lines.json、eval/ocr_gt_100.tsv 等）tracked 逐位未动（git status 実査：本夜 tracked 改动＝README/ROADMAP/SHIFT_LOG/kundoku_rules/accept_night/verify の 6 件のみ、OCR 系入力含まれず）、本夜唯一产品代码改动＝`kundoku_rules.py` の訓読表示层（OCR 管线不经过）→ CER raw **0.3568**／norm **0.3053** 逐位不变
- **guwenbert 本夜未跑**：原因——N71（AutoClaw 主仓会话）满负荷継続＋任务书本夜明令禁 OCR／禁 guwenbert 全量（本夜影响面＝假名散布段，已由 golden_8165 全量双对照逐位覆盖，N68 §7 同口径）

## 5. 拒案表（0 变差硬门，模拟门逐行证据）

| 候选 | 改写 | 改善/变差 | 拒因（一句话） |
|---|---|---|---|
| なかれ→莫かれ（guard 莫） | 84 | 68/**1** | kokyo09-5 15→16：白文 莫 は「莫大於」構文・exp 莫し——莫 行は exp 莫かれ/莫し 混在で guard 分割不可達 |
| なかれ→莫（裸形） | 84 | 66/**10** | gabei-2 等 exp 莫かれ 行で かれ 落とし→字形死 |
| なかれ→莫し | 84 | 68/**14** | 同上逆側→字形死 |
| なかれ→勿（裸形） | 32 | 6/**21** | moshisono-1 等 exp 勿かれ 行→字形死 |
| なかれ→勿し | 32 | 6/**25** | 同上→字形死 |
| はある→或（短 key） | 12 | 12/0 | **過門**だが長 key はあるいは と同効果——誤発火リスク上位（「限りはある」等）で不採用 |
| はそれ→も其れ | 10 | 9/0 | **過門**だが 其れ repl（Δ−0.002）が も其れ（−0.001）に劣る→不採用 |
| もし→若し | 55 | 34/**1** | kyugyu-2 66→67：got もし ↔ exp 冒頭 仮令 の前置構文；裸形 若 で翻案収録 |
| べき→可き | 103 | 86/**6** | omoi-1/p-gekirin-1/kenro-1/mobosansen-1 等 exp 自写仮名 べし/べき——N55 gap 実数再確認 |
| 陳→陣（無条件文字置換） | 75 | 24/**30** | exp 側自書 陳 39 回（ichigenchi-1/enjaku-1 等）——1:1 表不可・guard は kana 規則のみで kanji→kanji 表現不可＝SHINJITAI 拒案 |
| ことな→勿/莫・るべ→可（B2 対） | 0 | — | 预检 0 行＝opcode アラインメント人工物（ことなかれ/べからず 系の分割痕）→候補不成立 |

N72 移交の复核終局：はざる者 2 行＝計数のみ核实（本夜不収・移交維持）、とも 224 行＝拒案維持（不触）、がため＝残量 0（L 収録完遂の検証）。

## 6. README / verify / ROADMAP 同步（⑤）

- README 数字行 4 处：数字节头（`night73-rulem`・Night 73・**主提交 `d338b21`**——wrap-up 提交里按 `git log -1` 取数写入）、テスト行 **283→307 passed**、規則エンジン行（**13.517**／**24/4000**＋N73 Rule M 注记＋`eval/night73_results_4000.json` 口径）、ルールチェーン行（Rule M 第 9 系列・**8 語**追加・禁止族 guard 分割の説明）
- `tools/verify_readme_facts.py`：Rule M 计数行追加＋归档源 night72→night73 切换（README 数字行更新的必要伴随、N68/N70/N72 同款先例）＋**テスト行 pytest 計数断言を新設**（`pytest --collect-only -q` 実行カウント 307 と README **307 passed** を照合＝N72 移交⑥対応）→ **17/17 OK、exit 0**
- ROADMAP.md 末尾 CLOSED 一行

## 7. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `73: ["night73_results_4000.json"]`（仅此一条，67/68/70/72 同式）
- accept 73：**PASS（fail=0 skip=0，140.8s）**——repo_clean ✓／pytest **307 passed = 307 collected**（65.8s）／eval_integrity（night73_results_4000.json 実查：id 唯一・自报数一致・expected 未改）✓／rule_regression ✓／engine_smoke ✓／perf_envelope（短句中位 12ms）✓／order_rate off **98.57%**（+0.00pp）／on **98.63%**（+0.00pp）退化页 0 ✓。1 回運行・SKIP なし（N72 首跑の git-unavailable skip は PATH 事前設定で回避）
- 备选②＝`eval/night73_sources2.md`：第二轮 8 候选**阴性**——最大新线索 nlp-waseda/Kanbun-LM（世界初の白文×書き下し対 3421 句・GitHub 無墙・成对体例齐备）が**数据源＝kanbun.info 唐詩選**で同源大重合（toushisen 行 ≈100% 重合）＋仓库无 LICENSE；KOKO 訓点資料訓読文コーパスは 1 经実装 <1000＋ninjal 域半阻断；阳性 0 件→不抓取、拍板事项なし

## 8. 移交

1. **opcode 词级挖（B2 切面）建议成文规矩**：本夜 8 条中 6 条（そく/はあるいは/ゆき/はそれ/何のごとし/もし）が B2 直接命中——N68/69/72 の「假名串 delta」切面より词边界精度が高い（align 崩れは预检で人工物と判別可能）。次夜の挖词は B2 を主切面に推す
2. なかれ→莫かれ の復活条件：kokyo09-5 1 行のみが死因（白文 莫 が「莫大於」構文）。80+ 行が exp 莫かれ/莫し で改善待ち——将来的に白文構文判別（莫＋大 co-occurrence guard 等）が可能になれば莫 rule は 80 行規模の再候補
3. 陳→陣 は SHINJITAI に登録不可（exp 自書 39 回）——kanbun.info 通假歸一を取り込むには guard 付き kanji→kanji 規則（新機構）が要る。75 行・30 変差の実数は night73_sim に归档済み
4. べき/るべ/ことな 族：N55/N68/N72 に続き本夜も変差で拒（6 変差・実数归档）——べ-family の结构性 gap は完全収口、再試推奨しない
5. はざる者 2 行（roushi33-2/utsuryo06-2）：key 含漢字「者」破純 kana 惯例の件は N72 から引き続き保留（拍板待ち、計数不变）
6. M の repl 裸形論証（もし→若）：exp 実書形（若、×2）＋共有字論証＋0 変差実測——「若し が 1 変差で落ちて裸形が通る」は N72 がため→為 と同型の翻案パターン、次夜以降の落选字形救済に転用可
7. pytest 計数断言（`--collect-only -q` 照合）を verify に追加済み——N70 型のテスト行漂移は今後機械的に落第する

## 9. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；全局 site-packages 一行未动 ✓（C 库は N72 の .night72_deps 隔离目录をそのまま利用、本夜 pip 実行なし）
- 只动允许清单内文件：backend/kundoku_rules.py、tests/test_night73_rule_m.py、tools/night73_heartbeat/mine/probe/sim/eval.py、tools/accept_night.py（仅 73 一条）、tools/verify_readme_facts.py（Rule M 计数行＋归档源必要伴随＋pytest 计数断言＝移交⑥、README 数字行の必要伴随）、README.md（数字行＋表头）、ROADMAP.md（末尾一行）、SHIFT_LOG.md、ACCEPT_LOG.md（accept 自動追加分）、eval/night73_*（candidates/mine/probe/sim/combo/results_4000/results_8165/sources2/accept_night_73）、REPORT_NIGHT73.md ✓；scratch 文件（夜中 31 個）用后即删 ✓
- 与 N71 零接触：本夜 D:\kanbun-kakikudashi に一度も入らず ✓；无 OCR 推理、无 guwenbert ✓；网络＝web 检索/页面读取のみ（备选②调研）、exec 直连なし ✓
- SHIFT_LOG 纯追加（'ab' 制・heartbeat 工具が byte 前後 print）✓；本地分支两提交、**未合 master、未推远程** ✓；审查器未拦任何文件 ✓

## 10. 偏差注记

1. 实跑（④）TestClient 全量真跑が N71 满负荷で 600s 超时→自动转后台跑完（4000 324s＋8165 ~470s）——「45 分钟規則」の対象段階（模拟门）は d0 缓存 6s で該当なし、加速重写不要；后台移行は ZCode 実行環境の標準挙動で、工程は跳していない
2. verify の pytest 計数断言は「verify_readme_facts.py（仅 Rule M 计数行＋pytest 计数断言）」の任务書許可にそのまま沿う（N72 移交⑥の実装）
3. はある→或／はそれ→も其れ は模拟门で**過門**（0 変差）だが品質基準で不採用——「収録数 8」は COMBO_ORDER 採用分のみを数え、過門不採用は拒案表に分けて実数归档（N72 がため→が為「過門だが劣る」の前例同式）。§0 初版の「拒案 9 项」は計数誤り（枚举は 10 項）→ 10 に修正（本 wrap-up で amend、master 未合・未推送のため安全）
4. 本夜工具用量：web_search 5 回＋web ページ读取 3 回（备选②调研のみ、抓取なし）；pip 0 回；OCR/guwenbert 0 回
