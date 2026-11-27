# REPORT_NIGHT107 — 項 4 実施夜：guard 変体字拡張 C1＋C4（N106 §3 実施建議の実施）

- 日期：2026-11-26（单会话・AutoClaw）
- 分支：`night107-item4-impl`（自 master `f5e0bf3`＝N105 wrap-up 分出）；**不合 master、未推远程**
- 任务书：Night 107 任务书——N106 REPORT §3 実施建議の項 4 を実施（guard タプル 2 変更のみ・新規則系列不設・C2/C8 は禁实施）
- 先例：N99/N104 規則夜型（sim 先行→収録→真跑→verify→accept）；変更本体は N72 悪んぞ (惡,悪)・N73 そく→即ち (即,卽)・N86 たりせ→為ら (爲,為) の「guard 新旧両形並查」成文慣例の適用（N106 §3＝(即,卽) 慣例の Generalization）
- 工具：`tools/night107_sim.py`・`tools/night107_eval_4000.py`・`tools/night107_eval_8165.py`（新 3 个・LF）＋`tests/test_night107_item4_impl.py`（新 1 个・7 tests）
- 实测证据：`eval/night107_sim.{json,txt}`・`eval/night107_changed_rows.json`（改写 2 行预测＝真跑对照源）・`eval/night107_results_{4000,8165}.json`（双口径归档）
- 基线＝night104 归档（N105 合并链尾・N106 が全 gate 锁定済み）：avgDist 4000＝**13.460**／8165＝**13.467**・exact **24/30**・词库 **1531**・行分类 **engine 7916 / echo 30 / rerun 218 / no_tail 1**

## 0. 结论（先说）

1. **項 4 两行收掉（N106 §2.1 設計どおり）**：C1＝Rule L がため→為 guard (爲,)→(**爲,為**)・C4＝Rule M 何のごとく→奈何ぞ guard (奈,)→(**奈,柰**)。製品変更は `backend/kundoku_rules.py` の guard タプル 2 行のみ（+12 B・恰 2 行差分＝patcher 逐行 diff 断言）——repl／链序／長词表／規則数（L 9 語・M 8 語）／golden expected は一字不変。
2. **sim→真跑逐位一致**：発火恰好 2 行（rikutou37-2 **44→43**・shiki050-4 **25→20**）・改善 2／変差 0・組合 Δ8165 **−0.001**（−6 字）・Δ4000 **0.000**（両行 4000 外）。真跑＝golden_4000 は night104 归档と**全行逐位一致 13.460/24/0**（改写 0 行）・golden_8165 は **13.466/30/0**（改写 2 行・new_text 逐位一致・計画外 0・欠落 0・変差 0）＝N106 §2.1 組合 preview の実機再現。
3. **N106 否決項は禁实施のまま未動**：C2（無/罔字拡張）・C8（tail→全文機構）は本夜も未測・未実装；項 5 は系（N106 §2.2 負結果＝放弃建议）・項 3/6/7/8/9 在庫・(c) 守り字后继字機構（改設計・棚上げ）＝一切未動。拍板事項残り（N98 §3 决策表）原样带入。
4. 数字：pytest **491**（484＋7）・verify **25/25** exit 0（N107 guard 変体字断言追加 24→25＋归档源 night104→night107 切换）・accept 107 PASS fail=0 skip=0（七门全绿）・词库 1531・行分类 7916/30/218/1・echo 30 行/no_tail 1 行不触。

## §1 设计（N106 §2.1/§3 引用・実装詳細）

**判別式＝guard 变体字拡張のみ**（N106 §2.1 実測表の採用候補 C1/C4）：

| 項 | 規則 | 現行 guard | 本夜 guard | 変体字の性質 | 死因（N106 §2.1） |
|---|---|---|---|---|---|
| C1 | Rule L がため→為 | (爲,) | (爲,為) | 為＝爲 の新字体（SHINJITAI_MAP[爲]＝為・guard_forms(爲)＝[爲,為] 派生可） | rikutou37-2 の tail は新字体 **為** を持ち（為之奈何）、guard 爲 旧字のみ硬编码が miss |
| C4 | Rule M 何のごとく→奈何ぞ | (奈,) | (奈,柰) | 柰＝奈 の異体字（**SHINJITAI_MAP 両方向に無い**＝guard_forms(奈)＝[奈] しか出ない→**リテラル tuple 必須**） | shiki050-4 の tail は異体字 **柰** を持ち（柰何續其後）・白文含柰は全域 shiki050-4 のみ（N106 S3 gate） |

- **成文慣例**：Rule M そく→即ち (即,卽)（N73）と Rule O たりせ→為ら (爲,為)（N86）が新旧両形 tuple の前例。C1 は O と同一 tuple、C4 は異体字をリテラルで並べる初例（guard_forms 派生に乗らない字形は tuple 直書き＝N69 がため 爲/爲 教訓・N72 惡/悪 同制式の延長）。
- **engine 語义**：guard 判定は実行時 `if guard and hb and not any(g in hb for g in guard): continue`（E〜U 全条同構・hb＝engine 行は norm(白文全文)／rerun 行は norm(tail)）——tuple への 1 字追加は「発火集合の単調拡大」でしかなく、既存発火行（爲 又は 奈 を含む白文）は挙動不変。
- **不採の確定事項**（N106 §2.1）：C2 無/罔字拡張（rikutou37-2 tail の 無 は 偶然一致＝為 の根拠にならない）・C6 何のごとく×無/罔（実測 0 発火）・C8 tail→全文機構（flip 177 行→pipeline 実変化 1 行 d±0＝両目標不救）・C9 tail 句型判別（rerun 行では guard 変体字 ≡ tail 句型判別＝同一述語で別機構不要）。

## §2 sim→真跑逐位对照（tools/night107_sim.py 19s→eval 双口径）

sim＝night99/104_sim 型（night104 归档 got に候補規則を解析適用・guard 判定は製品と同一の `any(g in hb)`・行分类/guard 语境は night98_audit 同款）。guard 変体字拡張は「既發火行は archived got に kana が残らない＝_apply_count 不発・guard miss 行のみ新発火」なので解析適用＝実 pipeline と完全同型（全链再適用は tests の style_fix_with_hakubun 断言で別途実証済み）。

| 測定 | 発火 | 改善/変差 | d0→d1 | Δ8165 | Δ4000 | sim | 真跑 |
|---|---|---|---|---|---|---|---|
| C1 単条 guard(爲,為) | 1（rikutou37-2） | 1/0 | 44→43 | −0.000 | 0.000 | ✓ | ✓（8165 改写 2 行内・4000 改写 0） |
| C4 単条 guard(奈,柰) | 1（shiki050-4） | 1/0 | 25→20 | −0.001 | 0.000 | ✓ | ✓（同上） |
| C3 对照 guard(爲,) 現行 | **0** | — | — | 0.000 | 0.000 | ✓ | —（残量確認） |
| C5 对照 guard(奈,) 現行 | **0** | — | — | 0.000 | 0.000 | ✓ | —（残量確認） |
| **combo C1+C4** | **2** | **2/0** | 44→43・25→20 | **−0.001**（−6 字） | **0.000** | ✓ | ✓ **逐位一致** |

- sim 硬断言（S1〜S6 一次 PASS）：行分类 7916/30/218/1・S2 链完整性＝night104 vs night101 归档 got diff **恰 17 行＝night104_changed_rows.json（Rule U 17 改写）の ID 集合**（基线＝night101＋Rule U の証明）・基线 avgDist 13.460/13.467 exact 24/30・词库 1531・guard_forms(爲)＝[爲,為]／guard_forms(奈)＝[奈]（柰 非 SHINJITAI＝リテラル根拠）／リテラル tuple は guard_forms 冪等・repl 终字形＋構造冪等（repl に kana 非含有）・**guard miss 残量＝恰 1 行ずつ**（がため∧爲 無し＝rikutou37-2 のみ・何のごとく∧奈無し＝shiki050-4 のみ＝N106「唯一の guard miss 行」再確認）・echo/no_tail 規則不可達・幂等 bad 0。
- 真跑（TestClient 完整链）：golden_4000＝**13.460/24/0・改写 0 行**（night104 归档全行逐位一致・両行 4000 外）／golden_8165＝**13.466/30/0・改写 2 行**（new_text 逐位一致・計画外 0・欠落 0・変差 0）。exact 24/30 不変・N99 変差 6 行集合・N104 変差 1 行 kokyo09-5 に触れず。

## §3 两行明细（N106 §2.1 dissect の真跑再現）

| 行 | cls | got 残量→本夜後 | tail（guard 语境） | tail 内守り字 | exp | d0→d1 |
|---|---|---|---|---|---|---|
| rikutou37-2 | rerun（tail 58 字） | 「…戦則不勝。之がため奈何。」→「…戦則不勝。**之為奈何**。」 | 「武王曰、敵之地勢、不可以伏其両旁、車騎又無以越其前後、…戦則不勝。**為之奈何**。」 | **為**（新字）・無（爲 旧字は全文にも無し） | 「之を為すこと奈何」 | **44→43** |
| shiki050-4 | rerun（tail 18 字） | 「今に乃に首七国を率す、紛なりて天下を乱す。**何のごとく其の後を続す**。」→「…**奈何ぞ其の後を続す**。」 | 「今乃首率七國、紛亂天下。**柰何續其後**。」 | **柰**（奈 は全文にも無し） | 「奈何ぞ其の後を続がしめん、と。」 | **25→20** |

- tests/test_night107_item4_impl.py が両行の実 tail 语境（night107_changed_rows.json の hb 同梱）で Rule 単体＋全链（style_fix_with_hakubun）双方を断言＝真跑 new_text と逐位一致。

## §4 回归清单実績（N106 §4 項 4 型全量）

1. **pytest tests -q**＝**491 passed**（15.78s・484＋test_night107_item4_impl.py 7 tests：正例 2 行・guard 反例〔無/罔＝C2/C6 不採ロック＋守り字全無＋旧字対照＋空白文〕・全域只改 2 行断言〔sim gates／C3/C5 对照 0 発火／guard miss 残量恰 1 行〕・構造ロック〔guard tuple 2 处のみ・(即,卽)/(爲,為) 先例不変・規則数 9/8 不変・repl 冪等〕・幂等＋現代句・链序不変〔T/U 領域併用・kokyo09-5 行型不変〕・night104 基线锚〔両行 d0＝44/25・両行 4000 外〕）。
2. **真跑双口径**（TestClient 全量）：§2 のとおり sim 逐位一致・計画外 0・欠落 0・変差 0・両行 4000 外。
3. **tools/verify_readme_facts.py**＝**25/25 exit 0**（guard 変体字断言追加＝CHECKS 24→25・needle は製品 tuple から派生「N107 で guard 変体字拡張（Rule L がため guard 爲/為・Rule M 何のごとく guard 奈/柰・規則数不変）」・归档源 night104→night107 切换・avgDist needle %.3f 尾零保持 13.460）。
4. **tools/accept_night.py 107**＝PASS fail=0 skip=0（七门全绿・NIGHT_ARTIFACTS[107]＝["night107_results_4000.json"] 登记）。
5. **不動確認**：词库 1531（209+291+1031 sim 実証）・行分类 7916/30/218/1・golden expected 一字不改・既存 26 規則系列と链序 E〜U 不変（S2 链完整性 diff 恰 17 行＝Rule U 分のみ）・kokyo09-5＋N99 変差 6 行集合不拡大・echo 30 行/no_tail 1 行不触。
6. **SHIFT_LOG／ACCEPT_LOG／ROADMAP**：心跳 4 行（開工/实施/真跑/wrap-up）・accept 自動追記・ROADMAP 末尾 1 行。

## §5 开工核验

- `git checkout -b night107-item4-impl master` → HEAD＝**f5e0bf3**（N105 wrap-up）✓
- `pytest tests -q`＝**484 passed**（12.71s）✓；已跟踪文件零改动 ✓（untracked は eval/ 历史缓存・ocr_samples 等既存のみ＝repo_clean 影響なし）
- 移交阅读：REPORT_NIGHT106 §2.1（C1/C4 全域実測表）・§3（実施建議）✓；`backend/kundoku_rules.py` Rule L がため→為 guard (爲,)／Rule M 何のごとく→奈何ぞ guard (奈,) 現行元组確認済（byte 級）＋先例 (即,卽)・(爲,為) 確認 ✓

## §6 禁止事项自查

- C2（無/罔字拡張）・C8（tail→全文機構）＝**未測・未実装**（N106 否決遵守）；項 5 は系・項 3/6/7/8/9・(c) 后继字機構＝一字未動；night106-mech-design 分支＝未碰（git show 読みのみ）。
- 词库（glossary_lexicon*）・golden expected・既存規則の repl/链序/長词表＝一字未改（sim S2 链完整性＋eval 全行逐位一致で実証）。
- 允许清单内文件のみ変更：`backend/kundoku_rules.py`（guard タプル 2 处）・`tools/night107_{sim,eval_4000,eval_8165}.py`（新 3）・`tools/accept_night.py`（NIGHT_ARTIFACTS 107 一条）・`tools/verify_readme_facts.py`（guard 断言＋归档源）・`tests/test_night107_item4_impl.py`（新 1）・`eval/night107_*`（新 5＝sim.{json,txt}・changed_rows・results_{4000,8165}）・`eval/accept_night_107.json`・`SHIFT_LOG.md`（心跳）・`ACCEPT_LOG.md`（accept 自動）・`REPORT_NIGHT107.md`・`ROADMAP.md`（末尾 1 行）・`README.md`（数字行＋Rule L/M guard 説明＋header）。
- 禁 OCR・禁 guwenbert・禁 eval 以外的网络（web_search 0・ページ取得 0・柰/爲 查证は N106 语料内対照の引用のみ）✓
- 本地提交（主提交＋wrap-up）、**未合 master・未推远程** ✓

## §7 记录偏差与坑位

1. **README header「hash→分支 tip」の解決**：数字と header の同一提交内変更（任务书）と「header hash→分支 tip」は自己参照不可能（header を含むコミット自身を指せない）——**N104 坑位③ 同型の解決**＝header は「night107-item4-impl・自 master f5e0bf3 分出」表記（分支起点 hash・N104 実績どおり）とし、verify は header を校验しない（N99 先例）。記録偏差として本節に明記。
2. **SHIFT_LOG は完全な UTF-8 でない**（byte[807]＝0xf3＝GBK 形态历史区域・N106 坑位③ 再確認）——心跳は UTF-8 バイナリ追加（\r\n・canary 243 写前后断言継続）で問題無いが、**ファイル全体を一括 decode する修正スクリプトは UnicodeDecodeError で落ちる**＝夜内修正は純バイト操作（bytes replace）で実施（本夜 2 度命中）。
3. **自動生成文の字形混淆**：爲（U+7232 旧字）が自動生成文では 為（U+70BA）に流れる事象が heartbeat 文で 2 回発生——SHIFT_LOG 未提交行を byte 級修正スクリプトで正規化（U+7232 6箇所）。**製品コード・README・verify・sim/eval ツールは最初から \u7232 エスケープまたは哨兵置換（爲→U+7232）で生成したため無影響**（import proof と verify needle で実証）。教訓＝爲 を含む全生成物は \u エスケープか哨兵置換で書く・bytes リテラルは \u エスケープを解釈しない（b"\u7232" は 6 文字の生バイト＝本夜 2 度命中・N95 坑位①の再確認）。
4. **guard tuple 変更の diff 検証**：+12 B・恰 2 行差分を patcher が逐行 diff で断言（full-line 単位）＝N96 坑位①（substring 一致で行頭欠落インシデント）の対処として行単位差分断言を採用。CRLF は保存（\r\n 数不変断言）。
5. **accept 試跑＝repo_clean 1 項 FAIL の設計行為**（N96/N94/N104 先例）——新文件 untracked 状態での試跑で repo_clean のみ FAIL＝主提交後に終跑 PASS・FAIL/PASS 两行とも ACCEPT_LOG 残す（N100 先例）。

## §8 次夜建议

- **合并夜**（night107-item4-impl 2 提交の master 合入・N100/N105 型）か、**残拍板項の在庫棚卸し**（項 7 嗟や・項 8/6 毋系在庫 Δ−0.000367/−0.000490・項 9 剥夹注管线・N84 残渣 2 行）か **(c) 改設計 probe**（got 側文末・係り結び系 2 次判別の可否＝报告-only）。
- 項 5 は系は N106 §3 のとおり「放弃」記載への拍板表更新待ち（機構側も不可分確定済み）。
- 等用户手推 origin/master（現状 rev-list 超前＝N101 链以後の未推提交＋本夜 2 提交）。
