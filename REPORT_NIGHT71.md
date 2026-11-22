# REPORT — Night 71（整本导入＋guwenbert 全量 h2h）

- 日期: 2026-11-21 21:30 开工 → 2026-11-23 04:0x 收尾（挂机约 30.5 小时，含夜间主机休眠中断段）
- 开工点: HEAD = ad18f20（= N70 wrap-up），pytest 260 passed，tracked 零改动，SHIFT_LOG byte807=243
- 主提交: 24f6af4 ＋ wrap-up（本报告），本地 master，未推远程
- 规则引擎口径: **零改动**（golden_4000 13.584 / golden_8165 14.632 维持，README 数字表不动，verify_readme_facts 13/13 维持）

## ② 整本导入：5 本全部完成，跳过 0 本

样书库 8 本中尚未导入的 5 本，一本接一本，每本 `tools/night71_verify_book.py <PID>` verify（manifest 实取页数、0 行页、OCR 失败、ASCII noise、sha16）：

| # | PID | 书名 | manifest 页 | verify ok | 0 行页 | ocr_fail | noise | sha16 | verify | OCR 耗时 |
|---|-----|------|------------|-----------|--------|----------|-------|-------|--------|----------|
| 1 | 1287221 | 竹取物語.上 | 28 | 27/28 | p001 | 0 | 0 | 54495441f3f4d515 | PASS | 472.1s |
| 2 | 10301438 | 人間萬事転馬（人間萬事翁馬） | 20 | 19/20 | p020 | 0 | 0 | 6b4e1de994b095ca | PASS | 779.0s |
| 3 | 9973821 | 伊藤博文関係文書 | 6 | 6/6 | — | 0 | 0 | 678b167f271d8f4f | PASS | 111.5s |
| 4 | 1288060 | 元和卯月本写本 | 19 | 17/19 | p018, p019 | 0 | 0 | a55f006fafdb3f83 | PASS | 274.1s |
| 5 | 1033232 | 墨場必携新註 | 582 | 582/582 | — | 0 | 0 | 3b514439ba3b9fb3 | PASS | 见下 |

- 0 行页均为原书空白/仅画页，与既有样书口径一致，不修不排。
- **墨場必携 1033232（582 页）运行史如实记**：
  - 第 1 轮 11-21 夜启动 → 跑到 p212 后夜间主机休眠，宿主重试重启从头（pages 缓存跳过下载、OCR 重算，原进度作废）；
  - 第 2 轮 02:19 起连跑到 20:50 p449 死于 `udkanbun.kaeriten` IndexError（第三方库 bug，p450 密页訓読触发；彼时管线等待窗 6h 亦因休眠时序错位，已先行改 12h 窗）；
  - 处置：新写 `tools/night71_import_resume.py`（每页整本落盘、重启页级续跑、kundoku 页级容错＝白文保留＋「(训读失败: …)」行），管线重试命令同步切 resume 版；
  - 第 3 轮（resume）p449→582：wall 187.7 分钟、OCR 11132.9s；p450 容错接住（verify kudashi_lines=0、白文 935 字在），[done] ok=581 skip=1；
  - 三轮 OCR 计时累计 74404.9s（≈20.7h，**含休眠冻结段与被宿主重启/硬杀造成的重算**——有效纯算远小于此，事故两条已入 SHIFT_LOG）。
- 导入产物：`eval/import_pid_<PID>/book.md`（5 本，pages/ 页图不入库）；运行日志 `eval/night71_import_*_log.txt`。

## ③ guwenbert 全量 8165 条（离线）＋规则逐条对照

- `tools/night71_guwenbert_full.py`：golden_8165 全量 8165 条、offset=0、HF_HUB_OFFLINE=1、进程内 AUX 补丁（`應,v,助動詞,必要,*`→`須` 同参）、每 500 条二进制追加 SHIFT_LOG 进度行。
- 结果：**OK 8165 / error 0 / exact 20 / avgDist 30.872，总耗时 211.8 分钟（≈3.5h）**（N67 长文 ~13.8s/条预估 5-12h，实际混合句长 ~1.6s/条，快于预估）。
- `tools/night71_h2h.py` 全量逐条对照（规则=night70_results_8165.json vs gwb=night71_guwenbert_8165.json，双方可比 8165，无抽样、无跳过）：
  - **逐条对决：规则更好 3221 ／ guwenbert 更好 2635 ／ 持平 2309**
  - **规则 avgDist 14.632（exact 30） vs guwenbert avgDist 30.872（exact 20）**
  - 分档要点：短句（≤20 字）双方接近（漢詩 6.989 vs 6.784，gwb 略胜）；规则在全部长句档明显更稳（>60 字 その他 72.015 vs 451.576；>60 字 漢詩 11.0 vs 165.5）；规则相对优势 top 见 `eval/night71_h2h.txt`（史记/吴子等长文段 gwb 重复生成崩坏 dist 2000+）。
- 产物：`eval/night71_guwenbert_8165.json`、`eval/night71_h2h.txt`；管线日志 `eval/night71_pipeline_log.txt`。

## ④ 验收

- pytest: **260 passed**（16.94s）
- accept 71: **PASS（fail=0 skip=0，30.2s）**；首跑 FAIL（repo_clean=已提交的 watchdog_log 被仍在跑的看门狗追加 1 行心跳）→ 停看门狗、checkout 丢弃增量、重跑 PASS；ACCEPT_LOG 两条如实留痕。
- verify 重跑: 5 本全 exit=0（json 内容确定性、无 diff）。
- NIGHT_ARTIFACTS[71] 登记 night70_results_4000.json（②导入与③gwb 均不产生新评测口径归档；71 无新口径，登记现行最新口径——任务书④明文许可）。
- 提交: 主提交 24f6af4（tools/night71_*×6＋eval/night71_*＋import_pid_5 本 book.md＋SHIFT_LOG＋ROADMAP＋accept_night.py）＋ wrap-up（REPORT＋SHIFT_LOG＋ACCEPT_LOG＋accept_night_71.json）；`git rev-list --count ad18f20..HEAD` = 2；未推远程。

## 已知问题（本夜新增/延续）

⑦ guwenbert 全量基线：gwb avgDist 30.872 全面差于规则 14.632（尤其 >60 字长文段崩溃级 451 vs 72），但短句漢詩档 gwb 略优（6.784 vs 6.989）——归档备查，不改任何口径，不做规则侧动作。

（延续）夜间主机休眠会冻结/重试后台进程：长跑挂机需 resume 安全设计（本夜 import_resume 页级续跑模式已验证有效，可复用）。
