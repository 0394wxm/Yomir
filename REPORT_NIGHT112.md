# REPORT_NIGHT112 — 合并夜（N111 → master・ZCode 单会话）

任务书：用户 Night 112——把 night111-followmap-impl（follow_map 機構实施夜・2 提交 ba25beb＋e1e0344）一次 --no-ff 合入 master。合并本体・字节账・冲突清单・口径交代的详录＝**REPORT_MERGE_111.md**（本报告为当夜总结与移交）。

## 0. 结论（先说）

**合并完成・全验收 PASS**：merge 提交 **77eae67**、冲突恰 1 处（SHIFT_LOG.md）字节安全并集（夜序 111<112・canary blob[807]=63/CRLF[807]=243 实测・接缝 0）、pytest **503 passed**、golden_4000 **13.455/24/0**・golden_8165 **13.464/30/0** 与 night111 归档**全行逐位一致（diff 0 行）＝合并零改动実証**、verify **26/26**、词库 **1531** 不动、accept **112 PASS fail=0 skip=0**（46.5s first-run 七门全绿・无 trial FAIL＝先登记提交后跑门の舞步通り）。master = 5633eca ＋ N111（ba25beb 機構収録＋e1e0344 wrap-up）。本夜 4 提交（心跳 5bc8718／merge 77eae67／登记 84eb7d0／wrap-up）＋合并带入 N111 两提交＝**rev-list 超前 origin 6**（4 own＋2 带入・N110 坑位記法）。**未推远程（等用户手推）**。

## §1 开工核验

master 5633eca ✓・pytest 491 passed（master 侧）✓・已跟踪零改动 ✓・分支 tip e1e0344（父 ba25beb）✓・merge-base 5633eca ✓・分支版 grep 核查（verify 归档源 night111／README 13.455+13.464+503／accept 111 条目）✓・REPORT_NIGHT111 §0/§5 読済（无 step 0：N111 报告数字自洽）。

## §2 合并

- 心跳提交 **5bc8718**（merge 前落位・N100 坑位①）。
- `git merge --no-ff night111-followmap-impl`：**冲突恰 1 处（SHIFT_LOG.md）**、其余（ACCEPT_LOG/README/ROADMAP/REPORT_NIGHT111/backend/tests/tools）全部自动并入。
- SHIFT_LOG 字节安全并集（tools/night112_merge_log.py・纯字节・禁 decode）：base 158859＋ours 追加 477（N112 心跳）＋theirs 追加 1443（N111 群 6 行）＝merged 160779・**接缝 0**・夜序 **111<112**（首版机械并集实测出夜序逆序→按夜号升序重排修正）・canary **blob[807]=63／CRLF[807]=243**（重排后重测同值＝base 段不动）・哨兵完整性 N111×6＋N112×1。
- merge 提交 **77eae67**。

## §3 验证（最终校验只对 night111 归档）

- pytest **503 passed**（491＋N111 12 条新测试）。
- golden_4000 全量（tools/night112_eval_4000.py・assert-only）：**13.455／24／0**、vs night111 归档 **diff 0 行**、vs night107 归档 diff 恰 N111 発火 12 行（4000 内）。
- golden_8165 全量（tools/night112_eval_8165.py・assert-only）：**13.464／30／0**、vs night111 归档 **diff 0 行**、vs night107 归档 diff 恰 N111 発火 15 行。
- 词库 **1531** 不动・verify **26/26 exit 0**・exact 24/30 不変。

## §5 口径交代（任务书必述事项・REPORT_MERGE_111 §5 同文）

N111 任务书的 golden 预期（4000 约 13.458–13.459／8165 13.465）＝sim 的機構純効果口径（(a) 単一 repl→follow・−7/−6 字）；golden 実測 Δ＝**raw→follow 総効果**（default_repl こと莫き 収録 −12/−14 字＋機構純効果 −7/−6 字＝−19/−20 字）、実測 4000 **13.455**／8165 **13.464**＝N106 follow 記録（−0.0023/−0.0050）逐位一致。**N111 报告数字自洽、记录偏差是任务书口径错（非报告数错）。合并夜的最终校验只对 night111 归档（13.455/13.464）、不拿任务书旧预期数当 gate。** 同型教训进坑位：**実施夜任务书的 golden 预期 Δ 必须写清比较基线（night107 归档＝raw 口径）**。

## §4 登记＋提交

- NIGHT_ARTIFACTS 加 `112: ["night111_results_4000.json"]`（归档源维持 night111・111 不补登记＝分支侧已登记・N108/N110 先例）・accept **112 PASS fail=0 skip=0**（46.5s・first-run PASS＝登记提交后跑门、无 trial FAIL）。
- README header：night111 分支版 → 合并后口径（Night 111 合并链 77eae67・分支起点 5633eca）・数字行 13.455/13.464/503 不変（合并零改动）。
- 提交链：心跳 **5bc8718** → merge **77eae67** → 登记 **84eb7d0**（NIGHT_ARTIFACTS＋README header＋REPORT_MERGE_111＋night112_eval_4000/8165＋night112_merge_log＋SHIFT_LOG）→ wrap-up（本报告＋ACCEPT_LOG＋accept_night_112.json＋SHIFT_LOG 收工心跳）。不合他处・不推远程。

## 附：项 6 拍板表待更新注记（本夜不改拍板表正文）

N109 §3 新版拍板表の「項 6 不統一（N103）＋毋系在庫」の記述は、**N103 の「不統一＝不実施」は字形統一の三方向（莫き/莫し/莫くんば など exp 字形混在）への判定**を指す。N111 はその三方向問題を **follow_map 機構（後继字判別）で実装解決した**（ことなき 規則そのものを莫系 guard 莫・10 字表で収録＝字形選択は機構の管轄・判错 3 行は文法構造差で (a) 値維持）。よって項 6 の記述は「機構で実装済み（N111）・毋系残量と判错 3 行の管轄注記に更新可」になるが、**拍板表正文の更新は下次在庫夜（N109 型）で行い、本夜は注記のみ**（合并夜＝拍板表を動かさない・N108/N110 先例）。次回在庫夜の入力候補＝この注记＋毋系在庫（N103 ことなき→こと毋き guard 毋 4 行＝本機構と同型の per-guard 拡張候補）＋判错 3 行（rongo1442-1/tonan-1/utsuryo03-7＝文法構造差・機構外）。

## §7 坑位（本夜新知・REPORT_MERGE_111 §6 同文）

1. 裸夜号哨兵（b"N111"）误匹配 REPORT_NIGHT111 等文件名＝夜序检查须锚定「日期 HH:MM N11n」行首模式（本夜实测・ours 心跳内容に REPORT_NIGHT111 §0/§5 文字があり断言誤発火）。
2. 首版机械并集（ours＋theirs 追加）は夜序逆（N112 行が N111 群の前）＝追加段は夜号升序で重排して接合（N110 同款の本夜再現）。
3. canary 双值＝0xf3 が blob offset 800・CRLF 形态で 807 にずれる（\r 偏移）＝LF/CRLF 两形态の [807] は别字节・两值都要实测。
4. N110 坑位継承：merge 前心跳提交・rev-list 計数含分支带入提交（本夜 4＋2＝6）・长跑 eval 以 exit code 判定・stderr 洪水丢弃重跑确认（本夜 golden 全量均 exit 0・无 stderr 洪水・实测 4000=136s／8165=约 300s）。
