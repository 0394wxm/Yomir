# REPORT_NIGHT66.md — 清理小活（Night 66）

日期: 2026-11-21 夜（AutoClaw 单会话，NEC 周积分内模型）
任务书: 仅限 ①开工核验 ②README 表头 commit 号 ③合并报告勘误 ④eval_ocr_gt 默认输出修复
⑤llm.py 词库注释 ⑥untracked 清理 ⑦验收两提交。不做新功能、不改规则、不改评测数据、
不动 golden*.json / GT；本地提交 master，不推远程。进入范围仅 D:\kanbun-kakikudashi。

## 1. 摘要

- 开工核验通过：`git log -1` = **54d2410**（= origin/master）；`pytest tests -q` = **214 passed**（12.27s）；
  `git status --porcelain --branch` 已跟踪文件零改动（untracked 567 项，见 §4）。
- README 表头两处 commit 号 bdf3e77 → 54d2410，其余数字一个未动；verify_readme_facts.py 与「数字」节逐行对上。
- REPORT_MERGE_62_64.md §7.3 原条目未动，其后追加勘误一行。
- eval_ocr_gt.py 默认输出改到未跟踪路径，冻结归档 eval/night36_cer.json 再也无法被默认覆盖；新增回归测试 1 条。
- llm.py 词库注释 209 → 500（实测 len(GLOSSARY_LEXICON)=500，仅改这一行注释）。
- untracked 清理：删 16 项、留 551 项（理由逐类注明）。
- 验收：pytest **215 passed**；accept_night.py 66 终跑 **PASS**（fail=0 skip=1；order_rate 与基线零退化）。
- 本地 master 两提交：主 **8eecb1d** ＋ wrap-up（本报告）；未推远程（领先 origin **2** 个提交）。
- 规则/逻辑/评测数据零改动：backend/ 仅 llm.py 一行注释；golden*.json / GT / 归档全部未触碰。

## 2. 每项改动与来源

### ② README.md 表头（两处，只改 commit 号）
- L14「数字」节表头：`` `master` bdf3e77 `` → `` `master` 54d2410 ``。
- L37「ブランチ統合状況」节：`最終 HEAD が `bdf3e77`` → `最終 HEAD が `54d2410``。
- `git diff` 全量核对：README 仅这 2 行变化，214 / 246 / 13.719 / 24-3998 / 7908·7883 / 4000·3975 /
  21 語 / CER 0.3568·0.3053 / 98.57·98.63·100 / 500 語 等数字均未动。
- 复核 `tools/verify_readme_facts.py`，输出与「数字」节逐行一致：
  SHINJITAI_MAP 246↔246 組；MERGE_WORDS 21↔21 語；Rule E/F/G/H/I = 5/4/4/3/6↔5+4+4+3 の 16 語＋Rule I 6 語；
  night64(golden_4000) total=4000 n=3998 exact=24 avgDist=13.719 errors=2↔13.719／24-3998（error 2 条を除く）；
  golden_4000 4000/3975↔4000 組・ユニーク 3975；golden_7908 7908/7883↔7908 組；
  ocr_gt_100.tsv 93 行（GT 92＋表头 1）↔GT 92 行；割注右先率基线 off=98.57% on=98.63% strict=100.0%↔98.57/98.63・厳密層 100%。
- 脚本不校验表头 commit 号 → **表头为人工核对 git log -1（HEAD=54d2410）**；未改脚本凑数。

### ③ REPORT_MERGE_62_64.md §7.3 勘误（只加一行）
- 在「3. known-issues 无需变（Rule I 不涉再読文字）。」之后按任务书原文追加（3 空格缩进续行，随原条目渲染）：
  `勘误（Night 65 同步后补记）：§7.3 判断只覆盖第 2 条（再読文字）；第 1 条与第 7 条已在 Night 65 按归档同步为 24/3998 与 N62 h2h 1366/1390/1151，第 2 条维持不变。`
- 原条目及其余 3 条未动；`git diff` 核对仅 +1 行。

### ④ tools/eval_ocr_gt.py 默认输出修复（第 3 次踩坑）
- 病根（读全文定位，行号为修复前）：L20 `OUT = os.path.join(ROOT, "eval", "night36_cer.json")` +
  L124 `out_path = sys.argv[2] if len(sys.argv) > 2 else OUT` —— 本工具的输出是**第 2 个位置参数**（没有 --out 旗标），
  不带参数重跑时默认落到已跟踪的 eval/night36_cer.json，一跑就覆盖冻结归档。
- 修法（改动最小）：OUT 常量改指未跟踪临时路径 **eval/night36_cer.tmp**（与既定可删模式 eval/*.tmp 一致）；
  docstring 产出说明同步更新。eval/night36_cer.json 只有**显式**作为第 2 参数传入才会被写。
- 验证（全量实跑，非干跑）：
  - (a) 无参数跑一次（exit 0）：输出写至 eval/night36_cer.tmp；`git status` 中 eval/night36_cer.json 无改动（无 M 行）；
  - (b) `git diff eval/night36_cer.json` 逐字节为空（diff 行数 = 0）；
  - (c) 附加证据：`git diff --no-index eval/night36_cer.json eval/night36_cer.tmp` 退出码 0 ——
        新跑输出与冻结归档**逐字节一致**（口径不变；整体 raw micro=0.3919/macro=0.3407、norm micro=0.3405/macro=0.3082，
        与归档内容完全相同）。README 的 CER 0.3568/0.3053 系 Night49 之后口径，与这份 Night36 归档不同源，两者本班均未触碰。
- 回归测试：新增 `tests/test_eval_ocr_gt_default_out.py`（1 条：断言默认输出路径 ≠ 已跟踪的 eval/night36_cer.json）。
  **pytest 214 → 215**。

### ⑤ backend/llm.py 词库注释
- 实测（`from backend.glossary_lexicon import GLOSSARY_LEXICON; len(...)`）= **500**（非抄记忆）。
- docstring 内「backend/glossary_lexicon.py 的 **209** 条文语词库查询」→「**500** 条」。仅此一行，零代码改动。

### ⑥ untracked 清理
- 删 16 项、留 551 项；待删清单逐个经 `git grep -F` 核查已跟踪的 REPORT_*.md / README.md 零引用后才删。
  明细见 §4。

## 3. 验收实数（⑦）

| 检查 | 结果 |
| --- | --- |
| `pytest tests -q` | **215 passed**（11.57s；= 214 + N66 回归测试 1） |
| `accept_night.py 66`（终跑 18:44:06） | **PASS**，fail=0 skip=1（27.4s）：repo_clean PASS（已跟踪零改动）；pytest 215=215 collected；eval_integrity **SKIP**（N66 未登记 NIGHT_ARTIFACTS，正常）；rule_regression / engine_smoke / perf_envelope（短句中位 16ms / 包络 3000ms）PASS；order_rate off 481/488=**98.57%**（基线差 +0.00pp）、on 503/510=**98.63%**（+0.00pp）、严格层 296/296=100%、退化页 0 —— 与基线零退化 |
| accept 66 首跑（18:42:33，提交前） | FAIL fail=1 —— repo_clean 如实报 5 个已跟踪文件未提交改动（即本晚待提交改动），验收门设计行为；Night 62 同款「FAIL→提交后终跑 PASS」惯例，FAIL/PASS 两行均如实留痕于 ACCEPT_LOG.md |
| `tools/verify_readme_facts.py` | 与 README「数字」节逐行一致（见 §2②） |
| SHIFT_LOG.md | 开工 18:29 / 收尾两行 UTF-8 追加；byte@807 = 0xF3（243）原样未动 |

## 4. untracked 清理清单

开工时 untracked 共 **567 项**（其中 eval/ocr_samples/** 占 526 项）；删除 **16** 项，保留 **551** 项。

### 删除（16 项；均命中任务书可删模式，且删前 grep 核查 REPORT_*.md / README.md 零引用）
| # | 文件 | 命中模式 |
| --- | --- | --- |
| 1 | eval/audit_authors.txt | eval/audit_*.txt |
| 2 | eval/audit_grep_keys.txt | eval/audit_*.txt |
| 3 | eval/audit_lsfiles.txt | eval/audit_*.txt |
| 4 | eval/audit_paths.txt | eval/audit_*.txt |
| 5 | eval/audit_push_readiness.txt | eval/audit_*.txt |
| 6 | eval/audit_secret_scan.txt | eval/audit_*.txt |
| 7 | eval/audit_secret_scan_run.txt | eval/audit_*.txt |
| 8 | eval/audit_prog.tmp | eval/*.tmp |
| 9 | eval/night59_patch_tail.tmp | eval/*.tmp |
| 10 | eval/night58_accept.txt | eval/*_accept.txt |
| 11 | eval/night60_accept.txt | eval/*_accept.txt |
| 12 | eval/night61_accept.txt | eval/*_accept.txt |
| 13 | tools/audit_authors.py | tools/audit_*.py |
| 14 | tools/audit_push_readiness.py | tools/audit_*.py |
| 15 | tools/audit_secret_scan_git.py | tools/audit_*.py |
| 16 | eval/night36_cer.tmp（本晚 ④ 验证产物） | eval/*.tmp |

- 删前证据核查：15 个原始待删文件名逐个 `git grep -F <名>` 已跟踪 REPORT_*.md / README.md → 全部零引用；
  全库粗查仅在 eval/accept_night_{58,59,60,61,63,65}.json（历史验收 JSON 记录「当时存在的未跟踪文件」快照）出现，
  属历史记录非活引用。另读 tools/accept_night.py 全文确认其为纯只读检查、不调用 audit 脚本，删除不影响验收门。
- #16 night36_cer.tmp 为本晚验证产物，与冻结归档逐字节一致、无独立信息量，按 eval/*.tmp 模式一并清走。

### 保留（551 项；逐类一句话理由）
- eval/merge62_facts.txt、eval/merge61_pytest_start.txt、eval/merge62_pytest_master.txt、eval/merge64_pytest_master.txt
  —— 任务书明示不动（合并报告 §9 已列为留档证据）。
- eval/night50_*（14 项）—— 任务书明示：是否入库待拍板。
- eval/ocr_samples/**（526 项：gt36 各页 line_*.png、gt36_hr/、gt36_view/、gt36_probe.png、hr_test.jpg）
  —— 任务书明示全部不动。
- eval/night58_accept_final.txt、eval/night59_accept_final.txt —— 不在可删模式内（eval/*_accept.txt 不匹配
  *_accept_final.txt），从严保留，是否清理待拍板。
- eval/night58_clock_probe.txt、eval/night58_pytest_start.txt、eval/night59_sim.txt、eval/night61_pytest_start.txt
  —— 不在可删模式清单内，从严保留。
- tools/night62_*.py —— 位于 eval10k clone，本班未进入、未触碰（本仓无此文件）。
- tests/test_eval_ocr_gt_default_out.py —— 本晚新增回归测试，随主提交入库。

## 5. 提交与移交

- 主提交 **8eecb1d**：README.md、REPORT_MERGE_62_64.md、tools/eval_ocr_gt.py、
  tests/test_eval_ocr_gt_default_out.py、backend/llm.py、SHIFT_LOG.md（6 文件，+36/−5）。
- wrap-up 提交：REPORT_NIGHT66.md（本报告）＋ SHIFT_LOG.md 收尾行 ＋ ACCEPT_LOG.md（FAIL/PASS 两行）＋
  eval/accept_night_66.json（终跑 PASS 版）。均属任务书允许清单，提交前 `git diff --cached --name-status` 逐项核对。
- **未推远程**：`git rev-list --count origin/master..master` = **2**（开工时 origin/master 已被用户推至
  54d2410，N65 时的账面 10 个领先提交已推送；本晚新增 2 个提交未推）。
- 移交下一班 / 待拍板：
  1. eval/night50_*（14 项）与 eval/merge62_facts.txt 等 §9 证据文件何时入库/清理，仍待用户拍板；
  2. eval/night58_accept_final.txt、eval/night59_accept_final.txt 不在既定可删模式（*_accept.txt）内；
     如需清理请先扩模式（如 eval/*_accept*.txt）再删；
  3. README CER 0.3568/0.3053（Night49 之后口径）与冻结归档 eval/night36_cer.json（Night36 口径，
     0.3919/0.3405）不同源——本班如实记录，均未触碰；如需在 README 标注 CER 出处可另行拍板；
  4. master 领先 origin 2 个提交，推送时机由用户定。

（Night 66 即停。）
