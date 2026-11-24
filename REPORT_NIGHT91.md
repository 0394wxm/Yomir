# REPORT_NIGHT91 — 合并 night88-rulep 进 master（Night 91，主仓合并夜）

## 1. 结论摘要

- 合并完成：master 59bb299 →（7422211 开工心跳）→ **1ea1566**（merge --no-ff night88-rulep，即 4cd618c 主提交＋c651617 wrap-up）→ **5e13057**（登记）→ 本 wrap-up。**Night 88（Rule P 零规则夜）自 N89/N90 词库链合入后仍未合的状态就此解消**。
- 冲突 **3 文件**（SHIFT_LOG.md／ACCEPT_LOG.md／ROADMAP.md，全部追加-追加——与 N85/N87/N90 的 1 文件不同，本夜 master 侧（N89/N90 心跳＋accept 行＋ROADMAP 行）与分支侧（N88 段）都改了这三个追加文件）→ 按 REPORT_MERGE_62_64 §5 / REPORT_MERGE_89 §3 **字节安全并集**全部解消（theirs＋d_ours、夜序 N88(11:03–11:31)→N89(12:31–14:24)→N90(14:49–15:15)、绝不文本三路合并），详见 REPORT_MERGE_88.md。
- 门禁全绿：pytest **443 passed**（开工 11.79s・合后 13.58s，N88 零规则无新测试＝数字不动是预期）；golden_4000 全量真跑 **13.491 / exact 24 / error 0** 与 night90 归档逐位一致（diff 0 行・89s）；golden_8165 全量真跑 **13.502 / exact 30 / error 0** 与 night90 归档逐位一致（diff 0 行）；词库 **1531**（本体 500＝核心 209＋extra 291、extra2 1031、唯一词形 209＋291＋1031＝1531）import 实测复核；verify_readme_facts **19/19 exit 0**；accept 91 **PASS（fail=0 skip=0，31.1s，登记后首跑即 PASS，七门全绿）**。

## 2. 开工核验（①）

- `git checkout master`：HEAD = **59bb299**（N90 wrap-up）✓；`git log -1 night88-rulep` = **c651617** ✓；`git merge-base master night88-rulep` = **35ba6e5** ✓（N88 自 35ba6e5 分出后 master 已走 N89＋N90 六提交，base 落后是预期）。
- `pytest tests -q` = **443 passed** ✓（11.79s）。
- 已跟踪文件零改动（untracked 仅 eval/ 历史缓存，merge 不受影响）✓。
- 前置阅读：REPORT_NIGHT88.md §0/§5/§7（零规则夜・阴性证明・拍板移交）与 REPORT_MERGE_89.md §3（字节安全并集方法论）确认済み。

## 3. 合并与冲突解法（②）

- 开工心跳先行提交（**7422211**，SHIFT_LOG 二进制追加 368 B・byte807=243 写前后断言・merge 拒脏树），随后 `git merge --no-ff night88-rulep -m "Merge night88-rulep"`。
- 冲突与任务书预测完全一致：**UU 3 文件**＝SHIFT_LOG.md／ACCEPT_LOG.md／ROADMAP.md；N88 分支新文件 16 个（REPORT_NIGHT88.md、eval/night88_* 9 个、tools/night88_* 5 个、eval/accept_night_88.json）整体自动入暂存区；其余自动合并（README／accept_night.py 等取 master 版——分支侧未动）。
- 解法＝字节安全并集（python 二进制，blob 纯 LF・startswith 双断言・CRLF 化工作副本・绝不文本三路合并）：

| 文件 | base(35ba6e5) | ours(7422211) | theirs(c651617) | d_theirs | d_ours | union blob | 工作副本(CRLF) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SHIFT_LOG.md | 130,770 B | 134,693 B | 132,206 B | 1,436 B（N88 段） | 3,923 B（N89＋N90 段） | **136,129 B** | 137,131 B |
| ACCEPT_LOG.md | 10,524 B | 10,690 B | 10,607 B | 83 B（N88 PASS 行 11:31:39） | 166 B（N89 14:21:50＋N90 15:13:15 行） | **10,773 B** | 10,906 B |
| ROADMAP.md | 36,772 B | 37,352 B | 37,734 B | 962 B（N88 状態行） | 580 B（N89 状態行） | **38,314 B** | 38,447 B |

  - 夜序并集＝theirs＋d_ours（theirs＝base＋N88 段，故 union＝base＋N88→N89→N90）；三文件双侧均 startswith(base)＝纯追加成立；
  - SHIFT_LOG 写前后断言 **byte807=243**（0xF3@807 混编码字节原样保留）、写后复读逐字节一致、冲突标记 0；
  - `git add` 后暂存 blob＝theirs＋d_ours **逐字节等价断言**通过后才 commit（N87 加保险步骤沿用）。
- 合并提交：**1ea1566**（`git log --oneline -4`：1ea1566 → 7422211 → 59bb299 → 8c977ca，符合预期链）。

## 4. 合并后门禁（③，关键口径：4000/8165 均与 night90 归档比）

| 检查 | 结果 |
| --- | --- |
| pytest tests -q | **443 passed** ✓（N88 零规则、无新测试，数字不动是预期） |
| golden_4000 全量真跑（tools/night91_eval_4000.py，TestClient 完整链） | **13.491 / exact 24 / error 0**，与 night90_results_4000.json 输出差异 **0 行** → `eval/night91_results_4000.json`（默认口径，NIGHT_ARTIFACTS[91]）✓（89s） |
| golden_8165 全量真跑（tools/night91_eval_8165.py） | **13.502 / exact 30 / error 0**，与 night90_results_8165.json 输出差异 **0 行** → `eval/night91_results_8165.json`（扩充归档，不登记默认口径）✓ |
| 词库 | import 实测：GLOSSARY_LEXICON **500**（＝核心 **209**（_OLD_SIZE）＋glossary_lexicon_extra **291**（as_dicts，词形全本体子集））＋LEXICON_EXTRA2 **1031**＝唯一词形 **1531**（_ORDERED_ALL=1531、extra2 与本体零交集）；N88 未碰词库 ✓ |
| verify_readme_facts | **19/19 exit 0** ✓（N88 未加 verify 断言，19 项为准） |
| accept 91 | **PASS fail=0 skip=0**（31.1s，登记提交后首跑即 PASS，七门全绿：repo_clean／pytest 443=443／eval_integrity（night91_results_4000.json 実查）／rule_regression／engine_smoke／perf_envelope／order_rate（off 98.57%・on 98.63%、退化页 0））✓ |

- eval 工具＝night90 版程序化克隆（基线换 night90 归档、文件名 token 逐个替换带出现次数断言、night87/night89 陈旧引用 grep 自检＝N87/N90 合并夜模板惯例）；night91_eval_4000.py 5,994 B／night91_eval_8165.py 6,051 B。

## 5. 登记（④）与提交链

- 登记（**5e13057**）：NIGHT_ARTIFACTS 加 `91: ["night91_results_4000.json"]`（**88 不补登记**——零规则夜不登记是 accept_night.py L247-249 的既定 skip 机制、N69/N74/N76 先例）＋eval 归档 2 件＋eval 工具 2 个＋README 数字节表头同步＋SHIFT_LOG 合并完成心跳（710 B・byte807 断言）。
- README 同步内容：数字节表头 →「Night 91 合并：night88-rulep 零规则夜（主 4cd618c＋wrap-up c651617）・合并提交 `1ea1566`」；数字行不动（テスト 443 passed・4000 13.491／24・8165 13.502／30・語釈辞書 1531 語 全部与合并后实况一致），header 与数字同提交收口。
- 提交链：59bb299 → 7422211（心跳）→ 1ea1566（merge --no-ff）→ 5e13057（登记）→ 本 wrap-up。**未合其他分支、未推远程**。

## 6. 事实漂移与遗留（如实，未动，留拍板）

- 无冲突遗留；SHIFT_LOG 混编码字节 0xF3@807（CRLF 工作副本形态）原样保留。
- **N88 §7 移交项随合并原样带入 master**（零规则夜产物、本夜一字未动）：①べきなり→可きなり 31 行 29 改善・Δ−0.006・p-gekirin-1 1 変差＝「変差 1 行許容」拍板が下りれば一発収録級（べからず族同枠提出事項）；②して→問す＝「発火行数≫B2 pair 行数⇒非語彙対応 scramble」判別実例（5 行 pair vs 162 発火）；③N86 からの拍板事项（べからず族 89 行 79 改善 5 変差／なかれ→莫かれ post-N 17 行 kokyo09-5 1 変差／がため・何のごとく 各 1 行 rerun tail guard 機構変更待ち／N84 §8 夹注残渣 8 行）——全部原样。
- N88 拒案数字对照复核全維持（るべ 91/7・べきか 25/2・べからず 79/5・なかれ 13/1・はざる blanket 1 変差＝N86/N72 完全一致）；Rule O 三键（はざる者／たりせ／なきか）残量全 0＝N87 收録確認。
- origin/master = 59bb299（用户手推 N90 链后未变）；本夜四提交未推远程，rev-list 待用户确认后自推。

## 7. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查＋night91_eval 逐位一致）；backend/**・词库（glossary_lexicon*.py）一字未改 ✓；kundoku_rules.py 一字未改（零规则分支合并・规则引擎不动）✓；site-packages 一行未动 ✓
- 允许清单内文件のみ（accept_night.py 仅 NIGHT_ARTIFACTS 一条、README 仅数字节表头、verify_readme_facts.py 未动＝无相关断言、分支文件只接受分支版本不手动改逻辑）✓
- 合并冲突文件只接受字节安全并集（3 文件），未手动改逻辑 ✓；golden_4000/8165 与 N90 归档逐位一致＝零行为变化的阴性证明 ✓
- 无 OCR／guwenbert／eval 以外网络 ✓（web_search 0・ページ取得 0）；临时脚本全部在 workspace scratch（仓库外）・仓库无残留 ✓
- 未合其他分支、未推远程 ✓；SHIFT_LOG 纯追加惯例保持（3 回追加・byte807=243 每回写前后断言）✓

## 8. 证据

- eval/night91_results_4000.json（[OK] 与 night90 逐位一致 13.491/24/0、diff 0 行）
- eval/night91_results_8165.json（[OK] 与 night90 逐位一致 13.502/30/0、diff 0 行）
- eval/accept_night_91.json（verdict PASS fail=0 skip=0 31.1s）
- ACCEPT_LOG.md N91 PASS 行；SHIFT_LOG N91 段（开工／合并／收尾）；REPORT_MERGE_88.md（合并专报・冲突 3 处字节明细）
