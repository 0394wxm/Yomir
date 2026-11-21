# REPORT_MERGE_62_64.md — 分支合并班：night64-rulei + night62-eval10000 → master

日期: 2026-11-21 16:42 班（合并专项，GLM-5.3-Flash 周末卡）
任务书: **合分支，不做新功能，不改规则、不改评测数据**。①开工核验 ②先合 night64-rulei
（rebase→解冲突→pytest 211→accept 64 重跑 PASS→合并提交）③再合 night62-eval10000
（rebase→解冲突→pytest 实跑→accept 62 重跑 PASS→合并提交）④本报告，不推远程。

---

## 1. 结论摘要

- **两个分支全部合入 master**：合并提交 `498cfcb`（N64）→ `e576172`（N62）。
  master 终态 `pytest tests -q` = **214 passed**（= 193 master 基线 + N64 的 18 + N62 的 3）。
- **规则与评测数据零改动**：`backend/kundoku_rules.py` 的变更只来自 N64 分支原样重放
  （Rule I + SHINJITAI 99 对）；golden*.json / GT / night60 归档均为分支原样带入，
  master 侧从未触碰。
- 全程**未推远程**（本班结束时 master 领先 origin/master **9 个提交**，见 §6）。
- 发现一处**合并后文档漂移**（未动，留拍板）：README「数字」节的 SHINJITAI 147 /
  pytest 193 / 分支状态节已被合并事实超越（代码现为 246 对 / 214 tests / 两分支已合入），
  详见 §7。

## 2. 开工核验（主仓 D:\kanbun-kakikudashi）

| 检查 | 结果 |
| --- | --- |
| `git log -1` | `dd9d24c`（N61 wrap-up）✓ 与任务书预期一致 |
| `pytest tests -q` | **193 passed**（15.04s）✓ |
| `master` vs `origin/master` | **两者同为 dd9d24c** —— 用户在本班开始前已把 N61 推上公开库（origin=github.com/0394wxm/Yomir.git）。本班之后的新提交再次领先 origin，是否推送由用户决定 |

两个 clone 状态：rulei（branch `night64-rulei` @ `6c2d69a`，origin=D:/kanbun-kakikudashi，
identity=wang，ocr_runtime/src 存在）；eval10k（branch `night62-eval10000` @ `7f24446`，
origin 同，identity=qa，ocr_runtime/src 存在）。**两个 clone 的 merge-base 都是 `b370761`**
（即都从 N63/N61 之前分叉）。

## 3. Step 1：合 night64-rulei（Rule I + SHINJITAI 246）

### 3a. 分支整形（rebase 前）
- clone 有 N64 会话**遗留未提交的验收产物**：`M ACCEPT_LOG.md`（+2 行：64 FAIL 13:00:13 →
  64 PASS 13:09:09）+ `?? eval/accept_night_64.json`（verdict PASS, checked_at
  2026-11-21T13:09:09, checks=[pass,pass,skip,pass,pass,pass,pass]）。rebase 要求干净树
  → 先按分支原样补提交为 `82cf982`（accept 输出 txt 保持未跟踪惯例）。分支 tip=82cf982。

### 3b. rebase 到 master（dd9d24c）
- 1/2（N64 主提交 6c2d69a）：干净重放 → `0ef3da0`。
- 2/2（验收产物 82cf982）：**ACCEPT_LOG.md 内容冲突**（master 侧有 N61 的 1 行 PASS 行，
  分支侧追加 64 FAIL/PASS 两行，双方 EOF 追加）→ **行级并集**（ours 92 行 + 分支 2 行，
  每行时间戳唯一无误并风险）→ `d53a964`。
- 技术注记：`git rebase --continue` 对冲突提交会拉起编辑器，非交互终端下 vim 失败
  （`Error reading input`）→ 用 `GIT_EDITOR=true`（Git for Windows usr/bin/true.exe）
  非交互继续，消息沿用原提交。

### 3c. 门禁（在 rebased 分支上，rulei clone 内实跑）
| 检查 | 结果 |
| --- | --- |
| `pytest tests -q` | **211 passed**（23.35s）——与任务书预期 193+18=211 一致 |
| `accept_night.py 64` | **PASS**（fail=0 skip=1，37.0s；pytest 门 211 passed = 211 collected；rule_regression/engine_smoke/perf 16ms/order_rate 98.57/98.63 退化 0 全过；eval_integrity SKIP=N64 未登记 NIGHT_ARTIFACTS，与原分支跑法同口径） |
- 重跑产物（ACCEPT_LOG 新行 + 重写的 accept_night_64.json）提交为 `cd2f0ee`。

### 3d. 合并提交
- `git fetch D:\kanbun-rulei night64-rulei` + `git merge --no-ff` → **`498cfcb`**
  （27 文件，+55,300 行：kundoku_rules.py +90、tests/test_night64_rule_i.py 155 行、
  REPORT_NIGHT64.md 210 行、eval/night64_* 归档一批）。
- 合并后 master 复跑 pytest：**211 passed**（18.35s）。

## 4. Step 2：合 night62-eval10000（golden_7908 归档 + QA 审计）

### 4a. rebase 到新 master（498cfcb，已含 N64）
- eval10k clone 身份 config 为 qa（QA 会话所设）→ 本班改设 wang/wang@localhost 作为
  **rebase committer**（作者字段原样保留：0c2c5e5/fd81eea=zwork、dac3f90=qa）。
- 1/3（主提交 7da8fbb）：**SHIFT_LOG.md 内容冲突**。该文件含历史混编码字节
  （0xF3@807，项目明文规矩：只许二进制追加、不许读全文重写）→ **字节安全并集**：
  master 侧 776 行原字节不动 + 分支新增（空行 + QA 心跳行 12:55）追加。
  过程纠错：首版行级去重把分支追加的**空行分隔符**误吞（该空行与文件中既有空行同形）
  → 复核 staged 内容后按 7da8fbb 原字节把空行补回 QA 行前（staged 777→778 行），
  保真分支原格式 → `0c2c5e5`（45 文件，+202,778：golden_7908.json 等，作者 zwork 保留）。
- 2/3（wrap-up c716e41）：**ACCEPT_LOG.md 内容冲突**。取证：c716e41 在**原分支历史里对
  ACCEPT_LOG.md 是零改动**（其版本=父提交版本=7358 字节），冲突纯因 master 侧已前进
  → 解法=保留 master 侧 7608 字节原样 + 分支侧 0 追加 → `fd81eea`
  （REPORT_NIGHT62.md 187 行 + eval/accept_night_62.json；SHIFT_LOG.md 本轮 git
  auto-merge 干净通过）。评估：N62 的 accept62 运行行**从未入过分支的 ACCEPT_LOG**
  （分支侧该文件自 b370761 起未变）——历史原样，不补造。
- 3/3（QA 提交 7f24446）：干净重放 → `dac3f90`。
- 3 个 QA 探针脚本（night62_koji_check/sample_pages/sitemap_inventory.py）维持
  **未跟踪**（QA 会话移交时的原状，是否入库=既有拍板项）。

### 4b. 门禁（在 rebased 分支上，eval10k clone 内实跑）
| 检查 | 结果 |
| --- | --- |
| `pytest tests -q` | **214 passed**（16.00s）——= 211（含 N64）+ N62 的 3（test_golden_7908.py）。任务书给的 196 是「只合 N62 不含 N64」口径（193+3）；任务书明示「如有测试叠加，以实跑为准」，实跑=214 |
| `accept_night.py 62` | **PASS**（fail=0 skip=1，38.9s；rule_regression/engine_smoke/perf/order_rate 98.57/98.63 退化 0 全过） |
- 重跑产物提交为 `624193e`。

### 4c. 合并提交
- `git fetch D:\kanbun-eval10k night62-eval10000` + `git merge --no-ff` → **`e576172`**
  （49 文件，+203,279 行：golden_7908.json 47,450 行、night62_results_7908.json
  71,491 行、REPORT_NIGHT62.md / REPORT_NIGHT62_QA.md、test_golden_7908.py 等，
  全部为归档/报告/测试，无 backend 规则变更）。
- 合并后 master 终态复跑 pytest：**214 passed**（21.30s）。

## 5. 本班方法学沉淀（可复用）

1. **追加型日志文件（SHIFT_LOG/ACCEPT_LOG）的 rebase 冲突**：不要用文本三方合并，
   用「ours 原字节 + theirs 相对其父提交的字节前缀差」精确追加；SHIFT_LOG 因混编码
   字节**只能**这么做。行级集合去重会把与既有空行同形的分隔行误吞（本班实际踩到并补救）。
2. 非交互环境跑 rebase：预先 `set GIT_EDITOR=true` 并把 `D:\Git\usr\bin` 加进 PATH。
3. clone 有未提交验收产物时先按原样补提交成显式 commit，再 rebase——rebase 不接受脏树，
   且这些产物本就该随分支走。
4. 合并顺序按任务书先 N64 后 N62，使 N62 的 rebase 直接落在含 Rule I 的 master 上，
   一次性暴露「测试叠加」终态（214）。

## 6. 提交号链与远程状态

```
dd9d24c (origin/master == 用户已推)
└ 498cfcb  merge night64-rulei
   ├ 0ef3da0 night64: Rule I + SHINJITAI 246（分支主提交重放）
   ├ d53a964 night64: 补提交验收产物（重放）
   └ cd2f0ee night64: rebase 后 pytest 211 / accept64 重跑 PASS
└ e576172  merge night62-eval10000
   ├ 0c2c5e5 night62: golden_7908（作者 zwork）
   ├ fd81eea night62: wrap-up（作者 zwork）
   ├ dac3f90 night62-QA: 审计报告（作者 qa）
   └ 624193e night62: rebase 后 pytest 214 / accept62 重跑 PASS
+ 本报告提交（REPORT_MERGE_62_64.md + SHIFT_LOG 行）
```

`git rev-list --count origin/master..master` = **9**（报告提交后为 10）。**未推远程**。

## 7. 合并后事实漂移（如实记录，未动，留拍板）

`tools/verify_readme_facts.py` 在合并后 master 上实跑输出：**SHINJITAI_MAP: 246 对**
（合并前 147）。由此，N61 刚重写的 README 出现以下过时点——**本班按任务书边界未改**，
需要用户点头后由下一班做一次「合并后文档同步」：

1. 「数字」节：SHINJITAI_MAP 147→**246**；pytest 193→**214**；规则链应加 **Rule I**
   （6 条かな→漢字、白文护栏）；可补 golden_7908 已入库的事实（评测归档口径仍以
   golden_4000 为默认基线，N62 的 7908 是扩充归档）。
2. 「未統合の作業ブランチ」节整体过时：两分支已合入 master，节内数字（13.241/25、
   13.719/24/pytest211）已成为 master 事实，节应改写或删除。
3. known-issues 无需变（Rule I 不涉再読文字）。
4. master 领先 origin 10 个提交，何时再推公开库由用户定。

## 8. 禁止事项自查

- 未改规则：`backend/kundoku_rules.py` 的全部变更来自 N64 分支原样重放，master 侧
  零手改；合并不产生新的规则逻辑。
- 未改评测数据：golden.json / golden_4000 / GT（ocr_gt_100.tsv）/ night60 归档在 master
  侧零触碰；分支带入的 golden_7908 等为其原样归档（其 expected 在 N62 侧已由
  QA 审计 47/47 现场抽查核过）。
- 未做新功能；未动 backend/、frontend/ 的 master 侧文件。
- 冲突解决只涉及 ACCEPT_LOG.md / SHIFT_LOG.md 两个日志文件的**追加并集**，且
  SHIFT_LOG 旧字节（含 0xF3@807）逐位未动。
- 未推远程；临时脚本放在 %TEMP%（不入库）。

## 9. 证据文件（未跟踪，按惯例留档）

- 主仓：eval/merge61_pytest_start.txt（开工 193）、eval/merge64_pytest_master.txt（合并 N64 后 211）、
  eval/n62rebase_pytest.txt 在 eval10k clone、eval/merge62_pytest_master.txt（终态 214）、
  eval/merge62_facts.txt（合并后 SHINJITAI 246 取证）
- rulei clone：eval/n64rebase_pytest.txt（211）、eval/n64rebase_accept.txt（PASS）
- eval10k clone：eval/n62rebase_pytest.txt（214）、eval/n62rebase_accept.txt（PASS）
