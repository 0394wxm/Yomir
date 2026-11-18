# REPORT_DAY7.md — D7：OCR 批量进度接口 + 前端进度条

日期：2026-11-18 / 班次：白天 D7 / 产物：`backend/main.py`（新增 3 个端点）、
`backend/ocr_engine.py`（可选进度回调）、`frontend/src/App.tsx` + `App.css`（入口 C）、
`tests/test_ocr_batch_progress.py`、`tools/day7_batch_progress_probe.py`、
`eval/day7_progress_curve.json`

---

## 1. 原来的问题

`POST /api/ocr/batch` 是同步阻塞的：2 张图 126 秒，接口期间不返回任何东西，
前端只有一个静态「识别中」，用户不知道跑到第几张、还要多久。

## 2. 新增的三个端点

原有 `POST /api/ocr/batch` **保持不变**（测试基线和既有调用方不受影响），
新加一对异步端点：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/ocr/batch/async` | 提交作业，立即返回 `{"job_id":...}`（实测 0.03s） |
| GET | `/api/ocr/batch/<job_id>` | 进度快照（percent / done / total / phase / current_file） |
| POST | `/api/ocr/batch/<job_id>/cancel` | 取消（当前这张跑完即停） |

作业在后台线程里**串行**跑（延续 Night 11「不并行压 Celeron」的决定）。
作业表只在进程内存，保留最近 20 个、超过 1 小时的在下次创建时清掉；重启即丢——
OCR 输出本就是草稿，落库的只有训读结果，所以没做持久化。

## 3. 第一版是怎么错的（这段保留）

第一版 percent 只按「整张图完成数」算。**真机一跑就露了**（第一次运行，完整输出）：

```
   3.3s  loading  0/2   0.0%  -         0/0
  36.8s  loading  0/2   0.0%  -         0/0
  38.9s  running  0/2   0.0%  detect    0/1   ndl_1287221_R0000002.jpg
  53.8s  running  0/2   0.0%  detect    0/1   ndl_1287221_R0000002.jpg
  56.1s  running  0/2   0.0%  recognize 0/16  ndl_1287221_R0000002.jpg
  83.4s  running  0/2   0.0%  recognize 15/16 ndl_1287221_R0000002.jpg
  85.5s  running  1/2  50.0%  detect    0/1   ndl_11892692_R0000003.jpg
 115.9s  running  1/2  50.0%  recognize 8/9   ndl_11892692_R0000003.jpg
 118.0s  done     2/2 100.0%  -         9/9
```

**0.0% 持续了 85.5 秒**，然后一步跳到 50.0%，再卡 30 秒。对用户来说和没有进度条一样。
（20 张图会更糟：每 45 秒才跳 5%。）

修正：`_job_percent()` 把**当前这张图内部的行级进度**折算进去，detect 占该图的
0–15%、recognize 占 15–100%。为此 `recognize_bytes()` 加了可选的
`progress_cb(phase, done, total)`，在检测前后、以及每识别完一行时回调
（行识别走线程池，但 `ex.map` 按提交顺序 yield，所以回调是顺序的）。

单调性为什么仍成立：done 增加时 frac 归零，但 `(done+1)/total` 的涨幅
（2 张图时 0.5 = 50 个百分点）永远大于丢掉的 frac 上限（0.15/total = 7.5 个百分点）。

第一版不是我事后编出来凑数的——上面这段是它的真实输出，下面第 4 节是改完之后的真实输出。

## 4. 真机实测（改完之后，2 张本地样张，真模型）

```
   0.1s  loading  0/2   0.0%  -         0/0
  29.1s  running  0/2   0.0%  -         0/0
  31.3s  running  0/2   0.0%  detect    0/1   ndl_1287221_R0000002.jpg
  46.4s  running  0/2   7.5%  recognize 0/16  ndl_1287221_R0000002.jpg
  53.0s  running  0/2  12.8%  recognize 2/16  ndl_1287221_R0000002.jpg
  59.8s  running  0/2  28.7%  recognize 8/16  ndl_1287221_R0000002.jpg
  68.8s  running  0/2  39.4%  recognize 12/16 ndl_1287221_R0000002.jpg
  73.3s  running  1/2  50.0%  detect    0/1   ndl_11892692_R0000003.jpg
 101.9s  running  1/2  57.5%  recognize 0/9   ndl_11892692_R0000003.jpg
 108.7s  running  1/2  76.4%  recognize 4/9   ndl_11892692_R0000003.jpg
 115.4s  running  1/2  95.3%  recognize 8/9   ndl_11892692_R0000003.jpg
 117.6s  done     2/2 100.0%  -         9/9
```

| 指标 | 值 |
| --- | --- |
| 提交返回耗时 | **0.03s**（不阻塞） |
| 总耗时 | 117.6s（第 1 张 43.5s / 第 2 张 44.6s，其余为模型加载） |
| percent 出现的不同值 | **12 个**：0.0 / 7.5 / 12.8 / 18.1 / 28.7 / 36.7 / 39.4 / 50.0 / 57.5 / 76.4 / 95.3 / 100.0 |
| 单调 | **True** |
| 观察到 recognize 阶段 | **True** |
| 识别结果 | 2/2 `ok`，16 行 / 9 行，与 Night 11 的样张一致 |

### 还是有两段「不动」

1. **模型加载 29 秒**（`loading` 阶段）。ONNX 加载是黑盒，无法细分，
   前端只能显示「加载模型（首次约 10–50 秒）」这行静态文案。
2. **detect 阶段整段不动**。这是本次没修干净的：`progress_cb` 只在 detect
   开始（0/1）和结束（1/1）各调一次，中间没有粒度。看上面的时间轴——
   73.3s 到 101.9s 整整 **28.6 秒**停在 50.0%。第一张图的 detect 也停了 15 秒
   （31.3s → 46.4s）。要修得改 RTMDet 的推理循环按 tile 回调，属于改动引擎内部，
   超出「加进度接口」的范围，本次不做。

所以准确的说法是：**recognize 阶段（占单张图约 2/3 时间）有逐行进度，
detect 阶段和模型加载阶段没有**。不是「全程平滑」。

## 5. 前端

入口 B（单张）旁边加了**入口 C：批量上传（多张，带进度）**：

- 多选图片 → 「批量識別（N 张）」→ 立刻出现进度条
- 进度条下方一行：状态 · `done/total 张（percent%）` · 当前阶段 `识别文字 4/16` · 已用秒数
- 再下方：当前文件名 + 已完成文件的逐条结果（行数 / 秒数）
- 跑动中显示「取消」按钮
- 完成后把所有成功文件的白文按顺序拼进白文框，并刷新纠错基线，可直接接「重新訓読」

轮询：1 秒一次，上限 15 分钟（20 张实测约 8 分钟，留 2 倍余量）。
进度条纯 CSS（`.progressbar` / `.progressfill`），`transition: width 0.4s`，
无新依赖。

## 6. 测试

`tests/test_ocr_batch_progress.py`（6 个用例，全部用桩引擎，不加载真模型）：

| 用例 | 断言 |
| --- | --- |
| `test_async_batch_progress_monotonic` | done 与 percent 单调不减；结束时 100%；**单张图内部至少 3 个不同的中间 percent**；观察到 recognize；results 与文件一一对应 |
| `test_async_batch_reports_error_per_file` | 单文件异常 → 该文件 `ocr_error`，作业仍 `done` |
| `test_async_batch_missing_runtime_is_job_error` | 运行时缺失 → 作业 `error` 且带提示 |
| `test_progress_unknown_job_404` | 未知 job → 404 |
| `test_async_batch_no_files_422` | 不传 files → 422（FastAPI 层拦截，与同步端点一致） |
| `test_cancel_marks_job` | 取消后 `cancelled`，且 `done < total` |

其中「单张图内部至少 3 个中间值」这条是**专门用来卡住第一版那种整图跳变实现**的：
旧实现在 2 张图时只可能产出 0/50/100 三个值，这条断言必挂。

全量：`pytest tests -q` → **21 passed**（原 14 + D7 新增 6 + prev_request_id 回归 1）。
前端：`npx tsc --noEmit` 无输出；`npx vite build` → 30 modules，`built in 9.28s`。

## 7. 修掉的一个并发 bug

自查时发现：作业在 `loading`（模型加载，数十秒）阶段被取消，`get_engine()`
返回后代码会无条件 `job["status"] = "running"`，把 `cancelled` 覆盖掉。
已加两处判断：engine 取回后再查一次 `cancelled`；收尾写 `done` 前也查一次。
`test_cancel_marks_job` 覆盖这条路径。

## 7.5 顺手修掉一个既有 422（不在 D7 范围内，但卡住主流程）

浏览器实测时**第一次点「重新訓読」直接失败**：

```
{"detail":[{"type":"int_type","loc":["body","prev_request_id"],
            "msg":"Input should be a valid integer","input":null}]}
```

根因在 `KundokuRequest.prev_request_id: int = None`（NIGHT7 写的）。
pydantic v2 认为 `None` 不是合法 `int`，而前端 `runKundoku()` 在
`lastRequestId === null` 时正是发 `"prev_request_id": null`。
所以**任何用户第一次点「重新訓読」都必然 422**——这是既有 bug，与 D7 无关，
但在浏览器里一测就撞上了。已改为 `Optional[int] = None`。

为什么原有 14 个测试没抓到：所有用例都不发这个字段（走的是「字段缺失」路径），
没有一条发显式 `null`。已补 `test_prev_request_id_null_accepted`。

`git log` 确认：`571d36e`（D5 前的提交）里这行就是 `prev_request_id: int = None`，
不是本次引入的。

## 7.6 浏览器实测（GUI，不是接口）

用真实浏览器（ZCode 内置 IAB）打开 `http://127.0.0.1:5173/`：

| 测试点 | 结果 | 证据 |
| --- | --- | --- |
| 页面加载、入口 C 渲染 | **通过**：出现「入口 C：批量上传（多张，带进度）」+「批量識別（0 张）」并按预期禁用 | `docs/day7_gui/t1_batch_entry_initial.png` |
| 入口 C 的 file input 属性 | **通过**：`accept="image/*"`、`multiple` 存在、未禁用 | DOM 只读检查（见下） |
| 点击「选择文件」上传 | **无法执行**：IAB 返回 `File uploads are not supported by iab` | 运行时能力限制，非页面 bug |
| 进度条从 0 涨到 100% | **未能通过 GUI 验证**（受上一条阻塞） | 改由 API 层实测覆盖（第 4 节） |
| 贴合主流程回归（粘贴 → 訓読） | **通过**：返り点㆒㆓㆑、書き下し「王は左右を顧みて而して他を言う」、語釈 4 条、导出按钮启用 | `docs/day7_gui/t2_kundoku_after_fix.png` |

入口 C 控件的只读检查结果：

```
fileInputs[1]: { multiple: "", accept: "image/*", disabled: null }
button "批量識別（0 张）": enabled = false
```

**必须说清楚**：进度条的运行态（跑动中的百分比、取消按钮、逐文件结果列表）
**没有在真实浏览器里看到过**。这条链路的证据来自三处：
① 接口层真机实测（第 4 节，117.6s、12 个梯度、percent 单调）；
② 6 个桩引擎自动化测试（第 6 节，含「单张图内部至少 3 个中间值」的硬断言）；
③ 浏览器里确认了控件渲染与禁用逻辑正确。
**渲染 → 点击 → 进度**这三段没有在 GUI 里连起来跑过一次。

## 8. 已知限制

1. **detect 阶段没有粒度**（本次最明显的缺口）：单张 15–29 秒里 percent 只从
   0 爬到 7.5，然后停住不动，直到该图 detect 结束。实测第二张图有 28.6 秒静止。
   修它要改 RTMDet 推理循环按 tile 回调，属引擎内部改动，本次不做。
2. **模型加载的 29 秒没有进度**。ONNX 加载是黑盒，只能给静态文案。
3. **作业不持久化**：进程重启后 `/api/ocr/batch/<id>` 返回 404，需重新提交。
4. **取消不打断正在跑的推理**，只保证不再开始下一张。ONNX 推理没有安全的
   中断点，强行杀线程会留下脏状态。
5. 前端只做了批量入口，**没有做「批量结果逐张预览 + 单张重跑」**，
   完成后是全部拼进白文框。多页书如果把无关页也选进来，需要手工删。
6. 没有并发压测：本机是单核 Celeron，同时开两个作业只会互相拖慢，
   作业表也没做互斥（没有「同一时间只允许一个作业」的锁）。
   单用户桌面场景可以接受，多用户部署前必须补。

## 9. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -m pytest tests\test_ocr_batch_progress.py -q
python tools\day7_batch_progress_probe.py    :: 真模型 2 张，约 2 分钟，写 eval/day7_progress_curve.json
cd frontend && npx tsc --noEmit
```

曲线原始数据：`eval/day7_progress_curve.json`。
