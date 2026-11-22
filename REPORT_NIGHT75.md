# REPORT_NIGHT75.md — Night 75：修词库 19 条错项

- 日期：2026-11-22 夜（周末卡，09:00 到期）
- 分支：`night75-lexicon-fix`（自 `night74-lexicon` 分出，基点 HEAD=6078100）
- 工作目录：`D:\kanbun-rulel`（与 N71 零接触；禁 OCR/guwenbert，本夜只有轻量真跑 golden_4000）
- 范围：**只修 N74 审计 §3.1 判「错」的 19 条**；其余 481 条一字未动；README 数字不动（词库仍 500 条）。

## 1. 开工核验

- `git checkout -b night75-lexicon-fix night74-lexicon`；HEAD=6078100 ✓（N74 wrap-up 提交）
- pytest 全套：**307 passed（118.92s）** ✓；已跟踪文件零改动 ✓

## 2. 修库：19 条处置（17 修 + 2 核验后不改）

### 2.1 逐条修前→修后对照（17 条）

| idx | 词形 | 字段 | 修前 | 修后 |
|---|---|---|---|---|
| 7 | 況んや | reading | ましてや | いわんや |
| 51 | たり | meaning | 活用：たり・て・たれ・たろ | 活用：たら・たり・たる・たれ |
| 60 | 犹ほ | reading | なおほぼ | なおほ |
| 60 | 犹ほ | meaning | （异体表記） | （異体表記） |
| 77 | 策うちて | reading | しむちて | むちうちて |
| 85 | 闚う | reading | のぞう | うかがう |
| 85 | 闚う | meaning | のぞく | のぞき見る（与训 うかがう 对齐） |
| 88 | 相謂いて | reading | あいていいて | あいいいて |
| 91 | 屠る | meaning | （俗に）ほしいままにする。屠る＝さばく。 | 切り裂く。いけにえをさばく（文語ほふる／現代仮名遣いほうる）。 |
| 114 | 一簣 | reading | いき | いっき |
| 126 | 异端 | word | 异端（简体＝死条目） | 異端 |
| 137 | 收拾す | word | 收拾す（简体＝死条目） | 収拾す |
| 160 | 然りて | meaning | …（supar 输出常见的接续形）。 | …（supar 出力でよく見る接続形）。 |
| 174 | 孰か学を好む | reading | しょかがくをこのむ | いずれかがくをこのむ |
| 178 | 画す | reading | えがくす | かくす |
| 182 | 事う | reading | まつらう | つかう |
| 204 | 守株 | reading | しゅじゅ | しゅしゅ |
| 212 | 子貢 | reading | しごう | しこう（extra 文件） |
| 499 | 雖 | reading | えど | いえど（extra 文件） |

（entries 7/51/60/77/85/88/91/114/126/137/160/174/178/182/204 在 backend/glossary_lexicon.py；212/499 在 backend/glossary_lexicon_extra.py。）

### 2.2 两条核验结论（不改，原因如下）

- **舎（idx 429）— 不改**。N74 的「错」判据是大辞泉训（おく・やどる）里没有「すつ」。本夜对照语料振り仮名等价物（golden_8165 書き下し文）：rongo0710-1「之を**舎つ**れば則ち蔵る」、rongo0604-1「山川其れ諸を**舎てんや**」、rongo1601-1「…と曰うを**舎きて**」——语料自身就把「舎」当「すつ/すてる」用（舎＝捨 的换字），与词库 word=舎／reading=す／meaning「舎つ。すてる。」完全一致。核验结论：**现值正确，不动**（N74 该条改判为语料惯例）。
- **玷く（idx 135）— 不改**。词典证据（N74 补抓页 x_玷：Wiktionary 訓「か-ける」、漢字辞典 訓「かける」）只有「かける」一训，建议中的「かく(つ)」系没有任何在册证据；语料 akujisenri-3 書き下し文写「終に艶詞の為に之を玷く」（无振り仮名可考）。核验结论：**证据不足，原样不动**，留待有 古語辞典级来源 时再拍板。

### 2.3 diff 行数

`git diff --numstat`：
- backend/glossary_lexicon.py **15 行改**（15 増/15 删）
- backend/glossary_lexicon_extra.py **2 行改**（2 増/2 删）
- 合计 **17 行 = 17 条修复**（另 2 条核验不改）✓；除两词库文件外，只有允许清单内的 SHIFT_LOG.md 追加与 tools/accept_night.py 的 NIGHT_ARTIFACTS 加 75 一条。其余 481 条词库内容一字未动（改写行的 old→new 全部逐字对应 §2.1 表）。

## 3. 验证（三道关）

1. **回归测试** `tests/test_night75_lexicon_fix.py`：**24 passed**。
   - 17 条修后值逐条断言（reading/meaning/词头）；
   - 舎／玷く 断言保持原值（防「顺手修」）；
   - Top-20 第 20 位「而」（存疑，N75 不修）断言 reading=て／meaning 未动；
   - 抽查 10 条（孔子/君子/金/天/者/然/曾子/楚/幸/誠）未动；
   - 词库总数断言 500。
2. **死条目复活**：`find_in_lexicon("異端を攻むるは、斯れ害あるのみ")` 命中「異端」——语料真实 3 行（itanosamu-1／kyorankito-1／daigaku00a-27）書き下し文都含「異端」，词头简体修正后**对真实语料复活**；「収拾す」用终止形文本「焚毀の書を収拾す」验证词形可命中。**如实记录一个局限**：akujisenri-2 書き下し文只有連用形「収拾し」（白文为「收拾」），终止形「収拾す」在该语料行不存在，find_in_lexicon 的精确子串匹配对该行仍不命中——这是词形设计与匹配机制的既有局限（残課題候选），不是本夜修复引入的回归。
3. **全量回归** `tools/night75_eval_4000.py`（TestClient 完整链真跑 golden_4000）：**engine OK 4000 / error 0；精确 24/4000；avgDist 13.517；与 night73_results_4000.json 输出不一致行 0**——词库不进规则引擎，数字与 night73 归档逐位一致 ✓。归档 eval/night75_results_4000.json。

## 4. 验收（④）

- tools/accept_night.py 的 NIGHT_ARTIFACTS 照 67/68/70/72/73 式加 `75: ["night75_results_4000.json"]`（仅此一处）。
- `python tools/accept_night.py 75`：
  - 首跑（主提交前）：**fail=1**——仅 repo_clean（SHIFT_LOG.md / tools/accept_night.py 为本夜合法改动但尚未提交，属「先验收后提交」的时序问题），其余 6 项全 PASS：pytest **331 passed = 331 collected**（307 + 本夜新回归 24）、eval_integrity PASS（night75_results_4000.json 已登记：4000 行、id 唯一、expected 与 golden.json 一致）、rule_regression / engine_smoke / perf_envelope / order_rate 全 PASS（order_rate 与基线差 +0.00pp，只测量不判死刑）。
  - 主提交后重跑（f184bf1）：**PASS（fail=0 skip=0，207.6s）**——pytest 331 passed = 331 collected（111.0s，收集 26.2s）；eval_integrity / rule_regression / engine_smoke / perf_envelope / order_rate 全 PASS（order_rate 与基线差 +0.00pp）。

## 5. 交付物与提交

- backend：glossary_lexicon.py（15 行）＋glossary_lexicon_extra.py（2 行），共 17 行，全部限于 19 条错项的字段。
- tests/test_night75_lexicon_fix.py（24 断言）；tools/night75_eval_4000.py、night75_log.py、night75_heartbeat.py、night75_roadmap.py；tools/accept_night.py 仅 NIGHT_ARTIFACTS 加 75。
- eval/night75_results_4000.json；SHIFT_LOG.md 追加；REPORT_NIGHT75.md；ROADMAP.md 末尾一行。
- 提交：主提交 + wrap-up，均在 `night75-lexicon-fix` 分支；不合 master、不推远程（等 N71 落地后与 72/73 一起合）。

## 6. 残課題（留给用户拍板）

1. N74 存疑 43 条仍待处理（其中需对照语料振り仮名的读音：牧す/釈て/喪ぼす/貳す/愈れる/止/未/布/失/樹 等）。
2. 玷く 的读音需 古語辞典级来源（KANJIDIC 只有 かける）。
3. find_in_lexicon 的精确子串匹配对「連用形文本 vs 终止形词形」（収拾す/収拾し 等）不命中——是否引入活用形展开由用户拍板。
4. SHIFT_LOG 首行误用 N74 标签（night74_log.py 复用所致），其后一律 N75 标签；append-only 不改历史。
