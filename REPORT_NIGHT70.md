# REPORT_NIGHT70 — Rule K backend 上线 ＋ 信長公記巻之中导入

日期：2026-11-22（Night 70 挂机段）
开工 HEAD：`9cbb6b9`（N69 wrap-up 点）；分支 master；未推远程。

## 0. 结果一句话

**Rule K 8 条按 N69 §6 移交表上线** `backend/kundoku_rules.py`（接 Rule J 链尾）；TestClient 双口径真跑与 N69 离线数**逐位一致**——golden_4000 **avgDist 13.584／exact 24／改写 467／改善 290／变差 0**、golden_8165 **avgDist 14.632／exact 30／改写 768／改善 402／变差 0**；accept 70 **PASS（fail=0 skip=0）**（NIGHT_ARTIFACTS[70] 登记，N68/N69 的 eval_integrity skip 缺口本夜闭合）；备选④信長公記巻之中（PID 781193，34 页）导入＋逐页核对 PASS。

## 1. 开工核验

- HEAD=9cbb6b9 ✓、tracked 零改动 ✓、pytest 241 passed ✓、SHIFT_LOG byte807=243 ✓
- 已读 REPORT_NIGHT69.md §4–§6（Rule K 收录判定／真跑数／移交表）与 REPORT_NIGHT63.md（整本导入方法＋N63 §4 GT CER 论证链）

## 2. Rule K 上线（②）

- `backend/kundoku_rules.py` 新系列 K：`K_KANA_TO_KANJI` 8 条（序＝COMBO_ORDER：hite→hete→hazu→hezu→iyashikumo→nanzo_kan→nanzo_gei→nanzo_katsu）＋`K_LONGER_WORDS`（8 条全部无更长词冲突＝空壳，维持系列同构）＋`style_kana_to_kanji_k`；`style_fix_with_hakubun` 链尾在 J 之后追加 K
- **guard=() 无条件语义显式化**：E〜J 世代的条件式 `if hb and not any(...)` 遇空 guard 时 `any(())=False` → 恒常 skip（＝死规则）。K 系列改为 `if guard and hb and not any(...)`——guard 空＝白文不问适用；**未用恒真字符串伪装 guard**（任务书红线），由 test 锁定（`test_rule_k_empty_guard_is_not_dead_rule`）
- Xぞ族 3 条共享 kana「なんぞ」、白文 guard（盍/奚/曷）互斥（N69 probe 実測多守り行＝無し）；上线后 test 复测互斥（`test_rule_k_nanzo_*` 5 项）＋真跑改写行集合与预测双向 0 差（见 §3）
- 拒案 4 条（はざる→わざる／とも→と／がため→が為に／つひに→ついに）**不上线**，死因（変差行对位・guard 0 命中・exp 无目标字形）写入 K 块注释代码内存档
- `tests/test_night70_rule_k.py` **19 项**：仮名遣い族各条正反例＋空 guard 语义锁＋Xぞ族互斥/无守り不动/多守り先胜＋表整形性＋拒案不复活＋链序 J→K＋幂等＋现代句探针＋`はず` 已知局限如实锁定
- 全量 pytest：**260 passed**（241＋19）

## 3. 真跑对照（③，与 N69 离线逐位一致）

- `tools/night70_eval.py`（night68_eval 同款机制：TestClient 完整后端链＋monkeypatch save_kundoku，单进程双口径顺序跑）
- 断言全过：
  - golden_4000：改写 **467＝预测 467**／改善 **290**／变差 **0**／avgDist **13.584**／exact **24**（N68 基线 13.684→K 后 -0.100）
  - golden_8165：改写 **768＝预测 768**／改善 **402**／变差 **0**／avgDist **14.632**／exact **30**（N68 基线 14.698→K 后 -0.066）
  - 双向 diff：预测有实跑无 **0**／实跑有预测无 **0**；error→恢复 **0**／仍 error **0**（N68 双口径 0 error 保持）
  - 进程内确定性自证：8165 前 4000 行与 4000 单跑输出**逐位一致**
- 归档：`eval/night70_results_4000.json`／`eval/night70_results_8165.json`（schema 同 N68：total/summary(by_bucket·by_genre)/results＋diff_ids_vs_n68）
- **GT CER 逐位不变**（结构性证明，N63 §4 同款论证链）：OCR/GT 链的全部输入文件（`eval/night68_gt_cer.json`、`eval/night49_gt_lines.json`、`eval/ocr_gt_100.tsv` 等）tracked 逐位未动（git status 空），本夜唯一产品代码改动＝`kundoku_rules.py` 的訓読显示层（OCR 管线不经过）→ CER raw **0.3568**／norm **0.3053** 逐位不变
- order_rate 零退化：accept 70 实测 off **98.57%**／on **98.63%**（差 +0.00pp，退化页 0）

## 4. 备选④：信長公記巻之中导入（N63 方法）

- manifest：**34 pages**（信長公記. 巻之中，NDL PID 781193；巻之上 781192＝51 页的续卷。Night 6 把 781193 误记「巻之下」，N63 已订正为巻之中——本夜导入与之一致）
- `tools/import_pid.py 781193`：下载 34/34（页图缓存 pages/，不入库）→ OCR → 訓読 → `eval/import_pid_781193/book.md`（**[done] ok=34 skip=0**，OCR 合计 958.0s／訓読 36.3s）
- `tools/night70_verify_book.py`（N63 verify 同口径；manifest 页数验证时实取 dl.ndl.go.jp，避免硬编码漂移）→ `eval/night70_verify.json`：**manifest=34＝下载页图 34＝book.md 页段 34** 三者一致、**ok=34/34、0 行页=0、OCR 失败=0**、纯 ASCII 噪声行 **0 行**、book.md sha256[:16]＝**95bb006c8d3ac7b5**
- 页图不入库（.gitignore 的 pages/ 下，N63 同款）

## 5. 验收与提交（⑤）

- `tools/verify_readme_facts.py`：**14/14 OK exit 0**（新增 Rule K 語数断言「**8 語**」；比对源从 night68_results_4000.json 切换到 night70_results_4000.json——README 数字行更新后旧期望值必 FAIL 的必要伴随，见 §6-4）
- README 数字行 4 处：数字节头（2026-11-22 時点・Night 70）、規則エンジン行（**13.584**／**24/4000**＋N70 Rule K 追加注记＋口径出处 night70_results_4000.json）、ルールチェーン行（Rule K 第 7 系列・**8 語**追加：仮名遣い 4 条無条件＋苟くも＋なんぞ三分）、已知問題①（24/4000 N70 口径、≤20字 3043 条 avg **7.695**、文体別漢詩 **6.884**／詩経 **5.108**／故事 **20.608**／論語 **26.138**）
- `tools/accept_night.py`：NIGHT_ARTIFACTS 加 `70: ["night70_results_4000.json"]`（仅此一条）→ accept 70 终跑 **PASS（fail=0 skip=0，30.6s）**：repo_clean／pytest 260=260／eval_integrity（night70_results_4000.json 实查：id 唯一・expected 未被改）／rule_regression／engine_smoke／perf_envelope／order_rate 全 PASS。首跑 FAIL（repo_clean＝主提交前 SHIFT_LOG 心跳未提交——N68/N69 同款已知形态）→ 主提交后重跑 PASS，FAIL 记录如实留存 ACCEPT_LOG.md
- 提交：主提交 `60912db`（backend/kundoku_rules.py、tests/test_night70_rule_k.py、tools/night70_eval.py・night70_verify_book.py・verify_readme_facts.py・accept_night.py、README、ROADMAP 末尾一行、SHIFT_LOG、eval/night70_results_*.json）＋ wrap-up（REPORT_NIGHT70.md・SHIFT_LOG・ACCEPT_LOG・eval/accept_night_70.json・eval/import_pid_781193/book.md・eval/night70_verify.json）；本夜 rev-list 计数＝2；未推远程

## 6. 偏差注记

1. exact 前后不变（24/24・30/30）＝K 的改写全部为距缩短或持平，无一变差（N69 sim 预测与真机逐位一致）——变差 0 门在真机复现
2. README 数字节头写「Night 70」不带 commit hash——wrap-up hash 无法自引用（N68b 同款处理）；統合状況节的 9fca166 表述是历史事实句，保持不动
3. `はず→わず` 无条件规则的已知局限（现代和文「来るはず（筈）」型输入也会被转换）写入代码注释＋test 如实锁定；本管线对象＝漢文訓読输出（筈义不出现）、语料内 8165 条実測 0 変差
4. verify 断言源切换（night68→night70 归档）超出「仅 Rule K 计数行」的字面——是 README 数字行更新的必然伴随（旧期望 13.684 对新 README 必 FAIL），如实记录
5. 巻之中 34 页——N63「单卷 ~45 分钟」估计以内（实测 OCR 合计 958s≈16 分钟）；verify_book 首跑在页图号解析处 exit 1（`int(f[1:])` 未去 .jpg 扩展名的拼接 bug）→ 修正（`f[1:-4]`）后 PASS，修正随 wrap-up 提交
6. N63 式图像对照抽检 6 页未做（任务书本夜口径＝结构性核对；積分预算克制）
7. 每周 1 万积分 2026-11-22 23:59 过期——本夜工具用量克制：无 web_search/fetch_content/图片/视频生成，全部本地执行
