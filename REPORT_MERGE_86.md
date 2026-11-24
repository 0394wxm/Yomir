# REPORT_MERGE_86 — 合并 night86-ruleo 进 master（Night 87，主仓合并夜）

## 1. 结论摘要

- 合并完成：master d4738a5 →（03c2de4 开工心跳）→ **994f530**（merge --no-ff night86-ruleo，即 15001cd 主提交＋596687f wrap-up）→ **f025adc**（登记）→ 本 wrap-up。
- 冲突 1 文件：SHIFT_LOG.md（追加-追加）→ 字节安全并集（REPORT_MERGE_62_64 §5 / N83・N85 惯例：CRLF 化 blob＋deltas 重建、byte807=243 前后断言、绝不文本三路合并）解消；ACCEPT_LOG／README／ROADMAP／backend/kundoku_rules.py／tools/verify_readme_facts.py 全部 git 自动合并成功。
- 门禁全绿：pytest **434 passed**（422＋N86 12）；golden_4000 真跑 **13.491 / exact 24 / error 0** 与 night86 归档逐位一致（diff 0 行）；golden_8165 真跑 **13.502 / exact 30 / error 0** 与 night86 归档逐位一致（diff 0 行——**不是 N85 的 13.505，13.502 正是本夜合入的 Rule O 15 行改写；13.491 正是 4000 内 8 行改写**）；词库 **500＋801＝1301**（唯一词形 209＋291＋801、零交集）import 实测复核；verify_readme_facts **19/19 exit 0**（分支版 19 项为准）；accept 87 **PASS（fail=0 skip=0，30.9s，登记后首跑即 PASS）**。

## 2. 开工核验

- `git checkout master`：HEAD = d4738a5 ✓；`git log -1 night86-ruleo` = 596687f ✓；`git merge-base master night86-ruleo` = d4738a5 ✓（N86 自 master 直分，无 clone 中转、无需 fetch）；pytest 422 passed ✓；已跟踪文件零改动 ✓。

## 3. 合并与冲突解法（主仓）

- 开工心跳先行提交（03c2de4，merge 拒绝脏树），随后 `git merge --no-ff night86-ruleo -m "Merge night86-ruleo"`。
- 冲突：仅 **SHIFT_LOG.md**（UU，追加-追加：master 侧 N87 心跳 1 行 vs 分支侧 N86 心跳 3 行，共同基线 d4738a5 之后双方都在尾部追加）。
- 解法（字节安全并集，python 二进制，绝不文本三路合并）：
  - base = `git show d4738a5:SHIFT_LOG.md`（128,772 B）、ours = `03c2de4`、theirs = `596687f`，三 blob 均纯 LF、断言 `ours.startswith(base)`／`theirs.startswith(base)`（双方都是纯追加）；
  - delta_theirs = 1,052 B（N86 三行：21:51 开工／22:54 挖词＋落地／22:57 收尾）、delta_ours = 238 B（N87 开工心跳 10:21）；
  - 工作副本按 N83 §5 惯例重建：**CRLF 化 base blob＋CRLF 化 deltas**（131,050 B），写前后断言 **byte807=243**（blob 形态该位为 63，243 是 CRLF 化工作副本形态的既定口径）；写后复读逐字节一致；
  - 夜序并集：N86 三行在前、N87 心跳收尾，分支行零改动（`git add` 后暂存 blob＝theirs＋d_ours＝130,062 B 等价断言通过后才 commit）。
- 其余文件全部自动合并成功并核验：README テスト行自动取分支值 **434 passed**（数字行 13.491／13.502・Rule O 3 語・ルールチェーン Rule O 句同）；ROADMAP 尾部自动接到 N86 closed 行；ACCEPT_LOG 尾部自动接到 N86 PASS 行；backend/kundoku_rules.py（Rule O 3 条）与 tools/verify_readme_facts.py（19 项版）整体取分支版。
- 合并提交：**994f530**（`git log --oneline -3`：994f530 → 03c2de4 → 596687f，符合预期链）。

## 4. 合并后门禁（关键口径：4000 与 night86 归档比、8165 与 night86 归档比）

| 检查 | 结果 |
| --- | --- |
| pytest tests -q | **434 passed**（422＋N86 的 12：tests/test_night86_rule_o.py）✓ |
| golden_4000 全量真跑（tools/night87_eval_4000.py） | **13.491 / exact 24 / error 0**，与 night86_results_4000.json 输出差异 **0 行** → `eval/night87_results_4000.json`（默认口径，NIGHT_ARTIFACTS[87]）✓ |
| golden_8165 全量真跑（tools/night87_eval_8165.py） | **13.502 / exact 30 / error 0**，与 night86_results_8165.json 输出差异 **0 行** → `eval/night87_results_8165.json`（扩充归档，不登记默认口径；不是 N85 的 13.505——Rule O 改写已随合并生效）✓ |
| 词库 | import 实测：GLOSSARY_LEXICON **500**＋extra.py **291**（词形全部本体子集、本体独有 **209**）＋LEXICON_EXTRA2 **801**＝唯一词形 **1301**（与 extra2 零交集）；N86 未碰词库 ✓ |
| verify_readme_facts | **19/19 exit 0** ✓（N86 分支版：归档源 night78→night86 切换＋Rule O 語数断言；master 旧版 18 项作废） |
| accept 87 | **PASS fail=0 skip=0**（30.9s，登记提交后首跑即 PASS，七门全绿）✓ |

## 5. 登记（⑤）与提交链

- 登记（f025adc）：NIGHT_ARTIFACTS 加 `87: ["night87_results_4000.json"]`＋eval 归档（night87_results_4000/8165）＋eval 工具（night87_eval_4000/8165）＋README 同步（数字行与 header 同一提交改完）＋SHIFT_LOG 合并完成心跳。
- README 同步内容：数字节表头 →「Night 87 合并：Rule O 3 条（主 15001cd＋wrap-up 596687f）・合并提交 `994f530`」；数字行合并已带入分支值（テスト **434 passed**、4000 **13.491**／24/4000、8165 **13.502**／30/8165、規則エンジン Rule O 3 語・ルールチェーン Rule O 句），header 与数字同一提交收口。
- 提交链：d4738a5 → 03c2de4（心跳）→ 994f530（merge --no-ff）→ f025adc（登记）→ 本 wrap-up。**未合其他分支、未推远程**。

## 6. 事实漂移与遗留（如实，未动，留拍板）

- 无冲突遗留；SHIFT_LOG 混编码字节 0xF3@807（CRLF 工作副本形态）原样保留。
- N86 移交项原样带入 master：なかれ→莫かれ post-N 残量 **17 行**（N84 rerun 追加 rikutou34-7）拍板事項待決（guard 机制或 kanji→kanji 機構追加で 80 行規模再候補）；べからず族 89 行 79 改善の 1 変差回避は不可（exp 自写仮名死因・0 変差硬門撤廃なら一発収録、提出のみ）；がため／何のごとく 残量 1 行ずつ（rikutou37-2／shiki050-4、rerun 行 tail 无守り字）救済要 guard 上下文機構変更；N84 §8 移交（夹注残渣 8 行・sonshi09-38・≤8 字尾段 30 行）本夜も一字未动。

## 7. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages 一行未动 ✓；词库文件一字未改 ✓
- 允许清单内文件のみ（accept_night.py 仅 NIGHT_ARTIFACTS 一条、README 仅数字行＋header、分支文件只接受分支版本）✓
- SHIFT_LOG 纯追加＋字节安全并集（byte807=243 前后断言）✓；无 OCR／guwenbert／eval 以外网络 ✓
- 未合其他分支、未推远程 ✓

## 8. 证据

- eval/night87_results_4000.json（[OK] 与 night86 逐位一致 13.491/24/0、diff 0 行）
- eval/night87_results_8165.json（[OK] 与 night86 逐位一致 13.502/30/0、diff 0 行）
- eval/accept_night_87.json（verdict PASS fail=0 skip=0 30.9s）
- ACCEPT_LOG.md N87 PASS 行；SHIFT_LOG N87 段（开工/合并/登记/收尾）
