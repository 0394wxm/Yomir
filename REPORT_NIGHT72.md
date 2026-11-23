# REPORT_NIGHT72 — Rule L 挖词＋上线（ZCode 并行线，master ad18f20 单会话）

日期：2026-11-22（Night 72 挂机段）；开工 HEAD：`ad18f20`（= N70 wrap-up 点）；分支 `night72-rulel`（独立目录 `D:\kanbun-rulel`，AutoClaw 的 N71 在主仓满负荷跑整本 OCR＋guwenbert——本夜与其零接触）；未合 master、未推远程。

## 0. 结果一句话

**Rule L 9 条收录（含 N69/N70 拒案翻案 3 条：つひに→終に・がため→為・はざる接続拆分）＋模拟全 0 变差＋组合 244 行改写／改善 239／变差 0／幂等坏 0**；TestClient 双口径真跑与离线模拟**逐位一致**——golden_4000 **avgDist 13.584→13.544／exact 24／改写 114（双向 0 差）**、golden_8165 **14.632→14.583／exact 30／改写 244（双向 0 差）**；pytest **260→283**；accept 72 终跑 **PASS（fail=0 skip=0）**；verify **15/15 exit 0**。拒案とも（1 変差）・べからず（5 変差）・がため落选字形（が為に 2／為に 3 変差）实数归档。

## 1. 开工核对与隔离

- `git clone D:\kanbun-kakikudashi D:\kanbun-rulel`（开工只读 clone 一次，此后未进主仓目录）→ `checkout -b night72-rulel master` → HEAD=`ad18f20` ✓、tracked 零改动 ✓
- git 身份 zwork@local 自配（clone 不继承主仓本地身份）
- **pytest 首跑 259+1**：`test_ocr_missing_runtime_message_shape` FAIL——fresh clone 缺 **gitignored 的 `ocr_runtime/`**（模型不入库，`backend/ocr_engine.py` 头注释记载的机器本地解压产物，需从 `D:\dlkotenocr-lite` 的 app.zip 解压）；按头注释原样解压后 **260 passed**，代码零改动。全程未跑 OCR 推理（只解压文件让 `is_available()` 反映真实环境，不违反本夜禁 OCR）
- SHIFT_LOG：clone@ad18f20 的 byte807=**0x28**（主仓 N71 现行文件的 0xF3@807 与本 clone 不同源——主仓文件在 N71 手里继续演化）；本夜全部 `'ab'` 追加（git diff **+N 行／−0 行**，前缀零改动）
- 方法论输入：REPORT_NIGHT68.md（Rule J 方法）＋REPORT_NIGHT70.md §2–§3（Rule K 上线＋真跑对照）＋REPORT_NIGHT69.md（拒案表与挖词四切面）

## 2. 挖词（②）

- 基线 = `eval/night70_results_8165.json`（K 后链尾真机归档，8165 条 0 error）。链尾断言：results/golden 同序；night69_combo 768 行 got==new_text；非 combo 行 got==night68 got（K 只改 combo 行的再验证，全部通过）
- `tools/night72_mine.py` 四切面 → `eval/night72_mine.json/.txt`：
  - **A 字符 delta**（shibu02 1310／[4000:7908) 3908／paren 257／全库）：頂位 為 Δ560（动词活用结构差为主，规则层不可达）、可/将/其…；SHINJITAI 系残量 0
  - **B 假名串 delta**：顶部 して/なりて/するを/みて…＝Night 24/25 定性结构差；词形级残量＝とも 162・がため 71・ゆえ 16・ただ 18・はじめ 15・いずくんぞ 20（Rule I 焉护栏外）・べず 10
  - **C 拒案复查专切**（はざる/とも/がため/つひに，任务书②指定）：**守り字旧字体三连发现**——がため 行白文 92/92 写「**爲**」（N69「guard 為 0 命中」死因修正：搜的是新字体 為、白文写旧字 爲）、いずくんぞ 悪-target 行白文写「**惡**」7 行、とも 行白文 224/224 写「**與**」（N69 的「与」guard 结论失效，但翻案仍不成：exp 主目标 と 168 行，repl 与に 121 変差）
  - **D SHINJITAI 1:1 残量 = 0 对**（N69 结论维持，本夜不扩充）
- `tools/night72_probe.py` 行级取证 → `eval/night72_probe.txt`；候选清单 `eval/night72_candidates.txt`（每条：词形・白文护栏・出现次数・exp 目标・判定）

## 3. 模拟门（③）

- `tools/night72_sim.py`（night69_sim 机制照抄：lev/apply_one/run/idempotent，19 候选单跑 → 0 变差门 → 组合 → 幂等 → 双口径离线真算）
- **性能注记**：首跑纯 Python lev 卡 **45 分钟**（N71 满负荷抢 CPU，进程实测 ~13% CPU）→ 按任务书记一笔后杀掉重写，三项加速（数值语义不变）：①Levenshtein C 库（`pip --target .night72_deps` **隔离目录**，不碰全局 site-packages；与纯 Python 参照实现 200 对真实行抽查逐位等价，import 失败自动回退）②d0=lev(got,exp) 全候选共享缓存只算一遍 ③未改动行跳过第二次 lev → 全程 **<2 分钟**
- **收录 9 条（单条全 0 变差）**：

| 规则 | 护栏（白文） | 改写 | 改善/变差 | Δ |
|---|---|---|---|---|
| つひに→終に | 終 21/21 | 21 | 20/0 | −0.005 |
| いずくんぞ→安んぞ | 安 | 33 | 33/0 | −0.009 |
| いずくんぞ→悪んぞ | 惡/悪 | 8 | 8/0 | −0.002 |
| ただ→但だ | 但 26/26 | 26 | 26/0 | −0.003 |
| ゆえ→由 | 由 23/23 | 23 | 23/0 | −0.003 |
| はじめ→始め | 始 30/30 | 30 | 30/0 | −0.007 |
| がため→為 | 爲 92/92 | 92 | 89/0 | −0.018 |
| はざるなり→わざるなり | （無＝接続拆分） | 13 | 13/0 | −0.002 |
| はざるを→わざるを | （無） | 7 | 5/0 | −0.001 |

- **拒案（0 变差门／無益，逐行证据 eval/night72_sim.txt）**：はざる→わざる（1 変差 24shihin10-4 17→18——接続拆分后 なり/を 翻案收录）、とも→と（1 変差 yoryoezu-1 93→94，exp 与に）、とも→与に guard 與/与（**121 変差**——與 修正后发火 224 行，exp 主目标 と）、がため→が為に（2 変差 rongo0518-1/mitabitsu-1）、がため→為に（3 変差）、がため→が為（过门 74 改善但劣于 repl 為——同一 kana 只収一条、落选字形不登録＝N68 ことごと\* 死条目教训）、べからず→可からず（5 変差 shushu-4 等——exp 自写仮名 べからず，N68 §8-3 结构性 gap 实证）、べず→可ず（目標 0・守り 0）、はざるか/はざるに（0 変差但 Δ−0.000，低于 N69 hezu −0.001 収録线→無益）
- **翻案要点（がため→為）**：repl 為 是 exp 实际写过的裸形（22 行），与全部 exp 字形（為す45/為22/為に7/が為に4/が為3/為り6/為る5）共享单字「爲→為」、编辑距离只降不升——N64 毋かれ「共享汉字只降不升」同款论证；N68 的 2 変差行是 repl が為に 混写造成，換 repl 后消失
- 组合幂等 bad=0；多守り行実測 1 行（sanryaku03-4 安∧惡）→ 表順先勝（安），语料内 0 変差
- 双口径离线真算：**4000 改写 114／改善 110／变差 0、13.584→13.544；8165 改写 244／改善 239／变差 0、14.632→14.583**；shibu02 改善 89／漢詩 57（子部长句段主矿脉）
- repl 终字形断言：`normalize_shinjitai(repl)==repl` 9/9（响应端 ortho=True 归一不改写→模拟与真机可比）

## 4. 上线＋真跑对照（④）

- `backend/kundoku_rules.py`：`L_KANA_TO_KANJI` 9 条（序=COMBO_ORDER）＋`L_LONGER_WORDS`（ただ＝E ただ 同款＋たださ；ゆえ＝ゆえん/ゆえに；其余 probe 實測无更长词冲突）＋`style_kana_to_kanji_l`（K 世代同款 `if guard and hb and not any(...)`——guard 空元组＝無条件、未用恒真字符串伪装）；`style_fix_with_hakubun` 链尾接 L（K 之后）
- `tests/test_night72_rule_l.py` **23 项全过**：每条正例（実語料行型）＋无护栏反例＋guard=() 空白文発火＋空白文 guard 規則発火（E〜K 同语义）＋いずくんぞ 多守り行先勝＋長語マスク（ただす/ただいま/ゆえん/ゆえに）＋表整形性（9 条・repl 終字形断言）＋拒案不复活＋**N69 変差行不触锁定**（真なりて奪はざるとも 一字不动）＋链序 K→L＋幂等＋现代句探针（はじめまして 等）＋经典句回归；全量 pytest **283 passed**（260＋23，57.9s）
- **TestClient 真跑**（`tools/night72_eval.py`：期望值从 `night72_sim.json` **读入不手抄**；基线自检 night70 归档 avgDist==sim avg_old ✓；monkeypatch save_kundoku）：
  - golden_4000：**avgDist 13.544／exact 24／error 0**；改写 **114＝预测 114（双向 0 差）**／改善 110／变差 0／持平 4
  - golden_8165：**avgDist 14.583／exact 30／error 0**；改写 **244＝预测 244（双向 0 差）**／改善 239／变差 0／持平 5
  - 进程内确定性：8165 前 4000 行与 4000 单跑**逐位一致**；error→恢复 0／仍 error 0
  - ⑯ 偏科：8165 分段 s4000 改善 110／s3908 127／s257 2；**shibu02 长句段改善 89／0 変差**、漢詩段 57／0——任务书「子部长句段」主矿脉再确认（分桶：≤20字 avg 7.679、文体別 漢詩 6.868／詩経 5.108／故事 20.547／論語 26.044）
- **GT CER 逐位不变**（结构性证明，N63 §4/N70 §3 同款论证链）：OCR/GT 链全部输入文件（eval/night68_gt_cer.json、eval/night49_gt_lines.json、eval/ocr_gt_100.tsv 等）tracked 逐位未动（git status 空），本夜唯一产品代码改动＝`kundoku_rules.py` 的訓読显示层（OCR 管线不经过）→ CER raw **0.3568**／norm **0.3053** 逐位不变
- **guwenbert 本夜未跑**：原因——N71（AutoClaw 主仓会话）正在跑整本 OCR＋guwenbert 全量、机器满负荷；且任务书本夜明令禁 OCR／禁 guwenbert 全量（本夜影响面＝假名散布段，已由 golden_8165 全量双对照逐位覆盖，N68 §7 同口径）

## 5. 拒案表（0 变差硬门，模拟门逐行证据）

| 候选 | 改写 | 改善/变差 | 拒因（一句话） |
|---|---|---|---|
| はざる→わざる | 39 | 28/**1** | 24shihin10-4（はざるとも）exp 奪われず；正 guard 不可達（目標行白文字交集∖非目標行＝無し）→接続拆分翻案 |
| とも→と | 224 | 164/**1** | yoryoezu-1 exp 与に；白文 224/224 旧字 與 也不可分 |
| とも→与に（guard 與/与） | 224 | 36/**121** | exp 主目标 と 168 行，与に repl 大面积反加距 |
| がため→が為に（guard 爲） | 92 | 63/**2** | rongo0518-1/mitabitsu-1 目标混写——repl 為 翻案收录 |
| がため→為に（guard 爲） | 92 | 79/**3** | kakini-2/rongo1601-1/kunshikano-1 |
| べからず→可からず（guard 可） | 82 | 72/**5** | exp 自写仮名 べからず 5 行（shushu-4 等）——N68 §8-3 结构性 gap 实证收口 |
| べず→可ず | 0 | 0/0 | 目標 0・守り 0 |
| はざるか/はざるに→わざる… | 7/2 | 3/0・1/0 | 0 変差但 Δ−0.000（低于 hezu −0.001 収録线）→無益 |

N69/N70 拒案 4 条复核终局：**つひに 翻案收录**（真实词形 終に＋守り 終 21/21）、**がため 翻案收录**（repl 為＋守り 爲）、はざる 接続拆分部分翻案（なり/を 2 条）、とも 拒案维持（1 変差＋與 guard 也救不了）。

## 6. README / verify / ROADMAP 同步（⑤）

- README 数字行 4 处：数字节头（`night72-rulel`・Night 72・**主提交 `1327089`**——wrap-up 提交里按 `git log -1` 取数写入）、テスト行 **241→283 passed**（N70 已漂移：N70 未把 241 同步到 260、verify 无该断言漏网——本夜一并修正）、規則エンジン行（**13.544**／**24/4000**＋N72 Rule L 注记＋`eval/night72_results_4000.json` 口径）、ルールチェーン行（Rule L 第 8 系列・**9 語**追加）、已知問題①（N72 口径 7.679／6.868／5.108／20.547／26.044）
- `tools/verify_readme_facts.py`：Rule L 计数行追加＋归档源 night70→night72 切换（README 数字行更新的**必要伴随**，N68/N70 同款先例，如实声明）→ **15/15 OK、exit 0**
- ROADMAP.md 末尾 CLOSED 一行

## 7. 验收（⑤）

- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `72: ["night72_results_4000.json"]`（仅此一条，67/68/70 同式）
- accept 72 首跑：**PASS（fail=0 skip=1）**——skip=repo_clean「git 不可用」（验收门子进程 PATH 无 git，本会话 shell 未设）；终跑（主提交后、`PATH=D:\Git\cmd;...` 设定下）**PASS（fail=0 skip=0，232.6s）**：repo_clean ✓／pytest **283=283**（121.6s）／eval_integrity（night72_results_4000.json 实查：id 唯一・expected 未改）✓／rule_regression ✓／engine_smoke ✓／perf_envelope ✓／order_rate off **98.57%**（+0.00pp）／on **98.63%**（+0.00pp）退化页 0 ✓。两次运行如实留存 ACCEPT_LOG.md

## 8. 移交

1. **guard 候补新旧字体并查（建议成文规矩）**：本夜 3 处旧字体守り字（惡/悪、爲/為、與/与）——kanbun.info 白文保持旧字体/異体字，mine/probe 的 guard 候补必须新旧两形并查；本夜 probe 首版自己复现了一次（いずくんぞ 悪 0 命中）、N69 的 gatame 死因同源。建议下夜把该规矩写进 mine/probe 模板
2. はざる残量 singleton：か(7)/に(2)/者(2)/の/は/有/所/兮/べ/こ/と(変差行) 各 1~2 行不收；其中 はざる者 2 行全是 わざる 目标，但 key 含汉字「者」破坏系列「纯 kana key」惯例——要收需先拍板
3. とも 结构性 gap：exp 在同行混写 と/与に/共に（yoryoezu-1 1 変差；repl 与に 121 変差）——N55 べき 类页面级编辑习惯，无运行时信号，不建议再试
4. べからず→可からず：5 行 exp 自写仮名 べからず（N68 §8-3 预言实数确认）——べき/べから/べからず 族结构性 gap 就此收口
5. Levenshtein 依赖：`.night72_deps/` 隔离目录（pip --target，未入库、未动全局 site-packages）；数值与纯 Python 参照 200 对逐位等价；是否入 requirements/gitignore 需拍板（tools 自带回退路径）
6. README テスト行 verify 断言缺失：N70 漂移（241→260 未同步）漏网——建议 verify 加 pytest 计数断言（拍板）
7. 45 分钟规则实践注记：模拟门首跑卡 45 分钟（N71 抢 CPU）——该步不可跳（后续全部依赖它），处置＝杀掉重写加速（C 库＋缓存，语义不变）；「跳过」指令对**必须经过的关键路径步骤**建议下夜任务书明确处置方式

## 9. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 实查）；全局 site-packages 一行未动 ✓（依赖装在 .night72_deps 隔离目录）
- 只动允许清单内文件：backend/kundoku_rules.py、tests/test_night72_rule_l.py、tools/night72_heartbeat/mine/probe/sim/eval.py、tools/accept_night.py（仅 72 一条）、tools/verify_readme_facts.py（Rule L 计数行＋归档源必要伴随）、README.md（数字行＋表头）、ROADMAP.md（末尾一行）、SHIFT_LOG.md、ACCEPT_LOG.md、eval/night72_*（candidates/mine/probe/sim/combo/results_4000/results_8165/accept_night_72）、REPORT_NIGHT72.md ✓；scratch 文件（eval/_*.txt・night72_*_progress.txt 等 7 个）用后即删 ✓
- 与 N71 零接触：开工只读 clone 一次（任务书明示的建库方式），此后未进 D:\kanbun-kakikudashi ✓；本夜无 OCR 推理、无 guwenbert ✓
- SHIFT_LOG 纯追加（git diff +N/−0）✓；本地分支两提交、**未合 master、未推远程** ✓；审查器未拦任何文件 ✓

## 10. 偏差注记

1. pytest 首跑 259+1＝fresh clone 缺 gitignored ocr_runtime（环境件非代码问题）；按 ocr_engine.py 头注释解压 app.zip 后 260，代码零改动——主仓不受影响（N71 的 ocr_runtime 原样在）
2. SHIFT_LOG byte807：clone@ad18f20 版本为 0x28（主仓 N71 现行文件的 0xF3@807 不同源）；本夜 'ab' 追加制，git diff 证明前缀零改动
3. README テスト行 241 系 N70 遗留漂移（N70 只更新了 4 处数字行、漏了テスト行；verify 无断言故漏网），本夜直接写 283（对 260 一次补上）
4. verify 归档源切换 night70→night72＋Rule L 计数行——超出「仅 Rule L 计数行」字面的必要伴随（N68→N67、N70→N68 同款先例）
5. 模拟门首跑卡 45 分钟按任务书记一笔；杀掉重写属步骤内加速（未跳步），见 §8-7
6. 本夜工具用量克制：无 web_search/fetch/图片/视频生成；pip 一次（清华镜像、隔离目录）；全部本地执行
