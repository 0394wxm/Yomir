# REPORT_DAY15.md — D15：验收门 pytest 基线改为动态计数（2026-11-19）

任务单第一项。起点 `6875284`，分支 `ds/dayshift-text-mining`。

**结果：`MIN_PASSED` 硬编码常量删除，改为 `pytest --collect-only` 动态计数；
Night 22 / Night 35 回测均 PASS（除 repo_clean 的未提交改动）；
并用两个注入实验验证了新口径的实际行为——一个抓得住，一个抓不住，如实记录。**

---

## 1. 为什么要改

D13 把口径从 `tests/test_api.py`（15 例）改成全量 `tests`（当时 50 例），
同时把下限写成 `MIN_PASSED = 50`。D14 加了 15 个测试后，我不得不手动改成 65。

这个「手动同步」有两个失效方向：

| 失效方式 | 后果 |
| --- | --- |
| 加了测试但忘了上调基线 | 新测试不在门的保护范围（D13 前的状态，最危险） |
| 删了测试但忘了下调基线 | 门会误报 FAIL（烦人但安全） |

两个方向都靠人记着，而人一定会忘。动态计数的做法是：**收集到多少个，就要求过多少个**。

---

## 2. 实现

### 2.1 新增 `_count_collected()`

```python
def _count_collected():
    """用 pytest --collect-only 数出当前测试总数（D15）。

    为什么不再用硬编码基线：D13 写死 50、D14 加测试后要手改成 65，
    忘了改基线就等于「新增测试不在门的保护范围」，改错了又会误判。
    动态计数让「收集到多少就必须过多少」始终成立，不需要人工维护。
    """
    p = subprocess.run([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    text = p.stdout or ""
    # 末行形如 "65 tests collected in 2.36s"；无测试时是 "no tests ran"
    m = re.search(r"(\d+) tests? collected", text)
    if m:
        return int(m.group(1))
    # 退回按行数数（每行一个 test id），过滤汇总/空行
    ids = [l for l in text.strip().splitlines()
           if "::" in l and not l.startswith("=")]
    return len(ids)
```

**为什么解析汇总行而不是数行数**：`--collect-only -q` 的输出是每行一个 test id，
末行是 `65 tests collected in 2.36s`。数行数要排除汇总行和空行，
而汇总行本身已经给了准确数字——直接读它更稳。退回分支只用于汇总行格式变化的极端情况。

### 2.2 `check_pytest()` 的判定

```python
expected = _count_collected()
...
if p.returncode != 0:
    c.fail("pytest 退出码 %d" % p.returncode)
elif c.detail["passed"] < expected:
    c.fail("通过数 %d < 收集数 %d（有测试没通过/没跑）" % (...))
elif c.detail["passed"] > expected:
    c.notes.append("通过数 %d > 收集数 %d（差异已记录）" % (...))
else:
    c.notes.append("%d passed = %d collected（%.1fs，收集 %.1fs）" % (...))
```

- `passed < collected` → **FAIL**（有测试失败、报错、或没跑）
- `passed > collected` → 记录但不 FAIL（参数化动态生成等边缘情况，不该误判）
- 相等 → PASS

顺带把 `failed / error / skipped / xfailed / xpassed` 全部写进 `detail`，
以前只记 `failed`。

### 2.3 常量删除

```python
# 删掉：
MIN_PASSED = 65

# 换成：
# D13/D14 曾用硬编码 MIN_PASSED（14 → 50 → 65）作为 pytest 通过数下限。
# D15 改成动态：pytest --collect-only 数出多少就要求过多少（见 _count_collected）。
# 不再有常量需要维护。
```

`findstr /n "MIN_PASSED" tools/accept_night.py` 现在只命中那行注释。

---

## 3. 两个注入实验（这是本项最重要的部分）

只跑一遍绿灯不足以说明门真的有用。我做了两个注入实验。

### 3.1 注入一个必失败的测试 → 门抓得住 ✅

```python
# tests/test_d15_selftest_probe.py
def test_deliberate_failure():
    assert False, "D15 selftest probe"
```

```
[FAIL] pytest  tests 全量通过
verdict: FAIL (fail=2 skip=0, 31.0s)
```

`eval/accept_night_22.json` 的 detail：

```json
{
  "collected": 66,
  "passed": 65,
  "failed": 1,
  "returncode": 1,
  "tail": ["FAILED tests/test_d15_selftest_probe.py::test_deliberate_failure - AssertionE...",
           "1 failed, 65 passed in 11.45s"]
}
```

**收集数 66、通过数 65 → FAIL。** 探针删掉后恢复 `65 passed = 65 collected`。

### 3.2 删掉两个测试 → 门抓不住 ❌（如实记录）

把 `tests/test_rule_d_kore.py` 里最后两个测试截掉：

```
[PASS] pytest  tests 全量通过
        - 64 passed = 64 collected（15.8s，收集 5.5s）
```

**门报 PASS。** 因为「收集到 64、过了 64」在动态口径下完全自洽。

### 3.3 这个取舍必须写清楚

| 场景 | 硬编码基线（D13/D14） | 动态计数（D15） |
| --- | --- | --- |
| 新增测试但忘记上调 | 新测试不在保护范围（**漏**） | 自动覆盖（**对**） |
| 测试失败 | FAIL（对） | FAIL（对） |
| 测试被删 | FAIL（**对**） | PASS（**漏**） |

**动态口径用「防删测试」换「自动覆盖新测试」。**

我认为这个交换是划算的，理由：

1. **「忘记上调」是必然会发生的**——D13→D14 我就已经遇到一次，只隔了一天。
   「删测试」是**故意行为**，会在 diff 里留下明显痕迹（`git diff` 里 `-def test_`）。
2. 门不是唯一的防线：`repo_clean` 要求工作区干净，任何删测试的提交都会出现在
   `git log -p` 里；pytest 文件本身也在版本控制下。
3. 如果两者都要，正确做法不是把数字写死，而是**把「已收集的测试 id 清单」存成文件**
   并与 `--collect-only` 的输出做集合比较（多退少补都报警）。这是可行的，
   但它引入一个新维护物（清单文件），且每次加测试要重新生成——本项没做，列在 §5 待拍板。

**这条写进报告的原因**：如果只写「改成动态了，回测通过」，读的人会以为门变强了。
实际是**换了一种强法**，代价明确。

---

## 4. 回测

```
python tools/accept_night.py 22
[FAIL] repo_clean     已跟踪文件有未提交改动   ← 即将提交的改动
[PASS] pytest         65 passed = 65 collected（14.1s，收集 5.6s）
[PASS] eval_integrity
[PASS] rule_regression
[PASS] engine_smoke
[PASS] perf_envelope
verdict: FAIL (fail=1 skip=0, 31.4s)

python tools/accept_night.py 35
[FAIL] repo_clean     ← 同上
[PASS] pytest         65 passed = 65 collected（14.4s，收集 4.8s）
[SKIP] eval_integrity Night 35 未登记评测归档
[PASS] rule_regression
[PASS] engine_smoke
[PASS] perf_envelope
verdict: FAIL (fail=1 skip=1, 30.2s)
```

提交后复跑两个门都是 PASS（见 `ACCEPT_LOG.md`）。

### 4.1 门变慢了多少

`24s → 31s`。多出来的是 `--collect-only` 的 **4.8–5.6s**（pytest 要 import 所有
测试模块，包括 `backend.main` 的导入）。这比原来多 25%。

**这是可以接受的**：门本来就是「提交前跑一次」的东西，不是 CI 每 PR 跑十次。
如果将来觉得慢，优化方向是让 `--collect-only` 复用已导入的模块（同进程），
但那会引入状态污染风险，本项没做。

---

## 5. 遗留

| # | 事项 | 说明 |
| --- | --- | --- |
| 1 | **动态口径抓不住「删测试」** | 见 §3.3。要堵这个洞需要「测试 id 清单」基线，本次没做 |
| 2 | 门耗时 24s → 31s | 主要是 `--collect-only` 的 5s 导入开销 |
| 3 | `passed > collected` 只记录不 FAIL | 参数化/动态生成时可能出现，误判成本高于收益 |

---

## 6. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
set "PYTHONIOENCODING=utf-8"
cd /d D:\kanbun-kakikudashi

python -m pytest tests --collect-only -q     :: 65 tests collected
python -m pytest tests -q                    :: 65 passed
python tools\accept_night.py 22              :: 65 passed = 65 collected
python tools\accept_night.py 35              :: 65 passed = 65 collected
```

注入实验（可选，验证门的行为）：

```bat
:: 3.1 必失败测试
python -c "open('tests/test_probe.py','w').write('def test_x():\n    assert False\n')"
python tools\accept_night.py 22   :: pytest FAIL（collected 66 / passed 65）
del tests\test_probe.py

:: 3.2 删测试（演示动态口径的盲区）
:: 截掉 test_rule_d_kore.py 末尾两个测试后：
python tools\accept_night.py 22   :: pytest PASS（64 = 64）← 盲区
```

---

## 7. 禁止事项自查

- expected 一字未改；未碰 `eval/golden*.json`、`eval/ocr_gt_*`、`REPORT_NIGHT36.md`、
  `backend/ocr*.py`、`ocr_runtime/`、已有评测归档
- 注入的探针文件已删除（`tests/test_d15_selftest_probe.py` 不存在于工作区）
- 临时改动的 `tests/test_rule_d_kore.py` 已从 `.bak` 恢复，`65 passed` 复核
- 13 个 Night36 未跟踪文件未 `git add`
- 全程未发图、未读图、未打开任何图片文件
- 只本地提交到 `ds/dayshift-text-mining`，未推远程，未动 master
