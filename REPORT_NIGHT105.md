# REPORT_NIGHT105 — 合并夜：N102＋N103＋N104 三分支顺序合入 master

AutoClaw・2026-11-26・单会话。分支＝master 本夜直做（心跳＋三合入＋登记＋wrap-up 共 6 提交）；**未推远程**（用户手推）。合并专题明细见 REPORT_MERGE_102_103_104.md。

## 1. 开工核验

- master＝origin/master＝`67b0d73`（N101 wrap-up）✓；`pytest tests -q`＝**476 passed**（24.16s）✓；已跟踪文件零改动 ✓。
- 三分支 tip＝`0b2cb1e`（night102-kotonaku-guard）／`638e004`（night103-kotonaki-sim）／`df1ea55`（night104-ruleu）＝任务书一致 ✓；三 merge-base 全＝`67b0d73` ✓（git rev-parse 一次多 rev fatal＝N95 坑位、逐个取）。
- 移交阅读：REPORT_NIGHT102 §6（项 8 guard 拡張拍板候補消滅＝无益拒・per-guard 変体 3 行改善在庫 Δ−0.000367・残拍板項顺位更新）／REPORT_NIGHT103 §4（三向统一收益相同・site 字形＝文脉正确活用形・**拍板建议不统一不实施**・正攻法＝機構側項 4/5）／REPORT_NIGHT104 §6（verify 归档源 night99→night104 注记・必要伴随 2 件）＋§8（坑位 4 条・移交清单）✓。

## 2. 三依次合并（每合一次验一次）

- 开工心跳 `b35a779`（merge 前落位＝N100 坑位①）。
- **合 1/3 N102**（merge `09ac09c`）：SHIFT_LOG 1 文件冲突（master 侧 N105 心跳 440 B vs theirs N102 段 1,036 B）→ 字节安全合流 149,221 B LF；ACCEPT_LOG/ROADMAP 自动合流。pytest **476** ✓。
- **合 2/3 N103**（merge `3311840`）：冲突 3 文件 → 合流 SHIFT_LOG 150,992／ACCEPT_LOG 12,111／ROADMAP 50,339 B。pytest **476** ✓。
- **合 3/3 N104**（merge `eaa4c01`）：冲突 3 文件 → 合流 SHIFT_LOG 152,942／ACCEPT_LOG 12,281／ROADMAP 51,403 B；README/verify/accept_night.py/backend/tests/eval 自动取 N104 版。pytest **484** ✓。
- 夜序（実測核对）：SHIFT_LOG N102（行 1034–1036）→N103（1037–1039）→N104（1040–1043）→N105（1044）／ACCEPT_LOG 102＜103＜104（FAIL/PASS 两行都留）／ROADMAP Night 102→103→104。canary blob `[807]`=63／CRLF `[807]`=243 双形断言（0 基索引・每次合流写前后＋暂存 blob 等价断言＋冲突标记 0）。

## 3. 登记・终验

- 登记 `9aeb2a3`：NIGHT_ARTIFACTS 加 `105: ["night104_results_4000.json"]`（**登记口径沿用 N104 归档**）；102/103 报告-only 不补登记（N91/N101 先例・accept_night.py L247-249 skip 机制）。
- 终验（只对 night104 归档）：pytest **484 passed**（16.21s）・golden_4000 TestClient 全量 **diff 0 行**／13.460／24／0・golden_8165 **diff 0 行**／13.467／30／0（合并＝引擎零改动実証）・词库 209+291+1031＝**1531**・verify **24/24 exit 0**（N104 版）。
- 终验对照工具注记：任务书允许编辑清单未含 `tools/night105_eval_*.py`＝「其余文件一律不碰」→ 双口径全量对照用 **workspace 临时脚本**执行、不落盘仓库（结果记录于本报告＋REPORT_MERGE_102_103_104.md §4）。

## 4. 验收

- accept 105：**PASS fail=0 skip=0**（首跑即过・七门全绿・pytest 484=484）——工作树 tracked 干净（报告为 untracked 不触发 repo_clean）＝无需設計行為重跑（N96/N100 条款备用未触发）。
- 六提交：`b35a779`（开工心跳）＋`09ac09c`（合 N102）＋`3311840`（合 N103）＋`eaa4c01`（合 N104）＋`9aeb2a3`（登记 105）＋wrap-up（本提交）。rev-list 超前 origin＝**12**（6 本夜＋6 分支提交）。
- 产品代码/词库/golden expected/tests/README/verify 在合并夜零改动（唯一内容变化＝三 append-only 日志合流＋accept_night.py 登记 1 行）；102/103 分支带入内容原样、104 的 Rule U 原样生效（484・13.460/13.467 维持）。

## 5. 坑位・移交

- 坑位①：SHIFT_LOG canary「byte807」是 **0 基索引**（blob `[807]`=63・CRLF `[807]`=243）；按 1 基读 `[806]` 得 26/40＝断言落空。任务书数字照抄前先实测定位。
- 坑位②：SHIFT_LOG 行格式夜间不统一——N102/N103 段行首＝「Night 102 heartbeat: …」（英文・带空格），N104 段＝「Night104 …」（中文连写）。行序核对不能只 grep 一种字样，须按实际段行目检。
- 坑位③： ours 侧 delta 跨夜混合（旧 N 段＋新 N105 心跳）时，简单 theirs+d_ours / ours+d_theirs 都会破坏夜序——按 N105 marker 拆分 ours delta、theirs 插中间（本夜実装・合 2/3 与 3/3 采用）。
- 坑位④：合并夜 eval 工具（night101 型）本夜任务书清单未允许→临时脚本执行并如实注记；次合并夜若清单允许，照 night101 型落盘（基线＝当夜登记归档・全行 diff=0 断言）。
- 移交（N98 §3 决策表 残・原样带入 master 未动）：4/5＝機構設計夜（rikutou26-5 語順構造差行・守り字後続字 guard 拡張機構〔N103 未実装〕）・7＝嗟や在庫（Δ−0.000367）・9＝剥夹注管线・N84 残渣 2 行・echo 30 行・項 6/8 在庫（N103 判不实施/N102 判无益・毋系 4 行 Δ−0.000490 のみ）。
- 次夜建议：機構設計夜 4/5（守り字後続字 guard 拡張機構の設計から）か报告-only 夜；等用户手推 origin/master（本夜 12 提交待推）。
