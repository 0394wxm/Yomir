# REPORT_NIGHT96 — Rule S 挖规则：1 字块 micro 区带（rows≤2）＋ B2 (べ,可) prefix 分離 副切面

- **分支**：`night96-rules`（自 master `9d3b8a8`＝N95 wrap-up 分出）。两提交
  （主提交＋wrap-up），**未合 master、未推远程**。
- **基线** = `eval/night95_results_8165.json`（N95 合并夜链尾真机归档
  13.498/30/0＝Rule R 生效後）。链尾断言：night95 vs night94 got 差异＝**0 行**
  （N95 合并夜逐位一致の実証）；`night95_results_4000.json` 前 4000 行逐位一致も断言。
- **行分类＝N84 fallback 分支复现**（import backend.main 現行分岐，実数
  **engine 7916／echo 30／rerun 218／no_tail 1**＝断言锁定）：規則可達 8134 行、
  echo 30 行と no_tail 1 行は規則不可達で除外——rerun 行の guard 上下文は**尾段**。

## 1. 开工核验（①）

- `git checkout -b night96-rules master`：HEAD＝`9d3b8a8` ✓；`pytest tests -q`
  ＝**462 passed** ✓；已跟踪文件零改动（untracked＝既存缓存/样张目录のみ）✓。
- 先读 REPORT_NIGHT94.md §2/§7（56 块枚举・T1〜T31・micro 区带移交⑤）与
  REPORT_NIGHT95.md §6（次夜建议：rows 2 以下 micro 区带か 2 字块 B2 长键）。
- SHIFT_LOG 心跳＝UTF-8 無 BOM 純追加（byte807=243 写前后断言×3 回）。

## 2. 挖词（②）：night96_mine → night96_probe → night96_sim

- **A1. 1 字块 rows>=3 残景**：**54 块**（N94 の 56 块から (ゆ,之) 3 行は Rule R
  収録で消滅・他 1 块は 12 行改写の块形移行で rows 2 に落ちた自然変動＝偏差注记 1）。
  (べ,可) 110・(は,将) 22・(は,未) 16・(の,之) 9・(た,為) 9…＝N94 表の同型配置
  （変動分を除き一致）。
- **A2. 1 字块 micro 区带 rows 1〜2（本夜主力）＝658 块全枚举**（rows 2＝71 块＋
  rows 1＝587 块・計 729 行）：内訳 は系 **278** 块／に 67／が 41／を 31／その他
  241——は系 blanket（N92 §7 移交①の 26 块実測裏付けに準拠）・を/に/が 格助词
  blanket・重排 artifact 型・专名 artifact 型（太行/阿史那社爾/流亡/歎詞 於 等）は
  **直接记拒＝649 块（probe 不進）**、任務書②の筛选規則どおり。
- **有语汇对应相の筛后手測＝9 試替（T1〜T9）**：
  - T1 か→哉（(か,哉) micro 2 pair・詩経反復 悠なるか→悠なる哉）・T2 なるか→なる哉
    （T1 の 2 字长键化＝**集約パス (a) 試み**）・T3 ず→毋く（(ず,毋) 2 pair・
    必ず→必毋く 論語子絶四）・T6 な→勿（rongo0604-1 ことなからん→こと勿からん）・
    T8 るか→可し（B3 micro 1 pair）・T4/T5 なきなり→勿かれ/毋かれ
    （**B2 micro rows<=3 快查で発見した新長键**・azamukuko-1/sonshi09-19/
    sonshi10-12/rikutou21-2/ichijicho-1/rongo1125-1/shindoku-1/daigaku06-1）＝
    **8 块 1 字/长键手測**＋T7 べきか→可し・T9 ことなき→こと莫き の B3/禁区对照
    2 条＝計 9 試替。
  - blanket 予測実数（TEMP 快查）：か×哉 guard＝106 発火≫2 pair・な×勿 guard＝
    36≫1 pair・ず×毋 guard＝8≫2 pair——N88 T3「発火≫pair⇒非語汇対応」の事前
    フィルタとして機能（预判で拒らず実測で確定）。
- **B2 rows>=4 常规挖复核**：**11 族＝るべ 27/22・べきか 23・して→使 7・してしむる 7・
  しむ 5・とも 5・して→問 5・たり 4・してしむ 4・なかれ 4・べきなり 4＝
  N86/N88/N92/N94 数字完全一致**（Rule R 生效後も変動なし・(すべ,可) 族は Rule Q
  収録で B2 から消滅のまま）。
- **B3. (べ,可) 族全扫（副切面：2 字块 B2 长键 prefix 分離）**：1 字块 (べ,可)
  110 行（exp 可 uniform 134 次）・guard 可 命中かつ got 含 べ＝248 行（blanket
  べ→可 は N86 既測 scramble のまま）；**B2 exp 頭 可 の pair＝10 件**
  （るべ→可 27・べきか→可し 20・べきなり→可く 2・べきなり→可くんば 1・
  べきなり→可けんや 1・べきか→可けんや 1・べきか→可し、と 1・べきか→
  可けんや、と 1・べきより→可し 1・るか→可し 1）——**すべ 系残存なし**＝
  (すべ,可) prefix 分離（すべからざる 等）は既收規則（N92 すべからず＋E〜N べから）
  で**吸収済み**と実証。族内未試 repl の実測＝べきか→可し 31 発火 26 改善/3 変差
  （T7・0 変差硬门で拒）。
- **C1 なかれ 残量**：17 行・莫かれ 13 改善／1 変差 kokyo09-5／3 same＝
  N78/N86/N88/N92/N94 完全一致（拍板事項のまま・本夜収録せず）。
- **C2 はざる 残量**：18 行・24shihin10-4 17→18＝1 変差維持（blanket 拒案のまま）。
- **C3 既收族残量**：がため 1・何のごとく 1（rerun 行＝機構変更拍板のまま）・
  Rule O 三键 0 残・Rule Q 二键：すべからず 0 残／**ことなく 5 残＝guard 外行**
  （白文無莫→規則不発火＝仕様どおりの健全状態・(な,莫) 5 残量と同一行集）・
  ゆく 残量＝guard 之 外の行（参考記録のみ）。
- **D SHINJITAI 1:1 残量**：0 対（N69〜N94 结论維持）。
- tools/night96_mine.py → eval/night96_mine.{json,txt}（2281 行・micro 全列＋样本
  got/exp 对照付き）。

## 3. Rule S 落地（③）：backend/kundoku_rules.py + 1 条

`S_KANA_TO_KANJI`（1 条・`S_LONGER_WORDS` 空壳＝probe/sim 実測後続冲突なし）＋
`style_kana_to_kanji_s`＋ pipeline（**Q→R→S 順**）。SHINJITAI_MAP 追加なし
（repl 勿かれ は normalize_shinjitai 不変・勿 は新旧変異なし）：

| # | key | repl | guard | 実績（sim 単条） |
|---|-----|------|-------|------------------|
| 1 | なきなり | 勿かれ | 勿 | 4 行 4 改善/0 変差 Δ−0.001960——白文 勿〜 の got「なきなり」对位＝ことなきなり→こと勿かれ 型（azamukuko-1 論語憲問「欺くこと勿かれ」/sonshi09-19 孫子「近づくこと勿かれ」/sonshi10-12 孫子「従うこと勿かれ」/rikutou21-2 越絶書・**rerun 行＝guard 上下文＝尾段で実発火**）。Rule M なかれ→勿かれ の活用形分割兄弟键 |

組合（1 条）：**4 行改写／改善 4／変差 0／幂等 bad 0**。engine+rerun 行のみ、
echo 30 行/no_tail 1 行は不触。

## 4. 拒案（night96_probe/sim 実数归档、再発防止は tests/test_night96_rule_s.py に锁）

- **(a) micro blanket scramble 4 試替**：
  - か→哉（guard 哉）：**104 発火 45 変差**（発火/pair=52）＝(か,哉) micro 2 pair は
    詩経反復の語汇対応だが か は疑問・反語・間投に全域発火する blanket——guard 哉
    では守れない（N88 T3 判定の実測適用）。
  - なるか→なる哉（T1 の 2 字长键化）：28 発火 15 変差＝**集約パス (a) 不成立**
    （なるか は 〜なるか/〜なる哉 以外の对位多数）。
  - な→勿（guard 勿）：31 発火 11 変差＝ことなき/なかれ/なからん 禁区残量含む
    blanket（T4 の 勿かれ 収録でも な 単形は不採）。
  - るか→可し（guard 可）：34 発火 11 変差＝blanket scramble。
- **(b) 変差混在 3 試替**：
  - ず→毋く（guard 毋）：7 発火 2 改善/3 変差——必ず→必毋く 2 行（shiwotatsu-1/
    rongo0904-1＝同一文の重複）は改善だが shindoku-1 の exp「必ず」（guard 毋 行でも
    該当字が exp 側に実在）で変差＝guard 分離不成（拒）。
  - なきなり→毋かれ（guard 毋）：4 発火 2 改善/2 変差——shindoku-1/daigaku06-1 の
    exp は「毋きなり」（こと 欠落・字形混在）＝単一 repl 不成（拒）。
  - べきか→可し（guard 可・B3 族内新 repl）：31 発火 26 改善/3 変差＝0 変差硬门拒
    （对照 べきか→可きか 31 発火 25/2 とは別 repl・N92 数字との一致は
    可きか 側で維持＝偏差注记 2）。
- **(c) 禁区（拍板事項・本夜も一字未动・对照再測のみ）**：
  - ことなき→こと莫き 15 発火 12 改善/**2 変差**（N92 T4 完全一致・exp 字形混在）。
  - なかれ→莫かれ 17 発火 13/1（kokyo09-5）・べからず→可からず 78 発火 70/**5**・
    べからざる→可からざる 82 発火 79/**1**＝N86/N88/N92/N94 数字完全一致。
  - べきなり→可きなり（禁区 1 変差 p-gekirin-1）・がため/何のごとく 各 1 行
    （rerun tail 機構変更待ち）・は系構文判別機構（N92/N94 移交）・ことなき 字形
    統一（データ側）・guard 外ことなく 5 行（白文側字形対応データ拍板候補）。
- **在庫再測**：嗟や→嗟乎 3 発火 3 改善/**0 変差 Δ−0.000367**＝収録線未達の無益拒
  （N94 在庫の継続・データ増強拍板待ち）。**本夜の新規在庫＝0 条**
  （線未達の 0 変差候補は出ず・達成候補 T4 は収録線 Δ−0.001960 で即収録）。
- **长尾扫描（uniform exp_seg・len>=3・発火<=120）＝N86/N88/N92/N94 枯竭の复核**：
  3 件（してなる→使うや Δ−0.001・なるをしむるの→令 Δ−0.002・はなる→少くして
  Δ−0.001）＝**N86/N88/N92/N94 拒案と逐字同名・5 夜連続**——scan 上は 0 変差＆
  Δ線達成の数字だが、同一乱序文の重複 2 行・repl 非語汇対応＝**N86 惯例
  「scramble patch 過拟合拒」で拒**（scan 由来の語彙対応候補枯竭確認・5 夜目）。

## 5. 验证（④）

- 回归测试 `tests/test_night96_rule_s.py` **7 tests**（正例×4 行型〔azamukuko/
  sonshi×2/rikutou rerun〕＋無護栏反例（毋 行・なからん 行）＋空白文语义＋
  拒案不复活 2 test（micro blanket 5 件・(べ,可) 族/禁区 4 件＋长尾 3 件）＋
  構造ロック（1 条・長詞表空壳・repl 终字形・链序 Q→R→S・R 併用）＋幂等/
  现代句/echo 行型）——**pytest 462→469 passed**（13.94s）。
- 真跑（TestClient 完整链・tools/night96_eval_4000.py / night96_eval_8165.py）：
  - **golden_4000：avgDist 13.489→13.488／exact 24/4000（不変）／error 0**——真跑
    改写 1 行（azamukuko-1）＝sim 预测と new_text 逐位一致、計画外 0・欠落 0・
    変差 0（N95 13.489/24/0 から**改善**）。
  - **golden_8165：avgDist 13.498→13.496／exact 30/8165（不変）／error 0**——真跑
    改写 4 行（azamukuko-1/sonshi09-19/sonshi10-12/rikutou21-2）＝sim 预测 4 行と
    逐位一致、計画外 0・欠落 0・変差 0（N95 13.498 から**改善**）。
  - 归档：eval/night96_results_4000.json（默认口径登记用）・
    eval/night96_results_8165.json（扩充归档）。
- `tools/verify_readme_facts.py` → **22/22 OK・exit 0**（N78/N86/N92/N94 先例同款の
  必要伴随：归档源 night94→**night96** 切换＋Rule S 語数断言追加＝21→22 项＋README
  数字行同步——テスト行 469・4000 行 13.488・8165 行 13.496・Rule S 句追加・
  口径 parenthetical night96_results）。

## 6. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `96: ["night96_results_4000.json"]`
  （仅此一条）。
- **accept 96：PASS（fail=0 skip=0）**——repo_clean ✓／pytest 469=469 ✓／
  eval_integrity（night96_results_4000.json 実查：id 唯一・自报数一致・expected
  未改）✓／rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate 退化页 0 ✓。
  （提交前试跑＝repo_clean FAIL のみ＝設計行為・六門全绿、主提交 5bbed94 後終跑
  PASS。）

## 7. 移交

1. **micro 区带の実質枯竭**：rows<=2 の 658 块中、は系 278・に 67・が 41・を 31
   ＝417 块が 4 系 blanket／artifact（直接拒）、其余 241 块の有语汇对应相は 8 块で
   実測→収録 1・拒 7——**1 字块手測は rows>=3（N94・56 块）と rows<=2（本夜・658 块）
   で計 714 块完掘**。次夜以降の 1 字块は新语料増強（データ側拍板）か、は系構文
   判別機構（N92 §7 移交①）の機構変更がない限り枯竭状態。
2. **B2 (べ,可) prefix 分離の完結**：(すべ,可) 型 prefix は既收規則吸収済み
   （B2 exp 頭可 pair に すべ 系残存なし）＝N92 すべからず 発見経路の系列は完掘。
   族内残存の未試 repl（べきか→可し 26/3・べきなり→可く 系 variants 混在）は
   0 変差硬门で拒——べからず族拍板（変差許容）が下りない限り新規収録余地なし。
3. **拍板事項（N86/N88/N92/N94 から原样带入・本夜一字未动）**：べからず族 89 行
   （可からず 78 発火 70 改善 5 変差・可からざる 82 発火 79/1＝0 変差门撤廃なら
   一発収録級）；べきなり→可きなり 31 行 29 改善 1 変差（p-gekirin-1）；なかれ→
   莫かれ post-N 17 行（kokyo09-5）；がため/何のごとく 各 1 行（rerun 行 tail
   guard 機構変更待ち）；は系 1 字块構文判別機構（N94 §7 移交①の 26 块実測に
   本夜 278 块 micro 追加）；嗟や→嗟乎 在庫化（Δ−0.000367・歎詞データ増強
   拍板待ち）；guard 外 ことなく 5 行（白文側字形対応データ拍板候補）；ことなき
   字形統一（データ側）；N84 §8 夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行。
4. **長尾 scan の 5 夜連続同名**：してなる→使うや・なるをしむるの→令・はなる→
   少くして 3 件は scan の数字上（0 変差＆Δ線達成）毎夜「収候補」として浮上するが、
   N86 惯例 過拟合拒で処理——**次夜以降も同名 3 件は自動拒扱い**（数字だけ見て
   収録しないこと・乱序文重複 2 行の非語汇対応）。
5. **次夜建议**：1 字块 micro 完掘・(べ,可) prefix 完掘により、規則側の残りは
   ①は系構文判別機構（機構変更拍板）、②べからず族/べきなりの「変差 1〜5 行許容」
   拍板、③がため/何のごとく の guard 上下文機構変更、④歎詞・字形統一など
   データ側拍板の 4 本に集約——規則 mining 自体は scan 枯竭＋micro 枯竭で
   **報告-only 夜（先例 N69/N74/N76/N88）か、2 字块 B2 の rows<=3 快查・新语料
   依存の在庫消化に移行**するのが現実的。

## 8. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查＋night96_eval 逐位一致）；
  backend/main.py・词库（glossary_lexicon*.py）一字未改 ✓；SHINJITAI_MAP 追加なし ✓
- 允许清单内文件のみ ✓：backend/kundoku_rules.py（Rule S 1 条＋comment＋pipeline
  1 行）、tests/test_night96_rule_s.py（新 7 tests）、tools/night96_mine.py・
  night96_probe.py・night96_sim.py・night96_eval_4000.py・night96_eval_8165.py
  （新 5 工具）、tools/verify_readme_facts.py（night96 归档源切换＋Rule S 語数断言
  のみ）、tools/accept_night.py（96 一条のみ）、eval/night96_*（mine/probe/sim/
  combo/results 9 ファイル＋accept_night_96.json）、SHIFT_LOG.md（心跳 4 行）、
  README.md（数字行のみ・header は合并夜まで不変＝N92/N94 先例）、ROADMAP.md
  （末尾 1 行＝N92 規則夜先例）、REPORT_NIGHT96.md ✓
- 临时脚本は $env:TEMP／AutoClaw ワークスペース（night96_mine/probe/sim/eval 生成・
  patch_rules_s・patch_sync×2・TEMP 快查 2 本）で仓库外・仓库に持ち込まず ✓
- SHIFT_LOG 纯追加（.NET/ python 絶対パス・UTF-8 無 BOM・byte807=243 写前后
  断言×3 回）✓；无 OCR／guwenbert／eval 以外の网络 ✓（web_search 0・ページ取得 0）
- 本地提交（主提交＋wrap-up）、**未合 master・未推远程** ✓

## 9. 偏差注记

1. **A1 rows>=3 区带 54 块（N94 56 块から −2）**：Rule R ゆく→之く の 12 行改写で
   (ゆ,之) 3 行块が消滅＋他 1 块が rows 3→2 に移行（micro 側へ）——块形の自然変動で
   拒案/在庫の実質には影響なし（B2 rows>=4 11 族は N86/N88/N92/N94 数字完全一致で
   健全性確認済み）。
2. **べきか→可し（T7）31 発火 26 改善/3 変差**：N92/N94 对照の べきか→**可きか**
   （31 発火 25/2）とは別 repl の新規実測値——对照数字の一致は 可きか 側で完全維持
   （本夜 sim gate：bekika 31/25/2）。可し repl の 変差 3 は N92 測定と矛盾しない。
3. **probe T9 ことなき→こと莫き の発火 15**（N92 T4 時点の 21 発火から減）：Rule Q
   ことなく 21 行収録（N92）と Rule R 12 行（N94）の既收行減の自然残量変動——
   変差 2 行（rousxi46-2/rikutou26-5）は N92 と同一行で維持（禁区判定不変）。
4. **accept_night.py 试跑 1 回（repo_clean FAIL のみ）＋終跑 1 回（PASS）**＝惯例
   どおり（FAIL/PASS 两行とも ACCEPT_LOG に残る）。
5. **任务书交付格式の「筛后手測 9」**：micro 区带 658 块のうち直接记拒 649 块
   （は系/を/に/が blanket・重排 artifact・专名＝任务书②の筛选規則で probe 不進）＋
   手測 9 試替（内 2 条＝B3 对照・禁区確認、7 条＝micro/长键新規実測）——「数が
   不少」と「手測のみ実測」の両立をこの配分で明記。
