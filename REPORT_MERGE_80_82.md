# REPORT_MERGE_80_82.md — Night 83 合并班：词库链 N80+N82 入 master（单会话）

- 日期：2026-11-23。主仓 `D:\kanbun-kakikudashi`（开工 HEAD=30a15d4，Night 81 wrap-up，origin/master 同步）＋ clone `D:\kanbun-rulel`（词库链工作仓）。
- 合并对象：分支 `night82-lexicon-expand3`（fetch 时 tip=9e256b0；step 0 修正后 tip=aad4a42）。自 `night80-lexicon-expand2`（6fba6a7）分出，含 N80 全部提交＋N82 两提交；**单次合并**（N82 已含 N80，未分两次）。
- 性质：合并夜。词库/规则/后端零手改——改动只来自分支带入＋四处冲突解决＋登记行。

## 1. 结论摘要

- 合并完成：master 30a15d4 →（31eda63 开工心跳）→ **bf18daf**（merge aad4a42）→ **c614075**（登记）→ 本 wrap-up。词库 824 → 1301（extra2 324 → 801＝N79 324＋N80 261＋N82 216；本体 500 不动）。
- 门禁全绿：pytest **415 passed**（393＋N80 11＋N82 11）；golden_4000 真跑 **13.495 / exact 24 / error 0** 与 night81 归档逐位一致（diff 0 行）；golden_8165 真跑 **14.526 / exact 30 / error 0** 与 night81 归档逐位一致（diff 0 行）；唯一词形 **209＋291＋801＝1301** 实测复核；verify_readme_facts **18/18 exit 0**；accept 83 **PASS（fail=0 skip=0，30.7s，登记后首跑即 PASS）**。
- 本地提交，未推远程（origin/master 仍 30a15d4，等用户手推）。

## 2. 开工核验

- 主仓 git log -1=30a15d4 ✓；pytest 393 passed（12.81s）✓；已跟踪文件零改动 ✓（untracked 为历史遗留杂物，未动）。
- clone：night82-lexicon-expand3 tip=9e256b0 ✓；merge-base(master, night82)=ad18f20——**与任务书预期 8d84613 不合，查明为良性后放行**：clone 的 master 停在 Night 70 wrap-up（ad18f20；词库各夜都在侧分支工作，clone master 从未前进），它是 8d84613 的祖先（merge-base --is-ancestor exit 0）；8d84613（N79 tip）⊂ 9e256b0 实测为真。主仓侧 fetch 后 merge-base(master, FETCH_HEAD)=**8d84613** ✓ 与任务书一致——实际合并基点正确。
- 段内提交数实测：N80 段（8d84613..6fba6a7）**13** 条（11 条 batch 进度心跳＋主提交 2752317＋wrap-up 6fba6a7）；N82 段 2 条（fb11eee＋9e256b0）。任务书「N80 全部 8 提交」为估计值，如实记录；整支合并不受影响。

## 3. step 0：N82 报告两处数字修正（clone 内，提交 aad4a42）

- (a) REPORT_NIGHT82.md §3「本体 500＋extra 291＋extra2 801」→「本体 209＋extra 291＋extra2 801」（总数 1301 不动）。口径实证（import 实测）：本体 GLOSSARY_LEXICON 500 词形全唯一；extra.py 291 词形**全部**是本体词形的子集（本体独有＝209）；extra2 801 与前两者零交集 → 唯一词形 209＋291＋801＝1301。
- (b) 双读法条数：报告称 12 条、§1.4 列出 14 条；以 backend/glossary_lexicon_extra2.py 文件实值为准——N82 追加 216 条中 reading 字段「A・B」両読み併記＝**32 条**（『・』『／』之外无其他分隔符）。修正：§1.4 首条改为「双读法 32 条（extra2 文件实值；下列 14 例为代表，非全数）」；次条注明主読み分歧 4 条（秋雨/門前/風雲/織女）含在 32 条内；§4 测试清单描述「双读法 12 条」→「双读法代表 8 条」（test_night82_lexicon_expand3.py 代表读法 51 例中含双读法 8 例；**该测试文件没有双读法计数断言**，故测试零改动）。条目本身一字未动。
- 修正提交 aad4a42（clone；修正后 clone pytest 复跑 385 passed）。

## 4. 合并与冲突解法（主仓）

- 开工心跳先追加 SHIFT_LOG（byte807=243 前后断言），合并拒脏树 → §5.3 显式心跳提交 31eda63。
- `git fetch D:\kanbun-rulel night82-lexicon-expand3` → FETCH_HEAD=aad4a42；merge-base=8d84613 ✓；`git merge FETCH_HEAD --no-edit`。incoming 16 提交。
- 冲突 4 文件（tools/accept_night.py 自动合并成功，无冲突标记）：
  - **SHIFT_LOG.md**：字节安全并集——ours 工作字节（ours blob CRLF 化）＋ theirs blob 相对 8d84613 的前缀差 5147 字节（theirs.startswith(base) 断言通过）；byte807=243 复验 ✓。尾部正确接上 N82 三行。
  - **ACCEPT_LOG.md**：同法（suffix 166 字节）；尾行 81/80/82 三条 PASS 齐全。
  - **README.md**：唯一冲突块＝テスト行（master 393／分支 385）→ 写 **415 passed**（合并后实测数，不是二选一）；語釈「文語 1301 語」行由自动合并带入。
  - **ROADMAP.md**：按夜序并集——以 theirs（base＋N80 行＋N82 行，纯 LF）为主干，插回 master 独有的 Night 71／Night 78 两条 CLOSED 行（Night 70 行后／Night 77 行后）；**顺带清除了 master blob 里 N81 合并夜遗留的冲突尾标记「>>>>>>> night79-lexicon-expand」**（本次并集天然清除）。
- tools/verify_readme_facts.py 合并零改动：其テスト行断言为 pytest --collect-only 动态计数，无词库条数静态断言——无需同步。

## 5. 合并后门禁（关键口径：与 night81 归档比，不是 N82 的 13.517）

- pytest tests -q：**415 passed**（13.23s）。
- golden_4000 真跑（tools/night83_eval_4000.py，86s）：engine OK 4000／error 0／exact **24**／avgDist **13.495**，与 night81_results_4000.json 输出不一致 **0 行**。规则引擎代码来自 master（Rule N 链尾），词库不进引擎——合并后口径就是 Rule N 口径 ✓。
- golden_8165 真跑（tools/night83_eval_8165.py）：**14.526**／exact 30／error 0，与 night81_results_8165.json 不一致 **0 行**。
- 词库总数：500＋801＝**1301** ✓（pytest test_extra2_size_and_total＋import 实测双确认；唯一词形 209＋291＋801＝1301）。
- tools/verify_readme_facts.py：**18/18 对上、exit 0**（テスト行断言动态计入 415）。

## 6. 登记（⑤）与提交链

- tools/night83_eval_4000.py／tools/night83_eval_8165.py＝night82/night81 同款脚本程序化改造：基线换 night81 归档、EXPECT/标签同步；逐个替换带出现次数断言，陈旧引用 grep 自检 clean。
- 归档：eval/night83_results_4000.json（默认口径登记）＋eval/night83_results_8165.json（扩充归档，不登记默认口径）。
- NIGHT_ARTIFACTS[83] = ["night83_results_4000.json"]（81 行后插入；ast.parse 通过）。
- README 数字节表头 →「Night 83 合并：词库链 N80+N82（含 step 0 报告修正 aad4a42）・主提交 `bf18daf`」；テスト行 415／Rule N 13.495/24/4000／词库 1301 語 均已在位。
- accept_night.py 83：**PASS（fail=0 skip=0，30.7s）** 7 门全绿（repo_clean／pytest 415=415／eval_integrity／rule_regression／engine_smoke／perf_envelope／order_rate）。
- 提交链：31eda63（心跳）→ bf18daf（合并）→ c614075（登记）→ 本 wrap-up。未推远程。

## 7. 事实漂移与遗留（如实，未动，留拍板）

- N81 遗留冲突尾标记（master ROADMAP）本班并集时清除（§4）；N81 无自己的 ROADMAP DONE 行（合并夜惯例），本班沿用不加。
- N79 待拍板 3＋8 条、N80 Wikipedia-only 保守排除 4 条（令尹・元王・宰我・大象）、N82 Wikipedia-only 20 条（翻案可注明）——全部一字未动等用户。
- clone（D:\kanbun-rulel）master 仍停在 N70 ad18f20——本班未动；是否 fast-forward 留用户拍板。
- README「ブランチ統合状況（Night 65 時点）」段与規則エンジン行尾「N78 の eval/night78_results_4000.json 口径」为旧表述（N81 起未改、verify 不查、任务书未要求）——保持原样。

## 8. 禁止事项自查

- 规则引擎/backend/词库内容/golden expected 一字未改；词库 extra2、tests、eval 归档只随分支合入，本班零编辑（REPORT_NIGHT82.md 修正按任务书授权在 clone 内进行）。
- 未碰 OCR／guwenbert；未进 D:\kanbun-eval10k / D:\kanbun-rulei。
- git add 全程精确文件清单（未用 add -A），.night72_deps/ 等缓存目录保持 untracked。
- 未推远程、未合其他分支。

## 9. 证据

- eval/night83_results_4000.json（13.495/24/0，diff_vs_n81=0）＋eval/night83_results_8165.json（14.526/30/0，diff_vs_n81=0）
- eval/accept_night_83.json（verdict PASS fail=0 skip=0）＋ACCEPT_LOG.md 83 行
- SHIFT_LOG.md 心跳 2 行（开工/收尾，byte807=243 每次写入前后断言）
