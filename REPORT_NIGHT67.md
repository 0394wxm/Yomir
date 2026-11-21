# REPORT_NIGHT67

## 0. 一句话结论

四个拍板项全部落地（顺序 ⑬→⑲→⑭→⑩）：⑬ 后端 2 行 AUX「應」runtime 补丁（golden_4000
error 2→0、avgDist **13.716**／exact **24**、既有 3998 行逐位 diff=0）；⑲ paren 257 对启用
（**golden_8165** = 7908+257，前缀逐字节一致、expected 一字未改，规则全量 8165 条
error 0／exact 30／avgDist 14.741，guwenbert h2h 规则 255／gwb 1／平 1）；⑭ 默认口径登记
NIGHT_ARTIFACTS[67]=night67_results_4000.json（eval_integrity 由 skip 转 PASS）；⑩ 否决结案
零代码。pytest **219**（215+1+3），accept 67 **PASS**（fail=0 skip=0），本地 master 两提交
**f4376ac**＋wrap-up，未推远程。

## 1. 开工核对

- `git log -1` = `920866d`（= origin/master，ahead 0）✓；pytest **215 passed**（12.3s）✓；
  已跟踪文件零改动 ✓。
- 承接调研（N59/N62/N64 归档）：⑬ 病根＝`udkundoku/auxiliary.py` AUX 25 键缺
  「應,v,助動詞,必要,*」（值照抄同 xpos 須）；⑨/⑭ 登记制＝`tools/accept_night.py`
  NIGHT_ARTIFACTS；⑲ 257 对 paren 在 `eval/night62_scraped_10k.json`（`_quality=="paren"`，
  预检：内部零重复、与 7908 前缀零冲突、expected 含應=0、白文含應=10）。
- 期间两次安全审查拦截（rule=scope_escalation）已由用户消息显式批准解除后继续。

## 2. ⑬ AUX 补丁（后端 2 行，site-packages 一行未动）

- **病根**（N59 定位，N57 定性修正）：MeCab 词典有「應」token 且 lemma 归一为應，
  缺的是 udkundoku AUX 活用表条目——任何含助動詞用法「應」的输入都会让整条 API
  请求 KeyError('應,v,助動詞,必要,*') →「訓読処理失敗」。
- **改动**：`backend/main.py` `_load_engine()` 内 2 行 runtime 补丁（附 3 行注释说明病根）：

  ```python
  import udkundoku.auxiliary as _aux_mod
  _aux_mod.AUX["應,v,助動詞,必要,*"] = _aux_mod.AUX["須,v,助動詞,必要,*"]
  ```

  幂等、进程内、N59 拍板路径 a；`tools/night67_guwenbert_new.py` 进程内加同款补丁
  （N62 §5 实证 guwenbert 与规则路径共享 kundoku 翻译层、同行同败，需同口径）。
- **回归测试**：`tests/test_night67_aux_ying.py` 1 条（含應输入不再 500/KeyError）。
- **golden_4000 全量重跑**：`tools/night67_eval_4000.py`（TestClient 完整后端链＝补丁经
  `_load_engine()` 生效，108s）→ `eval/night67_results_4000.json` + `eval/night67_eval_4000.txt`：
  - **n=4000、errors=0（2→0）、exact=24、avgDist=13.716**；
  - 确定性对照 vs `night64_results_4000.json`：既有 3998 行逐位 **diff=0**；error 恢复恰好
    `['toushisen043-16','toushisen135-12']`（135-12 dist=4，与 N59 内存探针预测
    「黄の綺心を知るべし」逐字一致；043-16 dist=13）；
  - 分档/文体如实：≤20字 7.741（24 条精确全在此档）、21-40字 21.476、41-60字 36.692、
    >60字 63.143；漢詩 6.905／故事 20.861／論語 26.472（新恢复 2 行入档）。

## 3. ⑲ paren 257 对启用（golden_8165 三件套）

### 3.1 数据面

- 来源：`eval/night62_scraped_10k.json` 的 `_quality=="paren"` 257 对（N57 当初以质量原因
  拒绝；本夜拍板启用），字段 id/source_url/hakubun/expected_kakikudashi/_src/_quality。
- 构建：`tools/night67_build_golden.py` → `eval/golden_8165.json`（**total 8165 = 7908+257**）
  + `eval/golden_8165_stats.json`；**skipped {}（零丢弃）**；uniq_hakubun 8140。
- 硬断言（构建时全部通过）：expected 逐字段一字不改（**⑲ 红线：257 对 expected 零改写**）；
  前 7908 条与 `golden_7908.json` 逐条 dict 相等；前缀 LF 归一后逐字节一致（工作树
  golden_7908.json 是 CRLF＝autocrlf checkout 伪差，blob 是 LF，字节断言按
  `.replace(b"\r\n", b"\n")` 归一后比对）；新增段 id 唯一、白文零重复。
- 新增段构成：字数 21-40字 17／41-60字 12／>60字 228；文体 漢詩 24／その他 222／
  故事 5／論語 6；栏目 shibu02 168／shibu01 31／syubu 24／syubu02 23／keibu 6／koji 5。
- 双保险测试：`tests/test_golden_8165.py` 3 条（shape 8165／前缀逐条一致／provenance 溯源）。

### 3.2 规则全量

- `tools/night67_eval_8165.py` → `eval/night67_results_8165.json` + `eval/night67_eval_8165.txt`：
  **TOTAL n=8165 errors=0 exact=30 avgDist=14.741**。
- 新增段 [7908:8165)：**257/257 OK、error 0、exact 0、avgDist 65.704**（>60字 228 条
  avg 72.184——paren 白文含ルビ括号＋子部长文，正是 N57 当初的质量顾虑，如实保留；
  对照漢詩 24 条 avg 9.583 属正常区间）。
- [0:7908) 对照 vs `night62_results_7908.json`：diff **1246 行**＝**改善 978／变差 1
  （24shihin14-1，dist 10→11）／显示层同距改写 267，总 dist −1213**；fixed 3 行
  （toushisen043-16、toushisen135-12、**zasshi-2**）。**归因**：该归档是 N64 合并前分支引擎
  产物，master 的 Rule I＋SHINJITAI 99 从未在 [4000:7908) 重跑过——与 N64 在 [0:4000)
  改写 656 行同机制（净收益方向一致），非本夜引擎变更。

### 3.3 guwenbert 新增段 + h2h（与 Night 62 同口径）

- `tools/night67_guwenbert_new.py`（HF_HUB_OFFLINE=1，进程内⑬同款补丁）→
  `eval/night67_guwenbert_new257.json`：**n=257、OK 257、error 0、exact 0、avgDist 578.825**。
- `tools/night67_h2h.py` → `eval/night67_h2h.txt`：可比 257，**规则更好 255／guwenbert
  更好 1／持平 1**；规则 avgDist 65.704 vs gwb 578.825，双方 exact 0；gwb 最小差距
  rikutou59-2（228 vs 229）。gwb 输出形态＝只译首句、余下白文原样照抄——对照
  N62 新增段短句（gwb 12.466 略优于规则 12.577），**长短句行为分化**如实记录。
- **超时偏差申报**：本步 ~59 分钟 >45 分钟预算——非卡死（50/100/150/200/250 检查点
  avg 432→503→543→553→593 稳定推进，~12s/条：paren 长文＋ルビ括号使 supar 解析慢一个
  量级），且为 ⑲ 必需产物，故未跳过；SHIFT_LOG 两次如实记录（任务书「卡 >45 分钟
  记录并跳过」的处理偏差，留用户裁定）。

## 4. ⑭ 默认口径登记（golden_3000 时代 → golden_4000）

- 改动：`tools/accept_night.py` NIGHT_ARTIFACTS 加 `67: ["night67_results_4000.json"]`
  （沿用 N9/N26 起「night→results 归档文件」登记式；golden_7908/8165 保持扩充归档，
  不登记为默认）。
- 任务书表述「golden_3000 → golden_4000」的仓内实体对应：NIGHT_ARTIFACTS 从未有过
  golden_3000 时代的实体登记（最后一条是 34），night 35-66 验收时 eval_integrity 一直
  skip=1；本夜登记把 67 的验收门从「跳过」变成「实查 night67_results_4000.json」。
- 生效证据：accept 67 中 eval_integrity 由 skip 转 **PASS**（「检查 1 个归档，id 唯一、
  自报数一致、expected 未改」——对照 eval/golden.json 500 条基线 expected 零 mismatch）。

### 默认口径切换前后对照（全部实测）

| 口径 | n | error | exact | avgDist | 出处 |
| --- | --- | --- | --- | --- | --- |
| golden_3000（⑬前） | 3000 | 1 | 21 | 16.026 | night64_results_4000.json [0:3000) 切片 |
| golden_3000（⑬後） | 3000 | 0 | 21 | 16.022 | night67_results_4000.json [0:3000) 切片 |
| golden_4000（⑬前·旧态） | 3998 | 2 | 24 | 13.719 | eval/night64_results_4000.json |
| **golden_4000（⑬後·本夜起默认）** | **4000** | **0** | **24** | **13.716** | **eval/night67_results_4000.json（已登记）** |
| golden_7908（扩充归档） | 7908 | 0 | 30 | — | night67_results_8165.json [0:7908)（N62 归档：n=7905/err 3/exact 25/avg 13.241） |
| golden_8165（扩充归档） | 8165 | 0 | 30 | 14.741 | eval/night67_results_8165.json |

新默认口径一句话：**n=4000、error 0、exact 24、avgDist 13.716（⑬修后）**。

## 5. ⑩ 否决关闭（零代码改动）

- 预处理代码一行未写。
- `ROADMAP.md` 末尾记 1 行：状态 CLOSED — ⑩「應→応 白文预处理」否决结案（Night 67）：
  Night 59 实证 no-op（18 行含應白文逐字节不变、error 照旧——lemma 归一到應，AUX 查键
  照样缺）；真正缺的是 udkundoku AUX 活用表条目，已由 ⑬ backend runtime 补丁修复
  （golden_4000 error 2→0）。
- 本报告 §0/§2 同记；原始出处＝REPORT_NIGHT59.md §4/§6（预处理模拟 0 收益 0 副作用、
  拍板依据表）。

## 6. ⑥ README/verify 同步

- `README.md` 只改 2 行：テスト **214→219 passed**；規則エンジン **13.719/24-3998（error 2
  を除く）→13.716/24/4000、error 0**，注明 `eval/night67_results_4000.json` 口径＋N67 AUX
  修正。其余数字（SHINJITAI 246、MERGE_WORDS 21、Rule E/F/G/H/I 5/4/4/3/6、OCR GT 93 行、
  割注右先率 98.57/98.63）一行未动；「已知の問題」节按「没动的数字一行不许碰」未动；
  表头 commit 号维持开工 HEAD `920866d`（自引用滞后，任务书明示不为此多跑一轮）。
- `tools/verify_readme_facts.py` 数据源 night64→night67（docstring、文件路径、print 标签）；
  实跑输出 `night67(golden_4000): total=4000 n=4000 exact=24 avgDist=13.716 errors=0`，
  与 README 对上；SHINJITAI/MERGE/Rule E-I/OCR/割注各数与 README 现值一致。

## 7. 验证汇总

- pytest：215 → **219 passed**（+⑬ 回归 1、+golden_8165 双保险 3），~15s。
- accept 67：首跑（提交前）FAIL＝repo_clean 对未提交改动如实报数（设计行为）；
  主提交后终跑 **PASS**（fail=0 **skip=0**，35.7s）：repo_clean／pytest 219=219／
  eval_integrity（⑭ 生效，skip→实查 PASS）／rule_regression／engine_smoke／perf 17ms／
  order_rate 98.57/98.63（+0.00pp、退化页 0）。FAIL/PASS 两行留痕 ACCEPT_LOG。
  任务书交付格式预写的「skip=1」与本夜实测不符：⑭ 登记使 eval_integrity 由 skip 转
  PASS，skip 实数=0（如实填实测数）。
- verify_readme_facts.py 对上（§6）。
- 提交：本地 master 两提交 **f4376ac**（主）＋wrap-up（本报告＋SHIFT_LOG＋ACCEPT_LOG＋
  eval/accept_night_67.json），未推远程；`git rev-list --count origin/master..master` = 2。
- 心跳：SHIFT_LOG 19:0x 开工/暂停、20:05、21:04、收尾各 1 行；byte807 全程 0xF3 未动
  （ReadAllBytes[807]=243 ✓）。

## 8. 禁止事项自查

- expected 一字未改：⑲ 红线 257/257 ✓；⑬ golden_4000 expected 不变 ✓；
  golden.json／golden_1000／golden_2000／golden_7908 零改动 ✓。
- site-packages 一行未动（补丁只在 backend/main.py 与工具进程内）✓。
- 未进 D:\kanbun-eval10k / D:\kanbun-rulei ✓；单会话未开并行 ✓。
- 保护性 untracked（night50_*、merge6*_pytest、ocr_samples/**、night36_cer.json 冻结
  归档等）零触碰 ✓。
- 本地提交不推远程 ✓；无 key/token 写入 ✓。
- 超时偏差如实申报：guwenbert 单步 ~59 分钟（>45 分钟预算），未跳过的理由与记录见 §3.3。
