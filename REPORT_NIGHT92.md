# REPORT_NIGHT92 — Rule Q 挖规则（kanbun-kakikudashi）

- 日期: 2026-11-24（单会话夜）
- 分支: `night92-ruleq`（自 master `b6a6248` 分出）；**未合 master、未推远程**
- 任务书: Rule Q 挖规则——B2 主切面长键手測（N88 教训：B2 定义扫不到 1 字块，(べ,可) 型
  手測拾到 べきなり→可きなり＝本夜主力；禁 OCR、禁 guwenbert 全量；backend/main.py・词库一字不改）
- 结果一句话: **Rule Q 2 条收录（ことなく→こと莫く・すべからず→可からず）**——
  1 字块枚举 16 块（行数≥6）→长键候选 8（T1〜T8）→**接受 2／拒绝 6**（scramble 4・
  変差 1・無益 1）；B2 rows≥4 复跑 11 族＝N86/N88 拒案全再确认；长尾扫描 3 件＝
  N86/N88 逐字同名 scramble（枯竭复核）；golden_4000 **13.491/24/0 持平**・
  golden_8165 **13.502→13.500/30/0 改善**（组合 37 行改写 15 改善／変差 0／幂等 bad 0）、
  accept 92 **PASS fail=0 skip=0**。

## 1. 开工核验（①）

- `git checkout -b night92-ruleq master` → HEAD = **b6a6248**（N91 wrap-up）✓
- `pytest tests -q` = **443 passed** ✓（14.15s）
- 已跟踪文件零改动（untracked 仅 eval/ 历史缓存・.night72_deps 等）✓
- 前置阅读：REPORT_NIGHT88.md §2/§9（べきなり発見経路＝(べ,可) 1 字块 B2 定义外・手測拾取；
  2 字键查漏 0 件）与 REPORT_NIGHT86.md §8/§9（B2 方法论：短 key 人工物拒案≠活用形 full key 死、
  prefix 长键回収；行分类断言 7916/30/218/1 の mine/probe/sim 組み込み）确认済み。

## 2. 挖词（②）：night92_mine → night92_probe → night92_sim

基线 = `eval/night91_results_8165.json`（N91 合并夜链尾真机归档 13.502/30/0；与 night90_results_8165.json
全行 got 逐位一致＝N88 零规则合并・got 不变，mine/sim 内断言再验证；night91_results_4000.json
前 4000 行一致）。**行分类＝N84 fallback 分支复现**（import backend.main の
detect_text_type/_ruby_tail_kanbun，実数 **7916/30/218/1**＝断言锁定）：規則可達 8134 行、
echo 30 行（白文直出）と no_tail 1 行は規則不可達で双口径すべて除外——rerun 行の
guard 上下文は**尾段**（main.py 現行分岐どおり、全文ではない）。

- **A. 1 字块枚举（主力・(べ,可) 型＝B2 定義外）**：SequenceMatcher replace 块・got 侧
  1 字假名 × exp 侧汉字头 → 行数≥6 の块 **16 块**——(べ,可) **118 行**（exp側 可(144)）、
  (は,将) 22（全 uniform 将に）、(は,未) 16（uniform 未だ・未央 1 行別対位）、(た,為) 9、
  (の,之) 9、(な,莫) 9、(て,為) 7、(は,有) 7、(も,与) 7、(は,少)/(は,白)/(は,行)/(は,来)/
  (は,尽)/(は,樹)/(は,闕) 各 6。tools/night92_mine.py → eval/night92_mine.{json,txt}。
- **B2. opcode 词级挖复跑（副切面）**：rows≥4 は **11 族**＝るべ 27 块/22 行・べきか 23・
  して→使 7・してしむる 7・しむ 5・とも 5・して→問 5・たり 4・してしむ 4・なかれ 4（既覆盖）・
  べきなり 4——**N88 数字完全一致**（基线逐位同の当然帰結＝再確認のみ）。
- **probe（tools/night92_probe.py、试替表 T1〜T8・発火/pair 比判定）**：
  T1 は→将に 22 pair **265 発火 207 変差**（発火/pair=12.0）＝scramble 拒（は 系助词全域、
  guard 将/將 でも「将軍/将たる」白文が大量発火）；T2 は→未だ 16 pair 172 発火 **131 変差**拒；
  T5 たる→為る 9 pair 113 発火 **20 変差**拒；T8 以て→以為えらく 7 pair 288 発火 **277 変差**拒
  （いずれも blanket key 発火 ≫ pair 行数＝語彙対応でない——N88 T3 して→問す 判別実例の适用）；
  **T3 ことなく→こと莫く（guard 莫）21 発火 11 改善/0 変差/same 10＝収候補**；T4 ことなき→
  こと莫き 15 発火 12 改善/**2 変差**（roushi46-2/rikutou26-5＝got 已含 莫かれ・exp 字形混在
  莫く/莫しで単一 repl 不成）拒；**T6 すべからず→可からず（guard 可）16 発火 4 改善/0 変差/
  same 12＝収候補**；T7 うべきなるのみか→可なるのみか 4 発火 0 改善＝無益拒。
  → eval/night92_probe.{json,txt}
- **sim（tools/night92_sim.py：単条 0 変差硬門＋N69 収録線 Δ<=−0.001＋組合双口径＋幂等＋
  長尾扫描）**→ eval/night92_sim.{json,txt} / night92_combo_changed_rows.json：
  - 单条门：**kotonaku_mokaku 収（21 改写 11 改善 0 変差 Δ−0.002）**・
    **subekarazu_kanarazu 収（16 改写 4 改善 0 変差 Δ−0.001）**——(べ,可) 118 行の未试
    prefix 形態（するべからず/るべからず と別の すべからず 連続列）＝N86 T4 るべからず
    prefix 3 変差 同族の分離回収。
  - 对照測定（現基线再確認・N86/N88 拒案の数字**完全一致**）：kotonaki_moki 2 変差
    （roushi46-2/rikutou26-5）・るべ→可 151 発火 91/**7**・べきか→可きか 31 発火 25/**2**・
    べからず→可からず 89 発火 79/**5**・べからざる→可からざる 82 発火 79/**1**（shiseinishite-1）・
    なかれ→莫かれ 17 発火 13/**1**（kokyo09-5）＝拍板事項のまま。
  - **長尾扫描（uniform exp_seg・len≥3・発火<=120）＝N88 枯竭の复核**：3 件
    （してなる→使うや・なるをしむるの→令・はなる→少くして）＝**N86/N88 拒案 3 件と
    逐字同名**（同一乱序文の重複 2 行・repl 非語彙対応＝scramble patch 過拟合拒）＝
    scan 由来の語彙対応候補枯竭確認（N88 §7 移交④の予測どおり）。
  - 組合（2 条）：**37 行改写／改善 15／変差 0／幂等 bad 0**。セグ別＝s4000 12 行
    （better 2）／s3908 24 行（better 12）／s257 1 行（better 1）。
- C1 なかれ 残量复核：**17 行、莫かれ 13 改善/1 変差 kokyo09-5/3 same＝N78/N86/N88 数字
  完全一致**（拍板事項のまま・本夜収録せず）。C2 はざる 残量 18 行、blanket 24shihin10-4
  17→18＝1 変差維持。C3 既收族残量：がため 1・何のごとく 1（N84 rerun 行＝機構変更
  拍板事項のまま）、Rule O 三键 0 残（収録確認）。D SHINJITAI 1:1 残量 **0 対**
  （N69/N72/N73/N78/N86/N88 结论維持）。

## 3. Rule Q 落地（③）：backend/kundoku_rules.py + 2 条

`Q_KANA_TO_KANJI`（2 条・Q_LONGER_WORDS 全空壳＝probe/sim 実測冲突なし）＋
`style_kana_to_kanji_q`＋ pipeline（O→Q 順）。SHINJITAI_MAP 追加なし（repl は既存
终字形のみ）：

| # | key | repl | guard | 実績（sim 単条） |
|---|-----|------|-------|------------------|
| 1 | ことなく | こと莫く | 莫 | 21 行 11 改善/0 変差 Δ−0.002——白文「莫〜」構文の got「〜ことなく」×exp「〜こと莫く」（rikutou08-3 rerun 行 含む）。Rule O なきか→莫し の **なく系兄弟**（否定連用形対位＝語彙対応） |
| 2 | すべからず | 可からず | 可 | 16 行 4 改善/0 変差 Δ−0.001——白文「可〜」構文の got「〜すべからず」×exp「〜可からず」。(べ,可) 1 字块 118 行锚定の prefix 分離＝**N88 べきなり発見経路（(べ,可) 型手測）の回収実証** |

組合（2 条）：**37 行改写／改善 15／変差 0／幂等 bad 0**。engine+rerun 行のみ、
echo 30 行/no_tail 1 行は不触。

## 4. 拒案（night92_probe/sim 実数归档、再発防止は tests/test_night92_rule_q.py に锁）

- **は→将に**（22 pair uniform 将にだが 265 発火 207 変差）：は 系助词 blanket——guard 将/將
  では「将軍・将たる・諸将」等名詞白文が大量発火＝語彙対応でない scramble。**は→未だ**
  （172 発火 131 変差）同死因（toushisen354-2 は は→未央 別対位＝字形混在でもあり）。
- **たる→為る**（113 発火 20 変差）：guard 為/爲 命中行中 たる blanket 発火＝N86 bare たり
  拒案の活用形 full key 再検でも不通。
- **以て→以為えらく**（288 発火 277 変差）：慣用句型だが 以て 全域発火。
- **ことなき→こと莫き**（2 変差 roushi46-2/rikutou26-5）：got 已含 莫かれ（N Rule族出力）×
  exp 莫く/莫し 字形混在＝単一 repl 不成（N78 落选字形教训の再確認）。
- **うべきなるのみか→可なるのみか**（4 発火 0 改善）：無益 Δ。
- 对照（N86/N88 拒案の数字完全一致）：るべ→可 91/7・べきか→可きか 25/2・べからず→
  可からず 79/5（exp 自写仮名 4＋可からざる 1）・べからざる→可からざる 79/1
  （shiseinishite-1）・なかれ→莫かれ 13/1（kokyo09-5・排除 guard/kanji→kanji 机制
  拍板待ちのまま）——本夜収録せず。
- **長尾 scramble patch 3 件**（してなる→使うや・なるをしむるの→令・はなる→少くして）：
  N86/N88 拒案逐字同名・過拟合拒（枯竭复核）。

## 5. 验证（④）

- 回归测试 `tests/test_night92_rule_q.py` **10 tests**（正例×2 族＋無護栏反例＋空白文语义＋
  拒案不复活 4 test（ことなき/なかれ・scramble blanket 4 条・べからず族 umbrella・
  長尾 scramble 3 件）＋構造ロック（2 条・長詞表空壳・repl 终字形・链序 O→Q）＋
  幂等/现代句/echo 行型）——**pytest 443→453 passed**（13.80s）。
- 真跑（TestClient 完整链・tools/night92_eval_4000.py / night92_eval_8165.py）：
  - **golden_4000：avgDist 13.491／exact 24/4000（不変）／error 0**——真跑改写 12 行＝
    sim 预测 12 行と new_text 逐位一致、計画外 0・欠落 0・変差 0。N91 归档
    （13.491／24／0）の「优于或等于」を満たす（Δ−0.001 は round で同値・持平）。
  - **golden_8165：avgDist 13.502→13.500／exact 30/8165（不変）／error 0**——真跑改写
    37 行＝sim 预测 37 行と逐位一致、計画外 0・欠落 0・変差 0（N91 13.502 から**改善**）。
  - 归档：eval/night92_results_4000.json（默认口径登记用）・eval/night92_results_8165.json
    （扩充归档）。
- `tools/verify_readme_facts.py` → **20/20 OK・exit 0**（N78/N86 先例同款の必要伴随：
  归档源 night86→**night92** 切换＋Rule Q 語数断言追加＋README 数字行同步——
  テスト行 453・8165 行 13.502→**13.500**・Rule Q 句追加・4000 13.491 は持平で不変）。

## 6. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `92: ["night92_results_4000.json"]`（仅此一条）。
- **accept 92：PASS（fail=0 skip=0）**——repo_clean ✓／pytest 453=453 ✓／
  eval_integrity（night92_results_4000.json 実查：id 唯一・自报数一致・expected 未改）✓／
  rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate 退化页 0 ✓。

## 7. 移交

1. **(は,将)・(は,未) 块の定性更新**：1 字块 uniform（将に 22・未だ 16）でも key が
   系助词 は なら blanket 発火 ≫ pair（12.0×/10.8×）で scramble——**guard は白文含字の
   正条件のみでは は を守れない**（守るには「主語位置限定」等の構文判別機構＝別拍板）。
   (べ,可) 118 行の残り（べからず族 89 行 79 改善 5 変差・るべ 91/7・べきか 25/2・
   べきなり 31/1 p-gekirin-1）は拍板事項のまま本夜一字未动。
2. **ことなき→こと莫き の死因**：got 已含 莫かれ（N Rule族出力済み）×exp 莫く/莫し
   混在——N Rule族（することなかれ 5 key）の repl が 莫かれ で確定した結果としての
   字形冲突。救うには exp 侧 字形統一（データ側拍板）が必要＝機構外。
3. **拍板事項（N86 から原样带入・本夜一字未动）**：べからず族 89 行 79 改善 5 変差
   （0 変差门撤廃なら収録可）；なかれ→莫かれ post-N 17 行（kokyo09-5 1 変差）；がため/
   何のごとく 各 1 行（rikutou37-2/shiki050-4＝rerun 行 tail guard 機構変更待ち）；
   べきなり→可きなり 31 行 29 改善 1 変差（変差 1 行許容拍板なら一発収録級）；
   N84 §8 夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行も未動。
4. **1 字块手測の収穫**：(べ,可) 型 1 字块→prefix 長键分離（すべからず）が N86 T4
   るべからず 3 変差 を 0 変差 で回避した＝「短 key 人工物拒案≠長键死」方法论の
   新実証（N88 べきなり発見経路の一般化）。次夜以降も 1 字块枚举→长键手測は
   B2 常規挖の主力補完として維持可。

## 8. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查＋night92_eval 逐位一致）；
  backend/main.py・词库（glossary_lexicon*.py）一字未改 ✓；SHINJITAI_MAP 追加なし ✓；
  site-packages 一行未动 ✓（Levenshtein は纯 Python 回退＝night91_eval lev と同一算法・
  归档 edit_distance と逐位一致を sim/eval で確認）
- 允许清单内文件のみ ✓：backend/kundoku_rules.py（Rule Q 追加のみ）、
  tests/test_night92_rule_q.py、tools/night92_{mine,probe,sim,eval_4000,eval_8165}.py、
  tools/verify_readme_facts.py（归档源切换＋Rule Q 語数＝N78/N86 先例の必要伴随）、
  tools/accept_night.py（92 一条のみ）、eval/night92_*（mine/probe/sim/combo/
  results_4000/results_8165/accept_night_92）、README.md（数字行＋テスト行＋Rule Q 句）、
  ROADMAP.md（末尾一行）、SHIFT_LOG.md、ACCEPT_LOG.md（accept 自動追加分）、
  REPORT_NIGHT92.md ✓
- 临时脚本は $env:TEMP（night92_hand1.py）で仓库外・scratch 无残留 ✓
- SHIFT_LOG 纯追加（.NET AppendAllText 絶対パス・UTF-8 無 BOM・byte807=243 写前后断言
  ×3 回）✓；无 OCR／guwenbert／网络 ✓（web_search 0・ページ取得 0）；本夜工具 web 使用 0
- 本地分支两提交（主提交＋wrap-up）、**未合 master、未推远程** ✓

## 9. 偏差注记

1. タスク書②の「接受硬门＝0 変差（任一变差即拒，不议价）」に従い、収録 2 条は
   いずれも単条・組合とも変差 0 を実測で満たす（sim 単条 21/16 行・組合 37 行）。
2. タスク書④の「数字须优于或等于 N91 归档」は golden_4000＝**持平**（13.491/24/0・
   Δ−0.001 は round 後同値）・golden_8165＝**改善**（13.502→13.500）で両方成立。
   変差 0 のため拒收条項に触れず。
3. probe T1/T2（は→将に/未だ）は pair 行数の uniform 性が高い（22/16 行全 uniform）に
   も拘らず blanket 発火 265/172 行で拒——「uniform 1 字块でも guard の白文含字では
   系助词を守れない」を T1〜T8 の実数として記録（§7 移交①）。
