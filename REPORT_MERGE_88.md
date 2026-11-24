# REPORT_MERGE_88 — night88-rulep 合并专报（Night 91，主仓合并夜）

## 1. 合并对象与几何

- 合并对象：`night88-rulep`（Night 88＝Rule P 挖规则**零规则夜**，自 master 35ba6e5 分出；主提交 **4cd618c**＋wrap-up **c651617**；accept 88 PASS fail=0 **skip=1**（skip=eval_integrity 报告-only＝N69/N74/N76 先例））。
- merge-base：**35ba6e5**（N87 wrap-up）。N88 分出后 master 已前进六提交（N89 词库频次 2 区两提交 d95afe3/76c678b＋N90 合并夜四提交 94966a6/edd8ce8/8c977ca/59bb299），base 落后是预期。
- 合并方式：开工心跳 **7422211** 先行提交 → `git merge --no-ff night88-rulep -m "Merge night88-rulep"` 单次完成 → 合并提交 **1ea1566**。

## 2. 冲突 3 处（追加-追加）与字节安全并集明细

master 侧（N89/N90）与分支侧（N88）自共同基线 35ba6e5 后都只做尾部追加，三文件双侧均 startswith(base)＝纯追加成立 → 按 REPORT_MERGE_62_64 §5／REPORT_MERGE_89 §3 方法论做 **theirs＋d_ours** 字节并集（夜序 N88 段在前・N89/N90 段在后，绝不文本三路合并）：

| 文件 | base blob | ours blob（7422211） | theirs blob（c651617） | d_theirs（N88 侧） | d_ours（master 侧） | union blob（暂存） | 工作副本（CRLF 化） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SHIFT_LOG.md | 130,770 B（纯 LF） | 134,693 B | 132,206 B | **1,436 B**（11:03 开工〜收尾段） | **3,923 B**（N89 五行 12:31–14:24＋N90 两行 14:49–15:15） | **136,129 B** | 137,131 B |
| ACCEPT_LOG.md | 10,524 B | 10,690 B | 10,607 B | **83 B**（`| 2026-11-24T11:31:39 \| 88 \| PASS \| fail=0 skip=1 \| 30.5s \|` 1 行） | **166 B**（N89 14:21:50・N90 15:13:15 各 1 行） | **10,773 B** | 10,906 B |
| ROADMAP.md | 36,772 B | 37,352 B | 37,734 B | **962 B**（Night 88 状態: DONE 行） | **580 B**（Night 89 状態: DONE 行；N90 合并夜无 ROADMAP 行） | **38,314 B** | 38,447 B |

断言链（全通过）：
1. 三 blob 纯 LF（无 \r\n、无孤立 \r）＋ `ours.startswith(base)`／`theirs.startswith(base)`；
2. union＝theirs＋d_ours＝base＋d_theirs＋d_ours，夜序 N88→N89→N90（N88 11:03–11:31 早于 N89 12:31–14:24 早于 N90 14:49–15:15）；
3. 工作副本 CRLF 化写入，SHIFT_LOG **byte807=243 写前后断言**（0xF3@807 混编码字节原样保留）＋写后复读逐字节一致＋冲突标记 0；
4. `git add` 后 `git show :0:<file>` 暂存 blob＝union **逐字节等价断言**（N87 加保险步骤沿用）后才 commit；
5. `git status` 无残留 UU／AA。

## 3. 合并带入清单（分支侧文件，只接受分支版本）

- **M（冲突并集）3**：SHIFT_LOG.md／ACCEPT_LOG.md／ROADMAP.md（上表）。
- **A（分支新文件）16**：REPORT_NIGHT88.md；eval/accept_night_88.json、eval/night88_combo_changed_rows.json、eval/night88_mine.{json,txt}、eval/night88_probe.{json,txt}、eval/night88_results_4000.json、eval/night88_results_8165.json、eval/night88_sim.{json,txt}；tools/night88_eval_4000.py、tools/night88_eval_8165.py、tools/night88_mine.py、tools/night88_probe.py、tools/night88_sim.py。
- 其余全部自动合并、取 **master 版**（分支侧未动）：README.md（N89/N90 数字行）、tools/accept_night.py（NIGHT_ARTIFACTS[89][90]）、backend/glossary_lexicon_extra2.py（1031）、tests/test_night79/80/82/89、tools/night89_* 9 个・night90_eval_* 2 个、eval/night89_*／night90_* 归档、REPORT_NIGHT89/90・REPORT_MERGE_89 等。

## 4. N88 内容对照（合并即阴性证明）

- 零规则夜：Rule P **0 条**收录、backend/kundoku_rules.py 一字未改、SHINJITAI 0 対、tests 无新文件（分支时 pytest 434＝当时基线；合并后 master 443＝434＋N89 的 9，与本夜预期一致）。
- 分支内阴性证明归档（eval/night88_results_4000/8165.json）与 night87 归档逐位一致（13.491/24/0・13.502/30/0）；本夜合并后 master 全量真跑再次确认与 **night90** 归档逐位一致（diff 0 行×2）——N89 词库扩充＋N88 零规则合并叠加后引擎输出零变化。
- N88 拒案复核数字与 N86/N72 完全一致（るべ 91/7・べきか 25/2・べからず 79/5・べからざる 79/1・なかれ 13/1 kokyo09-5・はざる blanket 24shihin10-4 1 変差）；Rule O 三键残量 0。

## 5. 合并前后对照表（master）

| 项 | 合并前（59bb299） | 合并后（1ea1566） | 变化 |
| --- | --- | --- | --- |
| pytest | 443 passed | **443 passed** | 0（零规则无新测试） |
| golden_4000 | 13.491／24／0 | **13.491／24／0**（与 night90 归档 diff 0 行） | 0 |
| golden_8165 | 13.502／30／0 | **13.502／30／0**（与 night90 归档 diff 0 行） | 0 |
| 词库 | 1531（209＋291＋1031） | **1531**（同・N88 未碰） | 0 |
| verify | 19/19 | **19/19 exit 0** | 0 |
| 规则引擎 | Rule A〜O | Rule A〜O（kundoku_rules.py 一字未改） | 0 |
| 仓库内容 | — | ＋N88 分支 19 文件（3 M 并集＋16 A）＋夜四提交 | 仅追加 |

## 6. 遗留

- N88 §7 移交项（べきなり族拍板级候補・して→問す 判別実例・N86 拍板事项・长尾 scan 枯渇判断）随合并原样带入 master，待用户拍板，本夜未动。
- NIGHT_ARTIFACTS **不登记 88**（零规则夜＝accept_night.py L247-249 既定 skip 机制）；91 照常登记 `91: ["night91_results_4000.json"]`。
- 未推远程：origin/master＝59bb299，本夜链 7422211→1ea1566→5e13057→wrap-up 待用户手推。
