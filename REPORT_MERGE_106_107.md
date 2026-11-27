# REPORT_MERGE_106_107 — Night 108 合并夜：night106-mech-design ＋ night107-item4-impl 依次入 master

- 日期：2026-11-27（单会话・AutoClaw）
- 任务书：Night 108 任务书（合并夜・--no-ff 两次・字节安全并集・不合他处・不推远程）
- 分支起点（merge-base 双侧实测）：**f5e0bf3**（N105 wrap-up）
- 合并链：开工心跳 **304ebe2** → 合并 106 **bcb5cc7**（父 304ebe2＋f3c0779）→ 合并 107 **939598a**（父 bcb5cc7＋4b73d8f）

## §1 开工核验（合并前）

| 检查 | 任务书期待 | 实测 | 判定 |
|---|---|---|---|
| master HEAD | f5e0bf3（N105 wrap-up） | f5e0bf379cf71d66abb8bbf7544115a567938414 | ✓ |
| pytest tests -q | 484 passed | 484 passed（26.13s） | ✓ |
| 已跟踪文件零改动 | 空 | 空（status 仅有历史遗留 untracked：eval/ 缓存・ocr_samples 等，N106 §5 同款） | ✓ |
| night106-mech-design | 主 1f0ac2a＋链尾 f3c0779 | rev-parse＝**f3c0779**（tip＝wrap-up），链＝f3c0779←1f0ac2a←f5e0bf3 | ✓（注记 A） |
| night107-item4-impl | 主 acfa938＋链尾 4b73d8f | rev-parse＝**4b73d8f**（tip＝wrap-up），链＝4b73d8f←acfa938←f5e0bf3 | ✓（注记 A） |
| merge-base × 2 | 均为 f5e0bf3 | f5e0bf3 ／ f5e0bf3 | ✓ |
| origin/master | f5e0bf3 未变 | f5e0bf3 | ✓ |
| core.autocrlf / safecrlf | （实测） | true ／ 未设 | — |

**注记 A（记录偏差）**：任务书「git rev-parse night106-mech-design＝1f0ac2a 链尾 f3c0779」的写法把主提交列在 rev-parse 之后；实测 rev-parse 返回的是分支 tip＝wrap-up 提交（f3c0779／4b73d8f），主提交（1f0ac2a／acfa938）是其父。分支内容与任务书实质完全一致（各恰两提交、都自 f5e0bf3 分出），合并带入的提交集合无差。开工时工作区签出在 night107-item4-impl（N107 收工状态），已先 `git checkout master` 再做正式核验（此时 pytest 491 为分支值，master 上重跑为 484）。

移交阅读：REPORT_NIGHT106 §3（実施建議：項 4 实施／項 5 放弃／(c) 改设计棚上げ）与 REPORT_NIGHT107 §0（項 4 已实施・sim→真跑逐位一致・审计已清）——**两夜均无 step 0 报告修正**。

## §2 合并 1/2：night106-mech-design（报告-only 機構設計夜・2 提交）

`git merge --no-ff night106-mech-design` → **冲突恰 1 处＝SHIFT_LOG.md（UU）**；ACCEPT_LOG／ROADMAP 在 master 侧无改动（本夜心跳只动 SHIFT_LOG）＝git 自动合流取分支值；分支新文件 11 个（REPORT_NIGHT106.md・tools/night106_{dissect,wa_pos,guard_nxt}.py・eval/night106_{dissect,wa_pos,guard_nxt}.{json,txt}・eval/accept_night_106.json）原样带入。

SHIFT_LOG 字节账（全程纯字节操作・blob 全 CR-free 实测）：

| 项 | 字节 |
|---|---|
| base（f5e0bf3 blob） | 153,659 B（canary blob[807]=**63**・0 基） |
| ours（HEAD＝304ebe2） | 153,980 B＝base＋**N108 开工心跳 321 B**（单行 ASCII・`Night 108 heartbeat: 2026-11-27T03:46:09Z …`） |
| theirs（night106 tip） | 154,817 B＝base＋**N106 段 1,158 B**（4 行 heartbeat） |
| **union ＝ base＋N106＋N108hb** | **155,138 B LF**（夜序 106＜108・N106 marker@153659 ＜ N108hb@154817） |
| 工作副本（CRLF 化） | 156,188 B（canary wc[807]=**243**・写前后断言） |

暂存 blob 与 union **逐字节等价**断言通过（155,138 B・canary[807]=63）。提交 **bcb5cc7**（merge --no-ff・父 304ebe2＋f3c0779）。**pytest 484 passed（14.71s）**＝106 零产品代码实证。

## §3 合并 2/2：night107-item4-impl（項 4 実施夜・2 提交）

`git merge --no-ff night107-item4-impl` → **冲突恰 3 处＝SHIFT_LOG.md／ACCEPT_LOG.md／ROADMAP.md（均 UU）**；N107 产品改动自动进索引：backend/kundoku_rules.py（guard 元组 2 处）・README.md・tools/accept_night.py・tools/verify_readme_facts.py ＋ 新文件 11 个（tests/test_night107_item4_impl.py・tools/night107_{sim,eval_4000,eval_8165}.py・eval/night107_{sim.json,sim.txt,changed_rows.json,results_4000.json,results_8165.json}・eval/accept_night_107.json・REPORT_NIGHT107.md）。merge-base 复核＝f5e0bf3。

### 3.1 SHIFT_LOG（ours 侧差分跨夜＝N105 坑位③ 同型：按段拆分、theirs 插中间）

| 项 | 字节 |
|---|---|
| base（f5e0bf3 blob） | 153,659 B（canary[807]=63） |
| ours（HEAD＝bcb5cc7）差分 | 1,479 B＝**N106 段 1,158 B＋N108 心跳 321 B**（与合并 106 落盘的两段逐字节相等断言通过） |
| theirs（night107 tip）差分 | **2,627 B**（空行开头＋4 行 Night107 段；**末行无终止符**・见注记 B） |
| **union ＝ base＋N106＋N107＋接缝 1 B＋N108hb** | **157,766 B LF**（夜序 106＜107＜108・N106@153659 ＜ N107@154818 ＜ N108hb@157445） |
| 工作副本（CRLF 化） | 158,821 B（canary wc[807]=243） |

**注记 B（接缝字节）**：night107 分支 SHIFT_LOG blob 末行（Night107 wrap-up 行）无结尾 LF（N107 wrap-up amend 修哨兵时的遗留形态）。并集在 N107 段与 N108 心跳之间补 **1 个接缝 `\n`**，使 N108 心跳独立成行；两侧差分内容逐字节原样（除接缝外零改写）。该 1 B 已计入上方字节账。

### 3.2 ACCEPT_LOG（ours 侧＝N106 单夜・直接 ours 前 theirs 后）

| 项 | 字节 |
|---|---|
| base | 12,366 B |
| ours 差分 | 85 B＝N106 PASS 行（`| 2026-11-26T14:20:47 | 106 | PASS | fail=0 skip=1 | 28.7s | …`）＝与 night106 分支自身差分逐字节相等断言通过 |
| theirs 差分 | 170 B＝N107 FAIL 行＋N107 PASS 行（试跑 FAIL＝repo_clean 设计行为の记录・与 N107 分支自身差分相等） |
| **union** | **12,621 B LF**（夜序 106＜107）；工作副本 12,776 B CRLF |

### 3.3 ROADMAP

| 项 | 字节 |
|---|---|
| base | 51,403 B |
| ours 差分 | 1,551 B＝N106 行（＝night106 分支自身差分相等断言通过） |
| theirs 差分 | 1,999 B＝N107 行 |
| **union** | **54,953 B LF**（N106@51403 ＜ N107@52971）；工作副本 55,095 B CRLF |

三文件暂存 blob 与 union **逐字节等价**断言全过（SHIFT_LOG 157,766 B・canary[807]=63）。提交 **939598a**（merge --no-ff・父 bcb5cc7＋4b73d8f）。**pytest 491 passed（14.79s）**（484＋test_night107_item4_impl.py 7 条随合并生效）。

## §4 防回滚核查（合并内容原样・防回滚 grep）

- README：**491**／**13.460**／**13.466** 各恰 1 处＝N107 版数字行在位 ✓
- tools/verify_readme_facts.py：归档源＝night107・N107 guard 変体字断言在位（25 项版）✓
- tools/accept_night.py：107 条目在位（108 条目为登记阶段追加・见 §5）✓
- backend/kundoku_rules.py：guard 元组 2 处（Rule L がため・Rule M 何のごとく）随合并生效・規則数不変 ✓
- golden expected・词库・链序：一字未动（§5 双口径逐位一致実証）✓

## §5 数字与验收（详见 REPORT_NIGHT108）

pytest 484→484→491；golden_4000 **13.460／24／0**・golden_8165 **13.466／30／0**（均与 night107 归档全行逐位一致・8165 对照 night104 归档 diff 恰 2 行＝rikutou37-2 44→43・shiki050-4 25→20）；verify **25/25** exit 0；词库 **1531**（500＋291＋1031）不动；accept 108 终跑 PASS fail=0 skip=0（试跑 FAIL＝repo_clean 1 项＝设计行为・FAIL/PASS 两行留 ACCEPT_LOG）。

## §6 坑位与注记

1. **SHIFT_LOG blob 末行无终止符（N107 遗留）**→ 并集接缝 1 B（§3.1 注记 B）；其余两文件 theirs 差分均以 LF 收尾，无需接缝。
2. **ours 侧差分跨夜拆分**（N105 坑位③ 同型）：合并 107 的 SHIFT_LOG ours 差分＝N106 段＋N108 心跳两段，用合并 106 落盘的段字节做逐字节相等断言后重组，theirs（N107）插中间——不依赖文本标记搜索。
3. **任务书 rev-parse 记法偏差**（§1 注记 A）：tip＝wrap-up 提交，实质与任务书一致。
4. canary 均按 **0 基索引**实测（blob[807]=63／CRLF[807]=243・写前后断言・禁 1 基读数）；SHIFT_LOG 非纯 UTF-8（byte[807]=0xf3 GBK 形态历史区域）＝并集全程纯字节操作、禁整文件 decode。
5. 生成文（心跳・脚本・报告・提交消息）全程不出现 U+7232 旧字形（用描述性文字・ASCII 时间戳风格心跳）＝N107 坑位③ 防御。
6. 关键步骤分次 exec、禁 `;` 链带病提交（N100 教训）；无 reset 重做发生。
