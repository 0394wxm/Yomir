# REPORT_NIGHT65.md — Night 65：README 合并后同步（master bdf3e77）

日期: 2026-11-21 班（Night 65，小件活单做；AutoClaw 积分内模型）
分支: `master`（在 bdf3e77 上直接做。README / verify 工具 / SHIFT_LOG 属文档面，无代码改动）
任务书: 用户指令（只做 README 文档同步，不碰规则、后端、评测数据；数字逐条对当前 master
代码/归档取数：SHINJITAI_MAP 246 对、pytest 214、规则链加 Rule I、golden_7908 已入库但默认
口径仍 golden_4000；「未統合ブランチ」节整节改写或删除；verify_readme_facts.py 重跑对上；
pytest + `tools/accept_night.py 65` 通过；写 REPORT_NIGHT65.md；本地提交在 master，不推远程；
单会话不开并行）。

---

## 1. 结论摘要

- **开工核验通过**：`git log -1` = `bdf3e77`（merge-shift report 提交）✓；`pytest tests -q`
  = **214 passed**（19.08s）✓；分支 = master；工作区无已跟踪改动（仅历史遗留未跟踪 scratch，
  未触碰）。
- **README.md 同步 11 处**（详见 §2/§3/§4）：「数字」节表头 commit `d3da2b3`→**`bdf3e77`**、
  テスト 193→**214**、規則エンジン 13.889/19/3998→**13.719/24/3998**（night64 归档口径）、
  ルールチェーン追加 **Rule I**（かな→漢字第 5 系列 6 語，列全六词）、正字化 147→**246 組**、
  評価セット行注明 golden_7908（7908 組）已入库 + **默认口径仍 golden_4000**；
  「未統合の作業ブランチ」节**整节改写**为「ブランチ統合状況（Night 65 時点）」；
  既知の問題① **19/3998→24/3998**（night64 分档/文体实数）、⑦补 N62 h2h 对决数；
  構成节与「起動とテスト」的 pytest 条数 193→**214**。
- **`tools/verify_readme_facts.py` 同步扩展**：Rule E/F/G/H→**E/F/G/H/I**（+I 6 語）、
  night60 归档行→**`eval/night64_results_4000.json`**（补 errors 打印）、追加
  **golden_7908_stats** 打印（默认口径注明）；重跑输出与 README「数字」节逐行对上（§6）。
- pytest 全量 **214 passed**；`python tools/accept_night.py 65` **PASS**（提交后终跑，fail=0
  skip=1）；本地提交两个（主提交 + wrap-up），**未推远程**（本班结束时 master 领先
  origin/master **12** 个提交）。
- 规则（`backend/kundoku_rules.py`）、后端其余文件、评测数据（golden*/GT/归档）零改动。

## 2. 数字取证清单（本次改动每个数字的来源，全部现场核对）

| README 里的数字 | 值 | 来源（本班实际核对） |
| --- | --- | --- |
| 开工 HEAD | `bdf3e77` | `git log -1`（提交题：merge-shift report，pytest 193→211→214、accept 64/62 rerun PASS） |
| テスト | **214 passed** | 实跑 `D:\Python312\python.exe -m pytest tests -q`（19.08s） |
| SHINJITAI_MAP | **246 組** | `len(SHINJITAI_MAP)`（verify 脚本打印；合并班 eval/merge62_facts.txt 同值） |
| Rule I | **6 語**、白文ガード＋長語マスク | `backend/kundoku_rules.py` `I_KANA_TO_KANJI`（けだし→蓋し／いずくんぞ→焉くんぞ／もし→如し／それ→夫れ／ただ→惟だ／なかれ→毋かれ，guard=蓋/焉/如/夫/惟/毋；`style_kana_to_kanji_i` 在 `style_fix_with_hakubun` 链尾） |
| E/F/G/H/I | 5 / 4 / 4 / 3 / **6** | verify 脚本（`len(E/F/G/H/I_KANA_TO_KANJI)`） |
| 規則エンジン（golden_4000） | avgDist **13.719**／exact **24**/3998、error **2** | `eval/night64_results_4000.json` summary（n=3998, exact=24, avg_edit_distance=13.719, errors=2, errors_detail=toushisen135-12/toushisen043-16） |
| 既知の問題①分档 | 24 条全部 ≤20 字（3041 条、avg **7.74**）；21 字超 0 | 同上 `by_bucket`（≤20字 exact 24；21-40/41-60/>60 均 exact 0）+ 24 条 exact 行白文长度实测（max 11 字） |
| 既知の問題①文体 | 漢詩 **6.903**／詩経 **5.157**／故事 **20.861**／論語 **26.472** | 同上 `by_genre` |
| golden_4000 | 4000 組／白文ユニーク 3975（不变行） | `eval/golden_4000_stats.json` |
| golden_7908 | **7908 組**／白文ユニーク **7883**、已入库 | `eval/golden_7908_stats.json`（total 7908 = base 4000 + new 3908）+ `git ls-files eval`（golden_7908.json/.stats 均已跟踪） |
| 7908 全量规则实测（統合状況节） | avgDist **13.241**／exact **25**（n=7905、error 3） | `eval/night62_results_7908.json` summary |
| N62 guwenbert 对决（既知の問題⑦） | gwb **12.466** vs 規則 **12.577**、規則勝 1366／gwb 勝 1390／引分 1151 | `eval/night62_h2h.txt`（追加段 3908 条、双方可比 3907、双方 error 1=zasshi-2） |
| MERGE_WORDS | 21 語（不变行） | verify 脚本 |
| OCR GT / CER / 割注率 / 語釈 500 | 92 行／0.3568・0.3053／98.57・98.63・100／500 語（均不变行） | verify 脚本 + `len(GLOSSARY_LEXICON)` 实测 500 |
| 統合提交号 | `498cfcb`／`e576172`／`bdf3e77` | `REPORT_MERGE_62_64.md` §6 提交链 + `git log` |

## 3. 「未統合の作業ブランチ」节的处置（整节改写）

原节（含「どちらも別の作業クローンで検証中で、この README の数字はすべて統合前の
`master`…」一句）随合并事实整体过时，**整节改写**为「**ブランチ統合状況（Night 65 時点）**」：

- 节题去掉「未反映」表述，正文写明两分支已于 2026-11-21 并入 master
  （`498cfcb`＝night64-rulei、`e576172`＝night62-eval10000、文書同期后 HEAD=`bdf3e77`），
  并声明「数字」表全部为統合后 master 实测值；
- 两个分支条目改标「（統合済み）」，各保留一句核心事实 + 归档出处：
  night64→Rule I＋SHINJITAI 246、13.889→13.719／19→24（`eval/night64_results_4000.json`）；
  night62→golden_7908 入库、**默认口径仍 golden_4000**、7908 全量归档 13.241/25
  （`eval/night62_results_7908.json`）；
- guwenbert h2h 细数从本节移至既知の問題⑦（§4），避免一处数字两处维护。

## 4. known-issues 的两处数字同步（对合并报告 §7.3 的必要扩展）

`REPORT_MERGE_62_64.md` §7.3 写「known-issues 无需变（Rule I 不涉再読文字）」——该判断
只覆盖第 2 条（再読文字）。第 1 条引用的 **19/3998** 及分档/文体实数、第 7 条的
「Night 60 口径」在合并后已与「数字」节不一致（README 内部自相矛盾），本次按归档实数
同步：①改 24/3998 + night64 分档（≤20 字 3041 条・avg 7.74・exact 24；漢詩 6.903／
詩経 5.157 vs 故事 20.861／論語 26.472）；⑦补 N62 扩展段 3907 条 h2h 对决数。
第 2 条（再読文字「未」のみ）与其余各条未动，与 §7.3 判断一致。合并报告本身未改。

## 5. verify_readme_facts.py 的变更

- import 增加 `I_KANA_TO_KANJI`，打印行改为 `Rule E/F/G/H/I`（5/4/4/3/6）；
- night60 归档行替换为 `eval/night64_results_4000.json`（README 規則エンジン行的口径），
  打印 total/n/exact/avgDist/errors；
- 追加 `eval/golden_7908_stats.json` 打印（total/uniq_hakubun＋「默认评测口径仍 golden_4000」注明）；
- 其余（SHINJITAI_MAP / MERGE_WORDS / golden_4000 / OCR GT 行数 / 割注右先率基线）不变；
  只读性质不变；docstring 更新为 Night 65 合并后同步版。

## 6. 验收

- `D:\Python312\python.exe -m pytest tests -q` → **214 passed**（19.08s，开工核验；accept
  门内复跑一致）。
- `python tools/verify_readme_facts.py` 重跑输出（与 README「数字」节逐行对应）：
  `SHINJITAI_MAP: 246 对`／`MERGE_WORDS: 21 条`／`Rule E/F/G/H/I: 5/4/4/3/6`／
  `night64(golden_4000): total=4000 n=3998 exact=24 avgDist=13.719 errors=2`／
  `golden_4000: total=4000 uniq_hakubun=3975`／`golden_7908: total=7908 uniq_hakubun=7883`／
  `ocr_gt_100.tsv: 93 行（GT 92＋表头 1）`／`割注右先率基线: off=98.57% on=98.63% strict=100.0%`
  ——**全部对上**。
- `python tools/accept_night.py 65` → **PASS**（提交后终跑；eval_integrity 为 SKIP：Night 65
  未登记 NIGHT_ARTIFACTS，与 63/64 同口径，仅查 eval/golden.json；repo_clean 按 N60 惯例在
  干净树上运行）。
- 本地提交两个：主提交（README.md / tools/verify_readme_facts.py / SHIFT_LOG.md / 本报告）
  + wrap-up（ACCEPT_LOG.md + eval/accept_night_65.json）。**未推远程**。

## 7. 禁止事项自查

- 未改规则：`backend/kundoku_rules.py` 零触碰；未动 backend/ 其他文件、frontend/、tests/。
- 未改评测数据：golden*.json（含 golden_7908）、GT（ocr_gt_100.tsv）、night* 归档零触碰。
- 未动 ROADMAP.md（本夜任务由用户直接下达，任务书未含；Night 62–64 亦无 ROADMAP 条目，
  惯例一致）。
- README 数字全部现场取数（代码 import 实测、归档 JSON/TXT 读取、git ls-files/log 实物），
  未从记忆或合并报告第二手转抄。
- `SHIFT_LOG.md` 按惯例 UTF-8 二进制续写追加一行（历史混编码字节 0xF3@807 原样未触碰，
  旧字节零改动）。
- 未推远程；无新增临时文件入库（本班核对输出全部在会话内，未落 eval/）。

## 8. 待拍板（移交用户）

1. master 领先 origin/master **12** 个提交（合并班移交 10 + 本班 2），何时推送公开库由用户定。
2. `REPORT_MERGE_62_64.md` §7.3 的「known-issues 无需变」与本夜第 1/7 条数字同步并存——
   如需在该报告补一行勘误（「①⑦随 N65 同步、②维持」），由用户决定（本班未动该报告）。
