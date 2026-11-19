# REPORT_DAY13.md — D13：三条拍板落地（2026-11-19）

白天班之后、夜班之前的一轮「收拾」。起点 `791e451`，分支 `ds/dayshift-text-mining`。

任务书三条（都是 REPORT_DAY12.md §10 的待拍板项，用户已拍板）：

1. `accept_night.py` 的 pytest 改成**全量** `python -m pytest tests -q`（50 例），跑 Night 22 和 Night 35 回测
2. 删 `frontend/src-tauri/sidecar/_internal/` 与 `frontend/src-tauri/target/release/sidecar/_internal/` 两个旧拷贝
3. `VITE_API_BASE` 尾斜杠归一化**留着不回退**

**结果：三条全部落地。验收门 pytest 由 15 例改为 50 例全量，Night 22 / 35 回测均 PASS；
两个旧拷贝（共 1,571 文件 / 976.0MB）已删除并留证；尾斜杠归一化保留（报告里写明理由）。**

---

## 1. 拍板项 1：验收门 pytest 口径改成全量

### 1.1 改了什么

`tools/accept_night.py`：

```python
# 改前
c = Check("pytest", "tests/test_api.py 全过")
p = subprocess.run([sys.executable, "-m", "pytest", "tests/test_api.py", "-q"], ...)
elif c.detail["passed"] < 14:            # 历史基线
    c.fail("通过数 %d < 14（历史基线）" % c.detail["passed"])

# 改后
c = Check("pytest", "tests 全量通过")
p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], ...)
elif c.detail["passed"] < MIN_PASSED:     # MIN_PASSED = 50
    c.fail("通过数 %d < %d（历史基线）" % (c.detail["passed"], MIN_PASSED))
```

新常量放在文件头部，带 D13 注释：

```python
# D13: pytest 检查的历史基线（全量 tests 的通过数下限）。
# 原来是写死的 14（test_api.py 的旧口径），现在全量是 50 例，
# 取 50 作为基线：任何一条测试消失都会让门 FAIL，防止「删测试换绿灯」。
MIN_PASSED = 50
```

### 1.2 为什么要提高基线，而不是只放开命令

只把 `tests/test_api.py` 换成 `tests`、基线仍留 14 的话，**删掉 36 个测试还能拿绿灯**。
所以基线同步提到 50。这条基线以后每次加测试都要跟着上调——
这是个真实成本，但比「门对新测试视而不见」便宜得多。

### 1.3 回测

```
python tools/accept_night.py 22
[FAIL] repo_clean        已跟踪文件有未提交改动：1 个   ← 即将提交的改动
[PASS] pytest            tests 全量通过
        - 50 passed（13.9s）
[PASS] eval_integrity
[PASS] rule_regression
[PASS] engine_smoke
[PASS] perf_envelope
verdict: FAIL  (fail=1 skip=0, 25.9s)

python tools/accept_night.py 35
[FAIL] repo_clean        ← 同上
[PASS] pytest            50 passed（15.2s）
[SKIP] eval_integrity    Night 35 未登记评测归档
[PASS] rule_regression
[PASS] engine_smoke
[PASS] perf_envelope
verdict: FAIL  (fail=1 skip=1, 25.8s)
```

**两个 FAIL 都只有 repo_clean**，原因是「有未提交改动」——提交后复跑应为全 PASS（§4 验证）。

### 1.4 副作用：门变慢了吗

`13.9s` / `15.2s` vs 原来的 `11.3s` / `~12s`。多出来的是 `test_rule_d_kore`（8 例）、
`test_sodashite_guard`、`test_ocr_batch_progress`、`test_lifespan_migration`（9 例）。
门整体 26s 左右，仍在可接受范围（原来 24s）。**没有为此做任何优化**——
这是「看得见」换来的代价，值得。

---

## 2. 拍板项 2：删两个旧 sidecar 拷贝

### 2.1 删前先证明它们确实是「未跟踪的构建产物」

```
git ls-files frontend/src-tauri/sidecar   → 0 行
git ls-files frontend/src-tauri/target    → 0 行

git check-ignore -v ...
  .gitignore:13:frontend/src-tauri/target/   ← target/release/sidecar/_internal/backend/main.py
  .gitignore:17:frontend/src-tauri/sidecar/  ← sidecar/_internal/backend/main.py
```

两条都命中 `.gitignore`，git 完全不管这两个目录。

### 2.2 删前取证（`tools/day13_purge_old_copies.py`，先 dry-run）

| 目录 | 文件数 | 体积 | 内含 main.py 有 on_event | 有 lifespan | dist JS 带死全局 |
| --- | --- | --- | --- | --- | --- |
| `sidecar/_internal` | 732 | 479.3 MB | **True** | False | 1 个 |
| `target/release/sidecar/_internal` | 839 | 496.7 MB | **True** | False | 1 个 |
| **合计** | **1,571** | **976.0 MB** | — | — | — |

`main.py` 时间戳：`2026-11-18 21:32` / `2026-11-18 20:46`，都是 D12 之前打包的。

**这就是 D12 报告里说的那个隐患**：如果将来谁把这俩目录 `git add` 进去，
会把带 `on_event` 的旧 `main.py` 和带死全局的旧 JS「复活」进仓库。

### 2.3 删除

```
python tools/day13_purge_old_copies.py --apply
frontend/src-tauri/sidecar/_internal                  files=732 MB=479.3  deleted in 0.7s
frontend/src-tauri/target/release/sidecar/_internal    files=839 MB=496.7  deleted in 0.7s
```

删后确认：两个目录只剩 `kanbun-sidecar.exe`（可执行文件本身没删——
它不是本次拍板项，且下次打包会被覆盖）。

### 2.4 保留了什么

- 证据 JSON：`eval/day13_old_copies.json`（删前快照 + 删除耗时 + apply 标记）
- 删除脚本：`tools/day13_purge_old_copies.py`（默认 dry-run，可复现「删前看到什么」）

**没有**动 `tools/day6_stage_sidecar.py`：下次打包它会重新生成 `sidecar/`，
那时复制的是 D12 之后的新代码（`lifespan`、无死全局）。这是正确的重建路径。

---

## 3. 拍板项 3：尾斜杠归一化保留

D12 把 `apiBase()` 改成：

```ts
return (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') ?? ''
```

**决定：保留。** 理由：

1. **只有一处生效路径**：本仓库所有构建方式都不设 `VITE_API_BASE`（默认空串），
   桌面壳走同源（后端托管 dist），浏览器开发走 vite 代理。`replace` 对空串是恒等操作。
2. **归一化是对的**：`VITE_API_BASE=https://x/api/` 在改前会拼出 `//api/kundoku`，
   多数服务器能容忍但不是所有都容忍（有的会 404 或重定向）。
   归一化后是确定行为。
3. **回退成本 > 收益**：回退要再改一次 `App.tsx` 并再跑一次 `tsc`/`build`，
   而它带来的唯一「好处」是保持一个 bug 的精确形状。

已在前端测试里锁定：`tests/test_lifespan_migration.py::test_frontend_has_no_kanbun_api_base_global`
只保证死全局不回来；尾斜杠行为本身没有专门测试（**这是遗留，见 §5**）。

---

## 4. 提交后复跑验收门

提交本次改动后：

```
python tools/accept_night.py 22 → verdict: PASS (6/6)
python tools/accept_night.py 35 → verdict: PASS (5/6 + 1 skip)
```

（原始输出见 `ACCEPT_LOG.md` 末尾两行与 `eval/accept_night_*.json`。）

---

## 5. 遗留（如实记录）

1. **`MIN_PASSED = 50` 是硬编码基线**。以后每加测试要手动上调，否则基线会
   落后于实际数量（安全方向：落后不会误放，只是不再是「一条都不许少」）。
   替代方案是「从上次提交记录的通过数读」，但这会让门依赖自身历史，暂不做。
2. **尾斜杠归一化没有专门单测**。要测它得跑 JS 测试框架（本仓库当前没有），
   或者把它抽成纯函数再在 build 里验证。本次没做。
3. **两个 `kanbun-sidecar.exe` 仍留着**（各约几十 MB）。它们也是旧拷贝，
   但删了会让 Tauri 的 resources 引用悬空（`Cargo.toml`/`tauri.conf.json` 指向 sidecar 目录）。
   下次打包重建是更安全的路径。

---

## 6. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
set "PYTHONIOENCODING=utf-8"
cd /d D:\kanbun-kakikudashi

python tools\accept_night.py 22            :: pytest 50 passed（全量）
python tools\accept_night.py 35            :: pytest 50 passed（全量）
python tools\day13_purge_old_copies.py     :: dry-run 测量（删后应报「不存在」）
```

---

## 7. 禁止事项自查

- expected 一字未改；未碰 `eval/golden*.json`、`eval/ocr_gt_*`、`REPORT_NIGHT36.md`、
  `backend/ocr*.py`、`ocr_runtime/`、已有评测归档
- 未碰 Night 9、Night 16-20、KuroNet、定价、部署
- 13 个 Night36 未跟踪文件未 `git add`
- 全程未发图、未读图、未打开任何图片文件
- 只本地提交到 `ds/dayshift-text-mining`，未推远程，未动 master
