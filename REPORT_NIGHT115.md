# REPORT_NIGHT115 — 剥夹注管線设计夜（項 9・report-only・ZCode 单会话）

## 0. 结论

- **本夜＝項 9 剥夹注管線的设计夜（report-only）**。backend/ 一字未改、产品代码零改动、真跑（TestClient 全量）不实施、NIGHT_ARTIFACTS[115] 不登记。全部产出＝sim 層（tools/night115_*.py 3 本）＋报告＋登记。
- **现状重测全項漂移 0**（night111 基线 4000 13.455/24/0・8165 13.464/30/0 归档再計算・行分类 7916/30/218/1・reachable 8134・残渣 2 行・sonshi09-38 no_tail d0=13・echo 30＝直出 14＋新字体化 16）。
- **形态分类＝実測 3 形態のみ**：①ruby 夹注（漢字（読み仮名）交织）251 行＝唯一の括号内注记形态・②rongo「N）」编号（dangling ）無（・非注记）6 行・③括号外混在（sonshi09-38 型）1 行。割注・傍注・無仮名（…）・空 （）・ASCII 括号・嵌套・整行注记＝**corpus 実測 0 行＝設計に書かない**（未実測形態禁載・任务书遵守）。
- **census（管線影響面定量）＝白文含（ 251 行**（分類別 echo 30／rerun 218／engine 2／no_tail 1）・**4000 内 0 行**＝注记面は golden_4000 subset の外に整体存在する（回帰構造的安全）。got 含（ 2 行・got 含（…仮名…） 2 行＝恰 B9 残渣 2 行・4000 内 0。
- **管線設計（Stage 0–3）＋sim 验证＝設計成立**：
  - Stage 0 检测＝`detect_text_type` 本体**不改**。新信号＝`has_ruby_annotation(text)`（B9 証拠式と同一 regex `（[^（）]*[ぁ-ゖー][^（）]*）`）・管線 scope＝**engine 分支行のうち ruby 注记を含む行（実測恰 2 行）**のみ剥いてから引擎。kana 分支（echo 30／rerun 218／no_tail 1）は **N84 尾段路径維持**＝既存の注记处理そのもの（変更ゼロ）。
  - Stage 1 剥离＝`strip_annotation(text)`＝仮名含 （…） span を全剥す（剥下物捨て＝拍板三选一の既定値）。**I1 非注记行 byte-identical（実測 7914/7914）・I2 冪等 strip∘strip=strip（8165/8165）・I3 剥後無括号（251/251）・I4 sonshi09-38 剥後も kana＝管線外維持**。
  - Stage 2 规则链＝剥離後 text は现行鏈 `_kundoku_result_for(…)` 零改动。Stage 3 输出契约＝got＝response 層 `normalize_shinjitai(kakikudashi)`・**I6 管線行 got に注记 span 不出現**（実測 2/2）。
  - **sim：残渣 2 行 双改善**＝rikutou59-2 d0=224→d1=**155**（Δ−69）・soji07-6 d0=36→d1=**23**（Δ−13）・现行 got 再現 byte-identical・**scope 内新增变差 0**＝設計成立。
  - **被否替代案（kana 分支 248 行全剥→引擎 reroute）＝変差 247・例外 1（utsuryo08-2 IndexError）・改善 0・same 0**＝reroute 封印の実測証拠（exp は尾段対齐のため全文経路は出力長大化で必败）。
- **期待回帰値（实施夜）＝4000 13.455/24/0 全行 byte-identical（scope 0 行）・8165 sum 109934→109852（avg 13.464→**13.454**・Δ−82＝残渣 2 行分）・exact 24/30 不変・diff 恰 2 行**。
- **待用户拍板（实施夜の前）**：①剥下注记去向三选一（**丢弃**〔sim 既定〕／sidecar／输出重贴）②detect_text_type 新信号命名（**helper `has_ruby_annotation` 推荐〔API text_type 契约不変〕** vs 第三 type 值 `kanbun_ruby`〔契约变更〕）。
- 拍板表正文未动（更新归在庫夜）。REPORT_NIGHT98/109/113 未动。分支 night115-annotation-design 两提交未合 master・未推远程。

## 1. 开工

- `git checkout -b night115-annotation-design master`：HEAD＝**4e335ac**（N114 wrap-up）✓・origin/master＝4e335ac（**rev-list=0 実測**）✓・已跟踪文件零改动 ✓・pytest tests -q＝**503 passed in 27.96s**（eval/night115_pytest_start.txt）✓。
- git identity：user.name=wang・user.email=wang@localhost（clone 不继承主仓本地身份の記録は本夜不要＝設定済みを確認）。
- 読済（grep 定位）：REPORT_NIGHT113 §2(e)（項 9 現状＝残渣 2 行・sonshi09-38・echo 30・drift 0）＋§3 項 9（在庫・拍板＝detect_text_type 口径改訂＋全量回帰必須）／REPORT_NIGHT109 §2(e)・§3 項 9／REPORT_NIGHT98 §3 項 9（B9 三项・记录偏差 N84「8 行」vs 実測 2 行）＋**audit B9 判定式＝tools/night98_audit.py 実装**（engine 行 ∧ 白文含（ ∧ got 含（…仮名…）〔re `（[^（）]*[ぁ-ゖー][^（）]*）`〕）。
- backend 読码（**一字未改・引用原文のみ**）：
  - `detect_text_type`（backend/main.py:116）：假名比例分流・`chars` は空白＋标点「、。，．・「」『』（）！？―ー」除外・**括号本身は分母除外だが括号内の仮名は分子に数える**（N84 根因の構造）。
  - N84 fallback ブロック（backend/main.py:142–166）：`_RUBY_TAIL_ECHO_MAX = 8`・`_RUBY_LEAD_JUNK`・`_ruby_tail_kanbun(text)`＝「（…）span に仮名含む」を ruby 証拠に最後の「）」後尾段純漢文を截取（尾段仮名含むなら ""）。
  - `kundoku()`（backend/main.py:339）：kana 分支（355）→ tail rerun（363）／echo 直出（390–394・response 層 `normalize_shinjitai` 394）／no_tail 空串（404）→ engine 分支（416 ENGINE None チェック→423 `_kundoku_result_for(text, merge, ortho, use_cache=cache, seg=seg)`→response 層 `normalize_shinjitai` 461）。
  - `_kundoku_result_for`（293）：use_cache=True は行分割＋_SENT_CACHE／False は整段路径（**seg は collections.defaultdict(float) 必須＝`seg["engine"] +=` が空 dict で KeyError**・本夜坑位①）→ `style_fix_with_hakubun`（334）。
- 允许编辑文件遵守：tools/night115_*.py（3 本）・eval/night115_*・SHIFT_LOG.md・ACCEPT_LOG.md・ROADMAP.md・REPORT_NIGHT115.md。禁碰区（backend/・词库 1531・golden expected・README・verify・tests・accept_night.py・REPORT_NIGHT98/109/113・night106–114 分支）一字未动（accept repo_clean 門で最終実証）。

## 2. 现状重测（sim-first・基线＝night111 归档・禁抄旧数＝归档再計算）

工具：`tools/night115_recheck.py`（4s）→ eval/night115_recheck.json + night115_recheck.txt（＋run ログ night115_recheck_run.txt）。**漂移 0 件・verdict PASS**。

- **基线再計算**：4000 **13.455/24/0**・8165 **13.464/30/0**（edit_distance/exact_match 归档字段再集計・N114 記録値と一致・error 0）。sum d0＝8165 **109934**／4000 **53820**（回帰 spec の換算基準）。
- **(A) 行分类復核**：engine **7916**／echo **30**／rerun **218**／no_tail **1**＝N113 記録 7916/30/218/1 一致・**reachable（engine+rerun）＝8134** 一致。
- **(B) 残渣 2 行・B9 判定式逐位重测**（判定式完全一致＝engine 行 ∧ 白文含（ ∧ got 含（…仮名…））：
  - **rikutou59-2**：d0＝**224**（＝归档 edit_distance 逐位一致）・d1(白文直出下限)＝182・白文（ 位置 **14 か所**・got（…仮名…）span **13 個**。got＝「太公曰く、騎するは十勝つ有りて九敗る。太公が（たいこうは）（いわと曰いて）く、…」・exp＝「太公曰く、敵人始めて至り、行陣未だ定まらず、…」——**exp は白文第 2 段（敵人始至…）の訓読のみ＝行内の内容対齐ずれが残差の主成分**（kana 残渣はその上に載る）。
  - **soji07-6**：d0＝**36**（归档一致）・d1(白文)＝31・白文（ 位置 3 か所・got span 3 個。got＝「漁父に曰く、漁（ぎょ）父は（ほは）（いわを曰いて）く、…」・exp＝「聖人は物に凝滞せずして、能く世と推移す。」＝**尾段（聖人不凝滯於物、而能與世推移。）の訓読のみ**・got の頭「漁父に曰く、」が exp 外の余分。
  - **got 残渣の実態＝原样 echo ではなく引擎加工型**：rikutou59-2 got span 13 中白文原样 5・**引擎加工（送り仮名/助词の括号内插入・変形）8**——例：白文（いわ）→got（いわと曰いて）／（いわを曰いて）・（たいこう）→（たいこうは）・（奈何）→（如何）。soji07-6 は 3 中原样 1・加工 2。B9 regex は got の形状だけ見るので捕捉可能だが「残渣＝注记の原样 echo」という直感は**誤り**（③ got 側・坑位③）。
- **(C) sonshi09-38**：cls＝no_tail・tail＝空串・got＝空串・**d0＝13**（N98/N109/N113 記録一致）。白文実態＝漢文＋書き下し（ruby 付）＋**括号外現代語注记**の三重混在行・最後の「）」後尾段に仮名含む（＝no_tail の機構的理由）→ **剥夹注管線不能造尾段・設計上この行は管線外と明記**（④ I4 で実証）。
- **(D) echo 30 行・構成重测＋逐行分類**：直出 **14**・新字体化 **16**・other **0**・d0==0 **0 行**（N113 記録一致）。**逐行分類＝白文含（…仮名…）注记 30 行・与夹注无关 0 行**——echo 30 行は全部注记行だが、exp は**尾段の訓読のみ**（例：toushisen006-10 got＝借問大将誰・exp＝借問す　大将は誰ぞ）→ **echo は剥夹注管線の scope 外＝N84 尾段路径維持が正**（④ S3 で 30 行全変差を実測）。
- **(E) census**：**白文含（ 251 行**（分類別 echo 30／rerun 218／engine 2／no_tail 1）・**4000 内 0 行**・got 含（ **2** 行・got 含（…仮名…） **2** 行（＝B9 残渣 2 行で非 engine 分支は 0）・4000 内 0 行。

## 3. 夹注形态分类（実測为准・禁臆造）

工具：`tools/night115_forms.py`（3s）→ eval/night115_forms.json + night115_forms.txt（探索 probe＝night115_forms_probe.txt）。**未実測形態の assert が全て 0**：無仮名 （…） span 行 0・空 （） 0・括号不釣合 0・ASCII 括号 0・整行＝（…） 0・嵌套 0。

- **形態 1＝ruby 夹注（漢字（読み仮名）交织形）・251 行**（唯一の括号内注记形態・白文含（ 251 行と全体一致）。分類別内訳 echo 30／rerun 218／engine 2／no_tail 1。span 総数 **13419**・**99.8% が直前漢字に接続**（字級 ruby）・span 内容長 1–6 字（語注級 >3 字 1164/13419）。现行引擎行为＝分類別に engine 2 行は got に加工残渣／rerun 218 は尾段のみ引擎（注记消失）／echo 30 は尾段直出／no_tail 1 は空串。**verdict＝剥（Stage 1・engine 分支行のみ）**。
- **形態 2＝rongo「N）」编号（dangling ）無（）・6 行**（rongo1125-1／1125b-1／1125c-1／1125d-1／1125e-1／1125f-1・行頭「1）」「2）」…の節番号）。注记ではない（開括号なし・ruby 証拠不成立・backend 注记「rongo 系「1）」编号无开括号，不触发」の実体）。**verdict＝留（剥対象外）**——strip regex は（…）の対を要求するので自然保存（I1 identity に含まれる・S1 実測）。
- **形態 3＝括号外混在（sonshi09-38 型）・1 行**：漢文＋書き下し（ruby 付）＋**括号外**現代語注记（「奔走而陳兵車者…敵が慌ただしく…」「武経本には「車」の字なし。」等）の三重混在。注记が括号外なので**剥夹注では救えない**（剥しても現代語注记が残る＝引擎への入力は仍混杂）。现行引擎行为＝no_tail 空串 d0=13。**verdict＝管線外**（データ構造の問題＝语料整形は別工程）。
- **got 側実測（入力形態ではなく出力側の証拠）**：got に（…）span が残る行＝恰 2 行（B9 残渣）。span の内訳＝rikutou59-2 13 個中**原样 5・引擎加工 8**／soji07-6 3 個中原样 1・加工 2（送り仮名/助词の括号内插入・（いわ）→（いわを曰いて）・（奈何）→（如何））。**「剥夹注」で got から消えるのはこの加工残渣ごと**（S2 で d 改善として実測）。
- **未実測（0 行＝設計に書かない）**：割注・傍注・無仮名（…）注记・空 （）・ASCII 括号・嵌套括号・整行注记。将来语料でこれらが現れた場合は Stage 1 规则の再審（実装夜の scope 外・本設計は実測面のみを管轄）。

## 4. 管線设计（Stage 0–3）＋sim 验证

工具：`tools/night115_sim.py`（約 200s・S3 全 248 行引擎実測込み）→ eval/night115_sim.json + night115_sim.txt。**設計関数は sim 層で再実装（backend 一字未改）**・実装夜はこの spec を backend/main.py に落とす。

### Stage 0 检测（落点＝読码後写死）

- **现行判定原文（backend/main.py:116 `detect_text_type`）**：「按假名比例分流：假名（平假名+片假名）占非标点字符 >30% 判为假名文学文本。」——括号「（）」は分母から除外されるが**括号内の仮名は分子に数える**ため、ruby 夹注行は仮名占比が跳ね上がり kana 误判→N84 fallback（尾段截取）へ流れる（N78 §8・N84 記録の通り）。
- **新增信号＝注记 flag（推荐案）**：`has_ruby_annotation(text)`＝regex `（[^（）]*[ぁ-ゖー][^（）]*）` の search（＝B9 証拠式・N84 `_ruby_tail_kanbun` の ruby 証拠判定と同口径）。**detect_text_type 本体・返り値・API text_type 字段は全部不変**。ratio 改訂（剥後 text で ratio 再計算）は**採用しない**——そうすると echo 30＋rerun 218 が kanbun に再分類されて全文経路へ流れ、S3 実測の通り 247 変差＋例外 1 で必败（後述）。
- **誤判 fallback**：kana 分支（echo／rerun／no_tail）は**一切触らない**——真・仮名文（竹取物語等）・N84 尾段路径・sonshi09-38 型はすべて现行動作のまま（I4・S1 実測）。設計管線が触るのは engine 分支行のうち `has_ruby_annotation(text)==True` の行だけ（実測恰 2 行＝rikutou59-2・soji07-6）。
- **落点（实施夜・写死）**：`has_ruby_annotation`／`strip_annotation` を backend/main.py **142–166 の N84 ruby ブロック直後**に追加。`kundoku()` の **engine 分支（416–423）**で `kaeriten_text, ... = _kundoku_result_for(text, ...)`（**423 行**）の直前に 1 か所挿入：`if has_ruby_annotation(text): text = strip_annotation(text)`（＋note 付与＝N84 fallback_note 先例）。kana 分支（355）・tail rerun（363）・echo/no_tail（390–404）は**一字不改**。

### Stage 1 剥离

- **剥什么**：仮名を含む全角 （…） span のみ（`RUBY_SPAN_RE.sub("", text)`）。無仮名 （…）・空 （）・ASCII 括号・dangling ） は剥ない（実測 0 行かつ regex が対を要求＝rongo 编号 6 行は自然保存）。
- **边界规则**：span は括号対内で完結（非貪欲・`[^（）]*` は括号を跨がない）・剥離により前後の字符は直接連結（十（じっ）勝（しょう）→十勝）・空白挿入なし・改行変換なし。
- **剥下的东西放哪（拍板三选一・sim 既定＝丢弃）**：
  1. **丢弃**（sim 既定・実測済）：got は純書き下しのみ・最简单・API 契約不変。ruby 情報は失われる。
  2. **sidecar**：剥下 span を response 追加字段（例 `annotations`）で別表返し。情報保持だが **API 契約变更**・前端工数。
  3. **输出重贴**：got の対応位置に ruby markup（ルビ）として貼り戻し。N3 `kaeriten_text_raw`（合字保持の raw 併配）の先例があるが、**got 位置と剥離位置の対位が引擎改写でズレる**（rikutou59-2 実測：白文（いわ）→got（いわを曰いて）＝位置対応は自明でない）→ 工数最大・別工程推奨。
- **幂等**：`strip_annotation(strip_annotation(x)) == strip_annotation(x)`——S1 で **8165/8165 実測 PASS**（剥後は括号消失で再一致の構造）。

### Stage 2 规则链（零改动）

- 剥離後 text は现行鏈へそのまま：`_kundoku_result_for(text, merge, ortho, use_cache=cache, seg=seg)` → `style_fix_with_hakubun`（Rule A/D…）→ GUARD_FOLLOWUP_RULES（N111 機構）→ response 層 `normalize_shinjitai`。**规则・词库・链序・backend/kundoku_rules.py 一字不改**。

### Stage 3 输出契约

- got＝`normalize_shinjitai(kakikudashi)`（response 層・461 行现行通り）・**注记 span は got に出ない**（I6・S2 実測 2/2）。
- text_type 字段＝"kanbun" 維持（注记 flag 案では分類值不变）・hakubun（response の echo 用原文）は**剥後 text を返すか原文を返すかは实施夜の拍板項**（sim では剥後を処理・response hakubun は原文のまま＝default・N84 先例では hakubun=text 原文）。
- db.save_kundoku・modern/glossary は剥後 text を受ける（キャッシュキーも剥後 text で自然分離）。

### 不变量（回帰门の核）

- **I1** 非注记行（7914 行）＝strip 恒等変換・byte-identical（S1 実測 7914/7914）。dangling ） 6 行・rongo 全行を含む。
- **I2** strip 冪等（8165/8165）。**I3** ruby 行剥後無括号（251/251）。
- **I4** kana 分支路径不変（sonshi09-38 剥後も detect=kana 実測・no_tail 空串維持）。
- **I6** 管線行 got 無注记 span（2/2）。
- **全量回帰 spec（实施夜）**：pytest **503**（实施夜で tests 追加なら 503＋N）・双口径真跑 vs night111 归档＝**4000 13.455/24/0 全行 byte-identical**（scope 0 行）・**8165 sum 109934→109852（avg 13.464→13.454）・diff 恰 2 行**（rikutou59-2 224→155・soji07-6 36→23）・其余 8163 行 byte-identical・exact 24/30 不変・verify **26/26** exit 0（归档源切替は N107/N111 先例）。

### sim 验证（tools/night115_sim.py・不写归档・产物 eval/night115_sim.json/.txt）

- **(S1) 不变量 I1–I4 実測**（8165 全行）：identity 7914/7914・冪等 8165/8165・剥後無括号 251/251・sonshi09-38 剥後 detect=kana。**全 PASS**。
- **(S2) 設計管線（scope 恰 2 行）**：
  - 現行再現＝`_kundoku_result_for(hb, True, True, use_cache=False)`＋response 層 `normalize_shinjitai` が**归档 got と byte-identical**（2/2・sim 鏈＝真鏈の検証）。
  - **rikutou59-2：d0=224 → d1=155（改善 Δ−69）**・**soji07-6：d0=36 → d1=23（改善 Δ−13）**——残渣 kana span（加工残渣含む）の消失分。設計 got は注记 span を含まない（I6）。**scope 内新增变差 0**。
  - 残差の主成分は内容対齐ずれ（rikutou59-2＝exp は白文第 2 段のみ・soji07-6＝exp は尾段のみ＋got 頭の余分「漁父に曰く、」）＝**剥夹注管線の救済域は注记残渣のみ**・対齐ずれは语料整形の別課題（管線外と明記）。
- **(S3) 被否替代案の証拠（echo30＋rerun218 の 248 行を「全剥→引擎」で走らせる＝実装しない・証拠収集のみ）**：**変差 247（echo 30 全行＋rerun 217）・例外 1（utsuryo08-2 IndexError＝现行鏈で 500 になる入力）・改善 0・same 0**。機構的理由＝echo/rerun の exp は**尾段の訓読のみ**（実測・§2(D)）で、全文経路の出力は exp より大幅に長くなる。→ **reroute は封印・kana 分支は N84 尾段路径維持が確定**。
- **判定门（任务书）＝残渣行改善 ∧ 新增变差 0 → 設計成立**：改善 2／変差 0／same 0＋I1–I6 全 PASS＋S3 変差 0（scope 外は路径不変のため変差なし）＝**成立**。
- sonshi09-38＝逐行明記で**管線外**（剥後も kana・no_tail 維持）・echo 無注记行＝**0 行**（実測 30 行全部注记行）・echo/rerun＝**N84 尾段路径維持**（S3 変差 247 の実測で封印）。

## 5. 实施夜移交

- **回帰门（全量）**：①pytest 503（tests 追加時は 503＋N）②双口径真跑 sim vs night111 归档＝4000 **13.455/24/0 全行 byte-identical**・8165 **sum 109934→109852（avg 13.454）・diff 恰 2 行・其余 byte-identical・exact 24/30 不変** ③verify **26/26** exit 0 ④accept PASS fail=0（报告後の実施夜は NIGHT_ARTIFACTS 登記要否をその夜の性質で判定）。
- **实施夜 allowlist（将触 backend 文件清单・設計時点で写死）**：
  - **backend/main.py のみ**：①142–166 の N84 ruby ブロック直後に `RUBY_SPAN_RE`／`has_ruby_annotation`／`strip_annotation` 追加 ②`kundoku()` 423 行直前に 1 か所挿入（strip＋note）。
  - **触らない**：backend/kundoku_rules.py（规则链零改动）・detect_text_type 本体・kana 分支・tail rerun・echo/no_tail パス・词库・golden expected・README・verify・tests（追加は可＝tests/test_night115_strip.py を实施夜が作る場合は pytest 503→503+N）・accept_night.py。
- **待用户拍板的问题**：
  1. **剥下注记去向三选一**：丢弃（sim 既定・実測済・got 純書き下し・API 契約不変）／sidecar（response 追加字段・契約变更）／输出重贴（ルビ貼り戻し・位置対位が引擎改写でズレる＝別工程推奨）。
  2. **detect_text_type 新信号命名**：helper `has_ruby_annotation`（推荐・B9 同口径・API text_type 契約不変）／第三 type 值 `kanbun_ruby`（text_type 字段の契約变更・frontend 影響）。
  3. （補足・既定値の確認）実施范围＝engine 分支注记行 2 行のみ・kana 分支 249 行（echo30＋rerun218＋no_tail1）は N84 維持＝S3 247 変差＋例外 1 の実測に基づく封印。rikutou59-2/soji07-6 の残差は内容対齐ずれ＝语料整形の別課題（本管線の域外）。
- **拍板表正文不动**（更新归在庫夜・N113 §3 のまま）。実施後の表更新項＝項 9「在庫」→「已実施（N116…）」は实施夜の wrap-up で行う。

## 6. 坑位

1. **`_kundoku_result_for(use_cache=False)` は `seg=collections.defaultdict(float)` 必須**——整段路径は `seg["engine"] += …` で辞書に直接加算するので空 dict だと KeyError。生产入口 `kundoku()` は `seg = collections.defaultdict(float)` を渡すので今まで顕在化しない。sim 層で呼ぶ時は必ず defaultdict を渡す（本夜開発中 1 回）。
2. **ortho 新字体化は response 層**（kundoku() 394/461 行 `kakikudashi=normalize_shinjitai(kakikudashi) if ortho else …`）で `_kundoku_result_for` の外——归档 got の再現には sim 側で自分で `normalize_shinjitai` を掛ける（無しでは 0/5・有りで engine 行 4/4 byte-identical。echo 行は尾段直出路径なので当然不一致）。
3. **got の注记残渣＝原样 echo ではなく引擎加工型**——引擎が送り仮名/助词を注记括号内に插入する（（いわ）→（いわを曰いて）・（奈何）→（如何））。B9 regex は got の形状だけ見るので捕捉可能だが、「残渣＝白文の注记がそのまま出たもの」という直感に頼ると分析を誤る。
4. **echo/rerun の expected は尾段対齐**——N84 語料整列の仕様。全文経路（全剥→引擎）は出力が exp より長くなり必败（S3 実測 変差 247・例外 1）。「剥夹注＝全文をきれいにして引擎へ」という一般化は kana 分支では禁物。
5. **JSON dump の tuple 键**＝`Counter((cls, verdict))` の键は JSON 非直列化（TypeError: keys must be str…）で json.dump が落ちる（本夜開発中 1 回・最初の sim 走行は測定完走後の出力段で崩溃＝測定値は run ログから救出済み・键を "cls|verdict" 文字列化して再走）。N113 坑位 2/3（集合比較・保存順）の近縁＝**「JSON に入れるものの键は最初から str」**。
6. **`.night72_deps` は現存しない**（night113_status.py が参照するが実ディレクトリ無し）→ 本夜の lev は全部**純 Python 回退**（night85_eval 同一算法・归档逐位一致実績）。整合確認＝自前 d0 が归档 edit_distance と逐位一致（rikutou59-2 224・soji07-6 36・sonshi09-38 13・rongo1442-1 54）＋再計算 avg 13.455/13.464 一致。今後新規ツールは `.night72_deps` 参照を書いても無害（try/except 必須）。
7. **CJK console redirect は mojibake**（N113 坑位④継承・本夜再確認）——CJK を含む print は Git Bash リダイレクトで cp1252 崩れ。tools 内は utf-8 落盘＋console は EXIT code 判定に使う。

## 交付对照（任务书「交付」の数値欄）

- 开工：HEAD＝4e335ac ✓・origin/master＝4e335ac（rev-list=0）✓・pytest 503 passed（27.96s）✓・目录 D:\kanbun-kakikudashi・分支 night115-annotation-design（自 master 分出）✓
- 现状：残渣 2 行（rikutou59-2・soji07-6・B9 逐位一致）・sonshi09-38 no_tail d0=13（管線外）・echo 30（直出 14＋新字体化 16・**含注记 30 行／无关 0 行**）・白文含（ **251** 行・got 含（…仮名…） **2** 行（4000 内 **0** 行）——与 N113 旧数一致 **全項**／漂移 **0** 项
- 设计：夹注形态 **3** 种（①ruby 夹注 251 行＝剥・②rongo「N）」编号 6 行＝留・③括号外混在 1 行＝管線外；got 側加工残渣 2 行は出力側証拠）；管線 Stage 0–3（检测＝detect_text_type 本体不改＋新信号 `has_ruby_annotation`（B9 同 regex）・剥离＝仮名含 （…） span 全剥＋冪等実測・规则链零改动・输出契约＝got 無注记 span＋text_type 不変）；sim：残渣 **2** 行改善 **2**／变差 **0**（**設計成立**）＋被否替代案変差 247・例外 1；不变量＝非注记行 byte-identical＋全量回帰 spec（pytest 503・双口径 vs night111・verify 26/26）。拍板表正文未动 ✓
- 验收：accept 115 PASS fail=0 skip=1（skip=eval_integrity；试跑 FAIL=repo_clean 1 項設計行為・FAIL/PASS 两行留 ACCEPT_LOG）・分支两提交＝主提交＋wrap-up・未合 master・未推远程（rev-list=2・master 4e335ac 未動）・NIGHT_ARTIFACTS[115] 不登记・禁碰区一字未动・心跳 **6 行**（开工 1＋進度 4＋收工 1）
- 报告＝D:\kanbun-kakikudashi\REPORT_NIGHT115.md（工具＝tools/night115_recheck.py・night115_forms.py・**night115_sim.py**・产物＝eval/night115_* 12 個＋accept_night_115.json）。实施夜待用户拍板：注记去向三选一（丢弃／sidecar／输出重贴）＋detect_text_type 新信号命名；分支两提交待合并夜合入后由用户手推。
