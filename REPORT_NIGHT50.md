# REPORT_NIGHT50

**日期**：2026-11-20（Night 50）
**模型**：deepseek-v4.1-flash-free
**分支**：本地 `master`，未推远程
**起点提交**：`9bebcc6`（night49: accept gate 49 PASS (141 passed)）
**任务书**：两件 —— A 修 pytest 收集隐患；B 补顺序测量门（只测量不判死刑）

---

## 0. 一句话结论

A 完成并提交（`d99dd8f`）：`tools/test_ocr*.py` 不再被任何 pytest 收集，
无路径 `pytest` 的收集耗时从 **306s 降到 3.3s**，`eval/` 328 个已跟踪文件
sha256 逐个不变，两个脚本直接运行仍然正常。

B 完成：`tools/accept_night.py` 新增第 7 项检查 `order_rate`，
跑 Night49 同源口径（进程内 import `night49_final`，不二次跑脚本、不写文件、
不覆盖已存档 json），输出生产口径右先率 / 严格层率 / 退化页数，
**永不以数值判 FAIL**。

---

## 1. 开工核对

```
git log -1  → 9bebcc6  night49: accept gate 49 PASS (141 passed)
pytest tests → 141 passed
```

上一会话 22:26 上游流式错误中断，A 的验证已做完但**改动未提交**
（`conftest.py`、`pytest.ini` 均为未跟踪），B 的 `check_order_rate` 未开始。
按指示：先提交 A，再做 B 收尾。

---

## 2. 任务 A：pytest 收集隐患（已提交 `d99dd8f`）

### 2.1 问题

`tools/` 下有 4 个「名字像测试、其实是脚本」的文件，**导入即执行**：

| 文件 | 导入时的副作用 |
| --- | --- |
| `tools/test_ocr.py` | 加载 OCR 引擎 + 识别 1 页（26.6s 加载 + 38.1s 识别） |
| `tools/test_ocr_samples.py` | 识别 4 页 × 2 模式，**重写 `eval/ocr_samples/*_clean__*.txt`** |
| `tools/test_ocr_chain.py` | 需要 8000 端口后端在跑 |
| `tools/test_udkundoku.py` | 加载 udkundoku 引擎（44s+） |

Night 49 踩过一次：无路径 `pytest` 收集并**执行**了 `test_ocr_samples.py`，
改写了 2 个已跟踪的样本 txt（REPORT_NIGHT49.md §15）。

### 2.2 修法（两层保险）

**第一层 `conftest.py`（仓库根，新建）**：`collect_ignore` + `collect_ignore_glob`
四文件全列。前者对同目录收集生效，后者兜「`pytest tools/` 显式指定」的情况。

**第二层 `pytest.ini`（新建）**：`testpaths = tests`。无路径 `pytest` 只收集
`tests/`，连 `tools/` 目录都不会进去。

两层是冗余设计：任一层失效，另一层独立拦住。`pytest tests`（验收口径）
的收集结果完全不变（141）。

### 2.3 三点验证（任务书要求）

验证前 `git status --porcelain --untracked-files=no` → `(none)`，
328 个 `eval/` 已跟踪文件的 sha256 快照落盘（`eval/night50_evalhash_before.json`）。

**① 无路径 `pytest` 不再收集、不再执行、不再改写 `eval/`**

```
python -X utf8 -m pytest -q        → 141 passed in 17.20s  (exit 0)
```

- 收集：`pytest --collect-only -q` → `tools collected: 0`，141 tests collected **3.30s**
  （修前同类收集要 306s——那 300 秒就是在跑 OCR）
- 执行：无 OCR 日志、无 `[engine] loaded` 输出
- 改写：运行后 sha256 快照与基线比对 →
  `快照 A: 328 文件；快照 B: 328 文件；并集 328 / sha256 变化: 0 / verdict: IDENTICAL`

验证后 `git status --porcelain --untracked-files=no` → `(none)`。

**② `pytest tests` 仍为 141 passed** —— 是（本次收尾又跑一次：`141 passed in 14.66s`）。

**③ 两个脚本直接运行仍能用** —— 是：

```
python -X utf8 tools/test_ocr.py
  [engine] loaded in 26.6s
  [ocr] elapsed 38.1s, 16 lines  （竹取物語开头，文本正常）
python -X utf8 tools/test_ocr_samples.py
  4 页 × 2 模式 = 8 条，全部输出正常（16/5/9/23 行）
```

注意：`test_ocr_samples.py` **按设计**会重写样本 txt，这是脚本的本来行为，
不是回归。跑完后 `git checkout -- eval/ocr_samples/` 恢复，再比对 sha256 →
**IDENTICAL**（328/328 不变）。

### 2.4 未跟踪的证据文件

`eval/night50_*.txt` / `eval/night50_evalhash_*.json` 共 11 个，是 A 的验证留痕
（git status 前后、哈希快照、bare pytest 输出、collect-only 输出）。**保留**，
不入库（`eval/` 下的临时证据，与既有 `night4x_*.json` 归档策略一致）。

---

## 3. 任务 B：顺序测量门（`order_rate`）

### 3.1 为什么需要

Night 49 的核心发现之一：**GT 92 行 CER 对阅读顺序是盲的**。
Night49 改了 34/47 页的行序（割注并排槽重排），CER 仍逐位不变
（raw 0.3568 / norm 0.3053，与 Night44/46 完全相同）。

也就是说，如果以后有人把顺序改坏，**现有 6 项验收门一个都不会响**。
所以需要一个独立指标。

### 3.2 实现

新增两个文件：

**`tools/night50_order_rate.py`（新建）—— 口径实现**

- `measure(directory, apply_filter, label)`：跑一条线，返回
  `tot / after / rate / rate_before / strict_n / strict_after / strict_rate /
  regress / strict_bad`
- **口径完全同源**：直接 `importlib` 载入 `tools/night49_final.py`，
  用它的 `find_pairs()` / `order_of()`，连版面过滤、`_main_group`、wmed
  的取法都走同一份代码。口径若分叉，这个门就没有可比性。
- 严格层 A_strict 判据与 `tools/night49_pair_quality.py` 逐字一致：
  `gap < 0.15*wmed ∧ |dy_top| <= 0.05*max(h) ∧ |dh| <= 0.15*max(h)`
- `BASELINE` 常量记录 Night49 改后基线：off 98.57%（481/488）、
  on 98.63%（503/510）、strict 100%（296/296）

**`tools/accept_night.py`（改 +97 行）—— 第 7 项检查 `check_order_rate`**

关键设计（按任务书要求）：

| 要求 | 实现 |
| --- | --- |
| 进程内导入，不二次运行脚本 | `importlib` 载入 `night50_order_rate`，调 `mod.measure()` |
| 不写入文件 | 包的 `main()` 才写 json；门只调 `measure()` |
| 不覆盖已存档 json | 全程不碰 `eval/night49_final.json` / `night50_order_rate.json` |
| 输出右先率 | `off 481/488 = 98.57%`、`on 503/510 = 98.63%` |
| 输出严格层率 | `strict 296/296 = 100.00%` |
| 输出退化页数 | `regress_pages`（相对「改前」基线） |
| 永不 FAIL | 只有 `pass` / `skip` 两种返回路径；异常也走 `skip` |

`Check.fail()` 在这个函数里**一次都没调用**。数值再低也只会让 notes 里的
数字难看，不会改变 verdict。

### 3.3 门槛数值实测（`python tools/accept_night.py 50 --no-pytest --no-log`）

```
[PASS] order_rate         割注右先率（只测量，不判死刑）
        - off 右先率 481/488 = 98.57%（基线 98.57%，差 +0.00pp）；
          严格层 296/296 = 100.00%；退化页 0
        - on 右先率 503/510 = 98.63%（基线 98.63%，差 +0.00pp）；
          严格层 293/293 = 100.00%；退化页 0
        - **只测量不判死刑**：阈值需用户拍板后才能转成 FAIL 判据
```

与 Night49 报告逐位一致，0 退化。

### 3.4 实现中踩的两个坑（记录）

1. **`night49_final.py` 在模块级调 `sys.stdout.reconfigure()`**，
   而 `redirect_stdout(StringIO())` 里的 StringIO 没有 `reconfigure` →
   `AttributeError`。修法：`_load_n49()` 做缓存，`main()` 里**先**在真实
   stdout 下预导入，再进重定向。
2. **`night49_final.py` 模块级把 `sys.argv` 截成 `[argv[0]]`**（它原先是脚本），
   而验收门带 `night` / `--no-pytest` 参数 → 会被一起抹掉。修法：
   载入前后存/取 `sys.argv` 快照。

两处都在 `night50_order_rate._load_n49()` 的 docstring 里写清了原因，
避免后人再踩。

### 3.5 以后要改成判死刑门，需要用户拍板

本门现在**只测量**。要转成 FAIL 判据，需先批准阈值。可选口径：

- `off`（生产口径）右先率下限，如 `< 95%` 即 FAIL
- `A_strict` 严格层必须 `== 100%`（Night49 起就是 100%，退化即真回归）
- 退化页数 `> 0` 即 FAIL（最严格；但改前基线会随算法演进而变，需同时维护）

**建议**：先只用「严格层 < 100%」或「生产口径 < 95%」这类粗阈值跑几夜，
观察正常波动后再收紧。**本夜不定，留作拍板项。**

---

## 4. 验证汇总

| 项 | 结果 |
| --- | --- |
| `git log -1` 起点 | `9bebcc6` ✓ |
| `pytest tests` | **141 passed** ✓ |
| 无路径 `pytest` 收集 tools | **0** ✓ |
| 无路径 `pytest` 改写 eval/ | **0**（328 文件 sha256 IDENTICAL）✓ |
| test_ocr.py 直接运行 | 16 行输出正常 ✓ |
| test_ocr_samples.py 直接运行 | 8 条输出正常 ✓ |
| `accept_night.py 50` 出现 order_rate 行 | ✓（PASS，3 行 notes） |
| order_rate 会 FAIL 吗 | **不会**（代码里无 `c.fail()` 调用）✓ |
| GT CER 不变 | **是**：raw 0.3568/0.2566、norm 0.3053/0.2242，与 N44/46/49 逐位相同 ✓ |
| 改 backend/ | **无**（`git status backend/` 空）✓ |
| 改 eval/ocr_gt_100.tsv、golden*.json、expected | **无** ✓ |
| 重跑 47 页全本 OCR | **无**（只跑了 GT 8 页，GT 门既有要求）✓ |
| 推远程 | 未推 ✓ |

---

## 5. GT CER

本夜**没有改任何 `backend/` 代码**（`git status backend/` 全程为空），只加了验收门的
一个只读检查，CER 理论上必然不变；仍实跑一次 GT 门作证据。

```
python tools/night49_gt_run.py
python tools/eval_ocr_gt.py eval/night49_gt_lines.json eval/night50_gt_cer.json
```

**结果：与基线逐位相同。**

```
overall: raw micro=0.3568 macro=0.2566 | norm micro=0.3053 macro=0.2242
```

| 指标 | Night50 | 基线（N44/46/49） | 差 |
| --- | --- | --- | --- |
| raw micro | 0.3568 | 0.3568 | 0 |
| raw macro | 0.2566 | 0.2566 | 0 |
| norm micro | 0.3053 | 0.3053 | 0 |
| norm macro | 0.2242 | 0.2242 | 0 |

8 页逐页 `unmatched_no` 全为 0；行数（9/16/16/5/5/20/6/25）与基线一致。

### 5.1 一处需要说明的副作用（已处理）

`tools/night49_gt_run.py` 把结果写回 **`eval/night49_gt_lines.json`（已跟踪文件）**，
所以这次 GT 门跑完后该文件被覆盖。逐行 diff 确认：**只有 `recognize_sec`
（8 页的耗时）变了，`lines` 的文字/坐标/行数、`layout_filtered`、`junk_filtered`、
`unmatched_line_no` 全部逐项相同** —— 这反过来又是一个「文本结果完全确定」的旁证。

处理：
1. 本次结果另存 `eval/night50_gt_lines.json` 作为 Night50 证据；
2. `git checkout -- eval/night49_gt_lines.json` 恢复 Night49 归档原样；
3. 恢复后 `git status --porcelain --untracked-files=no` 只剩验收门自身写入的
   `ACCEPT_LOG.md`（该文件被 `check_repo_clean` 豁免）。

**待拍板（新增）**：`night49_gt_run.py` 应该加个 `--out` 参数或改成按夜命名，
否则每次跑 GT 门都会覆盖上一夜的归档。本夜不改（属工具口径变更）。

---

## 6. 待拍板（编号 = 下一班的下单清单）

1. **order_rate 要不要转成判死刑门，阈值取多少。** 现在是纯测量。
   可选：生产口径下限（如 95%）/ 严格层必须 100% / 退化页 > 0 即 FAIL。
   **建议先观察几夜再定。**
2. **`tools/night49_gt_run.py` 会覆盖已跟踪的 `eval/night49_gt_lines.json`**
   （每次跑 GT 门只差 `recognize_sec`）。建议加 `--out` 或按夜命名。
3. **`eval/night50_*` 那批临时证据文件**（11 个）要不要入库。
   当前策略：保留在磁盘、不入库，与既有 Night4x 证据归档一致。
4. Night49 §16 的 5 项状态：
   - ① 顺序门 → **本夜已补**（测量版）
   - ② `tools/test_ocr*.py` 收集 → **本夜已修**（A）
   - ③ 割注配对口径是否收紧到 A_strict → 仍未定（本门双口径都报，未强制）
   - ④ `KANBUN_OCR_WARICHU` 开关保留 → 仍未定
   - ⑤ Night47 §8 / Night48 §11 条目 → 状态不变

---

## 7. 禁止事项自查

- 未发图、未读图（全部用 `line_boxes` 坐标与 OCR 文本）
- 未改 `eval/ocr_gt_100.tsv`、`eval/golden*.json`、任何 expected
- 未重跑 47 页全本 OCR（只跑 GT 8 页产品流，GT 门既有要求）
- 未碰 Night 9、16–20 的代码与归档
- 未推远程；全部改动只在本地 `master`
- 未删除任何历史归档
- 验证 A 的那一次无路径 `pytest` 是**刻意测试**，跑前跑后都做了
  `git status --porcelain --untracked-files=no` 留底（均为 `(none)`）
- 被 `test_ocr_samples.py` 按设计重写的 2 个样本 txt 已 `git checkout --` 恢复，
  并复验 sha256 IDENTICAL

---

## 8. 本次改动清单

```
新文件  conftest.py                       pytest 收集排除（第一层）
新文件  pytest.ini                        testpaths = tests（第二层）
新文件  tools/night50_hash_eval.py         eval/ 已跟踪文件 sha256 快照
新文件  tools/night50_cmp_hash.py          两份快照比对
新文件  tools/night50_order_rate.py        顺序门口径实现
改文件  tools/accept_night.py             +97 行：check_order_rate（第 7 项）
```

提交：`d99dd8f`（A：conftest.py + pytest.ini + 两个 hash 工具）。
B 的改动在 A 之后单独提交。
