# REPORT_DAY12.md — D12：死代码清理 + on_event 迁移 + 测试补到 50（2026-11-19）

白天班清单第 5 项（也是本次班次最后一项）。起点 `28c7097`，分支 `ds/dayshift-text-mining`。

**结果：`__KANBUN_API_BASE__` 死代码删除（Rust 侧确认 0 引用）、
`@app.on_event("startup")` → `lifespan` 迁移完成（DeprecationWarning 2 → 0）、
pytest 41 → **50 passed**、`npx tsc --noEmit` 干净、`vite build` 成功、验收门除 repo_clean 外全 PASS。**

---

## 1. 任务与边界

任务书写的是三件事：

1. 删 `__KANBUN_API_BASE__`（**先确认无引用**）
2. 修 `on_event` DeprecationWarning
3. 补测试到 **50 passed**，写 REPORT_DAY12.md 提交

不许改 expected、不许碰图片/OCR 轨道、不许推远程。本项全部照办。

---

## 2. 死代码确认（先查再删）

`python tools/grep_repo.py __KANBUN_API_BASE__` 的完整命中（删除前）：

| 位置 | 性质 |
| --- | --- |
| `frontend/src/App.tsx:11-14` | **唯一的功能性读取**（`window as ...` 后取属性） |
| `frontend/src/vite-env.d.ts:4-5` | 注释（提到「Rust 侧也能通过它注入」） |
| `REPORT_DAY6.md:109 / 303 / 305 / 310 / 394` | 历史报告，D6 就记录了「注入路径没有实测 / main.rs 里根本没有这段」 |
| `frontend/src-tauri/sidecar/_internal/frontend_dist/assets/*.js` | 打包产物（minified，未跟踪） |
| `frontend/src-tauri/target/release/sidecar/_internal/frontend_dist/assets/*.js` | 同上（未跟踪） |

**Rust 侧 0 处注入代码**——这一点 D6 的 §7.2 已经查过，这次复核一致：
`frontend/src-tauri/src/*.rs` 里没有 `__KANBUN_API_BASE__` 这个字符串。

结论：这是「读一个永远不存在的全局变量」的分支，删掉不改变任何运行时行为。

### 改动

```ts
// 删除前
function apiBase(): string {
  const injected = (window as unknown as { __KANBUN_API_BASE__?: string }).__KANBUN_API_BASE__
  if (injected) return injected.replace(/\/$/, '')
  return (import.meta.env.VITE_API_BASE as string | undefined) ?? ''
}

// 删除后（顺手把 VITE_API_BASE 的尾部斜杠也归一化——原来只有 injected 分支归一化）
function apiBase(): string {
  return (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') ?? ''
}
```

`vite-env.d.ts` 同步删掉那条说明，改成「D12 已删除，该注入从未实现」。
保留一行指向 `REPORT_DAY6.md §7.2` 的注释——**删代码但不删历史**，
免得下一个人从报告里读到这名字又把它加回来。

---

## 3. on_event → lifespan 迁移

### 3.1 改动结构

迁移有个必须注意的顺序问题：`lifespan` 必须在 `app = FastAPI(...)` **之前**定义，
因为 `lifespan=lifespan` 是构造参数，不是事后注册。原文件里 `app` 在第 124 行、
`ENGINE`/`_load_engine()` 在它后面，所以这次是：

```
import ... from contextlib import asynccontextmanager     ← 新增
...
ENGINE = None / ENGINE_ERROR = ""                          ← 上移（lifespan 要用 _load_engine）
def _load_engine(): ...
@asynccontextmanager
async def lifespan(_app): ...                              ← 原 startup() 函数体，末尾 yield
app = FastAPI(..., lifespan=lifespan)                      ← 下移到这里
```

### 3.2 行为逐条对齐（迁移前 vs 迁移后）

| 行为 | 迁移前 `startup()` | 迁移后 `lifespan()` | 一致 |
| --- | --- | --- | --- |
| 建表 | `db.init_db()` 第一条 | 同 | ✅ |
| 惰性模式判定 | `KANBUN_LAZY_ENGINE in ("1","true","yes","on")` | 同 | ✅ |
| 惰性模式 | 起 `engine-loader` 守护线程 | 同 | ✅ |
| 普通模式 | 同步 `_load_engine()` | 同 | ✅ |
| 引擎失败 | 捕获、写 `ENGINE_ERROR`、不阻止启动 | 同 | ✅ |
| OCR 探测日志 | `logger.info("ocr available: %s", is_available())` | 同 | ✅ |
| 关停 | 无 | `yield` 后无收尾（与原来一致） | ✅ |

唯一的代码形态变化：内层 `_bg()` 里的 `global ENGINE_ERROR` 从 `except` 块里
提到了函数开头——语义完全等价（Python 的 `global` 是编译期声明，位置不影响行为），
只是原来那个位置在 `except` 里看着别扭。

### 3.3 取证：警告真的少了两条

`tools/day12_warn_check.py` 把 HEAD 版 `backend/main.py` 导出到仓外临时目录，
在各自子进程里 `import` 并用 `warnings.catch_warnings(record=True)` 计数：

```
=== 当前工作区 backend.main ===
count=0
rc=0

=== HEAD 版（@app.on_event）===
count=2
  on_event is deprecated, use lifespan event handlers instead.
  on_event is deprecated, use lifespan event handlers instead.
rc=0
```

**2 → 0。** 两条分别来自 `@app.on_event("startup")` 和它对 `app.add_event_handler` 的内部调用。

### 3.4 值得记录的一点：仓库里还有两处 on_event 命中

`python tools/grep_repo.py on_event` 会命中：

```
frontend/src-tauri/sidecar/_internal/backend/main.py:142
frontend/src-tauri/target/release/sidecar/_internal/backend/main.py:142
```

这两处是**打包时的旧拷贝**（`git ls-files` 对这两个目录返回空，全是未跟踪构建产物）。
源码里唯一的 `on_event` 出现在迁移说明的 docstring 里。下次谁 grep 到这两行，
先确认它在不在 `git ls-files` 里，不要在源码里找。

---

## 4. 测试 41 → 50

新增 `tests/test_lifespan_migration.py`，9 例：

| 测试 | 锁什么 | 怎么锁 |
| --- | --- | --- |
| `test_no_on_event_handlers_registered` | `app.router.on_startup/on_shutdown` 必须为空 | 直接断言（on_event 会长回来） |
| `test_lifespan_is_wired_into_app` | `app.router.lifespan_context is m.lifespan` | 防止「定义了 lifespan 却没传给 FastAPI」 |
| `test_lifespan_calls_init_db` | 建表在加载引擎**之前** | monkeypatch 两个依赖，记录调用顺序 → `["init_db","load_engine"]` |
| `test_lifespan_sync_mode_loads_engine` | 普通模式同步加载 | 断言 `_load_engine` 被调用且 `ENGINE_ERROR` 为空 |
| `test_lifespan_lazy_mode_loads_in_background` | sidecar 模式不阻塞 | 设 `KANBUN_LAZY_ENGINE=1`，`threading.Event` 等后台线程 |
| `test_lifespan_swallows_engine_failure` | 引擎失败不阻止启动 | 假 `_load_engine` 抛错，断言 `ENGINE_ERROR` 含错误文本 |
| `test_lifespan_closes_cleanly` | `yield` 之后无异常 | 正常跑完即通过 |
| `test_import_has_no_startup_deprecation_warning` | 警告不许回来 | **子进程** `-W error::DeprecationWarning` 导入（本进程已导入过，警告只出一次） |
| `test_frontend_has_no_kanbun_api_base_global` | 前端死代码不许长回来 | 逐行去 `//` 注释后查 `App.tsx` / `vite-env.d.ts` |

最后一条第一版写错了：直接对全文 `assert "..." not in body`，结果被**我自己写的说明性注释**
绊倒（注释里提到了这个名字）。改成「只查代码行」后通过——**这说明测试要锁的是代码，
不是文字**，与 D11 那条「护栏要用逐条核对验证」是同一类教训。

`python -m pytest tests -q` → **50 passed in 13.27s**（原 41 + 9）。

---

## 5. 前端侧验证

```
npx tsc --noEmit          → 无输出（干净）
npx vite build            → ✓ 30 modules transformed, built in 7.79s
                            dist/index.html 0.41 kB / index-*.css 3.55 kB / index-*.js 234.96 kB
```

`frontend/dist/` 在 `.gitignore:10`，构建产物不入库。

---

## 6. 验收门

```
python tools/accept_night.py 35
[FAIL] repo_clean        已跟踪文件有未提交改动：3 个   ← 即将提交的改动，行为正确
[PASS] pytest            15 passed（11.3s）             ← 门的子集口径，不是全量 50
[SKIP] eval_integrity    Night 35 未登记评测归档
[PASS] rule_regression   Rule C' 护栏正常；ふ→う/は曰く 正常；正字化幂等；合并词表 21 条
[PASS] engine_smoke      6 项全部符合约定
[PASS] perf_envelope     短句中位 9ms
verdict: FAIL (fail=1 skip=1, 24.0s)

python tools/accept_night.py 22
[FAIL] repo_clean        ← 同上
[PASS] pytest
[PASS] eval_integrity    ← Night 22 有归档，真的查了
[PASS] rule_regression
[PASS] engine_smoke
[PASS] perf_envelope
verdict: FAIL (fail=1 skip=0, 28.0s)
```

两个 FAIL 都只有 repo_clean，原因就是「有未提交改动」，提交后自然消失（D11 时同样的现象）。

**注意 `pytest 15 passed` ≠ 全量 50**：`accept_night.py` 的 pytest 检查只跑
`tests/test_api.py`（D2 时按当时的测试文件清单写的）。全量在 `python -m pytest tests -q`。
这不是 bug，但看门的人容易误会，这里明写一句。

---

## 7. 交付物

| 文件 | 说明 | 行数 |
| --- | --- | --- |
| `backend/main.py` | on_event → lifespan；`app` 下移；导入 `asynccontextmanager` | +23 / -9 |
| `frontend/src/App.tsx` | 删 `__KANBUN_API_BASE__` 分支；`VITE_API_BASE` 也做尾部斜杠归一化 | +2 / -6 |
| `frontend/src/vite-env.d.ts` | 删死代码说明 | +2 / -2 |
| `tests/test_lifespan_migration.py` | 9 个锁定测试 | 新文件 ~170 行 |
| `tools/day12_warn_check.py` | 迁移前后 DeprecationWarning 计数取证 | 新文件 |
| `REPORT_DAY12.md` | 本文件 | — |

---

## 8. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
set "PYTHONIOENCODING=utf-8"
cd /d D:\kanbun-kakikudashi

python -m pytest tests -q                 :: 50 passed
python tools\day12_warn_check.py          :: count=0（当前）/ count=2（HEAD 版）
python tools\accept_night.py 35           :: 除 repo_clean 外全 PASS（未提交时）
cd frontend && npx tsc --noEmit && npx vite build
```

---

## 9. 禁止事项自查

- **expected 一字未改**：本项没碰任何 `golden*.json` / 评测归档
  （`eval/accept_night_22.json`、`eval/accept_night_35.json` 的变动是**验收门自己写的**，
  D2 已把它们列入 gate-owned 白名单）
- 未碰 `eval/ocr_gt_*`、`REPORT_NIGHT36/37/38.md`、`backend/ocr*.py`、`ocr_runtime/`、
  `eval/golden.json`、`eval/golden_1000.json`、已有评测归档
- 未碰 Night 9、Night 16-20、KuroNet、定价、部署
- 13 个 Night36 未跟踪文件**没有** `git add`（提交时按路径逐个 add）
- 全程未发图、未读图、未打开任何图片文件
- 只本地提交到 `ds/dayshift-text-mining`，未推远程，未动 master

---

## 10. 遗留（如实记录，留给你拍板）

1. **`accept_night.py` 的 pytest 检查只覆盖 `tests/test_api.py`**。
   现在全量测试有 4 个文件、50 例，门只跑其中一个（15 例）。
   门因此错过了 `test_lifespan_migration.py` / `test_rule_d_kore.py` / `test_sodashite_guard.py` /
   `test_ocr_batch_progress.py` 的回归。**改不改口径是决策，不是 bug 修复**，D12 没动。
2. **`frontend/src-tauri/sidecar/_internal/` 与 `target/release/sidecar/_internal/` 是旧拷贝**，
   里面有旧版 `main.py`（仍带 `on_event`）和旧 dist JS（仍带死分支）。
   它们是构建产物、未跟踪、下次 `tools/day6_stage_sidecar.py` 重跑会覆盖。
   如果将来有人把这两个目录加进 git，就会把死代码「复活」进仓库。
3. **`apiBase()` 的尾部斜杠归一化**是本项的顺带修正（原来只有 `injected` 分支做）。
   若 `VITE_API_BASE` 本来就以 `/` 结尾（例如 `https://x/api/`），改前会拼出 `//api/kundoku`、
   改后是 `/api/kundoku`。这是行为变化，但只在「构建时显式设了带尾斜杠的 VITE_API_BASE」时生效；
   本仓库当前的所有构建方式都不设它（空串默认）。**如果要求绝对零行为变化，这一处可以回退**，
   只需要删 `?.replace(/\/$/, '')` 那一段。
