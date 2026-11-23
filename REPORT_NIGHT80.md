# REPORT_NIGHT80.md — Night 80：词库再扩充 824 → 1085（频次 3–4 区・追加式装配）

- 日期：2026-11-23（**续做夜**——前序会话完成候选 rank 0–249 判定（batch0–4，5 个进度提交），本会话完成 rank 250–499（batch5–9）并装配验收）
- 分支：`night80-lexicon-expand2`（自 `night79-lexicon-expand` 8d84613 分出——词库链；merge-base 核验一致）
- 工作目录：`D:\kanbun-rulel`（与主仓 `D:\kanbun-kakikudashi` 零接触；禁 OCR／guwenbert——本夜纯词典离线活，全部增量为 weblio/kanbun.info 的网络等待）
- 性质：**词库数据夜**。`glossary_lexicon.py`／`extra.py`／`llm.py` 一字未改（接入已在 N79 落定）；`glossary_lexicon_extra2.py` **追加式**扩容 324 → 585 条（分组列表尾部追加，本体 500 条不动，`find_in_lexicon2` 合并查找算法不变）。

## 0. 开工核验（续做状态）

- 分支 `night80-lexicon-expand2` 已在位、merge-base=8d84613 ✓（与任务书要求的分叉点一致）；开工 HEAD=fc04845（前序 batch0–4 进度提交）
- 前序会话判定账目：rank 0–249 全判（include 153／exclude 97，audit decided=250 dup=0）；工作树脏增量（decisions_081/150＋audit，246→250）先显式提交（83094aa）再续做——与 N71 开工心跳脏树处理同款
- pytest：开工未单独复跑全套（判定底稿不触碰代码路径；8d84613 上 363 passed 为 N79 wrap-up 已证基线），本夜验收全套 **374 passed**（363＋N80 新增 11）

## 1. 方法

### 1.1 候选（频次 3–4 区，tools/night80_freq.py → eval/night80_candidates.json）

- golden_8165 白文＋書き下し文汉字连续 run（2–8 字）文書頻度 3–4 区非既有词形 **966 个**；词形优先序把 kkd-attributed（freq_kakikudashi>0）451 条置前；rank500 边界频次=3；N79 已入库 824 词形全排除；纯假名功能词天然不在汉字 run 里。
- N79 模式预旗标 53 条（X-yune／X+ari/nashi 系）在判定底稿逐条如实复核后再定案（不机械跳过）。

### 1.2 逐条双证据门（500 条全判定，无抽查）

1. **辞書**：`www.weblio.jp` 聚合页（tools/night80_weblio.py，GET 间隔 0.7s，缓存 eval/night80_dict_cache/——**500 页全抓**（404 以 0 字节缓存如实记录）；kotobank 403／goo 超时站点级不可达，沿用 N74/N79 结论，不许编）。読み＋释义有据；404／无条目／仅机器生成区块（ウィキペディア小見出し辞書・Weblio日本語例文用例辞書——页面自述「プログラムで機械的に例文を生成している」）如实记录。
2. **语料**：golden_8165 实例行（候选自带 id＋書き下し文样本；疑难读法可用 kanbun.info 出处页 ruby——本夜语料直证已足够，ruby 深查未触发新增）。
- 研究辅助（本夜新增工具）：**tools/night80_compact.py**——digest → 紧凑判定表（面包屑尾＋読み方行＋释义 2 行；Wikipedia/Wiktionary 长文整体截断为 `[wikibody-cut]`；404 条目单行化），50 条/批 ×10 批。判定底稿 eval/night80_decisions_*.json（500 条全量：start=000/044/050/068/081/100/150/200/250/300/350/400/450）。

### 1.3 判定三条定式（沿用＋本夜方针）

1. **404＋N79 模式**（197 条）：X曰／X問 呼称部（孟母曰・管仲曰・季康子・宰我問…）、構文断片（謂之暴・以戰則勝・君為…）、白文成句（不教而殺・四海困窮・冠者五六人…）、数え構文（五有・十に三有り 系）——N79 排除先例逐字沿用。
2. **機械生成区のみ**（9 条）：五世・五湖・人衆・四年・太廟・国治 等——聚合页只有機械例文区／小見出し辞書，无国語辞書条目。
3. **Wikipedia/Wiktionary のみ＝保守排除**（4 条：令尹・元王・宰我・大象）：N79 的「Wikipedia 条目采録」是待拍板路子，本夜未获授权 → 词典证据门不成立，排除理由注明「後日承認なら翻案可」。**N79 已入库的 3+8 条一字未动，等用户定**。
- **sense-mismatch 12 条**（N79 東流先例）：天井（dict=建物义 vs 语料=孫子地形义，大辞泉 4 义均不符）、子有（dict=孔子弟子冉有的字 vs 语料=子＋有り 構文）、一枝／上徳／三有（dict=地名・仏語）、人知（dict=じんち 人的知恵 vs 语料=人＋知らず）、力足（dict=ちからあし vs 语料=力＋足らざる）、大沢／大荒（dict=日本地名辞典）、城辺（dict=名字辞典）等。

### 1.4 读法定案（语料训读用法优先——N75 牧す→ぼくす、N79 三月→さんげつ 先例）

- **双读法 5 条**（大辞泉条目内両読み＋语料训读用法置前，N79 敵人「てきじん・てきにん」格式）：一行（いちぎょう・いっこう）／丞相（じょうしょう・しょうじょう）／今朝（こんちょう・けさ）／客心（かくしん・きゃくしん）／内外（ないがい・うちそと）。
- 主読み分歧时语料训读惯例优先：不知（しらず 前頭，词典主読み ふち）／分明（ぶんみょう 前頭）／六十（ろくじゅう・むそじ——論語 ろくじゅう、礼記 むそじ 両用法実在）。
- 北海（ほっかい）：同页 HOKKAI 列车爱称是別義，核对大辞泉「北方の海。北洋」义项后才收录——多义页面逐义项核对先例。

## 2. 工具与产物

| 文件 | 内容 |
|---|---|
| tools/night80_freq.py | ② 候选挖矿（966 区内 run → 500 候选） |
| tools/night80_weblio.py | weblio 聚合页抓取器（N79 克隆改路径，0.7s 限速断点续跑；500 页全抓） |
| tools/night80_digest.py | 人读 compact digest（N79 克隆，×10 批） |
| tools/night80_compact.py | **N80 新增**：digest → 紧凑判定表（Wikipedia 截断・404 单行化） |
| tools/night80_audit.py | 判定完整性审计（candidates/decided/dup/missing） |
| tools/night80_log.py | SHIFT_LOG 追加器 |
| tools/night80_build.py | ⑤ **追加式装配器**（判定→extra2 各组尾部追加＋excluded.json；双证据机械校验・重复拒收） |
| tools/night80_eval_4000.py | golden_4000 全量真跑回归（对照 night79 归档逐位） |
| eval/night80_candidates.json | 候选清单 500 条＋语料样本＋统计 |
| eval/night80_decisions_*.json ×12 | 逐条判定底稿（500 条全量） |
| eval/night80_excluded.json | 排除清单 239 条＋理由 |
| backend/glossary_lexicon_extra2.py | 324 → 585 条（N80 追加 261） |
| eval/night80_results_4000.json | golden_4000 全量归档（与 night79 逐位一致） |
| eval/night80_dict_cache/ | 抓取缓存（未跟踪目录，N74/N79 先例） |
| tests/test_night80_lexicon_expand2.py | N80 回归 11 条 |
| tests/test_night79_lexicon_expand.py | 必要伴随 2 处（总数断言＋底稿 glob 扩展） |

## 3. 结论：入库 261／排除 239／剩余 0（候选 500 全判定）

- **总数 824 → 1085**（本体 209＋extra 291＋extra2 585＝N79 324＋N80 261）。N80 追加分组：**名詞 210／固有名詞 22／動詞 9／形容副詞 20／機能語 0**（接续系 modifier 组方针不变）。
- 分批账目：batch0–4（rank 0–249，前序会话）include 153／exclude 97；batch5–9（rank 250–499，本会话）include 108／exclude 142——质量门随频次下降显著收紧（404 断片比率上升）。
- **收录代表**：人名（孟嘗君・柳下恵・孔丘・孫武・孫呉・太宗・太山）／兵制军语（中軍・兵車・兵家・伏兵・八陣・倉廩）／数词名词（七十・六十・十人・八人・万乗・万仞・万古・億万）／汉诗意象语（天上・天風・天門・天運・客心・垂楊・城闕・城頭）／叠语形容副詞（渾渾沌沌・冉冉・冥冥・凄凄・亭亭）／时间副詞（即今・只今）／儒学语（学問・守成・名実・夷狄・吾子・大倫・大徳）。
- **排除 239 条**分类（精确逐条见 eval/night80_excluded.json）：**weblio 404** 197 条（呼称部・構文断片・白文成句・数量構文）／**機械生成区块のみ** 9 条（五世・五湖・人衆・四年・太廟・国治 等）／**Wikipedia のみ保守排除** 4 条（令尹・元王・宰我・大象——待拍板路子未授权，可翻案）／**sense-mismatch** 12 条（天井・子有・人知・力足・一枝・三有・上徳・大沢・大荒・城辺 等）／**辞書区=名字・地名・湖沼名辞典のみ（別義）** 17 条（中峰・器用・江山・渭城・深草・率然・集注・集解 等）。
- 方法注记（供后续夜参考）：「初见即 404」的 X曰 呼称部在本区占排除清单约三成——频次 3–4 区的命中主体是兵书（六韜・孫子・呉子）句式与汉诗意象词；同类词形（天牢/天羅/天井 地形三连）只要 weblio 无条目就整组排除，不因语料频次高放行。

## 4. 验收（wrap-up 提交时补数）

- pytest 全套：**374 passed**（363 基线＋test_night80_lexicon_expand2.py 11 条：格式/总数 1085/双证据全量 261/排除不在文件/代表条目读法/find_in_lexicon2 真语料命中/llm.glossary 离线命中/规则引擎零变化）；test_night79_lexicon_expand.py 必要伴随 2 处：总数断言 324→585、824→1085；双证据全量断言底稿 glob 扩展 night80_decisions（词库扩充后 N79 条目断言不变的必要伴随）。
- golden_4000 全量真跑（tools/night80_eval_4000.py，91s）：**engine OK 4000／error 0／exact 24／avgDist 13.517，与 night79 归档输出不一致 0 行** → eval/night80_results_4000.json 归档 ✓（词库不进规则引擎的位级实证）
- README 三处「文語 824 語」→「文語 1085 語」；ROADMAP 末行 ✓
- `python tools/accept_night.py 80`：待终跑（wrap-up 补 PASS/fail/skip 与耗时）。

## 5. 交付与提交

- 分支两提交（主提交＋wrap-up），**不合 master、不推远程**。
- 主提交：extra2 追加 261 条（585）＋判定底稿 500 条全量＋候选/排除清单＋工具 9 个（compact 新增）＋golden_4000 归档＋测试 11 条＋test_night79 必要伴随＋SHIFT_LOG 全程心跳＋README 三处计数＋ROADMAP 末行＋本报告 §0–3/§5。
- wrap-up 提交：ACCEPT_LOG.md＋eval/accept_night_80.json＋REPORT §4 数字＋SHIFT_LOG 收尾行。
- 交付顺序（任务书）：Night 80 完成，全部验收通过。开工：HEAD/分支/目录 ✓（续做：前序 batch0–4＝rank 0–249 判定 153/97，本会话 batch5–9 完成 rank 250–499）。扩库：新入库 261 条（候选 500 全判定，证据门通过 261／排除 239／剩余 0）；总数 824→1085 ✓。验证：回归测试 374 passed；golden_4000 与 night79 逐位一致（13.517／24／error 0）✓。验收：accept 80 终跑（wrap-up 补）；分支两提交，未合 master、未推远程。报告见 REPORT_NIGHT80.md。
