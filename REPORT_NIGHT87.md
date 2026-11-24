# REPORT_NIGHT87 — 合 N86 进 master（AutoClaw，主仓合并夜，night87 单会话）

## 0. 结果一句话

night86-ruleo（N86 Rule O 3 条，15001cd＋596687f）以 `--no-ff` 合入 master：冲突 1 文件（SHIFT_LOG.md 追加-追加，字节安全并集解消、byte807=243 前后断言）；合后 pytest **434 passed**、golden_4000 **13.491/24/0** 与 night86 归档逐位一致、golden_8165 **13.502/30/0** 与 night86 归档逐位一致（Rule O 3 条＝8 行 4000 改写＋15 行 8165 改写随合并生效）、词库 1301 实证、verify 19/19 exit 0（分支版 19 项为准）、accept 87 **PASS fail=0 skip=0**（30.9s 首跑即过）。

## 1. 开工核验

master HEAD = d4738a5 ✓；分支 tip = 596687f ✓；merge-base = d4738a5 ✓（N86 自 master 直分，无 clone 中转、无需 fetch）；pytest 422 passed ✓；已跟踪文件零改动（untracked 仅历史 eval/ 缓存）✓。前置阅读：REPORT_NIGHT86 §0/§5/§7（Rule O 3 条・12 tests・13.491/13.502・移交）与 REPORT_MERGE_84 §3（字节安全并集方法论）确认済み。

## 2. 合并与冲突

- 提交链：d4738a5 → **03c2de4**（开工心跳）→ **994f530**（merge --no-ff）→ **f025adc**（登记）→ 本 wrap-up。
- 冲突 **1** 文件：SHIFT_LOG.md（master 侧 N87 心跳 1 行 vs 分支侧 N86 心跳 3 行，均纯尾部追加）。字节安全并集：base=d4738a5 blob、ours=03c2de4、theirs=596687f，`startswith(base)` 双向断言通过，工作副本按 CRLF 化 blob＋deltas 重建（131,050 B、byte807=243 写前后断言）、夜序 N86 三行＋N87 一行、分支行零改动（暂存 blob＝theirs＋d_ours 130,062 B 等价断言通过）。ACCEPT_LOG／README／ROADMAP／verify_readme_facts／kundoku_rules.py git 自动合并成功（README テスト行取分支值 434）。

## 3. 合后验证（数字是死的，逐项对）

- pytest tests -q：**434 passed**（=422＋N86 的 12：tests/test_night86_rule_o.py）✓
- golden_4000 全量真跑（tools/night87_eval_4000.py）：**13.491／24／0** 与 night86_results_4000.json 逐位一致、diff 0 行（不是 N85 的 13.495——8 行改写正是本夜合入的 Rule O 改进）✓ → 归档 eval/night87_results_4000.json（NIGHT_ARTIFACTS[87]）
- golden_8165 全量真跑（tools/night87_eval_8165.py）：**13.502／30／0** 与 night86_results_8165.json 逐位一致、diff 0 行（不是 N85 的 13.505——15 行改写随合并生效）✓ → 归档 eval/night87_results_8165.json（扩充归档，不登记默认口径）
- 词库 1301 条不动（N86 未碰词库）：import 实证 GLOSSARY_LEXICON 500＋extra.py 291（词形全部本体子集）＋LEXICON_EXTRA2 801＝唯一词形 1301（本体独有 209＋291＋801、与 extra2 零交集）✓
- tools/verify_readme_facts.py：**19/19 exit 0** ✓（N86 分支版 19 项为准：Rule O 語数断言＋归档源 night78→night86 切换；master 旧版 18 项作废）
- README 同步：数字行已随合并取分支值（テスト 434、4000 数 13.491、8165 数 13.502、規則エンジン行 Rule O 3 語・ルールチェーン Rule O 句）；数字节表头 →「Night 87 合并：Rule O 3 条（主 15001cd＋wrap-up 596687f）・合并提交 `994f530`」——数字与 header 同一提交（f025adc）改完 ✓

## 4. 验收（⑤）

- NIGHT_ARTIFACTS 加 `87: ["night87_results_4000.json"]`；accept 87 **PASS fail=0 skip=0**（30.9s，登记后首跑即 PASS，七门全绿：repo_clean／pytest 434=434／eval_integrity（night87_results_4000.json 実查：id 唯一・自报数一致・expected 未改）／rule_regression／engine_smoke／perf_envelope／order_rate（off 98.57%・on 98.63%、退化页 0））。
- 本地提交（登记 f025adc＋wrap-up），**未合其他分支、未推远程**。

## 5. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages／词库一字未改 ✓
- 允许清单内文件のみ（accept_night.py 仅 NIGHT_ARTIFACTS 一条、README 仅数字行＋header hash、分支文件只接受分支版本）；合并冲突文件只接受分支版本＋字节安全并集（SHIFT_LOG），未手动改逻辑 ✓
- 无 OCR、无 guwenbert、无 eval 以外网络 ✓；SHIFT_LOG 纯追加惯例保持 ✓
