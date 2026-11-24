# REPORT_NIGHT88 — Rule P 挖规则（kanbun-kakikudashi）

- 日期: 2026-11-24（单会话夜）
- 分支: `night88-rulep`（自 master `35ba6e5` 分出）；**未合 master、未推远程**
- 任务书: Rule P 挖规则（B2 方法论第八遍；禁 OCR、禁 guwenbert 全量；backend/main.py・词库一字不改）
- 结果一句话: **Rule P 0 条收录（零规则夜・N69/N74/N76 报告-only 先例）**——全通道挖尽：
  B2 rows≥4 十一族＝禁区 5（使役×4・とも）＋N86 已测拒案 3（るべ/べきか/たり bare）＋新鲜 2
  （べきなり→可きなり **1 変差**・して→問す scramble 89 変差）全拒；长尾扫描 3 件＝N86 scramble
  patch 逐字同名（過拟合拒）；2 字键查漏 0 件；SHINJITAI 0 対；对照复核全維持。
  golden_4000 **13.491/24/0**・golden_8165 **13.502/30/0** 与 night87 归档**逐位一致**
  （kundoku_rules.py 一字未改の阴性证明）、accept 88 **PASS fail=0 skip=1**（skip=eval_integrity）。

## 1. 开工核验（①）

- `git checkout -b night88-rulep master` → HEAD = **35ba6e5**（N87 wrap-up）✓
- `pytest tests -q` = **434 passed** ✓（13.1s）
- 已跟踪文件零改动（untracked 仅 eval/ 历史缓存）✓
- 前置阅读：REPORT_NIGHT86.md §2/§4/§7（B2 挖词＋拒案＋拍板项）与 REPORT_NIGHT87.md §0
  （合并链尾口径：4000 13.491／8165 13.502）确认済み。

## 2. 挖词（②）：night88_mine → night88_probe → night88_sim

基线 = `eval/night87_results_8165.json`（N87 合并链尾真机归档 13.502/30/0；与 night86_results_8165.json
全行 got 逐位一致＝mine/sim 内断言再验证）。**行分类＝N84 fallback 分支复现**（import backend.main の
detect_text_type/_ruby_tail_kanbun，実数 **7916/30/218/1**＝断言锁定）：規則可達 8134 行（engine＋rerun）、
echo 30 行（白文直出）と no_tail 1 行は規則不可達で mine/probe/sim 双口径すべて除外——rerun 行の
guard 上下文は**尾段**（main.py 現行分岐どおり、全文ではない）。

- **B2 opcode 词级挖**（replace 块・got 侧纯假名≥2 × exp 侧汉字头・守り字新旧两形并查）：
  行数≥4 は **11 族**——るべ→可（27 块/22 行）、べきか→可（23）、して→使（7）、してしむる→使（7）、
  しむ→使（5）、とも→与（5）、して→問（5）、たり→為（4）、してしむ→使（4）、なかれ→莫（4・既覆盖）、
  べきなり→可（4）。tools/night88_mine.py → eval/night88_mine.{json,txt}。
  内訳＝**禁区 5 族**（使役 して/してしむる/しむ/してしむる→使・とも→与＝任务书「不重挖」）＋
  **N86 已测拒案 3 族**（るべ→可 T1・べきか→可きか T5・bare たり→為＝字形混在で不収の記録分）＋
  **新鲜 2 族**（べきなり・して→問す）＋既覆盖 1（なかれ）。
- **probe**（tools/night88_probe.py、试替表 T1〜T6＋取证 D1〜D3）：
  T1 べきなり→可く 31 発火 6 改善/**24 変差**拒（なり破壊死）；T2 べきなり→可くんば 5/**25 変差**拒；
  T3 して→問す 162 発火 7/**89 変差**拒；T4 るべ→可 91/**7 変差**＝N86 T1 数字完全一致
  （拒案維持）；T5 べきか→可きか 25/**2 変差**（omoi-1/mobosansen-1）＝N86 T5 完全一致；
  T6 べからず→可からず 79/**5 変差**＝N72/N86 完全一致（任务书「本夜只复核」完了）。
  → eval/night88_probe.{json,txt}
- **sim**（tools/night88_sim.py：単条 0 変差硬門＋長尾扫描＋幂等＋双口径）→ eval/night88_sim.{json,txt}：
  単条門 7 条（新鲜 2＋对照 5）——**新鲜唯一 收録線達成候选 べきなり→可きなり：31 行 29 改善/
  1 変差（p-gekirin-1 8→9）Δ−0.006＝0 変差硬门拒**（最接近的一条、§7 移交①）；して→問す
  89 変差拒；对照 5 条（るべ/べきか/べからず/べからざる/なかれ）全部 N86/N72 数字完全一致＝拒案維持。
  **长尾扫描**（uniform exp_seg・len≥3・発火≤120）：3 件 0 変差＆線達成＝してなる→使うや・
  なるをしむるの→令・はなる→少くして——**与 N86 拒案 3 件逐字同名・同 pair=2・同 Δ**
  （基线逐位同の当然帰結）＝非語彙対応 scramble patch・過拟合拒（N86 新惯例・任务书②）。
- **2 字键查漏**（临时脚本・$env:TEMP・仓库外）：uniform exp_seg・pair≥2・発火 2~120＝**0 件**
  （るべ は発火 151 过大 skip、(べ,可) 型 1 字块は B2 定義外で扫不到＝べきなり长键は手測で拾った）。
- **C1 なかれ 残量复核**：17 行、なかれ→莫かれ 13 改善/**1 変差 kokyo09-5**/3 same＝N86 数字完全一致
  （拍板事項のまま・本夜収録せず）。
- **C2 はざる 残量复核**：18 行（はざる者 収録分除く）、blanket 24shihin10-4 17→18＝1 変差維持
  （N69/N72/N86 拒案のまま）。
- **C3 既收族残量**：がため 1・何のごとく 1（N84 rerun 行・guard 上下文機構変更＝拍板事項のまま）、
  **Rule O 三键 はざる者/たりせ/なきか 全 0 残**（N87 合并生效の収録確認）。
- **D SHINJITAI 1:1 残量 0 対**（N69/N72/N73/N78/N86 结论維持）。

## 3. 落地（③）：零规则夜

backend/kundoku_rules.py **一字未改**（収録 0 条）；SHINJITAI_MAP 追加なし；tests 无新文件
（pytest 434 不变＝N69 先例——収録 0 のため「每条新规则正例＋guard 反例」対象なし、既存拒案は
tests/test_night86_rule_o.py が既に锁死済み、本夜新鲜拒案は行级 exp 変差で規則として存在し得ない）。

## 4. 拒案（night88_mine/probe/sim 実数归档）

- **べきなり→可きなり**（新鲜・最接近）：31 行 29 改善/**1 変差 p-gekirin-1**（exp 自写仮名 べきなり・
  白文「柔可狎而騎也」の可＝可狎義で guard 可 と非分離）——N55 べき→可き（4 変差）と同一死因の
  长键再現＝**0 変差硬门拒**。字形混在（可く 2/可くんば 2/可けんや 2）で単一 repl も不可。
- **して→問す**：B2 5 行 uniform（問す）だが全域発火 162 行 89 変差——guard 問 で発火行が
  B2 pair 行の 32 倍＝**語彙対応でない**（「して」は構造差）。
- **使役族**（して→使う 133 変差・しむ 72・してしむ 3・してしむる 1）：禁区不重挖＝N86 のまま。
- **とも→与に**（137 変差）：禁区＝N72/N86 のまま。
- **るべ→可**（91/7）・**べきか→可きか**（25/2）：N86 T1/T5 拒案維持（基线逐位同の再確認）。
- **べからず族**（べからず 79/5・べからざる 79/1 shiseinishite-1）：N72/N86 拒案維持＝任务书复核完了
  （exp 自写仮名 4〜5 行死因・0 変差门撤廃拍板なら一発収録可＝提出のみ）。
- **なかれ→莫かれ post-N**（13/1 kokyo09-5）：N78 备选⑥のまま（排除 guard/kanji→kanji 机制拍板待ち）。
- **はざる blanket**（C2 24shihin10-4 1 変差）：N69/N72/N86 拒案維持。
- **長尾 scramble patch 3 件**（してなる→使うや・なるをしむるの→令・はなる→少くして）：
  N86 過拟合拒の再確認（同一乱序文の重複 2 行・repl 非語彙対応）。

## 5. 验证（④）

- 真跑（TestClient 完整链・tools/night88_eval_4000.py / night88_eval_8165.py）＝**零规则夜の阴性证明**：
  - **golden_4000：avgDist 13.491／exact 24/4000／error 0**——与 night87_results_4000.json
    逐位一致、diff **0 行**（87s）。
  - **golden_8165：avgDist 13.502／exact 30/8165／error 0**——与 night87_results_8165.json
    逐位一致、diff **0 行**。
  - 両口径とも N87 归档（13.491／24／0・13.502／30／0）の「优于或等于」を満たす
    （零改动＝等号成立・任一变差で拒收の条項に触れず）。
  - 归档：eval/night88_results_4000.json・night88_results_8165.json（阴性证明归档；零规则夜＝
    NIGHT_ARTIFACTS 不登记・accept 走 skip=1 报告-only 先例）。
- `tools/verify_readme_facts.py` → **19/19 OK・exit 0**（README 数字行不変＝零改动、同步不要・
  N78/N86 の「数字变了才同步」条項に該当せず）。

## 6. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS **不登记 88**（零规则夜报告-only＝N69/N74/N76 先例・
  「Night 88 未登记评测归档文件，只查 golden.json」が eval_integrity skip の機構）。
- **accept 88：PASS（fail=0 skip=1、30.5s・首跑即 PASS）**——repo_clean ✓／pytest 434=434 ✓／
  eval_integrity skip（golden_2000 2000 条・id 唯一・前 1000 条逐字段一致 ✓）／rule_regression ✓／
  engine_smoke ✓／perf_envelope ✓／order_rate（off 98.57%・on 98.63%、退化页 0）✓。

## 7. 移交

1. **べきなり族（新拍板级候选の記録）**：長键 べきなり→可きなり は 31 行 29 改善・Δ−0.006
   （収録線達成）だが p-gekirin-1（exp 自写仮名）1 変差で 0 変差门不通——N55 べき（4 変差）/
   N58 須らく（5 変差）と同型の「ページ別編集習慣」死因。guard 可 の正表記分離は機構的に不可
   （guard は白文含字の正条件のみ・p-gekirin-1 の白文にも可 が含まれる）。「変差 1 行許容」の
   拍板が下りれば一発収録級——べからず族（89 行 79 改善 5 変差）と同枠の提出事項。
2. **して→問す 判別実例**：B2 uniform 族でも guard 全域発火なら scramble（語彙対応でない）——
   「発火行数 ≫ B2 pair 行数 ⇒ 非語彙対応」を night88_probe T3 が実証（5 行 pair vs 162 発火）。
   scan 系候補判定の新チェックとして転用可。
3. **拍板事項（N86 から原样带入・本夜一字未动）**：べからず族 89 行 79 改善 5 変差（0 変差门
   撤廃なら収録可）；なかれ→莫かれ post-N 17 行（kokyo09-5 1 変差・排除 guard/kanji→kanji
   拍板待ち）；がため/何のごとく 各 1 行（rikutou37-2/shiki050-4＝rerun 行 tail guard 機構変更
   待ち）；N84 §8 夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行も未動。
4. **长尾扫描の枯渇**：2 夜連続で同名 3 件のみ（N86/N88）——scan 由来の語彙対応候補は
   たりせ/なきか（N86 収録）で尽きた公算。次夜以降は scan 新規性が薄い前提で B2 主切面の
   长键手測（(べ,可) 型 1 字块＝本夜べきなりの発見経路）を主に据えるのが効率的。

## 8. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查＋night88_eval 逐位一致）；backend/main.py・
  词库（glossary_lexicon*.py）一字未改 ✓；**kundoku_rules.py 一字未改（零规则夜）**✓；site-packages
  一行未动 ✓（Levenshtein は纯 Python 回退＝night87_eval lev と同一算法・归档 edit_distance と
  逐位一致を sim/eval で確認）
- 允许清单内文件のみ ✓：tools/night88_{mine,probe,sim,eval_4000,eval_8165}.py、
  eval/night88_*（mine/probe/sim/combo/results_4000/results_8165/accept_night_88）、SHIFT_LOG.md、
  ACCEPT_LOG.md（accept 自動追加分）、REPORT_NIGHT88.md、ROADMAP.md（末尾一行）✓；
  accept_night.py・verify_readme_facts.py・README・tests・backend/** 未改（零规则夜で不要）✓
- 临时脚本は $env:TEMP（night88_scan2.py）で仓库外・scratch 无残留 ✓
- SHIFT_LOG 纯追加（.NET AppendAllText 絶対パス・UTF-8 無 BOM・byte807=243 写前后断言×3 回）✓；
  无 OCR／guwenbert／网络 ✓（web_search 0・ページ取得 0）；本夜工具 web 使用 0
- 本地分支两提交（主 `4cd618c`＋wrap-up）、**未合 master、未推远程** ✓

## 9. 偏差注记

1. 任务书②の「接受硬门＝0 变差（任一变差即拒，不议价）」に従い、べきなり→可きなり（Δ−0.006・
   29/31 改善）は収録線達成でも **1 変差で拒**——N86 の べからざる（Δ−0.011・1 変差）と同型の
   「变差 1 行だけ」死。阴性夜の帰結だが、候補の存在と死因は §7 移交①として記録済み。
2. 零规则夜のため tests/README/accept_night.py/verify_readme_facts.py 全部不改＝N69/N74/N76
   先例どおり。任务书⑤の「NIGHT_ARTIFACTS 照例加 88」は有规则時の条項、零规则時は同条項の
   「skip=1・skip=eval_integrity」が優先（accept_night.py L247-249 の無登记 skip 機構）——
   eval/night88_results_4000.json は④の阴性证明として作成・コミット済みだが登记対象外。
3. probe T3 して→問す は B2 rows≥4 族の中で唯一「uniform exp_seg」だったが発火 162 行＝
   B2 pair 5 行の 32 倍——「guard で全域発火する B2 族は語彙対応でない」判定の実証例として
   §7 移交②に記録（N86 scramble 3 件の系列に同名追加）。
