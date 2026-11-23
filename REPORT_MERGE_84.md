# REPORT_MERGE_84 — 合并 night84-empty-got 进 master（Night 85，主仓合并夜）

## 1. 结论摘要

- 合并完成：master dce1ba6 →（3dbb3f1 开工心跳）→ **c35fce7**（merge --no-ff night84-empty-got，即 9fbb5b0 主提交＋6e5661e wrap-up）→ **1ff3c15**（登记）→ 本 wrap-up。
- 冲突 1 文件：SHIFT_LOG.md（追加-追加）→ 字节安全并集（REPORT_MERGE_62_64 §5 / N83 惯例：CRLF 化 blob＋raw suffix 重建、byte807=243 前后断言、绝不文本三路合并）解消；ACCEPT_LOG／README／ROADMAP 全部 git 自动合并成功。
- 门禁全绿：pytest **422 passed**（415＋N84 7）；golden_4000 真跑 **13.495 / exact 24 / error 0** 与 night83 归档逐位一致（diff 0 行）；golden_8165 真跑 **13.505 / exact 30 / error 0** 与 night84 归档逐位一致（diff 0 行——**不是 N83 的 14.526，13.505 正是本夜合入的 N84 改进**）；词库 **500＋801＝1301**（零交集）import 实测复核；verify_readme_facts **18/18 exit 0**；accept 85 **PASS（fail=0 skip=0，31.3s，登记后首跑即 PASS）**。

## 2. 开工核验

- `git checkout master`：HEAD = dce1ba6 ✓；`git log -1 night84-empty-got` = 6e5661e ✓；`git merge-base master night84-empty-got` = dce1ba6 ✓（N84 自 master 直分，无 clone 中转、无需 fetch）；pytest 415 passed ✓；已跟踪文件零改动 ✓。

## 3. 合并与冲突解法（主仓）

- 开工心跳先行提交（3dbb3f1，merge 拒绝脏树），随后 `git merge --no-ff night84-empty-got -m "Merge night84-empty-got"`。
- 冲突：仅 **SHIFT_LOG.md**（UU，追加-追加：master 侧 N85 心跳 1 行 vs 分支侧 N84 心跳 4 行，共同基线 dce1ba6 之后双方都在尾部追加）。
- 解法（字节安全并集，python 二进制，绝不文本三路合并）：
  - base = `git show dce1ba6:SHIFT_LOG.md`（126,808 B）、ours = `HEAD`（127,050 B）、theirs = `6e5661e`（127,898 B），三 blob 均纯 LF、断言 `ours.startswith(base)`／`theirs.startswith(base)`（双方都是纯追加）；
  - delta_theirs = 1,090 B（N84 四行：18:20 开工／18:40 根因定性／18:55 修法验证／18:58 收尾）、delta_ours = 242 B（N85 开工心跳 20:46）；
  - 工作副本形态按 N83 §5 惯例重建：**CRLF 化 base blob＋raw suffix**（`base.replace(b"\n", b"\r\n") + d_theirs + d_ours`），写前后断言 **byte807=243**（blob 形态该位为 63，243 是 CRLF 化工作副本形态的既定口径）；写后复读 129,117 B 逐字节一致；
  - 夜序并集：N84 四行在前、N85 心跳收尾，分支行零改动（`merged == theirs + d_ours` 等价断言）。
- 其余文件全部自动合并成功并核验：README テスト行自动取分支值 **422 passed**；ROADMAP 尾部自动接到 N84 行；ACCEPT_LOG 尾部自动接到 N84 PASS 行。
- 合并提交：**c35fce7**（`git log --oneline -4`：c35fce7 → 3dbb3f1 → 6e5661e → 9fbb5b0，符合预期链）。

## 4. 合并后门禁（关键口径：4000 与 night83 归档比、8165 与 night84 归档比）

| 检查 | 结果 |
| --- | --- |
| pytest tests -q | **422 passed**（415＋N84 的 7：tests/test_night84_empty_got.py）✓ |
| golden_4000 全量真跑（tools/night85_eval_4000.py） | **13.495 / exact 24 / error 0**，与 night83_results_4000.json 输出差异 **0 行** → `eval/night85_results_4000.json`（默认口径，NIGHT_ARTIFACTS[85]）✓ |
| golden_8165 全量真跑（tools/night85_eval_8165.py） | **13.505 / exact 30 / error 0**，与 night84_results_8165.json 输出差异 **0 行** → `eval/night85_results_8165.json`（扩充归档，不登记默认口径；不是 N83 的 14.526——N84 改进已随合并生效）✓ |
| 词库 | import 实测：GLOSSARY_LEXICON **500**（词形全唯一）＋LEXICON_EXTRA2 **801**（词形全唯一）＋零交集＝唯一词形 **1301**；N84 未碰词库 ✓ |
| verify_readme_facts | **18/18 exit 0** ✓ |
| accept 85 | **PASS fail=0 skip=0**（31.3s，登记提交后首跑即 PASS，七门全绿）✓ |

## 5. 登记（⑤）与提交链

- 登记（1ff3c15）：NIGHT_ARTIFACTS 加 `85: ["night85_results_4000.json"]`＋eval 归档（night85_results_4000/8165）＋eval 工具（night85_eval_4000/8165）＋README 同步（数字行与 header 同一提交改完）。
- README 同步内容：数字节表头 →「Night 85 合并：N84 ruby 夹注 kana 分流 fallback（主 9fbb5b0＋wrap-up 6e5661e）・合并提交 `c35fce7`」；テスト行 **422 passed**（合并自动带入）；**新增 golden_8165 行 13.505／30/8165**（N84 改进；扩充归档口径、默认口径 golden_4000 13.495/24/4000 不变）。
- 提交链：dce1ba6 → 3dbb3f1（心跳）→ c35fce7（merge --no-ff）→ 1ff3c15（登记）→ 本 wrap-up。**未合其他分支、未推远程**。

## 6. 事实漂移与遗留（如实，未动，留拍板）

- 无冲突遗留；SHIFT_LOG 混编码字节 0xF3@807（CRLF 工作副本形态）原样保留。
- N84 移交项原样带入 master：含（）但假名占比 ≤0.3 的 8 行（rikutou59-2／soji07-6 等）kanbun 分支夹注残渣出力未动；KANBUN_KANA_RATIO 口径未改；sonshi09-38 无尾段保持空串；≤8 字尾段 30 行为白文直出（note 标注 N84）。

## 7. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages 一行未动 ✓；规则引擎/词库文件一字未改 ✓
- 允许清单内文件のみ（accept_night.py 仅 NIGHT_ARTIFACTS 一条、README 仅数字行＋header、分支文件只接受分支版本）✓
- SHIFT_LOG 纯追加＋字节安全并集（byte807=243 前后断言）✓；无 OCR／guwenbert／eval 以外网络 ✓
- 未合其他分支、未推远程 ✓

## 8. 证据

- eval/night85_results_4000.json（[OK] 与 night83 逐位一致 13.495/24/0、diff 0 行）
- eval/night85_results_8165.json（[OK] 与 night84 逐位一致 13.505/30/0、diff 0 行）
- eval/accept_night_85.json（verdict PASS fail=0 skip=0 31.3s）
- ACCEPT_LOG.md N85 PASS 行；SHIFT_LOG N85 段（开工/合并/登记/收尾）
