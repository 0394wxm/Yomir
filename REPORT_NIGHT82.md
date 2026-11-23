# REPORT_NIGHT82.md — Night 82：词库再扩充第三波 1085 → 1301（频次 3–4 区剩余 rank500–965・追加式装配）

- 日期：2026-11-23（单会话完成 466 条全判定）
- 分支：`night82-lexicon-expand3`（自 `night80-lexicon-expand2` 6fba6a7 分出——词库链；merge-base=6fba6a7）
- 工作目录：`D:\kanbun-rulel`（与主仓 `D:\kanbun-kakikudashi` 零接触；禁 OCR／guwenbert——本夜纯词典离线活）
- 性质：**词库数据夜**。`glossary_lexicon.py`／`extra.py`／`llm.py` 一字未改（接入已在 N79 落定）；`glossary_lexicon_extra2.py` **追加式**扩容 585 → 801 条（分组列表尾部追加，本体 500 条不动，`find_in_lexicon2` 合并查找算法不变）。N79 待拍板两项（同語彙 3 条＋Wikipedia 8 条）与 N80 Wikipedia-only 保守排除 4 条（令尹・元王・宰我・大象）**一字未动，等用户定**。

## 0. 开工核验

- 开工 HEAD=6fba6a7 ✓（=任务书要求）；分支 `night82-lexicon-expand3` 新建 ✓；工作树零改动（仅 5 个惯例 untracked 缓存目录）✓
- pytest 开工复跑全套：**374 passed**（12.84s，N80 开工漏跑项本夜不重犯）

## 1. 方法

### 1.1 候选（频次 3–4 区剩余，tools/night82_freq.py → eval/night82_candidates.json）

- 复跑 N80 挖矿：golden_8165 白文＋書き下し文汉字连续 run（2–8 字）文書頻度 3–4 区，**基线 824 词形重构**（現行 1085 − N80 判定 500 語中已入库 261 語；重构后恰 824 ✓）
- **zone 全量再算＝966 与任务书一致 ✓；N80 同款排序下 rank 0–499 与 night80_candidates.json 逐词逐位一致（决定论验证 ✓）**；残り rank 500–965＝**466 条**（freq 4 区=0／kkd 直证 360／3 字以上 130／pre_exclude 旗标 21），rank 用 N80 絶対番号
- 排除 N80 已判 500 条与已入库 1085 词形后产出候选；N79/N80 的 Wikipedia 保守路子与待拍板条目全部不在范围

### 1.2 逐条双证据门（466 条全判定，无抽查）

1. **辞書**：`www.weblio.jp` 聚合页（tools/night82_weblio.py，**466 页全抓**，404 以 0 字节缓存如实记录；缓存 eval/night82_dict_cache/——未跟踪目录）。読み＋释义有据；404／无条目／仅机器生成区块（例文用例辞書・ウィキペディア小見出し辞書）如实记录。kotobank 403／goo 超时站点级不可达，沿用 N74/N79/N80 结论，不编。
2. **语料**：golden_8165 実例行（候选自带 id＋書き下し文样本）；kkd 直证 360 条走自动语料引证；**白文 run（k=0）且为正词条的 4 条**（善哉・好學・屈原・約束）以 golden_8165 白文行手工引证（善哉問／孰爲好學／屈原旣放／約束符信）；同形异义逐义项核对（小過＝過失義（易卦はウィキ区のみ）、日長＝ひなが 春昼長義、旧国・新書・既往・迷惑・行楽 等语料义一致才收录；平台＝梁孝王の台名・建徳＝老子義・水光＝水面の光 と辞書現代義不符で排除——N79 東流・N80 天井 先例）。
- **单步超 45 分钟处置（N72 惯例）**：weblio 抓取初速 ~38 秒/頁（未圧縮 200KB）で 466 页预估 5 小时——**杀掉单流重写为 gzip 传输（语义不变：同 URL 同 HTML 解析，传输 3–5 倍减）＋ 4 路分段并发（每路仍 0.7s 限速）**，466 页 ~6 分钟完成；SHIFT_LOG 留一行记录。
- 研究辅助（本夜新增工具）：**tools/night82_judge.py**——紧凑判定入力（`rank|word|V|cat|reading|meaning|note`，1 行 1 条）→ N80 同款 decisions JSON 展开器。自動採証はパンくズ以降の実在辞書区から【見出し】＋読み方行を引用（ページヘッダーメニューの辞書名リンク誤採用を防ぐ修正 2 回——尚書/川原 の「古語辞典」メニュー行、大辞泉区前の「索引トップ」等 JUNK 行）。DE:／CE: 手差し上書き欄あり。判定底稿 eval/night82_judge_*.txt（10 批）＋eval/night82_decisions_*.json（10 批 466 条全量）。

### 1.3 判定三条定式（N79/N80 沿用＋本夜実績）

1. **404＋断片系**（184＋既証パターン 26＝210 条）：X曰 系呼称部（曹公・燕人・漁父曰・象曰…）、X+ari/nasi 系（将必・才有・徳無・意無・誅有…）、白文成句（不然・然後・如切如磋・良弓蔵・己所不欲…rank800 以降の h-only run はほぼこれ）、数え構文（五六十・五十人・五十歩・百乘之家…）、兵書専門語（六韜の扶胥・転関・通索・飛江・険戦・鼙鼓・驍騎・蒺藜、孫子の迂直・聖智・絶地、尉繚子の踵軍、商君書の開塞 等——weblio 不載は N80「同类词形只要 weblio 无条目就整组排除」先例で排除）。
2. **機械生成区のみ**（9 条）：幾時・幾歳・散地・日落・色無・益無・行止・一歳・心有——例文用例辞書のみで国語辞書条目なし。
3. **Wikipedia のみ＝保守排除**（20 条）：斉王・昌意・江城・江声・江海・清江・終南・趙王・高辛・高樹・黄鶴・武城・武陵・司馬穣苴・李将軍・公子糾・夏后氏・飛将・桑乾・尾生——N80 令尹・元王・宰我・大象 同款、理由に「後日承認なら翻案可」を注明。**N79 已入库 3+8 条一字未动**。
- **sense-mismatch／専門辞典別義**（11 条）：平台（dict＝印刷機・書店台 vs 语料＝梁孝王の台名）、建徳（dict＝日本南朝年号 vs 语料＝老子義）、水光（dict＝隠語大辞典「銀」の隠語 vs 语料＝水面の光）、日辺（地名辞典ニッペ）、空林・尾生（名字・地名辞典別義）、飄飄（実用日本語表現辞典「飄々」現代義 vs 语料＝風のひるがえるさま）、王必（三国志小事典 vs 構文断片）、新豊・即墨・彭沢（三国志小事典のみ・読み方不載）等。
- **実用日本語表現辞典・植物名辞典は语料义一致なら採録可**と本夜で運用確定（従来・日中・要塞・酒家・道徳・窮寇・穆穆・花草——N80 が排除したのは「別義」の場合のみで、同義の専門辞典は排していない）。

### 1.4 读法定案（语料训读用法优先——N75 牧す・N79 三月・N80 双读法 先例）

- **双读法 32 条**（extra2 文件实值：N82 追加 216 条中 reading 字段両読み「A・B」併記者全数；大辞泉条目内両読み＋语料训读用法置前。下列 14 例为代表，非全数）：山上（さんじょう・やまのうえ）／布衣（ふい・ぬのきぬ——語料「布衣の交わり」ふい 前頭）／広大（こうだい・ひろだい）／微妙（びみょう・みみょう）／敵国（てきこく・てっこく）／日長（ひなが・にっちょう）／海上（かいじょう・うなかみ）／白骨（はっこつ・しらほね）／沈沈（ちんちん・しんしん）／徳行（とっこう・とくぎょう）／賢聖（けんじょう・けんせい）／遥遥（はるばる・はろばろ）／愛子（あいし・まなご）／鬱金香（うこんこう・うっこんこう）。
- 主読み分歧时语料训读惯例优先（4 条，含在上述 32 条内）：秋雨（しゅうう・あきさめ——漢詩 しゅうう 前頭）／門前（もんぜん・かどさき）／風雲（ふううん・かざぐも）／織女（しょくじょ・たなばた）。
- 寒空（さむぞら）：辞書は和語読みのみ、漢詩訓 かんくう は辞書不載——辞書に従い さむぞら のみ記録（N80 北海 逐义项核对の逆適用：証拠なき読みを造らない）。

## 2. 工具与产物

| 文件 | 内容 |
|---|---|
| tools/night82_freq.py | ② 候选挖矿第三波（966 再算＋N80 rank0-499 决定论验证 → 466 候选） |
| tools/night82_weblio.py | weblio 抓取器（N80 克隆＋**gzip 传输**；0.7s 限速断点续跑；466 页全抓・4 路并发実施） |
| tools/night82_digest.py | 人读 digest（N80 克隆，×10 批） |
| tools/night82_compact.py | digest → 紧凑判定表（N80 克隆） |
| tools/night82_judge.py | **N82 新增**：紧凑判定入力 → decisions JSON 展开器（自動採証＋DE:/CE: 手差し） |
| tools/night82_audit.py | 判定完整性审计（466 全判・dup 0・missing 0） |
| tools/night82_log.py | SHIFT_LOG 追加器（絶対パス） |
| tools/night82_build.py | ⑤ 追加式装配器（N80 克隆改 N82 マーカー；機械校验・重复拒收） |
| tools/night82_eval_4000.py | golden_4000 全量真跑回归（对照 night80 归档逐位） |
| eval/night82_candidates.json | 候选清单 466 条＋语料样本＋统计 |
| eval/night82_judge_*.txt ×10 | 紧凑判定底稿（466 条全量） |
| eval/night82_digest_*.txt ×10 / compact_*.txt ×10 | 研究用 digest（466 条） |
| eval/night82_decisions_*.json ×10 | 逐条判定底稿（466 条全量） |
| eval/night82_excluded.json | 排除清单 250 条＋理由 |
| eval/night82_audit.txt | 审计结果（decided=466 dup=0 missing=0） |
| backend/glossary_lexicon_extra2.py | 585 → 801 条（N82 追加 216） |
| eval/night82_results_4000.json | golden_4000 全量归档（与 night80 逐位一致） |
| eval/night82_dict_cache/ | 抓取缓存 466 页（未跟踪目录，N74/N79/N80 先例） |
| tests/test_night82_lexicon_expand3.py | N82 回归 11 条 |
| tests/test_night79_lexicon_expand.py | 必要伴随 3 处（总数断言 585→801・1301、底稿 glob 扩展 night82_decisions） |
| tests/test_night80_lexicon_expand2.py | 必要伴随 2 处（总数断言 585→801・1085→1301） |

## 3. 结论：入库 216／排除 250／剩余 0（候选 466 全判定）

- **总数 1085 → 1301**（本体 209＋extra 291＋extra2 801＝N79 324＋N80 261＋N82 216）。N82 追加分组：**名詞 172／固有名詞 28／動詞 9／形容副詞 7／機能語 0**（接续系 modifier 组方针不变）。
- 分批账目（rank 区间・in/out）：500–549 35/15；550–599 31/19；600–649 35/15；650–699 31/19；700–749 30/20；750–799 34/16；800–849 16/34；850–899 4/46；900–949 0/50；950–965 0/16——**质量门随词长与词域收紧**（2 字詩語・人名が主命題の rank500–799 と、白文成句のみの rank800 以降で乖離）。
- **收录代表**：漢詩意象語（寒空・寒雨・封侯・斜日・玉壺・梁園・楼蘭・江月・江村・滄浪・滄海・落月・薄暮・笙歌・紅顔・青松・雨中・雲梯・雲漢・雲間）／兵制军语（戦車・戦闘・攻守・楼船・軍容・軍門・覇王・諸将・財用・進止・節制・窮寇）／人名地名（尚書・廷尉・張良・廬山・巫山・揚州・荊州・涼州・陽関・隴山・渭水・李衛公問対系 藺相如・諸葛亮・閔子騫・比干・屈原・漢武・神農・扶桑・蓬萊・瀟湘）／儒学語（尋常・小子・小過・至徳・郷党・郷原・顚沛・聚斂・忠言・良薬・美言・善哉・好學・関雎）／叠语形容副詞（繊繊・穆穆・潺湲・遥遥・沈沈）／時間語（平旦・平明・日中・日夕・歳寒・旬日・時節・旧時・長生・淹留）。
- **排除 250 条**分类（精确逐条见 eval/night82_excluded.json）：**weblio 404（断片・白文成句・呼称部・数え構文・兵書専門語）** 184 条＋**N79 既証パターン（X-yune／X+ari/nasi）** 26 条／**機械生成区块のみ** 9 条／**Wikipedia のみ保守排除** 20 条（翻案可を注明）／**sense-mismatch・専門辞典別義** 11 条。
- 方法注记（供后续夜参考）：①rank500–965 は N80 が残した「辞書に在る語」の後段で、freq4 区＝0——白文 run（k=0）比率が急増し rank800 以降はほぼ白文成句断片；②「X+有り／無し」構文断片は 2 字でも 3 字（才・徳・色・益・光輝・君子 接続）でも同一扱い；③weblio 抓取は gzip 化で 5 時間→6 分（N72 >45 分处置の実例）；④判定入力を pipe 区切り 1 行 1 条にして展開器で N80 同款 JSON に機械展開——exclude 250 条の reason 記述コストを約半減。

## 4. 验收（wrap-up 提交时补 accept 数字）

- pytest 全套：**385 passed**（374 基线＋test_night82_lexicon_expand3.py 11 条：格式/总数 801・1301/双证据全量 216＋底稿 include 全入库/排除 250 全量不在库＋代表 20 条引用形不在文件/代表条目读法 51 条/双读法代表 8 条/assert find_in_lexicon2 真语料命中 6 行/llm.glossary 离线命中/规则引擎零变化）；test_night79_lexicon_expand.py 必要伴随 3 处（总数断言 801・1301、底稿 glob 扩展 night82_decisions——N79 条目断言不变の必要伴随）；test_night80_lexicon_expand2.py 必要伴随 2 处（总数断言 801・1301）。
- golden_4000 全量真跑（tools/night82_eval_4000.py，105s）：**engine OK 4000／error 0／exact 24／avgDist 13.517，与 night80 归档输出不一致 0 行** → eval/night82_results_4000.json 归档 ✓（词库不进规则引擎的位级实证）
- README 更新：三处「文語 1085 語」→「文語 1301 語」＋テスト行「**307 passed**」→「**385 passed**」（verify_readme_facts の pytest 計数断言が collect 実数と一致するための必要伴随——N73 起の歴史漂移を本夜で解消）
- `python tools/verify_readme_facts.py`：**README 比对 17/17 对上・exit 0** ✓（N80 漏报本项、本夜补上）
- ROADMAP 末行 ✓
- `python tools/accept_night.py 82`（主提交 fb11eee 之后跑）：**PASS（fail=0 skip=0，31.7s）**——首跑即 PASS（主提交后才跑，无 repo_clean 预跑 FAIL），七门全过：
  - repo_clean（untracked 仅缓存目录 `.night72_deps/`＋`eval/night74/79/80_dict_cache/`＋`night79_ruby_cache/`＋`night82_dict_cache/`，N72/N74 先例）／pytest **385 passed = 385 collected**／eval_integrity（night82_results_4000.json 4000 条、id 唯一、expected 一致）／rule_regression（Rule C' 护栏＋合并词表 21 条）／engine_smoke／perf_envelope（短句中位 16ms）／order_rate（off 98.57% on 98.63%，基线差 +0.00pp）
- 分支两提交（主提交＋wrap-up），**不合 master、不推远程**。

## 5. 交付与提交

- 分支两提交（主提交＋wrap-up），**不合 master、不推远程**。
- 主提交：extra2 追加 216 条（801）＋判定底稿 466 条全量（judge/digest/compact/decisions）＋候选/排除/审计清单＋工具 9 个（judge 新增）＋golden_4000 归档＋测试 11 条＋test_night79/80 必要伴随＋SHIFT_LOG 全程心跳＋README 三处计数＋テスト行＋ROADMAP 末行＋本报告 §0–3/§5。
- wrap-up 提交：ACCEPT_LOG.md＋eval/accept_night_82.json＋REPORT §4 accept 数字＋SHIFT_LOG 收尾行。
- 交付顺序（任务书）：Night 82 完成，全部验收通过。开工：HEAD = 6fba6a7 ✓；pytest 374 passed ✓；目录 D:\kanbun-rulel、分支 night82-lexicon-expand3 ✓。扩库：新入库 216 条（候选 466 全判定，证据门通过 216／排除 250／剩余 0）；总数 1085→1301 ✓。验证：回归测试 385 passed；golden_4000 与 night80 逐位一致（13.517／24／error 0）✓；verify 17/17 exit 0 ✓。验收：accept 82 PASS（fail=0 skip=0，pytest 385=385）；分支两提交，未合 master、未推远程。报告见 REPORT_NIGHT82.md。
