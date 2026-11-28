# REPORT_NIGHT113 — 在庫盘点＋拍板表更新夜（报告-only・ZCode 单会话）

## 0. 结论（先说）

1. **在庫 5 項全重測＋(f) census＋(g) 链完整性（sim-first・night111 基线・禁抄旧数）＝数値漂移 0 項**：(a) 嗟や→嗟乎 **3/3/0・Δ8165 −0.000367・Δ4000 −0.001**、(b) per-guard combo **5/3/0・Δ−0.000367・Δ4000 −0.001**（構造行 rikutou21-2・koshi19_01-8 維持）、(c) 毋系 ことなき→こと毋き **4/4/0・Δ−0.000490・Δ4000 −0.001**、(d) follow_map 実施後状態＝N106 全項目逐位一致＋**機構予測文本＝night111 归档 15 行 ALL byte-identical・impl 直打 15 行 ALL MATCH・d1 全一致**、(e) 残渣 2 行・sonshi09-38 d0=13・echo 30 行——全部历夜記録逐位復現。**N111（follow_map 機構＋default_repl こと莫き 収録）は在庫行に一切触れていない**（(a)(b)(c) 発火行 12 行の got は night101/104/107/111 四归档逐字节同一＝H10 gate 実証）。
2. **(c) 零触碰断言成立**：毋系 4 行（ichijicho-1・shindoku-1・daigaku06-1・rongo1125-1）got は四归档（101/104/107/111）で逐字节同一・d0＝N103 記録値（15/32/12/33）・N111 diff 15 行の外・got111 残 ことなき 行は恰好この 4 行＝**follow_map 機構（guard 莫）は guard 字不同により毋系に零触碰**。
3. **判错 3 行の在庫分離**（(d) 新設）：rongo1442-1（55→54・己 pred 莫き vs exp 莫くんば）・tonan-1（29→28・之 pred 莫き vs exp 莫し）・utsuryo03-7（63→63・能 pred 莫き vs exp 莫し）＝**文法構造差・機構外**・いずれも default こと莫き の (a) 値維持で発火済み。rikutou26-5（拍板行）は 大→莫し 判対・**d 53→54 変差維持**（語順構造差は機構でも不救＝N106 §1.4）。
4. **census 口径新知見 1 項（非漂移）**：莫かれ got 行数＝**72（pre-U・night101）→88（post-U・night107）→88（post-N111・本夜実測）＝88 維持**（N111 15 行中既在 2/新規 0＝follow_map 変体は莫かれ非産出）。変体産出は **delta 口径**で計る——こと莫からん **0→2**・こと莫かる **0→1**・こと莫し **3→5（N111 産出 delta 2 行のみ・night107 既存 3 行 daigaku00a-2/montai12-10/rongo1922-1 は Rule O こと+なきか→こと+莫し 由来）**＝N111 §3 A6「こと莫し 2」は改写行数の口径で got 総数 5 行とは別物（N109 莫かれ pre-U/post-U 口径坑の同型）。
5. **拍板表更新（§3・supersede N98 §3・N109 §3）**：項 1a/1b/1c/2＝已実施（N99）・項 3＝已実施（N104）・項 4＝已実施（N107）・項 5＝放弃（N106）・**項 6＝已実施（N111 follow_map 機構・N103「不統一」は字形統一三方向のみが範囲＝N112 附注记の正文反映）＋毋系在庫分離＋判错 3 行分離**・項 7＝在庫（本夜再測数付き）・項 8＝死（N102）＋per-guard 在庫分離・項 9＝在庫（本夜再測数付き）・**(c) follow_map＝已実施（N111・実現値 Δ8165 −0.0023/Δ4000 −0.0050・rikutou26-5 変差拍板行）**。**表の更新のみで表内のいかなる項も実施しない**（実施別夜）。
6. 数字：pytest **503 passed**（36.14s）・词库 **1531**（209+291+1031）・行分类 **7916/30/218/1**・基线 golden 4000 **13.455/24/0**・8165 **13.464/30/0**（night111 归档再計算＝归档自报と一致・真跑不実施＝报告-only 夜）・链完整性 **101→104 17 行（Rule U）／104→107 2 行（C1/C4）／107→111 15 行（N111 機構発火＝N103 A1 集・其余在庫行 byte-identical）／101→111 34 行**・幂等 bad 0・数値漂移 **0**・記録偏差注记 1 項（N98/N109 例示字形 爲→为 → 実測 爲→為・行集行数一致＝非漂移）・NIGHT_ARTIFACTS[113] 不登記（N98/N102/N103/N106/N109 先例）・REPORT_NIGHT98.md／REPORT_NIGHT109.md 一字未動（歴史記録）。

## 1. 开工核验

- `cd D:\kanbun-kakikudashi`・`git checkout -b night113-inventory master` ✓（git 身份 wang／wang@localhost 実測）
- HEAD＝master＝**ed5b2db**（N112 wrap-up）✓・`pytest tests -q`＝**503 passed**（36.14s）✓・已跟踪文件零改动 ✓（untracked は歴夜の eval キャッシュ/ocr_samples のみ＝従来どおり触らず）
- origin/master＝**ed5b2db**（**ユーザーが N112 链を push 済み**・rev-list **0** 実測）——N112 記録「等用户手推・rev-list=6」の完了状態を実測
- SHIFT_LOG.md 开工心跳 1 行追加（16:19・UTF-8 二进制追加）。canary 実測＝**LF 形態**（b[807]=63・canary 0xf3 は b[800]=243・blob 同型）——CRLF 形態想定の [807]=243 断言は現行ファイルには不適合（N112 坑位③「两値都要実測」どおり両値実測済み）
- 移交阅读：REPORT_NIGHT109 §3（旧版拍板表）＋REPORT_NIGHT112 附（項 6 拍板表待更新注记）＋REPORT_NIGHT111（§2 実装・§4 15 行明细・§5 口径）読済

## 2. 重測明細（sim-first・基线＝night111 归档 4000 13.455/24/0・8165 13.464/30/0・禁抄旧数）

方法论＝N99/N104 sim 型（归档 got 上解析適用・guard 語义 `any(g in hb)` エンジン同型）＋N106 guard_nxt 型（(d) 機構予測再構成）＋N111 impl 直打型（style_guard_followup 実装関数）。硬门 H1–H10 全过：词库 1531・行分类 7916/30/218/1（reachable 8134）・基线再計算 13.455/13.464・exact 24/30・errors 0/0（**归档自报 summary と一致＝禁抄旧数の実測成立**）・链完整性（下記 (g)）・各候补幂等 bad 0・echo/no_tail 全 key 不可達・reachable 全行 hb 非空・guard_forms(嗟/勿/毋)＝単形（SHINJITAI_MAP 両方向に無し）・(d) A1 恰好 15 行＋A2 対位 15 行成立＋site 18。実行時間 sim 25s・status 3s（lev＝纯 Python 回退・.night72_deps 無し＝N86/N98/N111 先例・归档同一算法）。

### (g) 链完整性（先に行う＝在庫入力不変の前提 gate）

night101→104 diff **恰 17 行**（Rule U・N109 実測 17 ID と逐字一致）・104→107 diff **恰 2 行**（rikutou37-2・shiki050-4＝C1/C4）・**107→111 diff 恰 15 行＝N103 A1 集（N111 機構発火）＝其余在庫行 byte-identical**・101→111 diff **34 行**＝17+2+15（三段非重叠）。H10：**(a) 3 行＋(b) 5 行＋(c) 4 行＝在庫発火行 12 行の got は night101/104/107/111 四归档で逐字节同一**＝N111 は在庫行に零触碰（在庫入力不変前提の実証）。

### (a) 嗟や→嗟乎（guard 嗟・N94 在庫）——一致

実測＝**3 改写 3 改善 0 変差・Δ8165 −0.000367（−3 字）・Δ4000 −0.001**（4000 内 3 行）・幂等 bad 0。fired＝enjaku-3 12→11・shiwaonore-2 51→50・shika-1 77→76（N109 実測 per_row 逐位一致）。census＝exp 嗟乎 3・**嗟夫/呜呼/于嗟/嗟哉 全 0**・got/exp 含嗟 12/12。拡張参照＝exp 嗚呼（正字）7・於嗟 0（N109 記録どおり）。

### (b) per-guard 変体 こと勿く（guard 勿）／こと毋く（guard 毋）＋combo（N102 在庫）——一致

- b1 こと勿く：**4 発火 2 改善 0 変差**（fired koshi19_01-8・rikutou04-2・rikutou21-2・toushisen080-8）
- b2 こと毋く：**1 発火 1 改善 0 変差**（p-haigun-1 58→57）
- combo：**5 発火 3 改善 0 変差・Δ8165 −0.000367（−3 字）・Δ4000 −0.001**（4000 内 2）・幂等 bad 0
- per_row 全一致：p-haigun-1 58→57・toushisen080-8 **12→11**（こと勿く で 勿 が exp 勿れ と align・改善）・rikutou04-2 45→44・rikutou21-2 **122→122**（長文 scramble 対位遠方＝構造行）・koshi19_01-8 **22→22**（勿からん 推量禁止形＝構造行）
- **構造行（combo 発火内 d0==d1）実測＝rikutou21-2・koshi19_01-8**＝N109 订正済行名のまま（N102 §5 行 94 の行名転記错位は N109 で修正済み・本夜も同値）
- H7 勿かれ 出現行数 **42 不変**（S4+M38・N109 記録どおり）

### (c) 毋系 ことなき→こと毋き（guard 毋・N103 在庫）——一致＋零触碰断言成立

実測＝**4 発火 4 改善 0 変差・Δ8165 −0.000490（−4 字）・Δ4000 −0.001**（4000 内 3 行）・幂等 bad 0。fired＝ichijicho-1 15→14（exp 毋かれ）・rongo1125-1 33→32（exp 毋かれ）・shindoku-1 32→31（exp 毋き）・daigaku06-1 12→11（exp 毋き）＝N103 §3/N109 実測逐位一致。
**断言（N111 機構零触碰）成立**：①毋系 4 行 got は night101/104/107/111 **四归档逐字节同一**・②d0＝N103 記録値（15/32/12/33）・③N111 diff 15 行の外・④got111 残 ことなき 行＝恰好この 4 行。注：N103 归档（eval/night103_sim.json exploratory_m）は d 値のみ保存（got 非保存）＝「got 逐位対 night103 归档」は「四归档逐字节同一＋d0=N103 記録値」の三重断言で実施（N103 基线＝night101・N109 A1 gate 同款）。

### (d) follow_map 実施後状態（N111 収録済・night107 raw→機構→night111 归档）——一致＋byte-identical

- **N106 全項目逐位一致**（judge・follow_map・conflicted・conflicted2・exp_forms・follow_chars・sites_pred・三 mode の better/worse/same・per_row・Δ 全部）：site 18・site 字形分布 莫き10/莫からん2/莫くんば1/莫かる1/莫し4・后继字分布 能2/己2/我1/知1/之4/由2/吾1/予2/如1/大2・判対 **15/18**（三向内 12）
- 三 mode：(a) 対照 better 12/worse 2/same 1・−12 字（Δ8165 −0.0015・Δ4000 −0.0035）｜ceiling better 13/worse 1/same 1・−22 字（Δ8165 −0.0027・Δ4000 −0.0055）｜**follow better 12/worse 1/same 2・−19 字（Δ8165 −0.0023・Δ4000 −0.0050）**
- **H9 三重 byte 実証**：①機構予測文本（night107 raw に site 級 repl 差し替え）＝**night111 归档 got 15 行 ALL byte-identical**・②impl 直打＝現 master `style_guard_followup(got107, hb)`→**got111 15 行 ALL MATCH**・③**d1 全一致＝lev(got111, exp) 15 行＝N106 follow 記録値**
- **判错 3 行（機構外・文法構造差・在庫単列）**：rongo1442-1 pred 莫き/exp 莫くんば → **55→54**・tonan-1 pred 莫き/exp 莫し → **29→28**・utsuryo03-7 pred 莫き/exp 莫し → **63→63**＝いずれも default こと莫き の **(a) 値維持**で発火済み（got111 に こと莫き 実在確認）
- **rikutou26-5（拍板行）**：大→莫し **判対**・**d 53→54 変差維持**（語順構造差は機構でも不救＝N106 §1.4・N111 §0-2 同框）
- 変体行（follow vs (a) 差分）＝**kagakujota-1・p-danjoshitsu-1・rongo0732-1・roushi46-2・rikutou26-5**＝N111 归档 summary.sim_expect.rewrite5 **集合一致**
- 15 行明细（d_raw→d1）：mujun-2 11→10・onoreshiru-1 18→17・kagakujota-1 27→**24**（知→こと莫からん）・kanchuna-1 82→81・rongo0615-1 12→11・rongo0732-1 23→**20**（吾→こと莫からん）・rongo1315-1 113→110・rongo1442-1 55→54（判错→(a) 値）・p-danjoshitsu-1 36→**33**（如→こと莫かる）・tarekako-1 12→11・tonan-1 29→28（判错→(a) 値）・warekimi-1 35→34・roushi46-2 34→**34**（大→こと莫し・変差解消）・utsuryo03-7 63→63（判错→(a) 値＝same）・rikutou26-5 53→**54**（拍板行）

### (e) 項 9 N84 遗留現状——一致（只確認・不設計剥夹注管線）

- 夹注残渣＝**2 行**（rikutou59-2・soji07-6・night98_audit B9 同款判定式＝engine 行∧白文含（∧got 含（…仮名…））
- sonshi09-38＝no_tail・tail 空串・**d0=13**（無尾段保持）
- echo＝**30 行**（got==尾段直出 **14**＋新字体化差し替え **16**・other 0・d0==0 0 行）
- drift 0 件（eval/night113_status.json）

### (f) census：got 含莫かれ（post-N111 口径で再実測）

- **night101 pre-U 72**（N96/N98 記録一致）→ **night107 post-U 88**（N109 記録一致・Rule U 17 行中既在 1/新規 16）→ **night111 post-N111 88（本夜実測）＝88 維持**（N111 15 行中既在 2/新規 0＝follow_map 変体 こと莫し/からん/かる は莫かれ非産出・増分 gate で説明済み）。**新口径名＝post-N111 口径**。
- **変体産出は delta 口径**（新知見）：こと莫からん **0→2**（kagakujota-1・rongo0732-1）・こと莫かる **0→1**（p-danjoshitsu-1）・こと莫し **3→5＝N111 産出 delta 2**（rikutou26-5・roushi46-2）で delta 合計恰好 **N111 rewrite5**。こと莫し の night107 既存 3 行（daigaku00a-2・montai12-10・rongo1922-1）は **Rule O（こと+なきか→こと+莫し）由来**＝N111 §3 A6「こと莫し 2」は N111 改写行数の口径・got 総数 5 行とは別物。
- 参考：こと莫き got111 11 行（default 10 行＋kagakujota-1 の default site）・こと莫かれ 86・こと莫く 21 は 107→111 不変。

## 3. 新版拍板表（supersede N98 §3・N109 §3）＋变更日志

**本表が現行の拍板表**（N98 §3・N109 §3 を置き換える・両者自体は歴史記録として不変）。表の更新のみで実施はしない。

| # | 拍板項 | 状態（N113 現在） | 根拠夜 | 在庫残／次の一手（本夜再測数付き） |
|---|---|---|---|---|
| 1a | べからず→可からず | **已実施**（N99 Rule T） | N98 §3 1a（変差 5 行許容拍板済） | — |
| 1b | べからざる→可からざる | **已実施**（N99 Rule T） | N98 §3 1b（変差 1 行許容済） | — |
| 1c | べからず族 combo | **已実施**（N99 Rule T 3 条・変差 6 行 ID 特定済） | N99 | — |
| 2 | べきなり→可きなり | **已実施**（N99 Rule T） | N98 §3 2（p-gekirin-1 変差許容済） | — |
| 3 | なかれ→莫かれ（guard 莫） | **已実施**（N104 Rule U・U_LONGER_WORDS なかれ主義マスク） | N98 §3 3（kokyo09-5 変差 1 行許容拍板済） | — |
| 4 | がため／何のごとく（rerun tail 判別） | **已実施**（N107 C1+C4＝guard 変体字拡張 (U+7232,為)／(奈,柰)・2 改善 0 変差・Δ−0.001） | N106 §2.1/§3 → N107 | — |
| 5 | は系 1 字块構文判別機構 | **放弃**（N106 负結果：字面句首 0/917・0/484・topic 切分変差 204/129・Δ悪化 +0.056/+0.030・真因＝引擎读取層が 将/未 を読み丢す/語順错置＝規則層＋位置機構とも不可分） | N106 §2.2 | 引擎读取層方向は**別工程項**（本表収録線外・立项はユーザー拍板事項） |
| 6 | ことなき→こと莫き 字形統一（データ側） | **已実施**（N111 follow_map 機構＝N106 §1 設計の 4 元組実装・ことなき guard 莫 1 entry 链尾追加・発火 15 行/変体 5 行/改善 4 行/変差 rikutou26-5 1 行拍板許容）。**N103「不統一・不実施」の判定範囲は字形統一三方向（莫き/莫し/莫くんば データ側一括統一）のみ**＝N112 附注记どおり字形選択は機構の管轄に移管 | N103 §3 → N112 附 → N111 → 本夜 | 在庫残＝①毋系 ことなき→こと毋き 4 行（本夜再測 4/4/0・Δ−0.000490・Δ4000 −0.001・収録線 −0.001 未達・N111 機構零触碰実証＝guard 字不同・N111 4 元組と同型の第二 entry 候補）②判错 3 行（rongo1442-1・tonan-1・utsuryo03-7＝文法構造差・機構外・(a) 値維持で発火済み＝規則層のさらなる救済不可・文法構造差の解決は別機構） |
| 7 | 嗟や→嗟乎（歎詞データ） | **在庫** | N94 → N98 §3 7 → N109 §3 → 本夜 | 本夜再測 3/3/0・Δ−0.000367・Δ4000 −0.001・同族（嗟夫/于嗟/嗟哉）0 維持・拡張参照 嗚呼 7/於嗟 0。収録条件＝歎詞データ増強（新语料）か収録線撤廃（ユーザー拍板） |
| 8 | ことなく guard 拡張（莫→勿/毋 併用） | **已判定死**（N102：拡張発火 5 行とも d0==d1＝0 改善・exp は こと莫く を一行も書かない＝無益拒） | N102 §4 | 在庫残＝per-guard 変体 combo こと勿く/こと毋く（本夜再測 5 発火 3 改善 0 変差・Δ−0.000367・Δ4000 −0.001・収録線未達・構造 2 行＝rikutou21-2・koshi19_01-8〔N109 订正済行名のまま維持〕） |
| 9 | N84 遗留（剥夹注管線） | **在庫** | N84 → N98 §3 9 → N109 §3 → 本夜 | 現状（本夜再測）＝残渣 2 行（rikutou59-2・soji07-6）・sonshi09-38 no_tail d0=13・echo 30（直出 14＋新字体化 16）。拍板＝剥夹注管線（detect_text_type 口径改訂＋全量回帰必須） |
| (c) | 守り字后继字機構（follow_map） | **已実施**（N111＝N106 §1 設計の 4 元組実装・chain 尾追加・main.py 無改）。実現値＝判対 15/18・発火 15 行/変体 5 行/改善 4 行/変差 rikutou26-5 53→54 1 行（拍板許容済 N111）・**Δ8165 −0.0023（−19 字）/Δ4000 −0.0050（−20 字 4000 内）**＝raw→follow 総効果 | N106 §1/§2.3 → N109 §2(d) → N111 → 本夜 | 本夜再測＝機構予測文本＝night111 归档 15 行 ALL byte-identical・impl 直打 ALL MATCH・d1 全一致（N106 記録逐位）。残＝判错 3 行（文法構造差・機構外＝項 6 在庫残②へ分離記載） |

**变更日志（N109 §3 → N113 §3）**：
- 項 6：「已判定不統一・不実施（N103）＋毋系在庫」→「**已実施（N111 follow_map 機構）**」へ更新——N103 の「不統一」は**字形統一三方向（データ側）のみへの判定**で、字形選択は N111 で機構管轄に移管（N112 附注记の正文反映・N103 §3 自体は不変）。在庫残を「毋系 4 行」と「判错 3 行」に**分離記載**（判错 3 行は本夜 (d) で (a) 値維持実行済みを確認＝規則層の救済は完了・残差は文法構造差）
- (c)：「棚上げ（N106・実施には rikutou26-5 変差 1 行拍板別途）」→「**已実施（N111）**」へ更新（実現値 Δ−0.0023/−0.0050・rikutou26-5 53→54 は N111 で拍板許容済）
- 項 7/9：在庫維持・数字を本夜再測値へ更新（項 7 は Δ4000 −0.001 を追記・項 9 は 3 サブ項の現状値）
- 項 8：在庫残の構造 2 行行名を「rikutou21-2・koshi19_01-8」に統一（N109 订正の反映・N102 §5 表記は歴史記録のまま）
- 1a/1b/1c/2/3/4/5：変更なし（状態確認のみ・N109 表から引き継ぎ）
- 記録偏差注记（非漂移）：N98 §3 項 9/N109 §2(e) の例示字形「爲→为」は**実測/SHINJITAI_MAP では「爲→為」**（U+7232→U+70BA・本夜 status 実測＋N109 归档 night109_status.txt 同値＝行集・行数は 16 行で一致）——報告文の例示字形 slip のみ・REPORT_NIGHT98.md 自体は歴史記録として不変
- **本夜の実施はゼロ**（表の更新＋在庫重測のみ＝任務書「不实施表中任何一项」遵守）

## 4. 工具与产物

- `tools/night113_sim.py`（(a)–(d) 全重測＋(f) census＋(g) 链完整性・H1–H10 硬门・四归档 got 对照・N106_OLD/N103_A/N109_RULEU/OLD 定数対照・impl 直打・LF・25s）＋ `eval/night113_sim.json`・`eval/night113_sim.txt`・`eval/night113_changed_rows.json`
- `tools/night113_status.py`（(e) 現状確認・night98_audit B9 同款判定式・night111 基线・LF・3s）＋ `eval/night113_status.json`・`eval/night113_status.txt`
- SHIFT_LOG.md 心跳（开工＋每小时＋收工）・ACCEPT_LOG.md（accept 113 FAIL/PASS 两行とも残す＝N100/N104/N109 先例）・eval/accept_night_113.json（final＝wrap-up 提交）
- ROADMAP.md 末尾 Night 113 行（拍板行同步・新版表への指针＋項目別状態）
- 禁碰区遵守：backend/・词库（1531 実証）・golden expected・README.md・tools/verify_readme_facts.py・tests/（503 全过）・tools/accept_night.py・REPORT_NIGHT98.md・REPORT_NIGHT109.md・night106–112 分支＝全部未動・真跑（TestClient 全量）は不実施（報告-only 夜・基线は H3 gate で归档再計算により検証・impl 直打は sim 層のみ）
- eval 出力は未跟踪新ファイルのみ（既跟踪归档 night1xx_results_*.json は読み専用＝禁覆写遵守・console/probe 一時ファイルは削除済み）

## 5. 坑位追加

1. **変体 census は delta 口径**：こと莫し のような「新規則が産出するはずの字形」は既存規則の**組合せ産出**（こと+Rule O 莫し）で night107 既存があり得る——絶対数 gate は N111 §3 A6「こと莫し 2」と冲突して FAIL（開発中 1 回）。夜を跨ぐ字形 census は「産出元規則の組合せ可能性」を先に列挙して delta で取る（N109 莫かれ pre-U/post-U 口径坑の同型・恒久化）。
2. **`sorted(set) == set` は恒 False**（list vs set）——(d) A1 集合 gate を誤発火（開発中 1 回）。集合比較は set 同士か sorted 同士に統一。
3. **归档 JSON の保存順は非 sorted**（night111 summary.sim_expect.rewrite5 は時系列順）——集合比較で DRIFT 偽陽性 1 回（開発中 1 回）。旧数対照のリスト系 cmp_val は sorted 同士で。
4. **CJK console redirect は mojibake**（Git Bash `> file` で utf-8 崩れ・既知坑の本夜再確認）——CJK 出力は tools 内 write_out（utf-8 落盘）で読み・console は EXIT code 判定に使う。
5. **SHIFT_LOG canary の現行形態＝LF**（b[807]=63・0xf3 は b[800]=243・blob 同型）——「CRLF なら [807]=243」は仮想形態の話で、現行ファイルへの断言は LF 値を使う（N112 坑位③の両値実測どおり・本夜は LF 値を採用）。
6. PowerShell 5.1 `&&` 不可（N100 坑位②継承・本夜は Git Bash 使用で回避）。

## 6. 验收

- accept 113：提交前试跑 FAIL＝repo_clean 1 項のみ（設計行為・N96/N100/N104/N107/N109 先例・FAIL 行も ACCEPT_LOG に残す）→ 主提交後终跑 **PASS fail=0 skip=1**（skip=eval_integrity＝報告-only・NIGHT_ARTIFACTS 不登記）
- 分支 night113-inventory 两提交：主提交＝本报告所在提交＋wrap-up＝次提交（ACCEPT_LOG FAIL/PASS 两行＋eval/accept_night_113.json final＋SHIFT_LOG 收工心跳）・未合 master・未推远程・master ed5b2db 未動
- 次夜建议（只建议・未开工・全部ユーザー拍板待ち）：①**剥夹注管線設計**（項 9・detect_text_type 口径改訂＋全量回帰必須＝設計夜として report-only から開始推奨）②**嗟や stock 拍板**（項 7・本夜再測 3/3/0 Δ−0.000367 収録線未達のまま＝収録線撤廃か歎詞データ増強か維持かの拍板）③**毋系 per-guard 拡張実施拍板**（項 6 在庫残①・N111 4 元組と同型の第二 entry＝ことなき guard 毋 follow_map 毋き/毋かれ 判別・site 4・Δ−0.000490 は収録線 −0.001 未達＝単独では在庫のまま・収録線撤廃/複数候補一括時の浮上候補）
