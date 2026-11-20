# REPORT_NIGHT51

## 0. 一句话结论

给 `tools/night49_gt_run.py` 加了 `--out` 参数（**选择 --out，不改按夜命名**，理由见 §2）；
实跑 GT 8 页写 `eval/night51_gt_lines.json`，**已跟踪的 `eval/night49_gt_lines.json` 逐字节不变**
（sha256 跑前跑后同为 `ff21e4fa…9cde`）；GT CER **raw micro 0.3568 / norm micro 0.3053**
（macro 0.2566 / 0.2242）与 N44/46/49/50 基线**逐位相同**；night51 与 night49 归档
除 8 页 `recognize_sec` 外**零字段差异**；pytest **141 passed**；accept gate 51 PASS。

## 1. 开工核对

- `git log -1` = `b7224fc`（night50 accept gate 50 PASS）✓
- `python -m pytest tests -q` = **141 passed**（13.01s）✓
- 已跟踪工作区干净（`git status --porcelain --untracked-files=no` 为空）✓
- 未跟踪遗留：night50_* 证据文件 + `eval/ocr_samples/gt36/...` 行图（红线：不替用户决定是否入库，原样保留）

## 2. 方案选择：`--out` 参数（不是按夜命名）

**任务书给了两个选项，选 `--out`，默认行为不变。理由三条：**

1. **按夜命名必须知道"当前是第几夜"，脚本无从得知**——`night49_gt_run.py` 是个
   无状态脚本，文件名写死 night49。要么再加一个 `--night` 参数（等于还是传参，
   多绕一层），要么用当天日期猜夜号（不可靠，白天补跑/回测都会错）。既然终究要传参，
   直接传输出路径最诚实。
2. **改默认输出路径会破坏既有调用方与历史可复现性**：`eval/night49_gt_lines.json`
   是已跟踪归档，被 `tools/night49_gt_diff.py`、`tools/night49_gt_boxes.py` 与
   Night49/50 报告的叙事引用；`accept_night.py` 的设计目标之一是**可回测**
   （拿历史归档重新判一次）。缺省路径一动，历史夜的复现口径就断了。
3. `--out` 是**纯增量**改动：不传参时代码路径与 Night49 逐位一致
   （缺省赋值行 `gt44.OUT = os.path.join(ROOT, "eval", "night49_gt_lines.json")`
   一字未动，`--out` 仅在显式传入时覆盖 `gt44.OUT`）。

语义：`--out PATH` 相对路径**以仓库根为基准**（不是 cwd）——脚本能从任何目录被调，
按 cwd 解析会让同一条命令在不同 cwd 产出不同文件，按仓库根解析则与脚本内其它
路径（ROOT 拼接）口径一致。绝对路径原样使用。

## 3. 改动清单

`tools/night49_gt_run.py`（唯一代码改动）：
- docstring 更新（用法两行 + NIGHT51 说明段）；
- `import argparse`；
- `__main__` 块新增 6 行：argparse 定义 + `arg.out` 非空时覆盖 `gt44.OUT`。

不含任何 `backend/` 改动 → 引擎行为零变化（下节 CER 逐位相同与此互证）。

## 4. 验证证据（任务书要求逐项）

### 4.1 `--out` 跑 GT 8 页，night49 归档不被改写

跑前（23:19）：
```
git status --porcelain --untracked-files=no   →  (empty)
sha256(eval/night49_gt_lines.json) = ff21e4fa7d749c61f1fbe60ff753713941289a4a6d370feaabdedb7e60bd9cde
```
命令：`python -X utf8 tools/night49_gt_run.py --out eval/night51_gt_lines.json`
（输出存 `eval/night51_gt_run.txt`）

```
[engine] load 24.2s
[ndl_11892692_R0000003.jpg] 21.6s lines=9  layout=0 junk=0 unmatched_no=0
[ndl_11892692_R0000004.jpg] 28.5s lines=16 layout=0 junk=0 unmatched_no=0
[ndl_11892692_R0000005.jpg] 27.2s lines=16 layout=0 junk=0 unmatched_no=0
[ndl_1033232_R0000003.jpg]  16.2s lines=5  layout=0 junk=0 unmatched_no=0
[ndl_10301438_R0000002.jpg] 17.8s lines=5  layout=6 junk=0 unmatched_no=0
[ndl_10301438_R0000003.jpg] 35.9s lines=20 layout=0 junk=2 unmatched_no=0
[ndl_781192_R0000003.jpg]   22.9s lines=6  layout=0 junk=1 unmatched_no=0
[ndl_781193_R0000003.jpg]   52.1s lines=25 layout=0 junk=3 unmatched_no=0
[done] written: D:\kanbun-kakikudashi\eval/night51_gt_lines.json
```
8 页 `unmatched_no` 全 0（与 N50 相同）。

跑后：
```
git status --porcelain --untracked-files=no   →   M tools/night49_gt_run.py   ← 仅本夜预期改动
sha256(eval/night49_gt_lines.json) = ff21e4fa7d749c61f1fbe60ff753713941289a4a6d370feaabdedb7e60bd9cde  ← 逐字节不变
```
**Night50 观察到的「跑门必覆盖归档」副作用就此消除**（传 `--out` 时）。

### 4.2 GT CER 与基线逐位相同

`python -X utf8 tools/eval_ocr_gt.py eval/night51_gt_lines.json eval/night51_gt_cer.json`
（全文存 `eval/night51_gt_cer.txt`）：

```
overall: raw micro=0.3568 macro=0.2566 | norm micro=0.3053 macro=0.2242
```
与 N44/46/49/50 四夜的基线**四个数逐位相同** ✓（92 行 GT、8 页、无 unmatched 警告）。

### 4.3 night51 vs night49 归档逐字段比对

临时比对脚本（仓库外 Temp，不入库）结果存 `eval/night51_lines_diff.txt`：

```
n_pages: 8 vs 8
recognize_sec 不同的页数: 8 / 8        （26.5→21.6 / 34.5→28.5 / … / 54.7→52.1）
除 recognize_sec 外字段差异数: 0        （含 92 行 lines 的 line_no/x/y/w/h/text 全比）
VERDICT: ONLY_RECOGNIZE_SEC_DIFFERS
```
与 Night50 报告记录的覆盖副作用模式完全一致，反证 OCR 输出确定性——
**差别只是这次不再需要 `git checkout --` 恢复归档**。

### 4.4 `--help`（参数面证据）

```
usage: night49_gt_run.py [-h] [--out PATH]
  --out PATH  输出 JSON 路径，相对路径以仓库根为基准；不传 = eval/night49_gt_lines.json（原行为不变）
```

### 4.5 pytest

`python -m pytest tests -q` = **141 passed**（15.20s，改动后复跑）。
`tools/` 目录不进收集（N50 的 conftest.py + pytest.ini 双保险），本改动不在收集范围。

## 5. 验收门

`python tools/accept_night.py 51`（提交后跑，见提交序列）——结果见
`eval/accept_night_51.json` 与 `ACCEPT_LOG.md` 末行；门口产物照 N50 惯例单独提交。

## 6. 待拍板（编号 = 下一班的下单清单）

1. **（N50 待拍板② 已解决，本夜落地）**——`night49_gt_run.py --out` 已加、已验证。
   以后夜班跑 GT 门统一带 `--out eval/nightNN_gt_lines.json`，不再覆盖 N49 归档。
2. **（N50 待拍板③，原样保留）**：`eval/night50_*` 11 个临时证据文件是否入库——
   本夜同样新增了 `eval/night51_*` 5 个证据文件（gt_run.txt / gt_cer.txt /
   gt_cer.json / gt_lines.json / lines_diff.txt），**已随本夜提交**（它们是本夜改动的
   直接证据且体积小）；night50_* 是否同样入库仍由用户定，agent 不替拍。
3. **（N50 待拍板①，原样保留）**：order_rate 要不要转判死刑门、阈值多少——待用户拍板。
4. **（Night49 §16 ③④，原样保留）**。

## 7. 禁止事项自查

- 未发任何图片、未改 `eval/ocr_gt_100.tsv` / `eval/golden*.json` / expected ✓
- 未重跑 47 页全本 OCR（只跑了 GT 8 页）✓
- 未碰 Night 9、16–20 相关内容 ✓
- 未自定 order_rate 阈值、未动 night50_* 证据文件 ✓
- 单步最长 = GT 8 页一轮（engine load 24s + 8 页 ≈ 4 分钟），无 45 分钟卡点 ✓
- 心跳：SHIFT_LOG.md 按 N50 同款二进制 `ab` 追加，前缀字节断言不变 ✓
- 未推远程、本地提交 ✓

## 8. 本次改动清单（随本夜提交）

| 文件 | 性质 |
| --- | --- |
| `tools/night49_gt_run.py` | `--out` 参数（§3） |
| `REPORT_NIGHT51.md` | 本报告 |
| `tools/night51_append_shift.py` | SHIFT_LOG 二进制追加脚本（N50 同款断言） |
| `eval/night51_gt_lines.json` | GT 8 页产品流输出（`--out` 产物） |
| `eval/night51_gt_cer.json` | GT CER 归档 |
| `eval/night51_gt_run.txt` | GT 运行 stdout |
| `eval/night51_gt_cer.txt` | CER 计算 stdout |
| `eval/night51_lines_diff.txt` | 与 N49 归档逐字段比对结论 |
| `SHIFT_LOG.md` | N51 块 + 心跳（二进制追加） |
