# REPORT_NIGHT104 — 拍板夜：なかれ→莫かれ 复活，允变差 1 行（kokyo09-5）

AutoClaw・2026-11-26・单会话。主仓 D:\kanbun-kakikudashi，分支 `night104-ruleu`（自 master `67b0d73` 分出）；**不合 master、未推远程**。

## 0. 拍板原文・工具・归档

- 拍板原文（任务书）：用户 2026-11-26 拍板（N98 §3 决策表項 3・N99 同框）：なかれ→莫かれ 允变差 1 行（kokyo09-5），撤 0 变差硬门仅限本条。排除 guard 已在 N86 实测否定，不再试。
- 工具：`tools/night104_sim.py`（night99_sim 型・基线＝night101 归档）＋ `tools/night104_eval_4000.py` / `night104_eval_8165.py`（night99_eval 型真跑回归・sim 逐位对照）。
- 归档（全部已跟踪）：`eval/night104_sim.json`・`eval/night104_sim.txt`・`eval/night104_changed_rows.json`（改写 17 行预测＝eval 对照源）・`eval/night104_results_4000.json`（默认口径登记）・`eval/night104_results_8165.json`（扩充归档）。

## 1. 开工核验

- master＝origin/master＝`67b0d73`（N101 wrap-up）✓；分支 `night104-ruleu` ✓；`pytest tests -q`＝**476 passed**（25.29s）✓；已跟踪文件零改动 ✓（历夜 untracked 缓存不碰）。
- 移交阅读：REPORT_NIGHT98 §3 項 3（17 改写 13 改善 1 変差・kokyo09-5 死因）＋REPORT_NIGHT99 §2/§4（拍板夜 sim→実跑逐位对照・変差行 ID 锁）✓。

## 2. sim（tools/night104_sim.py・基线＝night101 归档・全部硬断言 PASS）

- 基线复核：行分类 engine 7916 / echo 30 / rerun 218 / no_tail 1（reachable 8134）✓・night101 vs night100 归档 got diff 0 行 ✓・基线 avgDist 4000=13.462 / 8165=13.469・exact 24/30 ✓・词库 209+291+1031=1531 ✓・lev 纯 Python 回退（.night72_deps 不存在）。
- S6（N102 教训の適用）：echo/no_tail 30+1 行の got に なかれ 无し（規則不可達＝製品側の空白文発火と sim skip の意味差は不発）・engine/rerun 全行 hb 非空 ✓。
- guard_forms(莫)＝["莫"]（莫 は新旧変異なし＝双形并查同形・SHINJITAI_MAP 非存在確認）✓。
- U1 なかれ→莫かれ（guard 莫）：**17 改写（4000 内 12）・13 改善（4000 内 8）・1 変差（kokyo09-5 15→16）・3 持平・Δ8165 −0.002・Δ4000 −0.002・幂等 bad 0**——N98 §3 項 3 実測 17/13/1 を night101 基线（Rule T 生效済み）で逐位复现（Rule T はなかれ行を改写しない前提を実測で検証）。
- 17 行の内訳＝post-N 残量の 〜ことなかれ 系 15 行（如き/興す/学ぶ/掃く/勝つ 等・N78 umbrella 拒の非 prefix 残量）＋裸 なかれ 2 行（kokyo12-2・kofuku-x13・両行持平）。変差行は **kokyo09-5 恰 1 行**＝拍板許容どおり（超出なし）。

## 3. Rule U 実装

- `backend/kundoku_rules.py`：`U_KANA_TO_KANJI` 1 条（なかれ→莫かれ guard 莫）＋ `U_LONGER_WORDS`＋`style_kana_to_kanji_u`＋链尾 `style_fix_with_hakubun` に T→U 追加。禁止族 guard 分割は I（毋かれ）→M（勿かれ）→U（莫かれ）で守り字三分割完了。
- **U_LONGER_WORDS「なかれ主義」マスク（計画外撞点の必要伴随）**：実装後 pytest で N64 `test_rule_i_probe_modern_japanese` の「ことなかれ主義」（事勿れ主義・白文「莫れ主義とは言わない」で guard 莫 が通る現代語複合語）が「こと莫かれ主義」に化ける撞点を検出→N73 もしの長詞 同款の安全弁として なかれ主義 をマスク（実語料 17 行に なかれ主義 非含有＝発火集合不変・sim CANDIDATES も同マスクに同期して再走＝全 gate 数字逐位不変）。`tests/test_night64_rule_i.py` は一字不動（許可文件外）。
- `tests/test_night104_rule_u.py` 8 条：正例 3（toushisen034-4/toushisen409-3/soko-3 行型）＋kokyo09-5 変差行ロック（got→new 15→16・N78 prefix keys との機構境界＝「すことなかれ」≠「することなかれ」を注記）＋sim ID 锁（17/13/1・worse_ids=[kokyo09-5]・pred_exact 24/30・changed4000=12）＋guard 反例（莫 無し＝一字不動）＋空白文発火（E〜K 世代同语义）＋I→M→U 守り字三分割（毋/勿/莫 の分消費）＋禁区不復活（T 键・ことなく・ことなき・嗟や・毋/勿かれ済み行・がため）＋構造ロック（1 条・マスク 1 件・repl 终字形・なかれ∉莫かれ）＋链序 T→U 併用＋べからず族との同一 chain・幂等＋無 kana 现代句・N84 echo 行型不動。
- `pytest tests -q`＝**484 passed**（476＋8・15.54s）。

## 4. 実跑双口径（TestClient 全量・sim 逐位一致）

- golden_4000：13.462→**13.460／exact 24／error 0**（改写 12 行＝sim 预测と new_text 逐位一致・計画外 0・欠落 0・変差 1 行 kokyo09-5 のみ）・Δ4000 −0.002＝sim 预测一致・NIGHT_ARTIFACTS 登记口径。
- golden_8165：13.469→**13.467／exact 30／error 0**（改写 17 行逐位一致・計画外 0・欠落 0・変差 1 行のみ）・Δ8165 −0.002＝任务书预期 ≈13.467 どおり・N98 §3 項 3 実測と一致。
- 変差行总数＝**1 行（kokyo09-5）**＝拍板上限どおり・新增変差 0・exact 24/30 不変（N98 預期どおり）。

## 5. kokyo09-5 変差行明细（拍板許容行・行動ロック済み）

- 白文「嚴父莫大於配天。」／got（night101）「父を厳して大なりて天を配すことなかれ。」／U 適用後「父を厳して大なりて天を配すこと莫かれ。」／exp「父を厳にするは天に配するより大なるは莫し。」
- d0=15→d1=16（+1）。got の「配**す**ことなかれ」は N78 prefix keys（「す**る**ことなかれ」等 5 键）に非匹配の「す＋ことなかれ」＝N78 umbrella「ことなかれ→こと莫かれ」拒の死行そのもの。U 収録で こと莫かれ になるが exp は「…大なるは莫し」（莫し＝終止形）＝字形差 1 字分の悪化。
- 死因＝白文「莫大」co-occurrence（嚴父莫大於配天）で guard 莫 が通ること＝N58/N68/N73/N78 定性の再現。N78 実測で判别式は否定済み＝排除 guard は不另加・死因は不修（拍板条件）。

## 6. verify・README・accept

- `tools/verify_readme_facts.py`：Rule U 語数断言追加（23→24 項）＋归档源切替。
- **归档源注记（任务书偏差の如实记录）**：任务书は「归档源 night101→night104」と記したが、実際の master 版 verify 归档源は `night99_results_4000.json`（N99/N102/N103 注记どおり・N102 坑位①の記録偏差）——本夜は**实际值 night99→night104** に切替（意图どおり）し報告に明記。
- 必要伴随 2 件：①avgDist needle を「**%s**」→「**%.3f**」に（归档 float 13.46＝尾零落ちと README 3 桁表記「13.460」の整合・同値）②テスト計数 484。verify＝**24/24 exit 0**。
- README：テスト行 484・規則エンジン 13.460／24/4000・拡張評価 13.467／30/8165（口径句＝N104 の `eval/night104_results_*.json`）・ルールチェーンに Rule U 句追加・header hash 行を night104-ruleu（Night 104 拍板夜・自 master 67b0d73 分出）に更新——**数字与 header 在同一提交内**（主提交）。注：自己参照不可能のため header が指す hash は分支起点 67b0d73（本夜実装の基线＝Night 101 wrap-up）；主/wrap-up の各 hash は ACCEPT_LOG と git log で確認可能。
- `tools/accept_night.py`：NIGHT_ARTIFACTS に `104: ["night104_results_4000.json"]` 追加。
- accept 104：**试跑（提交前）＝FAIL repo_clean 1 项のみ（設計行為＝未提交変更）・他 6 门 PASS**（35.6s）；**主提交後の终跑＝PASS fail=0 skip=0**（FAIL/PASS 两行とも ACCEPT_LOG に残す＝N100 先例）。

## 7. 禁止事项自查

- 词库 1531 一字未动（sim 词库 gate＋実装で词库文件未触）・golden expected 一字未改（eval は読むだけ）。
- 禁区 4–9 项（がため/何のごとく・は系・ことなき字形統一〔N103 判不实施〕・嗟や在庫・ことなく guard 外〔N102 判无益〕・N84 遗留）一字不碰。
- night102/night103 分支未碰・`tests/test_night64_rule_i.py` 等 許可文件外は一字不動・OCR/guwenbert 不使用・eval 以外の网络 0 命令（全ローカル実行）。
- SHIFT_LOG 心跳＝开工/sim PASS/収録＋実跑 3 行＋wrap-up final（UTF-8 二进制追加・CRLF）。

## 8. 坑位・移交

- 坑位①：kokyo09-5 の死因を語る時「することなかれ」（N78 済みキー）と「すことなかれ」（N78 非匹配・本夜 U が唯一触れる死行）の 1 字差を混同しない——报告文の「すことなかれ」は後者。
- 坑位②：guard 系規則の収録夜は pytest の現代語 probe（N64 ことなかれ主義 型）が初めての撞点になる——sim の corpus gate には見えないので、**収録夜の pytest は必ず走り、probe 撞点は長詞マスク（N73 もし 同款）で守る**（test 側は許可文件外＝製品側 U_LONGER_WORDS で対応）。
- 坑位③：verify の avgDist needle は归档 float の尾零落ち（13.46）で README 3 桁表記と表記不一致になり得る＝**归档源切换時は needle の表示桁数も確認**（%.3f）。
- 坑位④：README 数字と header を同一提交に置く場合、header が指せる hash は分支起点（自己参照不可）＝N99 型「数字行主提交・header wrap-up」パターンとの使い分けは任务书の指示次第。
- 移交（N98 §3 决策表 残・全部一字未動）：4/5＝機構設計夜（rikutou26-5 語順構造差行・守り字後続字 guard 拡張機構〔N103 未実装〕）・7＝嗟や在庫（Δ−0.000367）・9＝剥夹注管线・N84 残渣 2 行（rikutou59-2/soji07-6）・echo 30 行・項 6/8 在庫（N103 判不实施/N102 判无益・毋系 4 行 Δ−0.000490 のみ在庫）。
- 次夜建议：合并夜（night104-ruleu 未合・两提交）か機構設計夜 4/5；等用户手推 origin/master。
