# REPORT_MERGE_113 — Night 114 合并夜（night113-inventory → master・ZCode 单会话）

## 0. 结论（先说）

**一次 --no-ff 合并完成・冲突恰 1 处（SHIFT_LOG.md）字节安全并集・夜序 113<114・canary 双形态实测确认・双口径真跑与 night111 归档全行逐位一致（diff 0 行）・verify 26/26・词库 1531 不动・accept 114 PASS fail=0 skip=0（试跑 FAIL=repo_clean 1 项＝设计行为）**。合并＝产品代码零改动実証（N113 は報告-only 夜・master 出力＝night111 归档逐位同一）。本夜 4 提交（心跳 a73989e／merge 59ca4cd／登记／wrap-up）＋合并带入 N113 两提交（306898f＋fa71e23）＝rev-list 超前 origin 6，未推远程（等用户手推）。

## §1 开工核验

master **ed5b2db**（N112 wrap-up）✓・origin/master＝ed5b2db（rev-list 超前 **0**＝N112 記録「等用户手推」の完了状態実測＝用户已推）✓・pytest 两侧 **503 passed**（master 22.01s／分支 20.25s・ともに exit 0）✓・已跟踪文件零改动 ✓・git 身份 wang／wang@localhost ✓。

分支核验：night113-inventory tip＝**fa71e23**（wrap-up 提交）、其父＝**306898f**（主提交）、merge-base＝**ed5b2db** ✓。分支 diffstat＝12 文件 +4406/-0（REPORT_NIGHT113・ACCEPT_LOG +2・ROADMAP +1・SHIFT_LOG +2・eval/night113_* 5 件＋accept_night_113.json・tools/night113_sim/status.py）＝任务书記載の報告-only 触碰範囲と逐項一致。

master 版 grep 核查防回滚：verify 归档源＝night111（`eval/night111_results_4000.json`）✓・README 含 13.455/13.464/503 ✓・accept_night.py 含 111/112 条目 ✓。REPORT_NIGHT113.md §0/§3/§5 読済（git show・分支侧）。

## §2 合并（一次 --no-ff）

- 心跳提交 **a73989e**（master 上先落一行・17:55・blob 161738＝161453+285＝N100 坑位①「合并前心跳提交」）。
- `git merge --no-ff night113-inventory` → **冲突恰 1 处：SHIFT_LOG.md（UU）**。ACCEPT_LOG.md・ROADMAP.md 自动并入（M staged）＝任务书予想どおり；REPORT_NIGHT113.md＋eval/night113_sim/changed_rows/status（json・txt）＋accept_night_113.json＋tools/night113_sim.py／night113_status.py＝**10 文件干净带入**（A staged）。
- **SHIFT_LOG 字节安全并集**（tools/night114_merge_log.py＝night112_merge_log 方法论克隆・assert-only・**纯字节操作・禁整文件 decode**）：
  - **字节账**：base（merge-base ed5b2db 版 blob）＝ **161453 B**・ours（含 N114 开工心跳 a73989e）＝ 161738 B（**+285**＝N114 心跳 1 行）・theirs（N113 tip fa71e23 版）＝ 161838 B（**+385**＝N113 心跳 2 行 16:19 开工＋16:47 收工）・**接缝 0**（两侧追加段都以 \n 终止・无补缝）・merged ＝ **162123 B**（＝161453+385+285+0）。
  - **夜序 113<114**：并集顺序＝base＋theirs 追加（N113 群 offset **161453–161623**）＋ours 追加（N114 行 offset **161838**）——机械并集（ours+theirs）会把 N114 行放在 N113 群之前＝夜序逆序（N112 坑位②同款）、本夜は夜号升序で直接構造＋並集内位置断言（`max(pos113) < min(pos114)`）で保証。心跳行锚定＝「YYYY-MM-DD HH:MM N11n」模式（ours＝{N114}・theirs＝{N113} 実測。裸 b"N113"/b"N114" 哨兵は REPORT_NIGHT113 等文件名に誤匹配＝N112 坑位①）。
  - **canary（0 基索引・两形态都要实测再写数）**：LF blob **[800]=243**（0xf3 混编码字节在 blob offset 800）／**[807]=63** ✓——并集前后同値（ours/theirs/merged すべて 243/63）＝base 段不動。**CRLF 虚拟形态 [807]=243** ✓（autocrlf=true 检出では 0xf3 が \r 挿入で offset 807 に偏移＝仮想形態）。SHIFT_LOG 非纯 UTF-8（0xf3×1）＝全程纯字节操作 ✓。**本夜は canary 断言を工具内 assert 化**（N112 は手測）。
  - **哨兵守恒**：N111=8・N112=4（base 由来）・N113=2（theirs）・N114=1（ours）＝merged 内全数保存（base＋両側追加の和で assert）。
- merge 提交 **59ca4cd**（父 a73989e＋fa71e23）・merged SHIFT_LOG blob **162123 B** 実測・rev-list 超前 4（＝本夜 2 提交＋N113 2 提交）。

## §3 验证（最终校验只对 night111 归档）

| 项 | 実測 | 期待 |
|---|---|---|
| pytest tests -q（合并後） | **503 passed**（15.60s）exit 0 | 503・0 新增 |
| golden_4000 全量（TestClient・tools/night114_eval_4000.py） | **13.455／24／0**・vs night111 归档 **diff 0 行**・vs night107 归档 diff 恰 **12 行**（＝N111 発火 4000 内 12 行）・138s exit 0 | 逐位一致 |
| golden_8165 全量（TestClient・tools/night114_eval_8165.py） | **13.464／30／0**・vs night111 归档 **diff 0 行**・vs night107 归档 diff 恰 **15 行**（＝N111 発火 15 行）・約 280s exit 0 | 逐位一致 |
| 词库 | **1531 不动**（core 500＝_OLD_SIZE 209＋extra 291・extra2 1031・_ordered_entries **1531** 実測＝N113 sim H1 gate 同式） | 不动 |
| verify_readme_facts.py | **26/26 exit 0**（归档源 night111・N111 断言在位） | 26/26 |
| exact | 24/30 不変 | 一致 |

长跑判定＝exit code（stderr は httpx INFO 洪水＝TestClient 既知・[OK] 行 grep 确认・N110 坑位）。两工具 assert-only＝归档に何も書かない（night111 归档不触碰）。合并＝产品代码零改动実証（N113 は backend/tests/golden/词库に一切触れず＝diffstat +4406/-0・全行逐位一致が実証）。

## §4 登记＋提交

- NIGHT_ARTIFACTS 加 `114: ["night111_results_4000.json"]`（归档源维持 night111・**113 不登记**＝報告-only N98/N102/N103/N106/N109 先例）。
- README header：Night 111 合并链 77eae67 → **Night 114 合并链 59ca4cd**（分支起点 ed5b2db・数字行 13.455/13.464/503 不変＝合并零改动）。**ROADMAP 無改**（合并夜先例 N110/N112＝ROADMAP に合并夜行を追加しない・実施夜のみ追加）。
- 登记提交：REPORT_MERGE_113.md（本文件）＋tools/night114_merge_log.py＋tools/night114_eval_4000.py／night114_eval_8165.py（assert-only 克隆）＋tools/accept_night.py（NIGHT_ARTIFACTS 114 条目のみ）＋README.md（header のみ）＋ACCEPT_LOG.md（試跑 FAIL 行）。
- wrap-up 提交：REPORT_NIGHT114.md＋ACCEPT_LOG.md（终跑 PASS 行）＋eval/accept_night_114.json（final）＋SHIFT_LOG.md（进度心跳）。
- 本夜 4 提交（心跳 a73989e／merge 59ca4cd／登记／wrap-up）＋合并带入 N113 两提交（306898f＋fa71e23）＝**rev-list 超前 origin 6**（N110 坑位：rev-list 计数含分支带入提交）。不合他处・不推远程。

## §5 口径交代（本夜必述）

1. **N113 记录偏差 1 項（非漂移）**：N98 §3 項 9／N109 §2(e) 的例示字形「**爲→为**」与実測／SHINJITAI_MAP「**爲→為**」（U+7232→U+70BA）之差＝**報告文の例示字形 slip のみ**・対象行集・行数（16 行）は一致＝数値漂移ゼロ（N113 status 実測＋N109 归档 night109_status.txt 同値）。REPORT_NIGHT98.md／REPORT_NIGHT109.md 自体は歴史記録として不変・本合并夜も一切不触（禁碰区遵守）。
2. **拍板表は REPORT_NIGHT113.md §3 で更新済み**（supersede N98 §3・N109 §3）：項 1a/1b/1c/2＝已実施（N99）・項 3＝已実施（N104）・項 4＝已実施（N107）・項 5＝放弃（N106）・項 6＝**已実施（N111 follow_map 機構**・N103「不統一」は字形統一三方向のみが範囲＝N112 附注记の正文反映）＋毋系在庫分離＋判错 3 行分離・項 7/9＝在庫（N113 再測数付き）・項 8＝死（N102）＋per-guard 在庫・(c) follow_map＝已実施（N111）。**本合并夜は拍板表に一切触れない**（表内実施項ゼロ・表の更新自体も N113 済み＝本夜は参照のみ）。
3. **N113 新坑位 3 項は本报告 §6 に恒久化収録**：変体 census は delta 口径／`sorted(set)==set` 恒 False（集合比較は型統一）／归档 JSON の保存順は非 sorted（旧数対照は sorted 同士）。

## §6 坑位追加（合并夜视角＋N113 新坑位の恒久化）

1. **（N113 §5 より恒久化）変体 census は delta 口径**：こと莫し のような「新規則が産出するはずの字形」は既有規則の組合せ産出（こと＋Rule O 莫し）で夜を跨ぐ既存分があり得る——絶対数 gate は N111 §3 A6「こと莫し 2」と冲突して FAIL（N113 開発中 1 回）。夜を跨ぐ字形 census は「産出元規則の組合せ可能性」を先に列挙して **delta** で取る（N109 莫かれ pre-U/post-U 口径坑の同型）。
2. **（N113 §5 より恒久化）`sorted(set) == set` は恒 False**（list vs set・N113 開発中 1 回）——集合比較は set 同士か sorted 同士に統一。
3. **（N113 §5 より恒久化）归档 JSON の保存順は非 sorted**（night111 summary.sim_expect.rewrite5 は時系列順・N113 DRIFT 偽陽性 1 回）——旧数対照のリスト系 cmp_val は sorted 同士で。
4. **canary 双值＝工具内 assert 化**：LF blob [800]=243（0xf3）／[807]=63・CRLF 虚拟形态 [807]=243——0xf3 は blob offset 800・CRLF 检出では \r 挿入で 807 に偏移＝**两形态の [807] は別の物理字节**（N112 坑位③の継承・本夜 night114_merge_log.py に assert 組み込み＝手測を廃止）。
5. **工作树サイズと blob サイズは別物（autocrlf=true）**：SHIFT_LOG.md 工作树＝162520 B（CRLF・1067 行×\r 追加）vs blob＝161453 B（LF）＝**git status 干净でも `wc -c` は blob と合わない**。字节账・canary・夜序の実測は全部 **blob 級（git cat-file ／ git show :n:PATH）**で行う＝本夜で標準化（N113 が blob 161838 実測していたのと同型）。
6. 其余承 N112：merge 前心跳提交・裸夜号哨兵誤匹配（本夜は「日期 HH:MM N11n」锚定で回避）・机械并集夜序逆序（本夜は夜号升序直接構造＋位置断言）・rev-list 含带入提交・長跑 exit code 判定・stderr 洪水は [OK] 行 grep 确认。
