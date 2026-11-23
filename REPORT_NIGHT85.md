# REPORT_NIGHT85 — 合 N84 进 master（AutoClaw，主仓合并夜，night85 单会话）

## 0. 结果一句话

night84-empty-got（N84 empty-got 249 行修，9fbb5b0＋6e5661e）以 `--no-ff` 合入 master：冲突 1 文件（SHIFT_LOG.md 追加-追加，字节安全并集解消、byte807=243 前后断言）；合后 pytest **422 passed**、golden_4000 **13.495/24/0** 与 night83 归档逐位一致、golden_8165 **13.505/30/0** 与 night84 归档逐位一致（N84 改进随合并生效）、词库 1301 实证、verify 18/18 exit 0、accept 85 **PASS fail=0 skip=0**（31.3s 首跑即过）。

## 1. 开工核验

master HEAD = dce1ba6 ✓；分支 tip = 6e5661e ✓；merge-base = dce1ba6 ✓（N84 自 master 直分）；pytest 415 passed ✓；已跟踪文件零改动 ✓。

## 2. 合并与冲突

- 提交链：dce1ba6 → **3dbb3f1**（开工心跳）→ **c35fce7**（merge --no-ff）→ **1ff3c15**（登记）→ 本 wrap-up。
- 冲突 **1** 文件：SHIFT_LOG.md（master 侧 N85 心跳 1 行 vs 分支侧 N84 心跳 4 行，均纯尾部追加）。字节安全并集：base=dce1ba6 blob、ours=3dbb3f1、theirs=6e5661e，`startswith(base)` 双向断言通过，工作副本按 CRLF 化 blob＋raw suffix 重建（129,117 B、byte807=243 写前后断言）、夜序 N84 四行＋N85 一行、分支行零改动。ACCEPT_LOG／README／ROADMAP git 自动合并成功（README テスト行取分支值 422）。

## 3. 合后验证（数字是死的，逐项对）

- pytest tests -q：**422 passed**（=415＋N84 的 7）✓
- golden_4000 全量真跑（tools/night85_eval_4000.py）：**13.495／24／0** 与 night83_results_4000.json 逐位一致、diff 0 行 ✓ → 归档 eval/night85_results_4000.json（NIGHT_ARTIFACTS[85]）
- golden_8165 全量真跑（tools/night85_eval_8165.py）：**13.505／30／0** 与 night84_results_8165.json 逐位一致、diff 0 行（不是 N83 的 14.526——这正是本夜合入的改进）✓ → 归档 eval/night85_results_8165.json（扩充归档，不登记默认口径）
- 词库 1301 条不动：import 实证 GLOSSARY_LEXICON 500（词形全唯一）＋LEXICON_EXTRA2 801（词形全唯一）＋零交集＝1301 ✓
- tools/verify_readme_facts.py：**18/18 exit 0** ✓
- README 同步：数字节表头 →「Night 85 合并…・合并提交 `c35fce7`」、テスト行 422（合并带入）、新增 golden_8165 行 13.505／30/8165、4000 数 13.495 不变——数字与 header 同一提交（1ff3c15）改完 ✓

## 4. 验收（⑤）

- NIGHT_ARTIFACTS 加 `85: ["night85_results_4000.json"]`；accept 85 **PASS fail=0 skip=0**（31.3s，登记后首跑即 PASS，七门全绿）。
- 本地提交（登记 1ff3c15＋wrap-up），**未合其他分支、未推远程**。

## 5. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages／规则引擎／词库一字未改 ✓
- 允许清单内文件のみ；合并冲突文件只接受分支版本＋字节安全并集（SHIFT_LOG），未手动改逻辑 ✓
- 无 OCR、无 guwenbert、无 eval 以外网络 ✓；SHIFT_LOG 纯追加惯例保持 ✓
