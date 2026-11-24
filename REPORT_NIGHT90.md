# REPORT_NIGHT90 — 合 N89 进 master（AutoClaw，主仓合并夜，night90 单会话）

## 0. 结果一句话

night89-lexicon-freq2（N89 词库频次 2 区 top500 全判定入库 230・1301→1531，d95afe3＋76c678b）以 `--no-ff` 合入 master：冲突 1 文件（SHIFT_LOG.md 追加-追加，字节安全并集解消、byte807=243 前后断言）；合后 pytest **443 passed**、golden_4000 **13.491/24/0** 与 night89 归档逐位一致、golden_8165 **13.502/30/0** 与 night89 归档逐位一致（词库不进规则引擎＝数字不动是预期）、词库 **1531** 实证（209＋291＋1031）、verify 19/19 exit 0、accept 90 **PASS fail=0 skip=0**（30.1s 首跑即过）。N88 零规则分支 night88-rulep 本夜不合、其文件一字未动。

## 1. 开工核验

master HEAD = 35ba6e5 ✓；分支 tip = 76c678b ✓；merge-base = 35ba6e5 ✓（N89 自 master 直分，无 clone 中转、无需 fetch）；pytest 434 passed ✓；已跟踪文件零改动（untracked 仅历史 eval/ 缓存）✓。前置阅读：REPORT_NIGHT89 §0/§3/§6（入库 230・分组・偏差注记）与 REPORT_MERGE_86 §3（字节安全并集方法论）确认済み。

## 2. 合并与冲突

- 提交链：35ba6e5 → **94966a6**（开工心跳）→ **edd8ce8**（merge --no-ff）→ **8c977ca**（登记）→ 本 wrap-up。
- 冲突 **1** 文件：SHIFT_LOG.md（master 侧 N90 心跳 1 行 vs 分支侧 N89 心跳 5 行，均纯尾部追加）。字节安全并集：base=35ba6e5 blob（130,770 B）、ours=94966a6、theirs=76c678b，`startswith(base)` 双向断言通过，工作副本按 CRLF 化 union blob 重建（134,099 B、byte807=243 写前后断言）、夜序 N89 五行＋N90 一行、分支行零改动（暂存 blob＝theirs＋d_ours＝133,103 B 等价断言通过）。ACCEPT_LOG／README／ROADMAP／glossary_lexicon_extra2.py（801→1031）／accept_night.py（NIGHT_ARTIFACTS[89]）／tests×4／tools/night89_*×9／eval/night89_* 全部 git 自动合并成功（README テスト行取分支值 443・词库数 1531）。

## 3. 合后验证（数字是死的，逐项对）

- pytest tests -q：**443 passed**（=434＋N89 的 9：tests/test_night89_lexicon_freq2.py）✓
- golden_4000 全量真跑（tools/night90_eval_4000.py，night89 版克隆・基线换 night89 归档）：**13.491／24／0** 与 night89_results_4000.json 逐位一致、diff 0 行 ✓ → 归档 eval/night90_results_4000.json（NIGHT_ARTIFACTS[90]）
- golden_8165 全量真跑（tools/night90_eval_8165.py）：**13.502／30／0** 与 night89_results_8165.json 逐位一致、diff 0 行 ✓ → 归档 eval/night90_results_8165.json（扩充归档，不登记默认口径）
- 词库 **1531 条**：import 实证 GLOSSARY_LEXICON **500**（N89 未碰本体）＋extra.py **291**（词形全部本体子集）＋LEXICON_EXTRA2 **1031**（801→1031）＝唯一词形 209＋291＋1031＝**1531**（extra2 与本体零交集）✓
- tools/verify_readme_facts.py：**19/19 exit 0** ✓（N89 未加 verify 断言，19 项为准）
- README 同步：数字行已随合并取分支值（テスト 443、語釈辞書 1531 語×2 处・本文 1531 語、4000 数 13.491、8165 数 13.502）；数字节表头 →「Night 90 合并：词库频次 2 区 230 条（主 d95afe3＋wrap-up 76c678b）・合并提交 `edd8ce8`」——数字与 header 同一提交（8c977ca）改完 ✓

## 4. 验收（⑤）

- NIGHT_ARTIFACTS 加 `90: ["night90_results_4000.json"]`；accept 90 **PASS fail=0 skip=0**（30.1s，登记后首跑即 PASS，七门全绿：repo_clean／pytest 443=443／eval_integrity（night90_results_4000.json 実查：id 唯一・自报数一致・expected 未改）／rule_regression／engine_smoke／perf_envelope／order_rate（off 98.57%・on 98.63%））。
- 本地提交（登记 8c977ca＋wrap-up），**未合其他分支（night88-rulep 未动）、未推远程**。

## 5. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages／词库文件一字未改 ✓
- 允许清单内文件のみ（accept_night.py 仅 NIGHT_ARTIFACTS 一条、README 仅数字行＋header hash、night90_* 工具与归档为本夜产物、分支文件只接受分支版本）；合并冲突文件只接受分支版本＋字节安全并集（SHIFT_LOG），未手动改逻辑 ✓
- 无 OCR、无 guwenbert、无 eval 以外网络 ✓；SHIFT_LOG 纯追加惯例保持 ✓
