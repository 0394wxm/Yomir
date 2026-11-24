# REPORT_MERGE_89 — 合并 night89-lexicon-freq2 进 master（Night 90，主仓合并夜）

## 1. 结论摘要

- 合并完成：master 35ba6e5 →（94966a6 开工心跳）→ **edd8ce8**（merge --no-ff night89-lexicon-freq2，即 d95afe3 主提交＋76c678b wrap-up）→ **8c977ca**（登记）→ 本 wrap-up。
- 冲突 1 文件：SHIFT_LOG.md（追加-追加）→ 字节安全并集（REPORT_MERGE_62_64 §5 / N83・N85・N87 惯例：CRLF 化 blob＋deltas 重建、byte807=243 前后断言、绝不文本三路合并）解消；ACCEPT_LOG／README／ROADMAP／backend/glossary_lexicon_extra2.py／tools/accept_night.py（NIGHT_ARTIFACTS[89]）全部 git 自动合并成功。
- 门禁全绿：pytest **443 passed**（434＋N89 9）；golden_4000 真跑 **13.491 / exact 24 / error 0** 与 night89 归档逐位一致（diff 0 行）；golden_8165 真跑 **13.502 / exact 30 / error 0** 与 night89 归档逐位一致（diff 0 行——词库不进规则引擎，两数与 N87 链尾值相同是预期）；词库 **500＋291＋1031＝1531**（唯一词形 209＋291＋1031、extra2 与本体零交集）import 实测复核；verify_readme_facts **19/19 exit 0**（N89 未加 verify 断言，19 项为准）；accept 90 **PASS（fail=0 skip=0，30.1s，登记后首跑即 PASS）**。

## 2. 开工核验

- `git checkout master`：HEAD = 35ba6e5 ✓；`git log -1 night89-lexicon-freq2` = 76c678b ✓；`git merge-base master night89-lexicon-freq2` = 35ba6e5 ✓（N89 自 master 直分，无 clone 中转、无需 fetch）；pytest 434 passed ✓；已跟踪文件零改动 ✓。
- 前置阅读：REPORT_NIGHT89 §0/§3/§6（入库 230／分组 proper 13・noun 192・verb 9・modifier 14・function 2／偏差注记 4 项）与 REPORT_MERGE_86 §3（字节安全并集方法论，N87 冲突仅 SHIFT_LOG）确认済み。N88 零规则分支 night88-rulep 本夜不合、其文件一律未动 ✓。

## 3. 合并与冲突解法（主仓）

- 开工心跳先行提交（94966a6，merge 拒绝脏树），随后 `git merge --no-ff night89-lexicon-freq2 -m "Merge night89-lexicon-freq2"`。
- 冲突：仅 **SHIFT_LOG.md**（UU，追加-追加：master 侧 N90 心跳 1 行 vs 分支侧 N89 心跳 5 行，共同基线 35ba6e5 之后双方都在尾部追加）。
- 解法（字节安全并集，python 二进制，绝不文本三路合并）：
  - base = `git show 35ba6e5:SHIFT_LOG.md`（130,770 B）、ours = `94966a6`、theirs = `76c678b`，三 blob 均纯 LF、断言 `ours.startswith(base)`／`theirs.startswith(base)`（双方都是纯追加）；
  - delta_theirs = 1,992 B（N89 五行：12:31 开工／13:29 挖矿＋取数／13:49 判定進捗／14:13 判定完成＋落地／14:24 收尾）、delta_ours = 341 B（N90 开工心跳 14:49）；
  - 工作副本按 N83 §5 惯例重建：**CRLF 化 union blob**（134,099 B），写前后断言 **byte807=243**（blob 形态该位为 63，243 是 CRLF 化工作副本形态的既定口径）；写后复读逐字节一致；
  - 夜序并集：N89 五行在前、N90 心跳收尾，分支行零改动（`git add` 后暂存 blob＝theirs＋d_ours＝133,103 B 等价断言通过后才 commit）。
- 其余文件全部自动合并成功并核验：backend/glossary_lexicon_extra2.py（801→1031・N89 追加 230）整体取分支版；README テスト行自动取分支值 **443 passed**（词库数三处 **1531**・数字行 13.491／13.502 同）；ROADMAP 尾部自动接到 N89 closed 行；ACCEPT_LOG 尾部自动接到 N89 PASS 行；tests/test_night79/80/82（必要伴随计数断言）＋tests/test_night89_lexicon_freq2.py（9 条）＋tools/night89_* 9 个＋eval/night89_* 归档・底稿・缓存清单整体取分支版；tools/accept_night.py 带入 NIGHT_ARTIFACTS[89]。
- 合并提交：**edd8ce8**（`git log --oneline -3`：edd8ce8 → 94966a6 → 76c678b，符合预期链）。

## 4. 合并后门禁（关键口径：4000 与 night89 归档比、8165 与 night89 归档比）

| 检查 | 结果 |
| --- | --- |
| pytest tests -q | **443 passed**（434＋N89 的 9：tests/test_night89_lexicon_freq2.py）✓ |
| golden_4000 全量真跑（tools/night90_eval_4000.py） | **13.491 / exact 24 / error 0**，与 night89_results_4000.json 输出差异 **0 行** → `eval/night90_results_4000.json`（默认口径，NIGHT_ARTIFACTS[90]）✓ |
| golden_8165 全量真跑（tools/night90_eval_8165.py） | **13.502 / exact 30 / error 0**，与 night89_results_8165.json 输出差异 **0 行** → `eval/night90_results_8165.json`（扩充归档，不登记默认口径；词库不进规则引擎＝与 N87 链尾值逐位相同是预期）✓ |
| 词库 | import 实测：GLOSSARY_LEXICON **500**＋extra.py **291**（词形全部本体子集、本体独有 **209**）＋LEXICON_EXTRA2 **1031**＝唯一词形 **1531**（extra2 801→1031・N89 追加 230，与本体零交集）；本体 500 条 N89 未碰 ✓ |
| verify_readme_facts | **19/19 exit 0** ✓（N89 未加 verify 断言，N86 分支版 19 项为准） |
| accept 90 | **PASS fail=0 skip=0**（30.1s，登记提交后首跑即 PASS，七门全绿：repo_clean／pytest 443=443／eval_integrity（night90_results_4000.json 実查）／rule_regression／engine_smoke／perf_envelope／order_rate（off 98.57%・on 98.63%））✓ |

## 5. 登记（⑤）与提交链

- 登记（8c977ca）：NIGHT_ARTIFACTS 加 `90: ["night90_results_4000.json"]`＋eval 归档（night90_results_4000/8165）＋eval 工具（night90_eval_4000/8165，night89 版克隆・基线换 night89 归档・文件名 token 全替换 grep 自检）＋README 数字节表头同步＋SHIFT_LOG 合并完成心跳。
- README 同步内容：数字节表头 →「Night 90 合并：词库频次 2 区 230 条（主 d95afe3＋wrap-up 76c678b）・合并提交 `edd8ce8`」；数字行合并已带入分支值（テスト **443 passed**、語釈辞書 **1531 語**・本文 1531 語、4000 **13.491**／24/4000、8165 **13.502**／30/8165），header 与数字同一提交收口。
- 提交链：35ba6e5 → 94966a6（心跳）→ edd8ce8（merge --no-ff）→ 8c977ca（登记）→ 本 wrap-up。**未合其他分支、未推远程**。

## 6. 事实漂移与遗留（如实，未动，留拍板）

- 无冲突遗留；SHIFT_LOG 混编码字节 0xF3@807（CRLF 工作副本形态）原样保留。
- **N88 分支 night88-rulep（零规则夜，4cd618c＋c651617）仍未合**——本夜按任务书只合 night89-lexicon-freq2，N88 文件一字未动；后续夜按任务书处置。
- N86 移交项原样带入 master（随 N87 已在 master）：なかれ→莫かれ post-N 残量 17 行／べからず族 89 行（79 改善 5 変差・exp 自写仮名死因）／がため・何のごとく 残量 1 行ずつ（guard 上下文機構変更で救済）／N84 §8 夹注残渣 8 行——本夜一字未动。
- N89 偏差注记 4 项随分支入库：test_night79/80/82 必要伴随（任务书允许清单外・N82 先例）、weblio 首回误抓（已重抓）、meaning 尾段剥離、機能語 2 条（以下・以来）break function=0 運用——均为 N89 判定済み事项，本夜只合并不改动。

## 7. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages 一行未动 ✓；词库文件一字未改（合并带入的分支版即最终态）✓
- 允许清单内文件のみ（accept_night.py 仅 NIGHT_ARTIFACTS 一条、README 仅数字行＋header、分支文件只接受分支版本）✓
- 合并冲突文件只接受字节安全并集（SHIFT_LOG），未手动改逻辑 ✓
- 无 OCR／guwenbert／eval 以外网络 ✓；N88 分支文件未触碰 ✓；SHIFT_LOG 纯追加惯例保持 ✓
- 未合其他分支（night88-rulep 未动）、未推远程 ✓

## 8. 证据

- eval/night90_results_4000.json（[OK] 与 night89 逐位一致 13.491/24/0、diff 0 行）
- eval/night90_results_8165.json（[OK] 与 night89 逐位一致 13.502/30/0、diff 0 行）
- eval/accept_night_90.json（verdict PASS fail=0 skip=0 30.1s）
- ACCEPT_LOG.md N90 PASS 行；SHIFT_LOG N90 段（开工／合并／收尾）
