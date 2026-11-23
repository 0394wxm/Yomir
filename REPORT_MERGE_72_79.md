# REPORT_MERGE_72_79.md — Night 81 合并班：规则链（72/73/78）＋词库链（74-79）→ master

## 1. 结论摘要

两个分支按任务书顺序合入 master，全程单会话、本地提交、未推远程：

```
cd2c123  Night 71 wrap-up（开工时 HEAD）
└ e90ce19  Night 81 心跳（开工核验，§5.3 显式提交）
   └ 96036e6  Merge branch 'night78-rulen'        ← 合并一：规则链 72/73/78（tip 95fa0ba）
      └ 76ded5a  Merge branch 'night79-lexicon-expand'  ← 合并二：词库链 74-79（tip 8d84613）
         └ ad72c0d  Night 81 登记（night81_eval_4000/8165＋归档＋NIGHT_ARTIFACTS[81]＋README 数字行）
            └ (wrap-up)  本报告＋REPORT_NIGHT81＋ACCEPT_LOG＋accept_night_81.json＋SHIFT_LOG
```

数字链：pytest **260 → 337（合并一）→ 393（合并二）**；golden_4000 两次合并后真跑均
**13.495 / exact 24 / error 0** 且与 night78_results_4000.json 逐位一致（0 行差异）；
golden_8165 真跑 **14.526 / exact 30 / error 0** 与 night78_results_8165.json 逐位一致；
词库 **500＋324＝824**。accept 81 **PASS（fail=0 skip=0，29.1s，首跑即过）**；
verify_readme_facts.py **18/18 exit 0**。

## 2. 开工核验（与任务书①逐项）

- 主仓 D:\kanbun-kakikudashi：`git log -1` = **cd2c123**（N71 wrap-up）✓
- `pytest tests -q` = **260 passed**（19.66s）✓
- 已跟踪文件零改动 ✓（`git status --porcelain -uno` 0 行；552 行输出全为未跟踪历史产物）
- clone D:\kanbun-rulel：night78-rulen = **95fa0ba** ✓、night79-lexicon-expand = **8d84613** ✓
- 已读 REPORT_MERGE_62_64.md §5（追加型日志字节安全并集、GIT_EDITOR=true、脏验收产物先原样提交）
  与 REPORT_NIGHT71.md §4（N71 落地状态）。
- 分支拓扑：night78-rulen 与 cd2c123 的 merge-base = ad18f20（N70）；词库链 tip 自带
  72/73 的副本提交（与规则链的同夜提交对象不同、日志段字节相同），与合并后 master 的
  merge-base = 807ad7d（N73 wrap-up 副本）——任务书「72/73 部分已合」即此。

## 3. Step 1：合 night78-rulen（规则链 72→73→78）

### 3a. 开工心跳与脏树处理

开工心跳先追加到 SHIFT_LOG，`git merge` 以「local changes would be overwritten」拒绝脏树；
按 §5.3 惯例先落显式提交 **e90ce19**（Night 81 心跳・开工核验），合并拿到干净日志文件。
事实备注：合并 pre-flight 触碰 SHIFT_LOG 时 autocrlf 把历史上 2 个裸 LF 行尾改写为 CRLF
（新行规范化后的内容与 cd2c123 版本逐字节等价，混编码字节 0xF3@807 未动，append-only 不变）。

### 3b. 冲突与解法（4 文件）

任务书预期冲突「只可能出在 SHIFT_LOG/ACCEPT_LOG」，实际 4 文件——多出的 2 个是
两分支对同一区域各自追加的文本冲突，均为并集语义，如实记录：

1. **SHIFT_LOG.md**：字节安全并集。ours 原字节＝CRLF 化 ours blob 重建（108,798 字节，
   byte807=243 逐字节验证）＋ theirs 相对 merge-base 的字节前缀差（3,833 字节 18 行，raw）。
   追加型不变量两侧均断言成立（base 是 ours/theirs 的公共字节前缀）。
2. **ACCEPT_LOG.md**：同法（ours blob ＋ theirs 前缀差 336 字节 4 行；全 LF 域）。
3. **ROADMAP.md**：文本并集——ours 的 N71 状态行在前，theirs 的 N72/73/78 状态行接后（夜序）。
4. **tools/accept_night.py**：NIGHT_ARTIFACTS 并集——71（N71 无新口径、复用 night70 归档）＋
   72/73/78 三条目并存（CRLF 字节级操作）。

### 3c. 合并后门禁（任务书③逐项）

- `pytest tests -q` = **337 passed**（12.93s）＝ 260＋23＋24＋30 ✓
- golden_4000 真跑（tools/night81_eval_4000.py，TestClient 完整链、monkeypatch save_kundoku，
  机制复用 night79_eval_4000.py）＝ **avgDist 13.495 / exact 24 / error 0**，
  与 night78_results_4000.json **逐位一致（0 行差异）** ✓（Rule N 口径）
- 合并提交 **96036e6**（--no-edit）。

## 4. Step 2：合 night79-lexicon-expand（词库链 74→75→76→77→79）

### 4a. 冲突与解法（3 文件；README / accept_night.py 自动并入）

本次是**分叉追加**：ours＝[71, 72, 73, 78]，theirs＝base(807ad7d)＋[74-77, 79]。
朴素尾部拼接会得到 71,72,73,**78**,74,75,76,77,79（78 行夜序错位），故按夜序插入：

1. **SHIFT_LOG.md**：ours 全字节保留（112,631）＋ 74-77 段插在 N78 段之前（边界＝ours 内
   `[2026-11-22T21:43 N78] Night 78 start` 行首，111,427，与 ours 的 72/73 段长度 2,629 精确吻合）
   ＋ 79 段接文件尾。结果 121,221 ＝ 112,631＋8,590（theirs 前缀差 29 行）。**byte807=243 未动**。
   关键验证：ours 侧 72/73 段与 base 追加段**字节完全相同**（11 行 2,629 字节），两分支
   72/73 日志无歧义，ours 版直接保留。
2. **ACCEPT_LOG.md**：同构夜序插入（9,860 ＝ 9,189＋671；74-77 的 accept 行插在 78 行前、
   79 行尾接）。
3. **ROADMAP.md**：文本并集重排为夜序 74, 75, 76, 77, 78, 79（ours 78 行插到 theirs 77 行后）。
4. README.md（N79 词库 824 行）与 tools/accept_night.py（NIGHT_ARTIFACTS 74/75/76/77/79）
   git 自动并入成功，无冲突。

### 4b. 合并后门禁（任务书④逐项）

- `pytest tests -q` = **393 passed**（13.01s）＝ 337＋24＋20＋12 ✓
- golden_4000 复跑 = **13.495 / 24 / 0** 逐位一致（0 行差异）✓（词库不进规则引擎，bit-exact 保持）
- golden_8165 真跑（tools/night81_eval_8165.py，同款机制）= **14.526 / exact 30 / error 0**，
  与 night78_results_8165.json 逐位一致 ✓
- 词库总数断言 **824 通过**：tests/test_night79_lexicon_expand.py 内 `N_BASE＋N_EXTRA==824`
  随 393 全绿；另独立 import 断言 `500＋324＝824` ✓
- 合并提交 **76ded5a**（--no-edit）。

## 5. 登记＋验收（任务书⑤）

- tools/night81_eval_4000.py → eval/night81_results_4000.json（默认口径归档）
- tools/night81_eval_8165.py → eval/night81_results_8165.json（8165 扩充归档，不登记默认口径）
- NIGHT_ARTIFACTS 加 `81: ["night81_results_4000.json"]`（仅此一条，CRLF 字节级插入）
- README 数字行同步：表头＝**76ded5a**（合并后 master 提交）、pytest **393 passed**、
  Rule N 口径（13.495/24/4000）、词库 824 語（随词库链已并入，核对无漂移）
- tools/verify_readme_facts.py **无需改动**（pytest 期望为 --collect-only 动态计算＝393；
  归档源切换无必要——本夜无新口径，登记现行链尾）
- verify 重跑：**18/18 对上、exit 0** ✓
- accept_night.py 81：**PASS（fail=0 skip=0，29.1s）**，首跑即过（登记先落提交，repo_clean 干净），
  eval/accept_night_81.json 在库，ACCEPT_LOG 一条 PASS 留痕（本班无 FAIL 行——首跑即 PASS）。

## 6. 提交号链与远程状态

- master 提交链见 §1；`git rev-list --count origin/master..HEAD` 见 REPORT_NIGHT81.md §⑤。
- **未推远程**（用户手推）。
- N79 待拍板两项（同語彙条目 3 条、Wikipedia/Wiktionary 8 条）按现状随词库链合入，
  用户另有决定再单开修复夜（任务书①明示）。

## 7. 禁止事项自查

- 规则与词库文件零改动（backend/kundoku_rules.py、glossary_lexicon*.py 只随分支合入，本班未编辑）✓
- golden expected 一字未改（4000/8165 双口径逐位一致即证）✓
- 未进 D:\kanbun-eval10k / D:\kanbun-eval 等无关目录；仅 fetch 自任务书指定的 D:\kanbun-rulel ✓
- 允许编辑清单外未碰任何文件（报告/工具/日志/README 表头数字行/ROADMAP 均在清单内）✓
- 禁 OCR、禁 guwenbert 全量 ✓（本班仅 TestClient 双口径真跑）
