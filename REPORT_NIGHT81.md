# REPORT — Night 81（合并夜：规则链 72/73/78 ＋ 词库链 74-79 入 master）

## ① 开工核验

- HEAD = **cd2c123**（N71 wrap-up）✓；`pytest tests -q` = **260 passed**（19.66s）✓；
  已跟踪文件零改动 ✓。
- clone D:\kanbun-rulel：night78-rulen = **95fa0ba** ✓、night79-lexicon-expand = **8d84613** ✓。
- 方法论输入：REPORT_MERGE_62_64.md §5（追加型日志字节安全并集／GIT_EDITOR=true／脏产物先提交）、
  REPORT_NIGHT71.md §4（N71 落地状态：260 passed、NIGHT_ARTIFACTS[71] 登记 night70 归档）。

## ② 取分支

主仓 `git fetch D:\kanbun-rulel` 后以 refspec 建本地分支引用，SHA 与 clone 一致
（95fa0ba／8d84613）。拓扑：night78-rulen 与 master merge-base=ad18f20（N70）；
词库链自带 72/73 副本提交（与规则链同夜提交对象不同、SHIFT_LOG 72/73 段字节相同），
与合并后 master merge-base=807ad7d（N73 wrap-up）。

## ③ 规则链合并（72→73→78）

- 开工心跳按 §5.3 先落显式提交 e90ce19（merge 拒绝脏树）。
- `git merge night78-rulen --no-edit` → 冲突 4 文件：SHIFT_LOG/ACCEPT_LOG（字节安全并集：
  ours 原字节＋theirs 相对 base 字节前缀差 3,833／336 字节）＋ ROADMAP（N71 行＋N72/73/78
  行夜序并集）＋ accept_night.py（NIGHT_ARTIFACTS 71 与 72/73/78 并集）。任务书预期 2 文件、
  实际 4 文件，均为两分支同区域追加的并集语义，如实记录（详见 REPORT_MERGE_72_79.md §3）。
- 门禁：pytest **337 passed**（＝260＋23＋24＋30）；golden_4000 真跑 **13.495／24／0**
  与 night78 归档逐位一致（0 行差异）。
- 合并提交 **96036e6**。

## ④ 词库链合并（74→75→76→77→79）

- `git merge night79-lexicon-expand --no-edit` → 冲突 3 文件（README/accept_night.py 自动并入）。
  SHIFT_LOG/ACCEPT_LOG 为**分叉追加**：ours=[71,72,73,78]、theirs=base＋[74-77,79]，
  按夜序插入（74-77 段插在 N78 段前、79 段尾接；ours 72/73 段与 base 追加段字节相同，
  ours 版保留）；SHIFT_LOG 结果 121,221＝112,631＋8,590，**byte807=243 未动**。
  ROADMAP 重排为夜序 74,75,76,77,78,79。详见 REPORT_MERGE_72_79.md §4。
- 门禁：pytest **393 passed**（＝337＋24＋20＋12）；golden_4000 复跑 **13.495／24／0** 逐位一致；
  golden_8165 真跑 **14.526／30／0** 逐位一致；词库 **500＋324＝824** 断言通过（测试内＋独立 import）。
- 合并提交 **76ded5a**。

## ⑤ 登记＋验收

- tools/night81_eval_4000.py（复用 night79_eval_4000 机制：TestClient 全量真跑＋与链尾归档
  逐位一致断言）→ **eval/night81_results_4000.json**；tools/night81_eval_8165.py 同款 →
  eval/night81_results_8165.json（扩充归档，不登记默认口径）。
- NIGHT_ARTIFACTS 加 `81: ["night81_results_4000.json"]`（仅此一条）。
- README 数字行同步：表头＝**76ded5a**、pytest **393 passed**、Rule N 口径（13.495／24／4000）、
  词库 **824 語**。tools/verify_readme_facts.py 无需改动（pytest 期望动态计算；无新口径）。
- verify 重跑：**18/18 对上，exit 0**。
- accept 81：**PASS（fail=0 skip=0，29.1s）**，首跑即过（登记先落提交 ad72c0d，repo_clean 干净）；
  eval/accept_night_81.json 在库；ACCEPT_LOG 一条 PASS（本班无 FAIL）。
- 提交：合并 96036e6＋76ded5a、心跳 e90ce19、登记 ad72c0d、wrap-up（本报告＋REPORT_MERGE_72_79
  ＋SHIFT_LOG＋ACCEPT_LOG＋accept_night_81.json）；`git rev-list --count origin/master..HEAD` = 27；
  **未推远程**。

## 已知问题（本夜新增/延续）

- 本班无新口径（合并夜）：golden_4000 维持 13.495／24／0（Rule N 口径）、golden_8165 维持
  14.526／30／0，均与 night78 链尾归档逐位一致；night81_results_4000.json 为回归证据归档。
- N79 待拍板两项（同語彙条目 3 条、Wikipedia/Wiktionary 8 条）随词库链按现状合入，
  用户另有决定再单开修复夜（任务书①明示）。
- git autocrlf 在合并 pre-flight 触碰 SHIFT_LOG 时将 2 个历史裸 LF 行尾规范为 CRLF
  （内容逐字节等价、0xF3@807 未动、append-only 不变）——后续夜班触碰该文件时仍会出现
  「LF will be replaced by CRLF」警告，属同源现象，不新增风险。
- （延续）夜间主机休眠会冻结/重试后台进程：长跑挂机需 resume 安全设计（本班单进程真跑
  ≤4 分钟×3 次，未触发）。
