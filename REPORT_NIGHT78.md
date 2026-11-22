# REPORT_NIGHT78 — Rule N 挖词＋上线（ZCode 并行线，night78-rulen 单会话）

日期：2026-11-22（Night 78）；开工 HEAD：`807ad7d`（= N73 wrap-up 点）；分支 `night78-rulen`（独立目录 `D:\kanbun-rulel` 续用，AutoClaw 的 N71 仍在主仓跑整本 OCR＋guwenbert——本夜与其零接触）；未合 master、未推远程。

## 0. 结果一句话

**Rule N 13 条收录（ことな族活用形分割 5 条＋現代語副詞族 8 条）＋模拟全 0 变差＋组合 97 行改写／改善 85／变差 0／幂等坏 0**；TestClient 双口径真跑与离线模拟**逐位一致**——golden_4000 **avgDist 13.517→13.495／exact 24／改写 55（双向 0 差）**、golden_8165 **14.546→14.526／exact 30／改写 97（双向 0 差）**；pytest **307→337**；accept 78 **PASS（fail=0 skip=0）**；verify **18/18 exit 0（Rule N 计数行新設）**。单条模拟 22 候选＝収 13（全 0 変差）＋拒 9（変差拒 1：koto_full umbrella 复现 kokyo09-5 死行；過門不採用 4：しばしば→屢・はいよいよ→弥・いよいよ→弥・〔＋たま→偶〻 は無益拒〕；無益拒 4：き/ぶ/く/つことなかれ）。备选⑥＝なかれ→莫かれ 复活条件调研（`eval/night78_mokaku.md`）：post-N 目標 16 行・12 改善／3 same／**1 変差（kokyo09-5 のみ）**，「莫＋大 co-occurrence guard」判別式仮説を**実測で否定**（kowokaete-4 莫大焉 行は こと莫かれ で陽性通過）——復活は排除 guard／kanji→kanji 機構の追加待ち（拍板）。

## 1. 开工核对与隔离

- `cd D:\kanbun-rulel`（N72 建立・N73 续用的 clone）→ `checkout -b night78-rulen night73-rulem` → HEAD=`807ad7d` ✓、tracked 零改动 ✓（仅未跟踪 `.night72_deps/`＝N72 遗留隔离目录＋`eval/night74_dict_cache/`＝词库链遗留，均不碰）
- git 身份 zwork/zwork@local 在 clone 内持久（无需重配）
- **pytest 首跑 307 passed（98.1s）——任务书记载 283 与实测不符**：283 是 N72 线（M 加 24 测试前）的旧数；开工点 `807ad7d` 是 N73 wrap-up，N73 报告 §4/§7 与 accept 73 归档均为 **307**（283＋24），测试文件清单（`git ls-files tests`）止于 `test_night73_rule_m.py`、词库链测试不在本线——基线与文档完全自洽，如实记档后按 307 继续（偏差注记 1）
- SHIFT_LOG 全程 `'ab'` 追加（heartbeat 工具 byte 计数 99308→100338、前缀零改动）＋每小时自动心跳（`tools/night78_heartbeat_loop.py`）
- 方法论输入：REPORT_NIGHT73.md（方法＋移交 7 项）＋REPORT_NIGHT72.md §8（移交）＋引擎内 N58/N68 的なかれ系拒案注记

## 2. 挖词（②）

- 基线 = `eval/night73_results_8165.json`（M 后链尾真机归档）。链尾断言：results/golden 同序；M combo 行 got==night73_combo.new_text；非 combo 行 got==night72 归档（M 只改 combo 行的再验证，全部通过）
- `tools/night78_mine.py` → `eval/night78_mine.json/.txt`：
  - **A 字符 delta**：M 后巨残＝為 Δ461（动词活用结构差・規則層不可達）・将 Δ248（白文方↔exp 将＝kanji→kanji）・可 Δ352（已覆盖）・其 Δ169・**不 Δ163**（exp 侧 不知/不幸 等词形成立 vs got 知らざる/幸ならず＝词组级重构）・**莫 Δ156**（ことな族＋なかれ 残量＝本夜主矿脉）
  - **B 假名串 delta**：顶部仍为 N24/25 定性结构差（して/なりて/するを…，全部标【结构】）
  - **B2 opcode 词级挖（主切面・N73 移交①）**：M 后残量対＝ことなかれ→莫 26・るべ→可 24・べきか→可 23・なかれ→莫 10・して→使 7・ことな→莫 6・しむ→使 5・とも→与 5・して→問 5——べ族/とも/して族全部是已收口/结构差；**ことな族是唯一未试新矿脉**
  - **C 拒案・移交复查**（任务书②指定）：とも 残量 224（拒案維持）／はざる残量 19 行・**はざる者＝恰 2 行（roushi33-2/utsuryo06-2）計数核实（拍板待ち・本夜も不収）**／**がため 残量 0 行（L 収録後残量検証 ✓ N73=0 复核）**／べ族 gap 收口済计数（べからず 83・べき 105・るべ 152——N73 移交④ 再試推奨しない）
  - **D SHINJITAI 1:1 残量＝0 対（N69/N72/N73 结论維持）**
- `tools/night78_probe.py` → `eval/night78_probe.json/.txt`（**ことな族全行取证**：128 行含 ことな、got_form 59 种活用形、**exp 自書 kana 0 行・白文守り 100% 覆盖**（莫/勿/毋/無）＋exp 字形 3 系混在（こと莫かれ/こと莫し/莫し）＋B2 長尾対 33 組＋逆向探查（不/無/与/令/必/曰/則/於/使/将）＋got 側 kana 候补计数（おいて/すなわち/かならず/いはく/**全部 got 0**——A 切面大 Δ 全是 kanji 选择差或空输出行））；`tools/night78_kokyo.py` → 死行前缀归属＋空 got 249 行计数＋現代副詞小族 got/exp 互补计数（しばしば 4/0・屢 0/4、やや 5/0・稍 0/5、たま 3/0・偶 3/6、ほとんど 3/0・殆 12/15、いよいよ 9/0・弥 4/12、なんぞ残量 7/胡 42/49）
- 候选清单＝night78_sim.py CANDIDATES 22 条（収 13／拒 9）
- **守り字新旧字体并查（N72 移交①）成文执行——且首次在 sim 内被抓到实际违规**：いよいよ族首版 guard 只写新字体 弥、白文写旧字体 **彌** → 0 発火，precheck 显示 新旧両形命中 9 行 → 修正为 guard（弥，彌）（M そく→即ち 的 即/卽 同款）；其余守り字（莫/屢/殆/稍/偶/胡）实测无双形问题

## 3. 模拟门（③）

- `tools/night78_sim.py`（night73_sim 机制照抄：lev/apply_one/run/idempotent，基线 = night73 真机 8165；C 库＋d0 缓存沿用（d0 2–3s），200 对等价抽查）——**45 分钟问题不在**（单条全 0s 级）
- **收录 13 条（单条全 0 变差）**：

| 规则 | 护栏（白文） | 改写 | 改善/变差 | Δ |
|---|---|---|---|---|
| することなかれ→すること莫かれ | 莫 16/16 | 16 | 12/0 | −0.001 |
| ざることなかれ→ざること莫かれ | 莫 10/10 | 10 | 7/0 | −0.001 |
| なることなかれ→なること莫かれ | 莫 10/10 | 10 | 8/0 | −0.001 |
| うことなかれ→うこと莫かれ | 莫 9/9 | 9 | 5/0 | −0.001 |
| ることなかれ→ること莫かれ | 莫 61/61 | 61 | 53/0 | −0.007 |
| はいよいよ→弥〻 | 弥/彌 6/6 | 6 | 6/0 | −0.005 |
| いよいよ→弥〻 | 弥/彌 9/9 | 9 | 9/0 | −0.005 |
| しばしば→屢〻 | 屢 4/4 | 4 | 4/0 | −0.002 |
| ほとんど→殆 | 殆 3/3 | 3 | 3/0 | −0.001 |
| はやや→稍く | 稍 2/2 | 2 | 2/0 | −0.001 |
| やや→稍 | 稍 5/5 | 5 | 5/0 | −0.001 |
| たま→偶 | 偶 3/3 | 3 | 3/0 | −0.001 |
| なんぞ→胡 | 胡 7/7 | 7 | 7/0 | −0.002 |

- **ことな族的设计要点**：exp 侧字形 3 系混在（こと莫かれ／こと莫し／莫し）で umbrella key ことなかれ→こと莫かれ は死行 **kokyo09-5**（白文「嚴父莫大於配天」＝**すことなかれ** 行・15→16 変差）で拒（N58/N68/N73 の なかれ→莫かれ 拒案と同死因の**機構境界再現**）；prefix keys は死行を避けて全 0 変差——**ることなかれ 1 本で なる/する/ざる/〜る 系 61 行を substring 覆盖**（repl ること莫かれ は各 prefix rule の出力と文字列同型＝順序独立、**2 順序実測同値** 55/97・13.495/14.526 逐位一致）
- **拒案（0 变差门／字形落选／無益，逐行证据 eval/night78_sim.txt）**：koto_full umbrella（**1 変差 kokyo09-5 15→16**——機構境界実証のための対照測定）、き/ぶ/く/つことなかれ 4 条（2/2/2/1 行、**0 変差だが Δ−0.000＜N69 収録線 −0.001＝無益**——N73 hezu 同款）、しばしば→屢（**過門 −0.002 同数**——exp 実書形 屢〻 ×3 の方が強く落选）、はいよいよ→弥／いよいよ→弥（**過門 −0.004**、弥〻 −0.005 に劣る→落选字形＝N73 其れ/も其れ 同款）、たま→偶〻（無益 −0.000、偶 −0.001 を採用）
- 多守り行：kikyorainoji-52（胡∧何）1 行のみ＝K 先勝で全改善（なんぞ→何ぞ は K の守り外…実測は N の 胡 が発火・変差なし）；ことな族の 莫∧勿／莫∧毋 多守り行＝0 行（I/M が事前処理済みの链不变式）
- 组合幂等 bad=0；双口径离线真算：**4000 改写 55／改善 45／变差 0、13.517→13.495；8165 改写 97／改善 85／变差 0、14.546→14.526**；s4000 45／s3908 40／s257 2；shibu02 25／漢詩 26
- repl 终字形断言：`normalize_shinjitai(repl)==repl` 13/13（＋拒案 repl も同検証）
- 本系列も **guard=() 無条件規則なし**（現代語副詞族も全て白文 guard 付き）

## 4. 上线＋真跑对照（④）

- `backend/kundoku_rules.py`：`N_KANA_TO_KANJI` 13 条（序=COMBO_ORDER、M 之后）＋`N_LONGER_WORDS`（**全 13 条空 tuple**——probe/sim 實測无更长词冲突：なんぞ は なんぞは/なんぞの 2 行を含むが 7 行全改善でマスク不要）＋`style_kana_to_kanji_n`（K 世代同款 `if guard and hb and not any(...)`）；`style_fix_with_hakubun` 链尾接 N（M 之后）。拒案死因（umbrella 変差行・無益 4 条・落选字形）写入 N 块注释存档
- `tests/test_night78_rule_n.py` **30 项全过（首跑一発）**：每条正例（実語料行型 isshoko-3/kenro-1/kamireikei-1/kokyo09-3・kowokaete-4（**莫大構文行の 0 変差改善を正例で固定**）/kanae-2/rongo1118-1/karewoshiri-3/rongo0910-1（**旧字体 彌 guard**）/toushisen138-11/toushisen227-2/manwojisu-1 等）＋無護栏反例（一字不動）＋**死行不触**（kokyo09-5＝すことなかれ は N 全键非該当を文字列で実証）＋収録線下不触（き/ぶ/く/つことなかれ）＋空白文発火（E〜M 世代同语义）＋表整形性（13 条・repl 終字形・guard=() なし・**新旧両形 guard 弥/彌 の明示**・はやや/はいよいよ 長 key 先行順）＋拒案不复活（umbrella/すことなかれ/き・ぶ・く・つ/落选字形 屢・弥・偶〻）＋**链不変式ロック**（盍∧胡 は K 先勝／莫∧勿 は M 先勝／莫∧毋 は I 先勝）＋链序 M→N＋幂等＋现代句探针＋经典句回帰。全量 pytest **337 passed**（307＋30，91.5s）
- **TestClient 真跑**（`tools/night78_eval.py`：期望值从 `night78_sim.json` **读入不手抄**；基线自检 night73 归档 avgDist==sim avg_old ✓；monkeypatch save_kundoku）：
  - golden_4000：**avgDist 13.495／exact 24／error 0**；改写 **55＝预测 55（双向 0 差）**／改善 45／变差 0／持平 10
  - golden_8165：**avgDist 14.526／exact 30／error 0**；改写 **97＝预测 97（双向 0 差）**／改善 85／变差 0／持平 12
  - 进程内确定性：8165 前 4000 行与 4000 单跑**逐位一致**；error→恢复 0／仍 error 0
  - ⑯ 分段：漢詩 6.978・孝経 8.952・詩経 5.088・論語 26.318・故事 20.497；本夜 13 条の改写は s4000 45／s3908 40（ことな族が論語/故事/漢詩に散布、現代語副詞族が漢詩段に集中）
- **GT CER 逐位不变**（结构性证明，N63 §4/N70 §3/N72 §4/N73 §4 同款论证链）：OCR/GT 链全部输入文件（eval/night68_gt_cer.json、eval/night49_gt_lines.json、eval/ocr_gt_100.tsv 等）tracked 逐位未动（主提交 `git show --stat` 實査：本夜改动＝README/ROADMAP/SHIFT_LOG/kundoku_rules/accept/verify/tests/tools＋eval/night78_* 新增のみ、OCR 系入力含まれず）、本夜唯一产品代码改动＝`kundoku_rules.py` の訓読表示层（OCR 管线不经过）→ CER raw **0.3568**／norm **0.3053** 逐位不变
- **guwenbert 本夜未跑**：原因——N71（AutoClaw 主仓会话）满负荷継続＋任务书本夜明令禁 OCR／禁 guwenbert 全量（本夜影响面＝假名散布段，已由 golden_8165 全量双对照逐位覆盖，N68 §7 同口径）

## 5. 拒案表（0 变差硬门／収録線，模拟门逐行证据）

| 候选 | 改写 | 改善/变差 | 拒因（一句话） |
|---|---|---|---|
| ことなかれ→こと莫かれ（umbrella） | 81 | 67/**1** | kokyo09-5 15→16：白文「嚴父莫大於配天」・すことなかれ 行——**機構境界の実証測定**（prefix 分割の根拠） |
| きことなかれ→きこと莫かれ | 2 | 2/0 | **Δ−0.000＜N69 収録線 −0.001＝無益**（ichinenkoku-1 型・如くは莫し 再構造） |
| ぶことなかれ→ぶこと莫かれ | 2 | 2/0 | 同上（rongo1709-1 莫きや 型） |
| くことなかれ→くこと莫かれ | 2 | 2/0 | 同上（toushisen034-4 型） |
| つことなかれ→つこと莫かれ | 1 | 1/0 | 同上（roushi78-1 型） |
| しばしば→屢 | 4 | 4/0 | **過門 −0.002 同数**——exp 実書形 屢〻（×3 行直書）を収録・裸字形落选 |
| はいよいよ→弥 | 6 | 6/0 | **過門 −0.004**——弥〻（−0.005）に劣る＝落选字形（N73 其れ/も其れ 同款） |
| いよいよ→弥 | 9 | 9/0 | 同上 |
| たま→偶〻 | 3 | 3/0 | **無益 −0.000**——偶（−0.001＝exp 偶坐 exact 型）を収録 |

備選⑥（report-only・不实现）：なかれ→莫かれ 復活条件＝post-N 残量 16 行（12 改善／3 same／1 変差 kokyo09-5 のみ）——**莫＋大 co-occurrence は判別式不成立**（莫大焉 行 kowokaete-4 は陽性通過済み）、莫如/莫能/莫敢/莫若… 15 種 co-occurrence が散在。復活は「排除 guard」か「kanji→kanji guard 規則」（N73 移交③と共用）の機構追加待ち＝拍板。详见 `eval/night78_mokaku.md`。

N72/N73 移交の复核終局：とも 224 行＝拒案維持（不触）、はざる者 2 行＝計数のみ核实（拍板待ち）、がため＝残量 0（検証 ✓）、べ族＝gap 收口済（再試推奨しない）。

## 6. README / verify / ROADMAP 同步（⑤）

- README 数字行 4 处：数字节头（`night78-rulen`・Night 78・**主提交 `0507e47`**——wrap-up 提交里按 `git log -1` 取数写入＝N73 TBD 同款）、テスト行 **307→337 passed**、規則エンジン行（**13.495**／**24/4000**＋N78 Rule N 注记＋`eval/night78_results_4000.json` 口径）、ルールチェーン行（Rule N 第 10 系列・**13 語**追加＋ことな族 prefix 分割・死行回避・新旧両形 guard の説明）
- `tools/verify_readme_facts.py`：Rule N 计数行追加＋归档源 night73→night78 切换（README 数字行更新的必要伴随、N68/N70/N72/N73 同款先例）→ **18/18 OK、exit 0**（pytest 計数断言 337 照合済み＝N72 移交⑥継続）
- ROADMAP.md 末尾 CLOSED 一行（`tools/night78_roadmap.py` 追加）

## 7. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `78: ["night78_results_4000.json"]`（仅此一条，67/68/70/72/73 同式）
- accept 78：**PASS（fail=0 skip=0）**——repo_clean ✓／pytest **337 passed = 337 collected**／eval_integrity（night78_results_4000.json 実查：id 唯一・自报数一致・expected 未改）✓／rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate off/on 退化页 0 ✓。1 回運行・SKIP なし（PATH 事前設定で N72 型の git-unavailable skip 回避）

## 8. 移交

1. **短 key artifact 拒案の再検原則（本夜の最大の方法論成果）**：N73 は「ことな→莫/勿・るべ→可＝opcode 人工物・预检 0 行」で拒んだが、**短 key の 0 行は「活用形 full key も死」を意味しない**——本夜は prefix 長 key（することなかれ 等）で 72 行回収。次夜以降、artifact 拒案の key 族は「prefix 長 key・suffix 長 key」で再検する価値あり
2. **空 got 249 行**（toushisen/rikutou/goshi 系に集中、`night78_kokyo.py` が実数化）：udkanbun エンジンが特定白文で空文字列を返す（Rule 層の外・avgDist を構造的に押し上げ）。OCR/guwenbert ではなく**パーサ系の調査候補**（拍板）——本夜は计数と分類のみ
3. ことな族取残し＝すことなかれ 7 行（死行 kokyo09-5 含む）＋き/ぶ/く/つ 7 行（無益拒案・収録線 −0.000）：今後の語料増で Δ が −0.001 を超えたら収録候補に再浮上（本夜の実数は night78_sim に归档済み）
4. なかれ→莫かれ 復活条件の数値確定（`eval/night78_mokaku.md`）：post-N 16 行 12 改善／1 変差——**排除 guard**（莫 ∧ 非莫大於）か **kanji→kanji guard 規則**（N73 移交③と共用）で 80 行規模の再候補になる。莫＋大 co-occurrence 単独は判別式不成立（kowokaete-4 莫大焉 陽性）
5. 現代語副詞族のパターン（エンジンが現代語 adverb を出す→exp は漢字＋okurigana・got/exp 互补計数が完璧な時は低リスク）：将来語料で たぶん/やがて/しだいに 等が同型で出たら同手順で掘れる
6. verify pytest 計数断言は 337 を機械照合済み——次夜のテスト行は 337＋N で更新（N70 型漂移は機械的に落第）
7. はざる者 2 行（roushi33-2/utsuryo06-2）：N72 から引き続き保留（拍板待ち、計数不变）

## 9. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；全局 site-packages 一行未动 ✓（C 库は N72 の .night72_deps 隔离目录をそのまま利用、本夜 pip 実行なし）
- 只动允许清单内文件：backend/kundoku_rules.py、tests/test_night78_rule_n.py、tools/night78_heartbeat(+loop)/mine/probe/kokyo/sim/eval/mokaku/roadmap.py、tools/accept_night.py（仅 78 一条）、tools/verify_readme_facts.py（Rule N 计数行＋归档源必要伴随）、README.md（数字行＋表头）、ROADMAP.md（末尾一行）、SHIFT_LOG.md、ACCEPT_LOG.md（accept 自動追加分）、eval/night78_*（mine/probe/sim/combo/results_4000/results_8165/mokaku/accept_night_78）、REPORT_NIGHT78.md ✓；scratch 文件（eval/_n78_* 22 個）用后即删 ✓
- 与 N71 零接触：本夜 D:\kanbun-kakikudashi に一度も入らず ✓；无 OCR 推理、无 guwenbert ✓；网络使用 0（本夜は内部データのみで候補構成が完結、外部語源調查不要）
- SHIFT_LOG 纯追加（'ab' 制・heartbeat 工具が byte 前後 print）✓；本地分支两提交（主 `0507e47`＋wrap-up）、**未合 master、未推远程** ✓；审查器未拦任何文件 ✓

## 10. 偏差注记

1. **任务书 pytest 基线数 283 与实测 307 不符**：283 是 N72 线旧数（M 的 24 测试前）；任务书指定的开工点 `807ad7d`（N73 wrap-up）的文档化真值是 307（N73 报告 §4/§7＋accept 73 归档 307=307），测试清单实查无词库链测试混入——**按 307 继续**（停机报数を要求する対不自主の不整合ではなく、文書連鎖で完全説明可能な数字の取り違え）。本报告与 SHIFT_LOG 全程记档
2. 模拟门内有 2 次候选设计修正（步骤内迭代、非跳步）：いよいよ族 guard 単形 弥 → 新旧両形 弥/彌（N72 移交①違反を sim が捕捉・0 発火修正）、収録順 dict 順 → COMBO_ORDER 明示（順序独立を 2 順序実測で検証・組合せ出力逐位一致）。45 分钟規則の対象段階では d0 缓存 2–3s で該当なし
3. 備選⑥は評価ラインと報告書に含めた（任务书「有余力才做」——真跑後に余力あり、产物 `eval/night78_mokaku.md`）。**阳性も阴性も手動実装なし**（等拍板）
4. 本夜工具用量：web_search 0 回・web ページ读取 0 回（备選②調查は内部データで完結）；pip 0 回；OCR/guwenbert 0 回
