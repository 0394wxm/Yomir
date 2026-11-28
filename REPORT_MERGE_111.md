# REPORT_MERGE_111 — Night 112 合并夜（night111-followmap-impl → master・ZCode 单会话）

## 0. 结论（先说）

**一次 --no-ff 合并完成・冲突恰 1 处（SHIFT_LOG.md）字节安全并集・夜序 111<112・canary 双值实测确认・双口径真跑与 night111 归档全行逐位一致（diff 0 行）・verify 26/26・词库 1531 不动・accept 112 PASS fail=0 skip=0**。合并＝产品代码零改动実証（master 出力＝N111 分支出力逐位同一）。本夜 4 提交（心跳 5bc8718／merge 77eae67／登记／wrap-up）＋合并带入 N111 两提交＝rev-list 超前 origin 6，未推远程（等用户手推）。

## §1 开工核验

master 5633eca（N110 wrap-up）✓・pytest **491 passed**（master 侧）✓・已跟踪零改动 ✓・origin/master=5633eca ✓。分支核验：night111-followmap-impl tip＝**e1e0344**（wrap-up・rev-parse 返回 tip 非主提交＝任务书注记通り）、其父＝**ba25beb**（主提交）✓、merge-base＝**5633eca** ✓。分支版 grep 核查防回滚：verify 归档源＝night111 ✓・README 含 13.455/13.464/503 ✓・accept_night.py 含 111 条目 ✓。

## §2 合并（一次 --no-ff）

- 心跳提交 **5bc8718**（master 上先落一行・N100 坑位①：合并夜开工心跳提交必须在 merge 前）。
- `git merge --no-ff night111-followmap-impl` → **冲突恰 1 处：SHIFT_LOG.md**（ACCEPT_LOG/README/ROADMAP/REPORT_NIGHT111 等全部自动并入＝N111 侧 master 未动这些文件）。
- **SHIFT_LOG 字节安全并集**（tools/night112_merge_log.py・纯字节操作・禁 decode）：
  - 字节账：base（merge-base 5633eca 版）= 158859 B・ours（含 N112 开工心跳）= 159336 B（**+477**）・theirs（N111 tip 版）= 160302 B（**+1443**）・**接缝 0**（两侧追加段都以 \n 终止・无补缝）・merged = **160779 B**。
  - 夜序 **111<112**：并集顺序＝base＋theirs 追加（N111 心跳群 12:03–12:55・offset 158859–159961）＋ours 追加（N112 行 13:37・offset 160302）——首版并集（ours+theirs 追加）实测出 N112 行在 N111 群之前＝夜序逆序、按夜号升序重排修正。心跳行锚定＝「2026-11-28 HH:MM N11n」模式（**裸 b"N111"/b"N112" 哨兵会误匹配 REPORT_NIGHT111 等文件名＝本夜实测坑位**・本会话心跳里 REPORT_NIGHT111 §0/§5 文字含大写 N111）。
  - **canary（0 基索引・先实测再写数）**：merged LF blob **[807]=63** ✓・CRLF 形态 **[807]=243** ✓（0xf3 混编码字节在 blob offset 800・CRLF 形态因 \r 偏移到 807・重排后重测同样 63/243＝base 段不动）。SHIFT_LOG 非纯 UTF-8（0xf3×1）＝全程纯字节操作 ✓。
  - 哨兵完整性：N111 群 6 行＋N112 1 行全保留。
- merge 提交 **77eae67**。

## §3 验证（最终校验只对 night111 归档）

| 项 | 実測 | 期待 |
|---|---|---|
| pytest tests -q | **503 passed**（491＋N111 12 条） | 503 |
| golden_4000 全量（TestClient） | **13.455／24／0**・vs night111 归档 **diff 0 行**・vs night107 归档 diff 恰 N111 発火 12 行 | 逐位一致 |
| golden_8165 全量（TestClient） | **13.464／30／0**・vs night111 归档 **diff 0 行**・vs night107 归档 diff 恰 N111 発火 15 行 | 逐位一致 |
| 词库 | **1531**（500+291+1031） | 不动 |
| verify_readme_facts.py | **26/26 exit 0**（归档源 night111・N111 断言在位） | 26/26 |
| exact | 24/30 不変 | 一致 |

合并＝产品代码零改动実証（tools/night112_eval_4000/8165.py・assert-only・不写归档）。

## §5 口径交代（本夜必述・REPORT_NIGHT111 §5 记录偏差的合并夜确认）

**N111 任务书的 golden 预期（4000 约 13.458–13.459／8165 13.465・−6/−7 字）写的是 sim 的機構純効果口径（(a) 単一 repl→follow）**；而 golden 実測 Δ 是 **raw→follow 総効果**（default_repl こと莫き 収録自体の効果 −12/−14 字＋機構純効果 −7/−6 字＝−19/−20 字），実測 4000 **13.455**／8165 **13.464** 与 N106 follow 記録（−0.0023/−0.0050）逐位一致。N111 报告数字自洽・记录偏差是任务书口径错（非报告数错）。**合并夜的最终校验只对 night111 归档（13.455/13.464），不拿任务书的旧预期数当 gate。** 同型教训进坑位：**実施夜任务书的 golden 预期 Δ 必须写清比较基线（night107 归档＝raw 口径）**。

## §4 登记＋提交

- NIGHT_ARTIFACTS 加 `112: ["night111_results_4000.json"]`（归档源维持 night111・111 不补登记＝分支侧已登记・N108/N110 先例）。
- README header：night111 分支版 → 合并后口径（Night 111 合并链 77eae67・分支起点 5633eca・数字行 13.455/13.464/503 不変＝合并零改动）。
- REPORT_MERGE_111.md（本文件）＋tools/night112_eval_4000/8165.py（登记提交）；REPORT_NIGHT112.md＋ACCEPT_LOG＋accept_night_112.json＋SHIFT_LOG（wrap-up 提交）。
- 本夜 4 提交（心跳 5bc8718／merge 77eae67／登记／wrap-up）＋合并带入 N111 两提交（ba25beb＋e1e0344）＝**rev-list 超前 origin 6**（N110 坑位：rev-list 计数含分支带入提交）。不合他处・不推远程。

## §6 坑位追加

1. **裸夜号哨兵误匹配文件名**：心跳行内容含 REPORT_NIGHT111 等文件名时 b"N111" in 判定误报——夜序检查须锚定「日期 HH:MM N11n」行首模式。
2. **首版并集夜序逆序**：ours(base+追加)+theirs 追加 的机械并集会把 ours 追加段（N112）放在 theirs 追加段（N111）前＝夜序逆——并集须按夜号升序重排追加段（N110 同款・本次实测再现）。
3. canary 双值（blob[807]=63／CRLF[807]=243）= 0xf3 在 blob offset 800、CRLF 形态偏移到 807——LF/CRLF 两形态的 [807] 指不同物理字节，两值都要实测。
4. 其余承 N110/N108：merge 前心跳提交・rev-list 含带入提交・长跑以 exit code 判定・stderr 洪水丢弃重跑确认（本夜 golden 全量均 exit 0・无 stderr 洪水）。
