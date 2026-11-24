# REPORT_NIGHT86 — Rule O 挖规则（kanbun-kakikudashi）

- 日期: 2026-11-23（单会话夜）
- 分支: `night86-ruleo`（自 master `d4738a5` 分出）；**未合 master、未推远程**
- 任务书: Rule O 挖规则（B2 方法论第七遍；禁 OCR、禁 guwenbert 全量；backend/main.py・词库一字不改）

## 1. 开工核验（①）

- `git checkout -b night86-ruleo master` → HEAD = **d4738a5**（N85 wrap-up）✓
- `pytest tests -q` = **422 passed** ✓（12.6s）
- 已跟踪文件零改动（git status porcelain untracked=no = 0 行；untracked 仅 eval/ 归档缓存）✓
- 前置阅读：REPORT_NIGHT78.md §8（B2 方法论：短 key 人工物拒案≠活用形 full key 死、prefix 长键回収）与 REPORT_NIGHT84.md §8（N84 移交：8 行夹注残渣与 kana 分流不在本夜范围）确认済み。

## 2. 挖词（②）：night86_mine → night86_probe → night86_sim

基线 = `eval/night85_results_8165.json`（N85 合并链尾真机归档 13.505/30/0；与 night84_results_8165.json
全行 got 逐位一致＝mine 内断言再验证）。**行分类＝N84 fallback 分支复现**（import backend.main 的
detect_text_type/_ruby_tail_kanbun，実数 7916/30/218/1＝断言锁定）：規則可達 8134 行（engine＋rerun）、
echo 30 行（白文直出）と no_tail 1 行は規則不可達で mine/sim/真跑双口径すべて除外——rerun 行の
guard 上下文は**尾段**（main.py 現行分岐どおり、全文ではない）。

- **B2 opcode 词级挖**（replace 块・got 侧纯假名≥2 × exp 侧汉字头・守り字新旧两形并查）：
  行数≥4 の pair は 11 族——るべ→可（27 块/22 行）、べきか→可（23）、して→使（7）、してしむる→使（7）、
  しむ→使（5）、とも→与（5）、して→問（5）、たり→為（4）、してしむ→使（4）、なかれ→莫（4・既覆盖）、
  べきなり→可（4）。tools/night86_mine.py → eval/night86_mine.{json,txt}。
- **probe**（tools/night86_probe.py、试替表 T1〜T12）：
  T1 るべ→可 blanket 151 発火 91 改善/**7 変差**拒；T2 べからず→可からず 89 発火 79/**5 変差**拒
  （N72 拒案 5 行の再現：exp 自写仮名 4＋可からざる 1）；T3 ざるべからず prefix 9 発火 8/**1 変差**
  （ryojo-3）拒；T4 るべからず prefix 59 発火 34/**3 変差**拒；T5 べきか→可きか 31 発火 25/**2 変差**
  （omoi-1/mobosansen-1・exp 自写仮名）拒；**T6 はざる者→わざる者 6 発火 6 改善/0 変差＝収候補**；
  T7 はざる blanket 24 発火 14/**1 変差**（24shihin10-4・N69 拒案維持）拒；T8 しむ→使う 158 発火
  20/**72 変差**拒；T9 してしむる→使う 26 発火 20/**1 変差**（sonshi05-3）拒；T10 してしむ→使う 60 発火
  31/**3 変差**拒；T11 して→使う 191 発火 22/**133 変差**（artifact 実証）拒；T12 とも→与に 245 発火
  37/**137 変差**（N72 拒案再確認）拒。→ eval/night86_probe.{json,txt}
- **sim**（tools/night86_sim.py：单条 0 変差硬门＋N69 収録線 Δ≤−0.001＋組合双口径＋幂等＋
  uniform exp_seg 長尾扫描）：→ eval/night86_sim.{json,txt} / night86_combo_changed_rows.json（§3〜4）。
- C1（N78 备选⑥ 复核）：なかれ 残量 **17 行**（N84 rerun 追加 1 行 rikutou34-7 含む）。なかれ→莫かれ
  guard 莫＝13 改善/**1 変差 kokyo09-5**/3 same、莫し＝15/**2 変差**、莫＝14/**2 変差**——
  **排除 guard／kanji→kanji 机制なしでは不通＝拍板事項のまま**（N78 mokaku 結論の現基线再確認）。
- C2（N72 移交复核）：はざる 残量 24 行の内 はざる者 **6 行**（2 engine＋4 rerun——N84 復帰行で
  N72 の 2 行→6 行に増殖）＝T6 収候補（§3）。はざるか 7 行は 3 改善/Δ−0.000＝無益。
- C3：既收族残量は がため 1 行（rikutou37-2＝rerun 行・尾段に 爲 無し→L guard 不発火＝N84 分支の
  正規挙動）と 何のごとく 1 行（shiki050-4＝同構造・奈 無し）のみ——両行とも不動（動かすには
  rerun 行の guard 上下文変更＝機構変更、本夜範囲外）。
- D：SHINJITAI 1:1 残量 **0 対**（N69/N72/N73/N78 結論維持）。

## 3. Rule O 落地（③）：backend/kundoku_rules.py + 3 条

`O_KANA_TO_KANJI`（3 条・O_LONGER_WORDS 全空壳＝probe 実測冲突なし）＋ `style_kana_to_kanji_o`
＋ pipeline（N→O 順）。SHINJITAI_MAP 追加なし（repl は既存终字形のみ）：

| # | key | repl | guard | 実績（sim 単条） |
|---|-----|------|-------|------------------|
| 1 | はざる者 | わざる者 | 無条件 | 6 行 6 改善/0 変差 Δ−0.001——N72 拍板待ち 2 行（roushi33-2/utsuryo06-2）＋N84 rerun 行 4 行（utsuryo03-5/19-2/24-2/shiki001a-7）。kanji 含み key＝M 何のごとし 前例；L はざるなり/を 接続拆分の第 3 段 |
| 2 | たりせ | 為ら | 爲/為（新旧両形） | 6 行 6 改善/0 変差 Δ−0.001——白文「使〜爲〜」でエンジンが 爲 を完了形 たり 出力（宰たりせしむ型）×exp 為らしむ。bare たり→為 族は exp 字形混在（為ること/為るや）で不収 |
| 3 | なきか | 莫し | 莫 | 3 行 3 改善/0 変差 Δ−0.001——白文「莫〜」反語構文の got「〜ことなきか」×exp「〜こと莫し」（M 何のごとく→奈何ぞ 3 行・収録線 −0.001 同款） |

組合（3 条）：**15 行改写／改善 15／変差 0／幂等 bad 0**。セグ別＝s4000 8 行／s3908 3 行／s257 4 行。

## 4. 拒案（night86_sim/probe 実数归档、再発防止は tests/test_night86_rule_o.py に锁）

- **べからず族**（79 行規模の最大残量・全键不通）：べからず→可からず（5 変差・N72 拒案の再現）、
  ざるべからず prefix（1 変差 ryojo-3・exp 自写仮名）、るべからず prefix（3 変差）、
  べからざる→可からざる（82 発火 79 改善/**1 変差 shiseinishite-1**・Δ−0.011 だが 0 変差門不通）。
  exp 自写仮名 4〜5 行が全字形共通の死因＝構造 gap（N68 §8-3 実証の再確認）。
- **なかれ→莫かれ post-N**（N78 备选⑥）：kokyo09-5 1 変差が残る限り不通＝**排除 guard／kanji→kanji
  机制の拍板待ち**。き/ぶ/く/つ/ぶべきことなかれ 5 key＝各 1〜2 行 0 変差 Δ−0.000＝無益拒の再確認。
- **使役族**（してしむる/してしむ/しむ/して→使う）：変差 1/3/72/133——exp 側構造差
  （〜からしむ/語順転換）で規則層不可達＝N24/25 STRUCTURAL 定性の再確認。
- **べきか→可きか**（2 変差＝exp 自写仮名）／**とも→与に**（137 変差・N72 拒案再確認）／
  **はざる blanket**（1 変差 24shihin10-4）／**はざるか**（無益 Δ−0.000）。
- **長尾扫描 scramble patch 3 件**（してなる→使うや・なるをしむるの→令・はなる→少くして）：
  いずれも同一乱序文の重複 2 行のみ、repl が語彙対応でない行個別パッチ＝過拟合で拒
  （収録線 Δ は満たすが普通规则の語彙対応要件を欠く——N73 人工物拒案の精神）。

## 5. 验证（④）

- 回归测试 `tests/test_night86_rule_o.py` **12 tests**（正例×3 族＋無護栏反例＋空白文语义＋
  拒案不复活 4 test べから族/はざる/使役/scramble+べきか+とも+なかれ＋構造ロック＋幂等/现代句/
  echo 行型）——**pytest 422→434 passed**（12.7s）。
- 真跑（TestClient 完整链・tools/night86_eval_4000.py / night86_eval_8165.py）：
  - **golden_4000：avgDist 13.495→13.491／exact 24/4000（不変）／error 0**——真跑改写 8 行＝
    sim 预测 8 行と new_text 逐位一致、計画外 0・欠落 0・変差 0。
  - **golden_8165：avgDist 13.505→13.502／exact 30/8165（不変）／error 0**——真跑改写 15 行＝
    sim 预测 15 行と逐位一致、計画外 0・欠落 0・変差 0。
  - 両口径とも N85 归档（13.495／24／0・13.505／30／0）の「优于或等于」を満たす。
  - 归档：eval/night86_results_4000.json（默认口径登记用）・eval/night86_results_8165.json（扩充归档）。
- `tools/verify_readme_facts.py` → **19/19 OK・exit 0**（N78 先例同款の必要伴随：归档源
  night78→night86 切换＋Rule O 語数断言追加＋README 数字行同步 13.491/13.502/テスト 434/Rule O 3 語）。

## 6. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `86: ["night86_results_4000.json"]`（仅此一条）。
- **accept 86：PASS（fail=0 skip=0、30.9s・首跑即 PASS）**——repo_clean ✓／pytest 434=434 ✓／
  eval_integrity（night86_results_4000.json 実查：id 唯一・自报数一致・expected 未改）✓／
  rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate 退化页 0 ✓。

## 7. 移交

1. **なかれ→莫かれ 拍板事項の更新**：post-N 残量 16→**17 行**（N84 rerun 追加 rikutou34-7・
   すことなかれ 行 81→80 改善側）。排除 guard（非「莫大於」）か kanji→kanji guard 規則の
   機構追加で 17 行 13 改善/1 変差/3 same → 80 行規模再候補（拍板条件は night78_mokaku のまま）。
2. **べからず族 89 行 79 改善の 1 変差回避は不可**（exp 自写仮名 4〜5 行が全字形共通死因）——
   拍板で「exp 自写仮名行の許容（変差 5 見込みで Δ−0.013）」を許すなら一発で収まるが、
   0 変差硬門の撤廃を伴うので提出のみ（本夜は収録しない）。
3. がため/何のごとく 残量 1 行ずつ（rikutou37-2/shiki050-4）＝rerun 行の尾段 guard 上下文が
   守り字を欠く N84 分支正規挙動——救うには rerun 行の guard を全文に広げる機構変更（別拍板）。
4. 長尾扫描の scramble patch 3 件は「語彙対応でない repl」拒案基準を初めて明文化した
   （Δ 線達成でも拒）——次夜以降の scan 系候補判定に転用可。
5. N84 §8 移交（夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行）は本夜も一字未动。

## 8. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；backend/main.py・词库
  （glossary_lexicon*.py）一字未改 ✓；site-packages 一行未动 ✓（Levenshtein C 库は
  .night72_deps 不在のため纯 Python 回退＝night85_eval lev と同一算法、归档 edit_distance と
  逐位一致を sim/pipeline で確認）
- 允许清单内文件のみ ✓：backend/kundoku_rules.py、tests/test_night86_rule_o.py、
  tools/night86_{mine,probe,sim,eval_4000,eval_8165}.py、tools/verify_readme_facts.py（归档源
  切换＋Rule O 語数＝N78 先例の必要伴随）、tools/accept_night.py（86 一条のみ）、
  eval/night86_*（mine/probe/sim/combo/results_4000/results_8165/accept_night_86）、
  README.md（数字行＋テスト行＋Rule O 句）、ROADMAP.md（末尾一行）、SHIFT_LOG.md、
  ACCEPT_LOG.md（accept 自動追加分）、REPORT_NIGHT86.md ✓；scratch 文件なし（pip 試行の
  .night72_deps 半成品は削除済み・pip 0 回成功）
- SHIFT_LOG 纯追加（.NET AppendAllText 絶対パス・UTF-8 無 BOM・byte807=243 写前后断言）✓；
  无 OCR／guwenbert／网络 ✓（web_search 0・ページ取得 0）；本夜工具 web 使用 0
- 本地分支两提交（主 `15001cd`＋wrap-up）、**未合 master、未推远程** ✓

## 9. 偏差注记

1. 任务书②の「るべから 27 行」型 B2 頭部候補（るべ→可）は T1〜T4 で 7/5/1/3 変差と全部不通——
   N78 §8-1 の prefix 長键再検を実行したが、べからず族は exp 自写仮名死因で长键でも救えなかった
   （ことな族と異なり守り字で分離できる行が存在しない）。方法論の限界確認として記録。
2. sim の長尾扫描（uniform exp_seg・len≥3・発火≤120）は本夜初导入——5 件の 0 変差候補を出したが
   2 件（たりせ/なきか）は語彙対応実証の上で収録、3 件は scramble patch で拒。scan は gate の
   補完であり、単独では収録判定をしない設計。
3. 行分类断言（7916/30/218/1）を mine/probe/sim 三脚本に組み込み——N84 分支の静的再現が
   崩れた場合は即停止する設計（真跑逐位一致の前提条件）。
