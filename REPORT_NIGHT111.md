# REPORT_NIGHT111 — 守り字後继字機構（follow_map）実施夜（ZCode 单会话・night111-followmap-impl 未合未推）

执行者：ZCode（单会话）。任务书：用户拍板 2026-11-28 11:50 点选「(d) follow_map 実施夜」。基线＝night107 归档（4000 13.460/24/0・8165 13.466/30/0）。

## 0. 结论（先说）

1. **機構実装＋収録完成・全验收 PASS**：N106 §1 設計（(kana, guard, follow_map, default_repl) 4 元組）を N109 §2(d) 逐位再验済みのまま実装・ことなき（guard 莫）1 entry 収録。**発火恰好 15 行・変体改写恰好 5 行・d 改善恰好 4 行・変差新增 0 行・冪等 bad 0**——night111_sim 全硬断言 PASS、実装 vs sim 15 行 ALL MATCH、双口径真跑 sim 逐位一致（4000 13.455/24/0・8165 13.464/30/0・diff 恰発火行・計画外 0・欠落 0・機構予測不一致 0）。pytest 491→**503 passed**・verify **26/26 exit 0**・accept **111 PASS fail=0 skip=0**。
2. **rikutou26-5（53→54）＝拍板許容行のまま維持**：機構は 大→莫し を判対（字形選択は機構の管轄）だが d 変差は語順構造差で残存（N106 §1.4 結論の機構側再確認）。0-worsening 门はこの 1 行のみ讓歩（N99 kokyo09-5/N104 同框）。
3. **記録偏差 1 項（数字口径・本夜新知見）＝任務書 golden 予想（4000 13.458–13.459・−6 字／8165 13.465・−7 字）は sim の機構純効果口径（(a) 単一 repl→follow）の転記で、golden 実測 Δ には default_repl 収録自体の効果（N106 (a) 分 −12 字/−14 字）が乗る**：実測＝**4000 13.455（13.460−20 字）・8165 13.464（13.466−19 字）**＝sim A9 raw→follow 総効果（N106 follow 記録 −0.0023/−0.0050 と一致）の理論値に丸め含め完全一致。任務書 sim 硬断言（15/5/4/0/−7/−6 字/冪等）は**全部 PASS**（任務書の Δ8165 −0.001(−7 字)・Δ4000 −0.002(−6 字) は (a)→follow 口径として sim で逐位確認済み）。
4. **機構の純効果（(a) 単一 repl→follow）＝d 改善 4 行・変差 0・Δ8165 −7 字・Δ4000 −6 字**：単一 repl で救えなかった 5 site（大 2・知/吾 2・如 1）を後继字判別で救う＝機構は (a) の真上乗せ（(a) に対して per-row で劣る行は一つも無い＝N106 §2.3 結論の実装確認）。

## §1 设计引用（本夜実装の根拠）

- **REPORT_NIGHT106 §1**：機構設計——4 元組 entry・follow_map（白文 guard 字直後 1 字→repl 変体）・containment guard 第一 gate 維持・対位失敗/表外後继字→default_repl（=発火不増の構造保証）・無 follow_map の既有規則零改动・链尾追加のみ（§1.3 第 5 条）・rikutou26-5 管轄判定（§1.4：字形選択は可・d 変差は語順構造差で不救）。
- **REPORT_NIGHT106 §2.3**：原型実測——後继字→活用形 表（多数決＋语料多数形 tie-break 莫き優先）・判対 15/18・衝突字 能/己/之（2 字後继 己知 も衝突）・follow モード better 12/worse 1/same 2・Δ8165 −0.0023（−19 字）・per-row 値。
- **REPORT_NIGHT109 §2(d)**：逐位再验——N106 `eval/night106_guard_nxt.json` と全項目一致（judge・follow_map・conflicted・三 mode per_row・Δ 全部）を night107 基线で確認済み＝本夜実装の前提。

## §2 実装（backend/kundoku_rules.py・main.py 無改）

任务书「backend/main.py（仅 rule loop 内 follow_map 选择分支——若 loop 在他处，先读再定，禁大改）」→ **loop は kundoku_rules.py 侧と判明**（main.py は style_fix_with_hakubun 1 呼び出しのみ・backend/main.py:334）。よって main.py は一字も触らない。

接続方式＝**N106 §1.2 の差し替え案（新 Rule 字母 V は切らない）**：機構を独立関数 `style_guard_followup` として `style_fix_with_hakubun` の chain 尾（U の直後）に 1 行追加＝N106 §1.3 第 5 条「链尾追加のみ＝既存链不変式」。既存 E〜U 全規則・词库・golden expected は一字も変えない（tests で链序 18 呼び出し順を lock）。

- `GUARD_FOLLOWUP_RULES`（N106 §1.1 のコード例通り・1 条）：
  `("ことなき", ("莫",), {"由":"こと莫き","予":"こと莫き","我":"こと莫き","之":"こと莫き","能":"こと莫き","己":"こと莫き","大":"こと莫し","知":"こと莫からん","吾":"こと莫からん","如":"こと莫かる"}, "こと莫き")`
- `GUARD_FOLLOWUP_TOKEN_RE`＝`こと莫かれ|こと莫く|こと莫き|こと莫し|ことなき`（対位は こと系 莫-token **全体**で 1:1——rikutou26-5 は got 莫-token 4↔白文 莫 4 で token#3↔莫#4 対位（N106 原型実測同款）＝ことなき だけ数えると対位がずれるため・N106 §1.2「got 中 kana 出現列」の原型実装の実態）。
- `_guard_followup_sites`（純粋関数・手順 1 containment→手順 2 対位（個数不一致→fail-safe default 全置換）→手順 3 後继字→手順 4 site 級 repl 差し替え）＋`style_guard_followup`（公開）。
- `GUARD_FOLLOWUP_LONGER_WORDS`＝`{"ことなき": ()}`（N106 18 site 実測で後続成形語なし＝空表維持）。
- 莫 は新旧変異なし（SHINJITAI_MAP 両方向に無し＝guard_forms 展開不要・単一 莫 直查）。

## §3 sim（tools/night111_sim.py・22s・基线 night107 归档）

硬断言（任務書・(a) 単一 repl→follow 口径）**全 PASS**：

| 門 | 実測 | 期待 |
|---|---|---|
| S1 行分类 | 7916/30/218/1 | 一致 |
| S2 词库 | 1531（209+291+1031） | 一致 |
| S3 基线 | 13.460/13.466・exact 24/30 | 一致 |
| A1 発火 | 恰 15 行（N103 ID 集） | 15 |
| A2 対位 | 15 行全成立（got token=exp token=白文 莫）・fail-safe 発火 0 | 一致 |
| A3 site | 18 個・後继字分布 能2/己2/我1/知1/之4/由2/吾1/予2/如1/大2・判対 15/18・表外 0 | N106 記録 |
| A4 (a) per-row | 15 行逐位＝N106 `per_row a` | 一致 |
| A5 follow per-row | 15 行逐位＝N106 `per_row follow` | 一致 |
| A6 改写 | 恰 5 行（こと莫し 2・こと莫からん 2・こと莫かる 1） | 任務書 |
| A7 改善/変差 | 恰 4 行（26→24・35→33・22→20・35→34）・変差 0・rikutou26-5 54→54 維持 | 任務書 |
| A8 Δ | −7 字（−0.0009）／−6 字（−0.0015） | −0.001／−0.002 |
| A9 raw→follow | −19 字（8165）／−20 字（4000 内）＝N106 follow 記録 | 一致 |
| A10 冪等 | bad 0（15 行） | 0 |

## §4 sim→実跑 逐位对照（15 行明细・night107 归档 d_raw→(a) d0→follow d1）

| 行 | cls | d_raw | (a) d0 | follow d1 | 変体 |
|---|---|---|---|---|---|
| mujun-2 | engine | 11 | 10 | 10 | （能＝多数決 default 同値） |
| onoreshiru-1 | engine | 18 | 17 | 17 | （己＝多数決 default 同値） |
| kagakujota-1 | engine | 27 | 26 | **24** | 知→こと莫からん（site#0 我＝default 同値） |
| kanchuna-1 | engine | 82 | 81 | 81 | （之＝多数決 default 同値） |
| rongo0615-1 | engine | 12 | 11 | 11 | （由＝default 同値） |
| rongo0732-1 | engine | 23 | 22 | **20** | 吾→こと莫からん |
| rongo1315-1 | engine | 113 | 110 | 110 | （予/之/之＝default 同値） |
| rongo1442-1 | engine | 55 | 54 | 54 | （己＝判错→(a) 値維持・exp 莫くんば） |
| p-danjoshitsu-1 | engine | 36 | 35 | **33** | 如→こと莫かる |
| tarekako-1 | engine | 12 | 11 | 11 | （由＝default 同値） |
| tonan-1 | engine | 29 | 28 | 28 | （之＝判错→(a) 値維持・exp 莫し） |
| warekimi-1 | engine | 35 | 34 | 34 | （予＝default 同値） |
| roushi46-2 | engine | 34 | 35 | **34** | 大→こと莫し（roushi46-2 は 変差解消→改善 1＝N106 持平→(a) 比較で改善） |
| utsuryo03-7 | engine | 63 | 63 | 63 | （能＝判错→(a) 値維持＝same） |
| rikutou26-5 | rerun | 53 | 54 | **54** | 大→こと莫し（判対）＝**拍板行・変差維持** |

実装 vs sim＝15 行 ALL MATCH（tools/night111_impl_check.py）。真跑（TestClient 完整链）で 15 行の got は機構予測文本と逐位一致（両口径とも機構予測不一致 0）。

## §5 真跑（TestClient 完整链・基线 night107 归档・sim 逐位一致）

| 口径 | 実測 | vs night107 | 期待 |
|---|---|---|---|
| golden_4000 | **13.455**／24／0 | diff 恰発火 4000 内 12 行・計画外 0・欠落 0 | 理論 13.455（−20 字） |
| golden_8165 | **13.464**／30／0 | diff 恰発火 15 行・計画外 0・欠落 0・新增変差 0 | 理論 13.464（−19 字） |

exact 24/30 不変（15 行はいずれも exact 非該当）。「改写 5 行与 sim 预测逐位一致」＝変体 5 行（kagakujota-1・p-danjoshitsu-1・rongo0732-1・roushi46-2・rikutou26-5）の実跑 got は機構（＝sim 同一アルゴリズム）予測文本と逐位一致。

**記録偏差（口径）**：任務書 golden 予想「4000 约 13.458–13.459（−6 字）／8165 13.465（−7 字）」は sim 硬断言の Δ（(a) 単一 repl→follow＝機構純効果）の転記。実際の golden Δ は **raw（ことなき 残量）→実装後**＝default_repl こと莫き の収録自体の効果（N106 (a) −12 字/−14 字）＋機構純効果（−7/−6 字）＝**−19/−20 字**＝13.466−0.00233→13.464・13.460−0.005→13.455。実測値は sim A9 の理論値と丸め含め完全一致（N106 follow 記録 −0.0023/−0.0050 と一致）。任務書の sim 硬断言自体は全 PASS・golden 予想のみ口径差＝本節に記録。

## §6 tests・verify・README・登记

- `tests/test_night111_followmap.py` 12 条＝pytest **503 passed**（491+12）：
  10 字 follow_map site 判定表（合成行・表内全字）・表外後继字/文末後继字 default fallback・衝突字 能/己/之 多数決 fallback＋判错 3 行実行型（(a) 値維持）・対位失敗 fail-safe（default 全置換）・対位（既存出力形を先に消費＝roushi46-2/rikutou26-5 token#2/#3）・任務書改善 4 行 d0→d1 lock・rikutou26-5 lock（53→54・(a) も 54＝語順構造差由来）・毋系 4 行不受影响（ichijicho-1 行型＋毋 3 行型）・冪等（実 8 行＋合成行）・链序不変（style_fix_with_hakubun 18 呼び出し順 lock＋chain 併用＋既存 chain 動作再確認）・sim JSON lock（15/18 判定表・per_row 15 行 N106 記録・Δ 値）。
- `tools/verify_readme_facts.py`：归档源 night107→**night111** 切换＋N111 守り字後继字機構断言追加（25→**26**、needle 製品 tuple 派生）＝**26/26 exit 0**。
- README：header（分支起点 5633eca 指定＝自己参照不可 N104 坑位③/N107 先例）・テスト **503 passed**・規則エンジン **13.455**／**24/4000**・拡張評価 **13.464**／**30/8165**・N111 機構说明（数字行＋ルールチェーン行）。数字与 header 同一提交内改完。
- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `111: ["night111_results_4000.json"]`（8165 併行归档・night107 归档不触碰）＝**N91/N96/N99/N104/N107 先例**。
- 归档：`eval/night111_results_4000.json`・`eval/night111_results_8165.json`（changed_ids_vs_n107 附記）。
- ROADMAP：Night 111 行追加。

## §7 记录偏差与坑位

1. **任務書 golden 予想口径差（§5 記録偏差）**：実測 13.455/13.464＝理論値一致・任務書 −6/−7 字 は機構純効果口径。次回同型任務書は「golden 予想 Δ には default_repl 収録効果（(a) 分）が乗る」に注意。
2. **4000 归档外発火行 3 行**（rikutou26-5・roushi46-2・もう 1 行）＝night111_eval_4000 の pred 集合は 4000 内 12 行のみ（工具修正済み・8165 は 15 行全部）。
3. **Levenshtein C（.night72_deps）は本 clone に無し**＝纯 Python 回退（night85_eval 同一算法・归档逐位一致実績）。sim/実装/テスト/真跑 全て同一纯 Python lev。
4. **fail-safe span 生成**：個数不一致時は `re.finditer(kana)` で全 site span（初版は find で 1 site のみ＝実装中に修正・sim と同一挙動に統一）。
5. **对位 token は こと系 莫-token 全体**（ことなき だけ数えると rikutou26-5/roushi46-2 型で対位がずれる）＝N106 §1.2 文言「got 中 kana 出現列」の原型実装の実態。entry 追設時は token 族の再確定が要る（コード注记済み）。

## §8 禁止事项自查

- 禁 OCR・禁 guwenbert・禁 eval 以外のネット＝遵守（全行程 offline）。
- 禁新开 Rule V 系列＝遵守（新 Rule 字母は切らず chain 尾 1 行追加＝N106 §1.2 差し替え案）。
- 禁碰：項 3/5/6/7/8/9・嗟や在庫・per-guard 変体・毋系在庫（N103 ことなき→こと毋き guard 毋 4 行＝ichijicho-1 行型で不発火 lock）・(c) 改設計 probe・N84 遗留・词库（1531 不动）・golden expected・night106–110 分支＝全て一字未动。
- 変差新增 0 行（rikutou26-5 54 維持＝拍板行のみ）・発火 15 行・改写 5 行＝任務書通り。
- 不合 master・不推远程・分支 night111-followmap-impl 两提交（主提交＋wrap-up）。
