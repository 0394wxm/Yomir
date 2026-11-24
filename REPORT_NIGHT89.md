# REPORT_NIGHT89.md — Night 89：词库频次 2 区扩充 1301 → 1531（频次 2 区 top500・全判定剩余 0）

- 日期：2026-11-24（单会话完成 500 条全判定）
- 分支：`night89-lexicon-freq2`（自 master `35ba6e5` 分出——N88 规则链分支未合，本夜自 master 直分）
- 工作目录：`D:\kanbun-kakikudashi`（禁 OCR／guwenbert；本夜为词库数据夜，weblio・kanbun.info 源页核对外，无其他网络）
- 性质：**词库数据夜**。`glossary_lexicon.py`／`extra.py`／`llm.py`／`kundoku_rules.py` 一字未改；`glossary_lexicon_extra2.py` **追加式**扩容 801 → 1031 条（本体 500 条不动，`find_in_lexicon2` 合并查找算法不变）。N79 待拍板两项（同語彙 3 条＋Wikipedia 8 条——已按现状合入 master）本夜一字未动。

## 0. 开工核验

- 开工 HEAD=35ba6e5 ✓（=任务书要求）；分支 `night89-lexicon-freq2` 新建 ✓；工作树零改动（untracked 仅历史 eval/ 缓存）✓
- pytest 开工**完整重跑**：**434 passed**（13.28s，N80 漏跑教训执行）

## 1. 方法

### 1.1 候选（频次 2 区 top500，tools/night89_freq.py → eval/night89_candidates.json）

- 复跑 N79/N80/N82 同口径挖矿：golden_8165 白文＋書き下し文汉字连续 run（2–8 字）文書頻度，**zone＝頻度 2**；
- **基线＝現行語彙 1301 語形＋N79/N80/N82 排除済み語形 668（179+239+250）＝1969**（排除形は语库に無いので明示排除しないと再浮上——本夜の追加処置、程序内断言で数を検証）；
- **頻次 2 区総量＝3074**；排序＝任务書 §②「按频次＋kkd 归属优先」＝(-freq, kkd 直証先, len, word)——N80/N82 の (-freq, len, kkd) と違い kkd を len より先（任务書明記の優先順に従う；freq 2 区は全件同頻度なので実効順＝kkd 先）；
- top **500** 全件が候補：**kkd 直証 500／白文のみ 0／len 分布 2 字×500**（2 字詩語・人名が主命題＝N82 観察の裏返し）；pre_exclude 旗标 27（X曰 9＋X+有/無 18）——旗标のみで fetch は 500 全件実施（N80/N82 同款）。

### 1.2 逐条双证据门（500 条全判定，无抽查）

1. **辞書**：www.weblio.jp 聚合页（tools/night89_weblio.py，**500 页全抓**，gzip 传输＋**4 进程分段并发**・各路 0.7s 节流——N82 加速法；404 以 0 字节缓存如实记录；缓存 eval/night89_dict_cache/——未跟踪目录）。404 195 页／OK 305 页。kotobank 403／goo 超時は N74 以降結論のまま再試行せず。
2. **语料**：golden_8165 実例行（候補自带 id＋書き下し文 snippet，kkd 直証 500 全件自動語料引证）。
- **判定補助**：night82 工具链の night89 版（digest→compact→**judge 展開器**→audit→build）。判定は compact 表＋dig志 取证を agent が読み、pipe 区切り 1 行 1 条で night89_judge_*.txt（10 批）に書き、展開器で decisions JSON（10 批 500 条全量）へ。自動採証はパンくズ以降の実在辞書区から【見出し】＋読み方行を引用；**页头菜单行の誤採証（面包屑に「>」がない页でメニューの「古語辞典」等 DICTNAMES 行を拾う）は DE: 手差しで回避**——一悪・三杯・去留・台榭・太平・小学の 6 条で発動。
- **单步处置**：weblio 首回克隆で night82_candidates.json 残留を検出（N82 词表 466 页を誤抓）——**全缓存削除＋词表修正＋500 页再抓**（语义不变の重写、SHIFT_LOG 留記録）；night89_build の空 FUNCTION 组块（`FUNCTION = []`）非対応を検出——閉括号行アンカー方式に書き直し（N82 では FUNCTION 追加 0 で発火しなかった路径）。
- **追加後体裁**：N82 判定の meaning は「语料：…（出典）」尾段込みで書かれていたため、**追加 230 行の meaning から尾段を剥離**（純释义＝N82 文件内既有风格統一、语料・辞書证据は decisions 底稿に全量残置）。

### 1.3 判定三条定式（N79/N80/N82 沿用＋本夜実績）

1. **404・断片系**（196 条）：X曰 系呼称部（主曰・仲曰・備曰・妻曰・密曰・孫曰・僧問…）、X+有/無 系構文断片（仁有・勇無・媒無・害無・主無…）、数え構文（三万・十一・千騎・五屯…）、主語＋動詞連接（吾知・吾老・子往・君去・客散・力屈…）、兵書専門語 404（天牢・天陣・余奇・偏箱・兵教・扶胥系…）、詩語 404（一雁・中宵・夜月・双闕・娥娥・孤鴻…）；
2. **sense-mismatch・専門辞典別義**（41 条）：一乗（dict＝仏語 vs 语料＝兵制単位）、五車（dict＝恵子五車 vs 軍制車五両）、人望（dict＝人気 vs 语料＝人が望む構文）、中略（dict＝省略記号 vs 三略中篇）、全曲・分限・力卒（dict 現代义 vs 尉繚子兵教条目名）、単車（dict＝オートバイ vs 一輌の戦車）、八寸（dict＝料理 vs 符の長さ）、八尺（dict＝やさか尊称 vs 長さ）、十手（dict＝武器 vs 十の手）、四維（dict＝礼義廉恥 vs 四綱で支える）、地大・国安・国富（構文 vs dict 义）、大黄（dict＝薬草 vs 強弩の名）、大風（dict＝強風 vs 大風歌）、大邑（Wiki 県名 vs 大きな邑）、周文（dict＝画僧 vs 周文王）、内則（dict＝内規 vs 礼記篇名）、小学→**収録**（朱子書名义が大辞泉に実在・DE: 手差し）との対比参照；
   **未許可専門辞典のみ**（実用日本語表現辞典・植物名辞典以外は N82 惯例で未許可）：河川湖沼名辞典（南湖・城池）、地名辞典（北門・十里・堂前・大林・原上・国門）、隠語大辞典（三勝・五火・六四・六寸）、三国志小事典（夷道・居延）、世界宗教用語大事典（共工・大尊）、短編小説作品名辞典（人未）、新語時事用語辞典（三山）——**翻案可を注明**；
3. **Wikipedia のみ＝保守排除**（10 条）：一経・上六・上将・予譲・劉氏・北人・太清・南斗・宣王・小白——N80 令尹・N82 断片 同款、理由に「後日承認なら翻案可」を注明；
   **機械生成区のみ**（20 条）：一善・一長・三隊・哀矜（Wiktionary）・事毎・事無・地無・天知・威神・南門・双峰・宮観・宋人・小白・家斉・小大・国門系・五兵…（例文用例辞書・Wiki小見出し・Wiktionary のみで国語辞書条目なし）；
   **解析 artifact**（1 条）：人言＝「夫人不言」の誤分割（大辞泉条目は在るが语料義と対位せず）。

### 1.4 读法定案（语料训读用法优先——N75 牧す・N79 三月・N80 双读法・N82 先例）

- **双读法 3 条**（dict 両読み併記・両読みとも常用）：一月（いちげつ・いちがつ——语料「一月主人笑うこと幾回ぞ」ひと月义で いちげつ 前頭）／万金（ばんきん・まんきん）／上客（じょうかく・じょうきゃく）。
- 语料训读用法で単一読み確定（代表）：塵埃 じんあい（ちりほこり でなく）／他人 たにん（あだびと でなく）／大海 たいかい（おおうみ でなく）／大衆 たいしゅう／伺候 しこう（さもらい でなく）／九十 きゅうじゅう／九日 きゅうじつ／六国 ろっこく／北面 ほくめん（きたおもて でなく）／公事 こうじ／大人 たいじん（論語义・うし でなく）／天台 てんだい。
- 寒山（かんざん）：大辞泉に「寒々とした冬の山」义が実在——詩僧义でなく语料义で採録（N80 北海 逐义项核对の適用例）。

## 2. 工具与产物

| 文件 | 内容 |
|---|---|
| tools/night89_freq.py | ② 候选挖矿（頻次 2 区・基线 1969 語形検証→top500・kkd 先排序） |
| tools/night89_weblio.py | weblio 抓取器（N82 克隆・gzip・0.7s 节流・4 进程并发実施・断点再開） |
| tools/night89_digest.py / night89_compact.py | 人读 digest／紧凑判定表（N82 克隆，×10 批） |
| tools/night89_judge.py | 紧凑判定入力 → decisions JSON 展開器（N82 克隆・BASE_RANK=0） |
| tools/night89_audit.py | 判定完整性审计（500 全判・dup 0・missing 0） |
| tools/night89_build.py | ⑤ 追加式装配器（N82 克隆改 N89 マーカー＋**空組塊対応**・機械校验・重复拒收） |
| tools/night89_eval_4000.py / night89_eval_8165.py | golden 全量真跑回归（对照 night87 归档逐位） |
| eval/night89_candidates.json | 候选清单 500 条＋语料样本＋统计 |
| eval/night89_judge_*.txt ×10 | 紧凑判定底稿（500 条全量） |
| eval/night89_digest_*.txt ×10 / compact_*.txt ×10 | 研究用 digest（500 条） |
| eval/night89_decisions_*.json ×10 | 逐条判定底稿（500 条全量） |
| eval/night89_excluded.json | 排除清单 270 条＋理由 |
| eval/night89_audit.txt | 审计结果（decided=500 dup=0 missing=0） |
| backend/glossary_lexicon_extra2.py | 801 → 1031 条（N89 追加 230） |
| eval/night89_results_4000.json / night89_results_8165.json | golden 全量归档（与 night87 逐位一致） |
| eval/night89_dict_cache/ | 抓取缓存 500 页（未跟踪目录，N74/N79/N80/N82 先例） |
| tests/test_night89_lexicon_freq2.py | N89 回归 9 条 |
| tests/test_night79/80/82_lexicon_expand*.py | 必要伴随（总数断言 801→1031・1301→1531・night89_decisions glob 追加） |

## 3. 结论：入库 230／排除 270／剩余 0（候选 500 全判定）

- **总数 1301 → 1531**（本体 500＋extra 291＋extra2 1031＝N79 324＋N80 261＋N82 216＋N89 230）。N89 追加分组：**名詞 192／固有名詞 13／動詞 9／形容副詞 14／機能語 2**（以下・以来——任务書「かな混じり接续系は modifier」に対し、両語とも純漢語機能語で function に帰属・N79 机制発見の適用範囲外を報告注明）。
- **收录代表**：儒学語（孝悌・中庸・天理・小学・大学系 学校・専一・嫌疑）／兵制军语（侵奪・侵掠・別軍・主将・奮撃・先知・先行・多力・勇士・兵刃・守禦系なし・大兵・大衆・大要・会戦系 合戦）／漢詩意象語（孤月・寒山・寒梅・塵埃・回風・五雲・天外・天際・地軸・威霊・名花系なし・傾国・丹心・娟娟・啾啾・切切・堂堂・便便・乱山・千山・千仞・中秋・半夜・今夕・宿昔）／人名地名官名（匈奴・単于・会稽・匡廬・六朝・天台・寒食・孫子・宰予・司徒・太守・太尉・四岳・六国・冢宰）／度量数詞（一尺・三寸・三尺・六尺・九十・三千・五日・五穀・五味・五音・六畜・八寸系なし）／概念語（一体・仁賢・国士・国政・国都・名誉・利害・前言・剛強・壮麗・危亡・危邦・脅威系なし・大患・大器・大匠・大音・大白・天帝・天心・天時・中情・中分・交情・名姓系なし・無言系 不言・不測・不用・不識・不道・不敏）。
- **排除 270 条**分类（精确逐条见 eval/night89_excluded.json）：**404・断片系 200**（X曰・X+有無・数え構文・主語＋動詞連接・辞書不載専門語・詩語 196＋dict 対位せず構文断片 4）／**sense-mismatch・専門辞典別義・対位せず 39**（27＋未許可専門辞典のみ 9＋対位せず 2＋作品名辞典 1）／**Wikipedia-only 保守 10**（翻案可注明）／**機械生成区のみ 20**／**解析 artifact 1**（人言）。
- 方法注记（供后续夜参考）：①頻次 2 区は kkd 直証が全件（top500）——3–4 区と違い白文のみの断片が前沿に来ない；②排除の主力は「主語＋動詞／数詞＋名詞の誤連接断片」（吾知・子往・国安・国富型）で、N82 の X+有無 型よりさらに広い；③sense-mismatch の新典型＝「dict の現代义・別人名义」（単車＝オートバイ、大黄＝薬草、周文＝画僧、大風＝歌名対比）；④未許可専門辞典の判別は「読みの対位」（キタモン・シロイケ・オオバヤシ＝日本地名で中国古典义と不一致）が有効；⑤重判防止に audit（dup/missing=0）を最後に必ず回す——本夜も 1 条（周文）の書き忘れを audit が捕捉。

## 4. 验收

- pytest 全套：**443 passed**（434 基线＋test_night89_lexicon_freq2.py 9 条：格式/总数 1031・1531/双证据全量 230＋底稿 include 全入库/排除 270 全量不在库＋代表 30 条引用形不在文件/代表条目读法 34 条（双読み含む）/find_in_lexicon2 真语料命中 5 行/llm.glossary 离线命中/规则引擎零变化）；test_night79 必要伴随 3 处（N_EXTRA 1031・総数 1531・night89_decisions glob——N82 先例）、test_night80 必要伴随 5 处・test_night82 必要伴随 5 处（同款总数断言）。
- golden_4000 全量真跑（tools/night89_eval_4000.py）：**engine OK 4000／error 0／exact 24／avgDist 13.491，与 night87 归档输出不一致 0 行** → eval/night89_results_4000.json 归档 ✓
- golden_8165 全量真跑（tools/night89_eval_8165.py）：**engine OK 8165／error 0／exact 30／avgDist 13.502，与 night87 归档输出不一致 0 行** → eval/night89_results_8165.json 归档 ✓（词库不进规则引擎の位级实证）
- README 更新：三处「文語 1301 語」→「文語 1531 語」＋テスト行「**434 passed**」→「**443 passed**」（verify_readme_facts の pytest 計数断言が collect 実数と一致するための必要伴随）
- `python tools/verify_readme_facts.py`：**README 比对 19/19 对上・exit 0** ✓
- ROADMAP 末行 ✓
- `python tools/accept_night.py 89`（主提交 d95afe3 之后跑）：**PASS（fail=0 skip=0，32.1s）**——首跑即 PASS，七门全过：
  - repo_clean／pytest **443 passed = 443 collected**／eval_integrity（night89_results_4000.json 4000 条、id 唯一、expected 一致）／rule_regression／engine_smoke／perf_envelope／order_rate（off 98.57% on 98.63%，基线差 +0.00pp）
- 分支两提交（主提交 d95afe3＋wrap-up），**不合 master、不推远程**。

## 5. 交付与提交

- 主提交：extra2 追加 230 条（1031）＋判定底稿 500 条全量（judge/digest/compact/decisions）＋候选/排除/审计清单＋工具 9 个＋golden_4000/8165 归档＋测试 9 条＋test_night79/80/82 必要伴随＋SHIFT_LOG 全程心跳＋README 四处计数＋ROADMAP 末行＋NIGHT_ARTIFACTS[89]＋本报告 §0–3/§5。
- wrap-up 提交：ACCEPT_LOG.md＋eval/accept_night_89.json＋REPORT §4 accept 数字＋SHIFT_LOG 收尾行。
- 交付顺序（任务书）：Night 89 完成，全部验收通过。开工：HEAD = 35ba6e5 ✓；pytest 434 passed ✓；目录 D:\kanbun-kakikudashi、分支 night89-lexicon-freq2 ✓。词库：频次 2 区候选 500／入库 230／排除 270／剩余 0；extra2 801→1031，总数 1301→1531 ✓。验证：回归测试 443 passed；golden_4000 13.491／24／0、golden_8165 13.502／30／0 与 N87 归档逐位一致 ✓；verify 19/19 exit 0。验收：accept 89 PASS（fail=0 skip=0，pytest 443=443）；分支两提交，未合 master、未推远程。报告见 REPORT_NIGHT89.md。

## 6. 偏差注记

1. **必要伴随 3 文件**（tests/test_night79/80/82_lexicon_expand*.py）は任务書允许清单に無いが、N82 夜が同一状況で「总数断言 801→1301・底稿 glob 拡張」の必要伴随を先行実施した先例に倣った（pytests 全过＝accept の FAIL=0 門の前提；每回の词库夜で必ず発生する機械的伴随・判断の余地なし）。内容＝计数定数 801→1031・1301→1531＋test_night79 の底稿 glob に night89_decisions 追加の 3 種のみ。
2. **weblio 首回誤抓**：night89_weblio.py 克隆時に `os.path.join(EV, "night82_candidates.json")`（コード行・eval/ 前缀なし）の置換漏れで N82 词表 466 页を誤抓——全缓存削除＋修正＋500 页再抓（缓存は rank+word 対位検証済み、结果への影響なし）。工具克隆の置換は**コード内のファイル名トークンも対象に**（本夜の坑位記録）。
3. **meaning 体裁**：判定入力の meaning に「语料：…（出典）」を含めて書いたため、build 後に追加 230 行の尾段を剥離して N82 既有风格（純释义）に統一——语料・辞書证据は decisions 底稿に全量残置（test_night89 双证据全量断言で担保）。
4. **機能語 2 条**（以下・以来）は N79 以来の「function=0」運用を初めて変えた——両語は純漢語機能語（かな混じり接续系ではなく任務書 modifier 条項の対象外）で、dict（実用日本語表現辞典）＋语料双证据を満たす。test の kind 断言（content/function）は既存のまま通過。
