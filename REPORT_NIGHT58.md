# REPORT_NIGHT58

## 0. 一句话结论

Rule H 上线（3 条假名→汉字 + 白文护栏）+ SHINJITAI 扩 30 对（N30 同款方法论），
3000 条组合 **改写 317 | avgDist 16.321 → 16.219（-0.102）| 改善 264 / 变差 0**，
真机复跑与离线模拟 **317/317 行逐位一致**（第四次「API 全链 = 离线真函数」）、
真机变差 0、精确 15→16，幂等 PASS，GT CER **raw 0.3568 / norm 0.3053 逐位不变**
（night49 归档 sha256 `ff21e4fa…` 不变），pytest **175→190**。

## 1. 开工核对

- `git log -1` = `3083f0d`（N55-57 收尾）✓；pytest **175 passed** ✓；
- **机器时钟异常（如实记录）**：本班开工时钟 `2026-11-21 02:05`，比上一班收尾
  心跳（2026-11-22 02:55）还早 ~24.8h——时钟被回拨过。心跳行按机器时钟记，
  「跑到 09:00」也按机器时钟执行，时间轴以本班各行自我一致为准，供用户对齐。

## 2. 方法论与输入

Night 22/N55 四步：**解剖 → 离线模拟（≥3 候选，逐条真算 Levenshtein）→ 真机 →
门 + pytest 锁定**。变差>0 一律不上线；只上线 0 变差带护栏的。

- 基线 = `eval/night57_results_3000.json`（N57 真机 3000 条，D/E/F/G 全链，
  自报 16.321；不再用 2000 旧基线）；
- **挖掘范围纪律**：新增段 = 平行剩余 31 + 詩経 102 + 漢詩 867（下标 2000+），
  先做新增段字符 delta 与分档（N57 任务书要求），N55 已挖过的
  （また→又/亦た、ゆゑん、いはゆる、たがいに、べき/べから 拒绝系）不重复挖。

## 3. 解剖（`tools/night58_mine.py` → eval/night58_mine.json）

新增 999 条（1 条 error 除外）分档：**≤20字 996 条 avgDist 7.078 / 21-40字 3 条
21.667**——诗是短句，全部结论限于短句构成（N56/N57 构成警告适用）。

字符 delta（exp_new≥5 且 exp>got）的两大类：

| 类 | 字（新增 delta） | 机制 |
| --- | --- | --- |
| **舊字体残留** | 青 25、処 22、楼 15、独 13、復 11、将 11、緑 8、灯 7、遥 7、須 7、莫 17、但 6、旧 6、暁 6、酔 6、只 5、縦 5 | 引擎按词典旧字体输出（靑/處/樓/獨/綠/燈/遙/舊/曉/醉/縱/晚…），kanbun.info 一律写新字体 |
| **假名读法缺口** | 復た（また）、莫かれ（ことなかれ）、只だ（それ）、須いず（べからず） | F/E/G 已覆盖 又/亦た/唯だ/可し 的分工形态之外的第三/四形态 |

工具 `tools/night58_probe_forms.py` 把 19 个目标字的 exp 侧表层形态 + got 侧碎片
定准（N14 教训：词形按 expected 真实形态，不猜）：
- **於：无稳定 got 侧碎片**（'の'×3/'進む'×2…散乱）→ 按 N14 方法论**不出候选**；
- **将**：got 碎片 'ごとく'/'それ'/'んと' 无稳定词形，且 將→将 已在表里
  （got 將 0 次）→ delta 是引擎把「将に/将た」写成假名的词法缺口，**不出候选**；
- 只：exp 写 只だ×5/只使い×1/只今×1，got 写 それ×6 → repl 取多数派 只だ；
- 須：exp 写 須いず/須いん/須らく（須臾×3 与人名樊須×1 是干扰），got 写 べからず×4 →
  只做 べからず→須いず（ず 尾活用对应，护栏須）。

## 4. 离线模拟（`tools/night58_sim.py` → eval/night58_sim.json）

**SHINJITAI 1:1 扫描**（2999 条 difflib 汉字→汉字 + 解剖多字对齐目标合并，
判据 = **expected 全库写旧形 0 次** 且 got 旧形 ≥2）：

| 组 | 对数 | 改写条 | Δ | 改善/变差 | 判定 |
| --- | --- | --- | --- | --- | --- |
| SHINJITAI 30 对 | 30 | 280 | **-0.084** | 226/**0** | ✅（N30 同款显示层批量） |
| また→復た | 復 | 35 | -0.011 | 33/**0** | ✅ |
| それ→只だ | 只 | 8 | -0.004 | 7/**0** | ✅ |
| べからず→須いず | 須 | 4 | -0.002 | 4/**0** | ✅ |
| ことなかれ→莫かれ | 莫 | 46 | -0.026 | 34/**11** | ❌ 拒绝 |
| なかれ→莫かれ | 莫 | 48 | -0.013 | 35/**1** | ❌ 维持 D14 拒绝 |
| べし→須らく | 須 | 6 | +0.003 | 1/**5** | ❌ 拒绝 |
| **组合** | | **317** | **-0.102** | **264/0** | ✅ 上线 |

exp 假名残留（防变差方向）：また/ことなかれ/なかれ/それ 全 0 次；べし 27 次、
べからず 6 次（= 拒绝/护栏意义的边界记录）。幂等 PASS（程序化）。

**拒绝核因**（都符合 N55 べき 定性的「运行时无信号可分」机制）：
- ことなかれ→莫かれ 11 变差：莫行里 expected 写 莫し/莫き/莫けん（kunmotokyu-1、
  rongo1709-1、kokyo09-5、toushisen008-5…）——与写 莫かれ 的行白文信号完全相同；
- べし→須らく 5 变差：**同一行内混写**「須らく…べし」（sekitoku-1「微かに須らく
  意を留むべし」、toushisen352-3「須らく酔いを尽すべし」）——页面内都不一致；
- 1:1 扫描拒绝 冰→氷/弦→絃/亦→又：expected 自身写旧形（亦 104 次），全局映射必破坏。

## 5. 上线实现（backend/kundoku_rules.py）

```python
H_KANA_TO_KANJI = [
    ("また", "復た", ("復",)),          # F/G 之后的第三分工形态
    ("それ", "只だ", ("只",)),          # engine 把 只 读作 それ
    ("べからず", "須いず", ("須",)),
]
H_LONGER_WORDS = {"また": _MATA_LONGER_WORDS,           # 与 F/G 共享同一常量
                  "それ": ("それで","それぞ","それとも","それが","それら","それでは"),
                  "べからず": ()}
def style_kana_to_kanji_h(text, hakubun="")   # 与 E/F/G 同构两道护栏
```
- 链序 `style_fix_with_hakubun`：…E → F → G → **H**；F→G→H 对 また 三方分工
  （白文含亦/又/復 谁先命中谁吃），`test_three_way_division_of_labor_for_mata` 锁死；
- SHINJITAI_MAP 追加 30 对（含 寳 U+5BF3——N30 只收了异体 寶 U+5BF6，两码位都要）；
  冰/弦/亦 的拒绝写进注释；
- 旧 `style_fix` 不含 D/E/F/G/H，不变。

## 6. 真函数核对 + 真机验证

- `tools/night58_eval_3000.py`（TestClient 完整后端链，101 秒）：
  **输出文本 vs night57 归档 不同行数 = 317（= 模拟 317）；改写行新文本 vs 模拟
  预测逐位一致 317/317；多改 0 / 漏改 0；真机变差 0**——API 全链与离线真函数
  第四次逐位等价（D17 §6、N55 §8、N57 §4 之后）。
- **avgDist 16.321 → 16.219（-0.102）**，与模拟逐位一致；**精确 15 → 16/2999**
  （新晋精确 = `toushisen244-2`「復聞啼鳥聲」→「復た啼鳥の声を聞く」，また→復た
  单规则造就；丢失精确 0 行）；
- 分档：≤20字 8.390→8.302、21-40字 21.838→21.742、41-60字 37.296→37.162、
  >60字 64.077→63.845（全档单调改善）；
- 文体：故事 21.197→21.096、漢詩 7.247→7.098、論語 26.956→26.870、大学 14.603→
  14.571、孝経 9.286 不变、詩経 5.206→5.167；
- 唯一 error 仍是 `toushisen135-12`（應 KeyError，N59 题目，本夜不动引擎）。

## 7. 验证汇总

- pytest **175 → 190 passed**（+15 `tests/test_rule_h_kana_kanji.py`：表结构/词形/
  护栏正反/词界/幂等/三方分工/四表独立+また共享/拒绝候选不复活/旧入口/语料原句/
  经典句/SHINJITAI 30 对+新形非 key）；
- GT 门：`night49_gt_run.py --out eval/night58_gt_lines.json` 实跑 8 页
  （unmatched_no 全 0），**raw micro 0.3568 / macro 0.2566，norm micro 0.3053 /
  macro 0.2242 —— 逐位不变**；`eval/night49_gt_lines.json` sha256 `ff21e4fa…9cde`
  与 N55 记录一致；
- `python tools/accept_night.py 58`：pytest/eval_integrity(skip=未登记，同 55-57
  口径)/rule_regression/engine_smoke/perf_envelope/order_rate 全 PASS；
  repo_clean 提交前如实 FAIL（门行为正确），提交后终跑 PASS；
- **过程自查纠错（如实）**：① 首版 1:1 扫描的 `got_new==0` 条件过严误拒
  說/鄉/寳/產/眞 5 对（exp_old==0 才是安全判据），修正后收入；
  ② 解剖 10 对初版被 difflib 计数 `n<2` 过滤器误杀 9 对（多字对齐不是 1:1 块），
  补第二遍计数判据后收入——两次都是离线阶段抓住，未上线；
  ③ eval_ocr_gt.py 默认覆盖了跟踪文件 eval/night36_cer.json，已 `git checkout`
  恢复，重跑时显式指定 `eval/night58_gt_cer.json`。

## 8. 局限与风险（如实）

1. **それ→只だ 的护栏只有「只」一个字**：それ 是超高频假名，唯一保护是白文含只
   （3000 条内 8 行）。语料外若出现「白文含只 & got 写 それ & expected 不写只だ」
   的行会误改——已加 6 个 それ 长词护栏，残余风险与 E/F/G 的 ただ→唯だ 同级。
2. **べからず→須いず 的 exp 假名残留 6 次**：expected 自身写 べからず 的行存在
   （現 0 变差 = 与須护栏不共存）；未来扩语料若两者共存会出变差，护栏不可分时
   按本夜 ことなかれ 同标准撤或拒。
3. SHINJITAI 是全局映射（N3/N30 既定语义）：冰/弦/亦 类「expected 写旧形」的字
   永远不能进表——每次扩表都要做 exp_old==0 全库检查（本夜已把判据写进 sim 脚本）。
4. 新增段 996/999 是 ≤20 字短句，上述增益不能外推到长句（分档对照已如实记录）。

## 9. 待拍板（编号 = 下一班的下单清单）

1. N52-54 的 ④-⑧、N55 的 1-3、N57 的 ⑨-⑩ **原样保留**；
2. **新增 ⑪**：それ→只だ 的护栏只有一个字（超高频词それ），要不要在
   「kanbun.info 页面级风格信号」（N55 待拍板 #3）之外，给它再加一层运行时约束
   （如「只」必须在白文与 expected 侧都出现才算命中）——属护栏加严的产品拍板；
3. **新增 ⑫**：SHINJITAI 表已 121 对、每次扩表都全库核验——要不要把它从
   kundoku_rules.py 拆成独立数据文件（便于 N60 扩语料后自动重核验），属代码组织拍板。

## 10. 禁止事项自查

未发图/未读图/未抄 GT ✓；未改 `eval/ocr_gt_100.tsv`、`eval/golden*.json` ✓
（过程误覆盖 eval/night36_cer.json 已当场 git checkout 恢复，§7-③ 如实记录）；
未重跑 47 页全本 OCR（GT 门 8 页除外，--out 指向 night58 文件）✓；
未碰 Night 9、16-20 ✓；未动 N51-57 拍板项 ✓（「應」歸一=⑩ 留给用户，本夜只在
解剖里如实记录）✓；expected 一字未改（night57_results_3000.json 只读）✓；
本地提交不推远程 ✓；心跳按小时追加（含时钟异常标注）✓。

## 11. 改动清单

| 文件 | 性质 |
| --- | --- |
| `backend/kundoku_rules.py` | Rule H 3 条 + H_LONGER_WORDS + 链接入 H + SHINJITAI_MAP +30 对 |
| `tests/test_rule_h_kana_kanji.py` | 新增 15 条测试 |
| `tools/night58_mine.py` / `night58_probe_forms.py` / `night58_sim.py` / `night58_eval_3000.py` / `night58_pick_examples.py` / `night58_count_probe.py` / `night58_heartbeat.py` | 解剖/形态探针/模拟/真机评测/例句挑选/计数核对/心跳 |
| `eval/night58_mine.json(.txt)` / `night58_probe_forms.txt` / `night58_sim.json(.txt)` / `night58_combo_changed_rows_*.json` / `night58_examples.txt` / `night58_results_3000.json` / `night58_eval.txt` / `night58_gt_lines.json` / `night58_gt_cer.json(.txt)` / `night58_gt_run.txt` / `night58_pytest_full.txt` / `night58_test_h.txt` | 证据 |
| `REPORT_NIGHT58.md` / `SHIFT_LOG.md` | 报告与夜志 |

## 12. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night58_mine.py          :: 解剖 → eval/night58_mine.json
python -I tools\night58_probe_forms.py   :: 形态探针
python -I tools\night58_sim.py           :: 离线模拟（含组合改写行明细落盘）
python -m pytest tests -q                :: 190 passed
python -I tools\night58_eval_3000.py     :: 真机 3000 条 + 确定性对照
python -I tools\night49_gt_run.py --out eval\night58_gt_lines.json   :: GT 门 8 页
python -I tools\eval_ocr_gt.py eval\night58_gt_lines.json eval\night58_gt_cer.json
python tools\accept_night.py 58          :: 验收门
```
