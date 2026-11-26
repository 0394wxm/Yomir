# REPORT_MERGE_102_103_104 — Night 105 合并夜：N102＋N103＋N104 三分支顺序合入 master

AutoClaw・2026-11-26・单会话。主仓 D:\kanbun-kakikudashi、master 起点 `67b0d73`（N101 wrap-up）。三分支同基 `67b0d73`，按时间顺序三依次 `--no-ff` 合入；**不合其他分支、未推远程**。

## 1. 三合流顺序与提交

| 顺 | 分支（夜） | 分支提交 | merge commit | pytest |
| --- | --- | --- | --- | --- |
| 1/3 | night102-kotonaku-guard（N102 报告-only・项 8 ことなく guard 外 5 行 sim 先验＝无益拒） | 29df57c＋0b2cb1e | `09ac09c` | 476 passed |
| 2/3 | night103-kotonaki-sim（N103 报告-only・项 6 ことなき字形统一 sim 再测＝不统一不实施建议） | 8d7ea77＋638e004 | `3311840` | 476 passed |
| 3/3 | night104-ruleu（N104 拍板夜・Rule U 1 条 なかれ→莫かれ guard 莫・変差 1 行 kokyo09-5 許容） | cc19eba＋df1ea55 | `eaa4c01` | 484 passed |

开工心跳 `b35a779`（merge 前落位＝N100 坑位①）、登记 `9aeb2a3`（NIGHT_ARTIFACTS +105）、wrap-up 另行提交（ACCEPT_LOG 参照）。

## 2. 冲突文件与合流字节数（全部字节安全合流・禁文本三方合流・N81/N91 先例）

- **合 1/3**：SHIFT_LOG 1 文件冲突（master 侧＝N105 开工心跳 440 B・theirs＝N102 段 1,036 B）；ACCEPT_LOG／ROADMAP 自动合流（master 侧零改动）。SHIFT_LOG union＝base 147,745＋N102 段 1,036＋N105 心跳 440＝**149,221 B LF**。
- **合 2/3**：SHIFT_LOG／ACCEPT_LOG／ROADMAP 3 文件冲突。SHIFT_LOG union＝147,745＋N102 1,036＋N105 心跳 440（ours）＋N103 段 1,771（theirs）＝**150,992 B LF**；ACCEPT_LOG＝11,941＋85（accept 102）＋85（accept 103）＝12,111 B；ROADMAP＝45,114＋2,320（Night 102 行）＋2,905（Night 103 行）＝50,339 B。
- **合 3/3**：3 文件冲突。SHIFT_LOG union＝147,745＋N102 1,036＋N103 1,771（ours）＋N104 段 1,950（theirs）＋N105 心跳 440＝**152,942 B LF**；ACCEPT_LOG＝11,941＋170（accept 102/103）＋170（accept 104 FAIL/PASS 两行）＝12,281 B；ROADMAP＝45,114＋5,225（Night 102/103 行）＋1,064（Night 104 行）＝51,403 B。
- 合流规则＝**夜序**（N91/N95/N100 先例）：ours 侧含跨夜混合 delta（N102/N103 段＝旧・N105 心跳＝新），按 N105 心跳 marker 拆分插序，最终文件夜序 **N102＜N103＜N104＜N105**（SHIFT_LOG 行 1034–1044 実測・ACCEPT_LOG 行序 102＜103＜104(FAIL/PASS)・ROADMAP Night 102/103/104 行序——三文件全部実測核对）。
- **canary 双形态断言**（N85/N100 教训・本夜实测确认索引）：blob `[807]`=63／工作副本 CRLF `[807]`=243（**0 基索引**＝第 808 字节；任务书「byte807」按 1 基读会得 26/40＝落空，坑位①）。每次合流写前后断言＋暂存 blob 等价断言（`:0:` blob == union 字节）＋冲突标记 0。

## 3. README／verify／accept_night.py 防回滚核对（合 N104 后 grep）

- verify 归档源＝`eval/night104_results_4000.json` ✓（night99 残留 0）＋Rule U 語数断言在位 ✓
- README：Rule U 句（第 16 系列・なかれ→莫かれ）＋数字 13.460／13.467／484 passed 全在位 ✓
- accept_night.py：NIGHT_ARTIFACTS 104 条目在位 ✓（105 条目＝登记提交 `9aeb2a3`）
- backend/kundoku_rules.py：`style_kana_to_kanji_u`＋`U_KANA_TO_KANJI`＋链尾 T→U 在位 ✓
- pytest 484（484＝476＋test_night104_rule_u 8）＝tests 未回滚 ✓

## 4. 终验对照（只对 night104 归档——唯一动口径的分支）

| 项 | 结果 |
| --- | --- |
| pytest tests -q | **484 passed**（16.21s） |
| golden_4000 TestClient 全量 | diff **0 行** vs night104 归档・avgDist **13.460**／exact **24**／error 0（88s） |
| golden_8165 TestClient 全量 | diff **0 行**・avgDist **13.467**／exact **30**／error 0（196s） |
| 词库 | 209＋291＋1031＝**1531** 不动 |
| verify_readme_facts | **24/24 exit 0**（N104 版） |
| accept 105 | PASS fail=0 skip=0（登记口径沿用 N104 归档・ACCEPT_LOG 参照） |

注：终验双口径对照用 workspace 临时脚本执行（任务书允许编辑清单未含 `tools/night105_eval_*.py`＝「其余文件一律不碰」——不落盘、结果如实记录于本报告；night101 型 eval 工具惯例在合并夜清单允许时才落盘）。
