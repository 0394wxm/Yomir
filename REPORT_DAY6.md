# REPORT_DAY6 — Tauri 桌面壳 + sidecar 打包（Night 14）

日期：2026-11-18
任务书条目：D6「桌面版离线：后端随壳启动、OCR 模型随壳打包、断网能跑訓読（現代語訳无 key 时仍占位）」
状态：**完成**（壳可启动、sidecar 随包、OCR 随包、断网可訓読；安装包未产出，见 §7）

---

## 1. 结论先说

桌面壳现在能自己拉起随包的后端、打开窗口、跑通訓読与 OCR：

| 验收项 | 结果 | 证据 |
|---|---|---|
| 壳启动 sidecar | ✅ | `[kanbun] sidecar 已启动: …\release\sidecar\kanbun-sidecar.exe` / `sidecar 端口 8000` |
| 窗口加载页面 | ✅ | 截图 `eval/day6_tauri_window.png`（含返り点・書き下し・入口 C 进度框） |
| 断网可訓読 | ✅ | `王顧左右而言他` → `王は左右を顧みて而して他を言う`（打包 exe 实测） |
| OCR 随包 | ✅ | 真实样本图 10 行 / 40 字 / 36.7 秒（打包 exe 实测） |
| 現代語訳占位 | ✅ | 无 key 时返回「待接入 LLM（占位）」，不出网 |
| 关窗清理 sidecar | ✅ | `CloseMainWindow()` 后 `tasklist` 无残留 |
| 端到端脚本 | ✅ | `tools/day6_sidecar_e2e.py` 6/6 通过 |
| 离线审计 | ✅ | `tools/day6_offline_audit.py` 12/12 通过 |
| 模块完整性审计 | ✅ | `tools/day6_pyz_audit.py` 17/17 必需模块在包内 |

体积从第一版的 **946.8 MB** 降到 **493.4 MB**（−453.4 MB，−47.9%）。

---

## 2. 为什么要 sidecar，而不是「Tauri 直接内嵌 Python」

三条被实测否掉的路：

1. **PyO3 把后端编进 Rust**：`udkanbun` 依赖 `ufal.udpipe` + MeCab 的 SWIG 绑定，
   在 Windows 上要用 MSVC 重编两个 C++ 项目，且 `unidic2ud` 会按包内相对路径找词典。
   改造面远超一天。
2. **Tauri 直接加载 `dist/` 再跨域调 127.0.0.1**：端口是动态的（8000 可能被占），
   每个请求都要 CORS 预检，CSP 要开白名单，且 `connect-src` 得写死端口。
3. **onefile PyInstaller**：每次启动要把几百 MB 解压到 `%TEMP%`。本机 Celeron，
   实测同类 onefile 启动要几十秒且窗口白屏。

选定方案：**onedir sidecar + 后端托管前端（同源）**。
- sidecar 用 stdout 打印 `KANBUN_PORT=<n>`，Rust 读到就把窗口指过去；
- 页面由同一个 FastAPI 进程发出，`/api/*` 天然同源，**零 CORS**；
- 端口冲突由 sidecar 从 8000 起自动找空闲端口解决。

---

## 3. 实现细节

### 3.1 `sidecar_entry.py`（入口）

```python
port = _free_port()                      # 8000 起找第一个空闲端口
sys.stdout.write("KANBUN_PORT=%d\n" % port)   # 必须先于 uvicorn，且 flush
sys.stdout.flush()
os.environ.setdefault("KANBUN_SIDECAR", "1")
uvicorn.run(app, host="127.0.0.1", port=port, ...)
```

`_bootstrap_paths()` 负责把 `_MEIPASS` 下的 `backend/` 挂上 `sys.path`，
并把 `KANBUN_OCR_SITE`/`KANBUN_OCR_SRC` 指向随包目录（否则会去读开发机的
`D:\dlkotenocr-lite`）。只监听 `127.0.0.1`，不暴露到局域网。

### 3.2 引擎异步加载（`backend/main.py`）

`KANBUN_LAZY_ENGINE=1` 时 startup 只 `threading.Thread(...).start()` 就返回，
端口立刻可用；前端自己轮询 `/health` 显示「引擎加载中」。

实测时间线（打包 exe，冷启动）：

| 时刻 | 事件 |
|---|---|
| 3.05 s | 打印 `KANBUN_PORT=8000`（窗口可开） |
| 22.02 s | `/health` 报 `engine_loaded=true`（可訓読） |
| 23.20 s | 首次 `/api/kundoku` 返回（含预热） |

普通模式（`KANBUN_LAZY_ENGINE` 未设）仍同步加载——测试依赖 startup 返回时
引擎已就绪，这个行为没动。

### 3.3 后端托管前端（零 CORS）

`_mount_web()` 在 `KANBUN_SIDECAR=1` 或 `KANBUN_SERVE_WEB=1` 时挂载：
- `/assets/*` → `StaticFiles`；
- `/` → `index.html`；
- 其余非 API 路径 → 回落 `index.html`（SPA）。

**踩到的坑（值得记下）**：一开始在 `_mount_web()` 里又注册了一个
`@app.get("/")`，结果前端首页永远拿不到——返回的是 JSON。
原因是 Starlette 的路由**按注册顺序匹配**，`root()` 在文件靠前处注册，
永远先命中，后注册的同路径路由不可达。
修法：`root()` 查模块级变量 `_WEB_DIST` 分流：

```python
@app.get("/")
def root():
    if _WEB_DIST:
        return _web_index()          # FileResponse(index.html)
    return {"service": "kanbun-kakikudashi", ...}   # 纯 API 模式不变
```

`tests/test_web_mount.py` 锁住了这个行为（4 个用例）。

### 3.4 前端侧

`App.tsx` 新增 `apiBase()`：

```ts
function apiBase(): string {
  const injected = (window as unknown as { __KANBUN_API_BASE__?: string }).__KANBUN_API_BASE__
  if (injected) return injected.replace(/\/$/, '')
  return (import.meta.env.VITE_API_BASE as string | undefined) ?? ''
}
```

三档优先级：Rust 注入 > 构建时 `VITE_API_BASE` > 空（同源）。
桌面壳走空字符串，请求 `/api/kundoku` 打到同一个进程。

另加 `/health` 轮询（1 秒一次，最多 90 次），页头显示
「引擎加载中…（首次启动约 10–30 秒）」或「引擎未就绪：<错误>」。
这不是装饰：sidecar 模式下端口 3 秒就开了，用户如果在这 19 秒里点訓読，
没这个提示就是纯粹的干等。

创建了 `frontend/src/vite-env.d.ts` 声明 `ImportMetaEnv` —— 项目原本没有
`vite/client` 类型，`import.meta.env` 过不了 `tsc`（TS2339）。

### 3.5 Rust 壳（`frontend/src-tauri/src/main.rs`）

```
setup()
  ├─ find_running_backend()        8000–8009 有东西就复用（不重复起）
  ├─ spawn_sidecar(resource_dir)   按候选路径找 exe，设 KANBUN_LAZY_ENGINE=1
  ├─ read_sidecar_port(60s)        读 stdout 的 KANBUN_PORT=
  └─ WebviewWindowBuilder::new(..., WebviewUrl::External(127.0.0.1:port))
RunEvent::Exit → child.kill() + child.wait()
```

sidecar 的启动从 `main()` 挪进了 `setup()`：`app.path().resource_dir()`
只有在 app 构建完成后才可用，而安装后 exe 就在 resources 里。

候选路径（按可能性排序）：
1. `<resource_dir>/sidecar/kanbun-sidecar.exe` — 安装后
2. `<exe_dir>/kanbun-sidecar/kanbun-sidecar.exe` — 同目录
3. `<exe_dir>/../../../dist/kanbun-sidecar/kanbun-sidecar.exe` — 开发

### 3.6 打包配置（`kanbun_sidecar.spec`）

onedir，`console=True`（Rust 要读 stdout）。随包内容：

| 内容 | 文件数 | 体积 |
|---|---|---|
| `unidic2ud/download`（qkana 词典） | — | 258.0 MB |
| `ocr_runtime/src`（模型 + 代码） | — | 78.9 MB |
| `ocr_site/onnxruntime` | 316 | 37.3 MB |
| `numpy.libs`（OpenBLAS） | — | 19.6 MB |
| `udkanbun/ud-kanbun.udpipe` | 1 | 16.2 MB |
| `ocr_site/PIL` | 105 | 13.8 MB |
| `udkanbun/mecab-kanbun` | 13 | 7.4 MB |
| `ocr_site/lxml` | 69 | 7.1 MB |
| `backend/` | 9 | — |
| `frontend_dist/` | 3 | — |
| **合计** | **733** | **493.4 MB** |

---

## 4. 体积优化的三轮实测

### 第一版：946.8 MB

`tools/day6_sidecar_size.py` 的头号条目：

```
295.2 MB  torch_cpu.dll
 30.0 MB  qkana_official.zip.part
```

`tools/day6_import_audit.py` 证明 `import udkundoku` / `import unidic2ud`
之后 `sys.modules` 里 torch 相关模块数为 **0** —— torch 纯粹是 PyInstaller
顺着 site-packages 里的 hook 误收集。`.part` 是下载残留，不是运行时数据。

### 第二版：526.5 MB（`excludes` + `skip_ext`）

加了 `excludes=[torch, transformers, …]` 和
`skip_ext=(".pyc",".part",".zip",".tmp")`。

此时发现 numpy 被装了两份：`_internal/numpy`（PyInstaller 自动收集 2.5.5）
和 `_internal/ocr_site/numpy`（我从 dlkotenocr 手动复制的 2.2.2）。
**冻结导入器（FrozenImporter 在 `sys.meta_path` 前部）优先于 `sys.path` 尾部的
`ocr_site`**，所以第二份永远不会被用到——纯死重量约 40 MB。移出 OCR_KEEP。

### 第三版：511.6 MB（收 udkanbun 数据）

引擎加载直接失败：

```
[ifs] no such file or directory: …\_internal\udkanbun\mecabrc
```

`udkanbun` 的 `.py` 被 PyInstaller 收了，但 `mecabrc` / `mecab-kanbun/` /
`ud-kanbun.udpipe` 是**数据文件**，不会自动收。改用：

```python
collect_data_files("udkanbun", excludes=["supar-kanbun/**"])
```

`supar-kanbun/` 是 442.1 MB 的 guwenbert 模型，而 `udkundoku.load()` 传
`model=None` 走 `ud-kanbun.udpipe`，用不到它。收进 20 个文件、23.6 MB。

### 第四版：491.8 MB（剔素材与误收集）

- `ocr_runtime/samples/`（12.3 MB 示例图）：`backend/` 与 `ocr_runtime/`
  全量 grep 无引用，纯素材。
- `nltk`（0.7 MB）、`emoji`（4.3 MB）：同上，无引用。

### 第五版（最终）：493.5 MB

**这一版比上一版大了 1.7 MB，因为把 networkx 加回来了** —— 见 §5。

---

## 5. 我犯的一个错，和它暴露的方法论问题

第四版打完包，`/api/ocr` 直接崩：

```
File "…\ocr_runtime\src\reading_order\order\smooth_order.py", line 8, in <module>
    import networkx as nx
ModuleNotFoundError: No module named 'networkx'
```

**为什么会错**：我把 `networkx` 写进了 `excludes`，理由是
`tools/day6_import_audit.py` 显示 torch 相关模块数为 0、「引擎包很干净」。
但那个脚本只扫了 `backend/` 和 `udkundoku`/`unidic2ud` 两个引擎包，
**没有扫 `ocr_runtime/`** —— 而 `ocr_runtime/src/ocr.py` 在模块顶层就
`from reading_order.xy_cut.eval import eval_xml`，链到 `smooth_order.py`
里的 networkx。

这个 bug 的恶劣之处：打包出来的 sidecar 能起、能訓読、`/health` 说
`ocr_available: true`，**只有真的传一张图才会崩**。如果不做 OCR 实测，
它会一路带着这个 bug 交出去。

**怎么修的**：
1. `excludes` 里去掉 `networkx`，并在注释里写明「OCR 阅读顺序排序用它」；
2. `day6_import_audit.py` 的扫描范围加上 `ocr_runtime/src`，在 docstring 里
   记下这个教训；
3. 新写 `tools/day6_import_audit2.py`：用 AST 从真实运行路径的源码抽 import，
   不再依赖人工清单；
4. 新写 `tools/day6_pyz_audit.py`：直接读 `PYZ-00.pyz` 的目录表判断包在不在
   （不能只看 `_internal/` 有没有同名目录 —— 纯 Python 包在 PYZ 里）；
5. 新写 `tools/day6_ocr_probe.py`：拿真实样本图打 HTTP，验证 OCR 真的能跑。

最终审计结果：

```
必需模块 17/17 OK   （含 networkx、PIL、lxml、onnxruntime、MeCab、ufal…）
刻意排除 6/6 已排除 （torch、matplotlib、cv2、yaspin、nltk、emoji）
```

---

## 6. 体积还能不能再降

现状 493.5 MB，其中 **470 MB（95%）是不可压缩的数据**：

| 项 | 体积 | 能不能去 |
|---|---|---|
| qkana 词典 `sys.dic` + `matrix.bin` | 247 MB | 不能。訓読的核心词典 |
| OCR 两个 onnx 模型 | 78.9 MB | 不能。OCR 的核心模型 |
| onnxruntime | 37.3 MB | 不能。推理运行时 |
| ud-kanbun.udpipe | 16.2 MB | 不能。依存解析模型 |
| mecab-kanbun 词典 | 7.4 MB | 不能。漢文分词词典 |
| numpy + OpenBLAS | 23 MB | 不能。OCR 预处理 |

**可再挤的空间**（未做，因为收益小、风险高）：
- `ocr_site/PIL` 13.8 MB：`_avif.cp312-win_amd64.pyd` 一个文件就 7.5 MB，
  AVIF 解码器对漢籍扫描件毫无用处。可删，省 7.5 MB。
- `ocr_site/lxml` 7.1 MB：可以试试换成 `xml.etree`，但要改 OCR 源码。
- `ccache` 之外的 `.pdb`：已经 `strip = true`。

结论：**想要显著更小，只能换分发形态**（例如把 qkana 词典做成首次运行下载，
但那违反「断网能跑」的任务要求）。493.4 MB 是这个架构下的合理值。

---

## 7. 没做到的 / 已知问题

### 7.1 安装包（NSIS）没有产出

`npx @tauri-apps/cli@2 build --no-bundle` 失败：

```
error: unexpected argument ';' found
Usage: cargo.exe build [OPTIONS]
```

CLI 把某个含 `;` 的东西当成参数传给了 cargo。直接 `cargo build --release`
可以成功（Rust 侧通过 `generate_context!` 在编译期读 `tauri.conf.json`），
所以**壳本身是验证过的**，缺的只是 NSIS 封装这一步。

为什么没继续：任务书要求「Rust 卡 45 分钟就停」。NSIS 打包需要下载
NSIS 插件包（联网），而本机是孤立沙盒，很可能下不下来。这属于「需要用户
拍板/联网」的事，不该在没网的环境里硬试。**§9 列出复现命令**。

### 7.2 `__KANBUN_API_BASE__` 注入路径没有实测

`App.tsx` 里写了 `window.__KANBUN_API_BASE__` 的读取逻辑，但 Rust 侧
**没有真的注入**（因为最终走的是同源方案，不需要）。这段代码目前是
「保留能力」而非「已验证路径」。诚实地说明：它没有测试覆盖。

写报告时发现原注释是**错的**——它写着「桌面壳：Rust 侧通过
`window.__KANBUN_API_BASE__` 注入实际端口」，但 `main.rs` 里根本没有这段
代码，且最终方案是同源、也不需要它。已改成准确描述（标明"当前未实现"），
避免后来的人按注释去找一段不存在的 Rust 代码。

### 7.3 关窗时的优雅退出

现在 `RunEvent::Exit` 里是 `child.kill()`（硬杀），不是 `terminate()`。
Windows 上 `Child::kill()` 调 `TerminateProcess`，uvicorn 收不到 CTRL_BREAK。
对 sidecar 这种无状态进程没影响（DB 是 SQLite，每个请求自己 commit+close），
但如果将来 sidecar 里有长事务或写文件的任务，需要改成先发信号再 kill。

### 7.4 引擎加载 22 秒，窗口前 22 秒不能訓読

已用前端提示缓解（「引擎加载中…」），但没做**预加载**（比如上次退出时
缓存引擎状态）。这属于性能优化，不在 D6 范围内。

### 7.5 只测了 Windows

所有路径分隔符、`sys._MEIPASS`、`taskkill` 都是 Windows 专用。
macOS/Linux 没有验证（也没有环境）。

### 7.5.1 Rust release 构建实测 25–35 分钟

`Cargo.toml` 里 `lto = true` + `codegen-units = 1`（体积优化配置），
首次构建整套 Tauri 依赖在本机（Celeron）上实测：

| 阶段 | 耗时 |
|---|---|
| `cargo check --release` | 34 s |
| `cargo build --release`（首次，全量依赖） | ~63 分钟（20:21 → 21:24） |
| `cargo build --release`（仅改 sidecar 资源） | 未单独计时 |

这已经超过任务书「单步卡 45 分钟就跳过」的阈值。
**但每次重编都是完整 LTO 链接，不是卡死**——`rustc.exe` 一直在占 CPU 和内存
（752 MB → 828 MB 缓增），产物最终正常生成。如果后续要频繁改 Rust 侧，
建议开发期把 `lto` 关掉，只在发版时开。

### 7.6 打包版没有跑完整回归

`pytest` 的 25 个用例跑在**源码环境**（`D:\Python312`），不是打包产物。
打包产物只做了：
- `/health`、`/`、`/assets/*`、`/api/kundoku`（e2e 6 项）
- 一次真实 OCR（10 行 / 40 字）
- 一次批量进度（未跑，但 D7 的代码路径与单张相同）

这个覆盖面对 D6 的验收项是够的，但不是「打包版全量回归」。

---

## 8. 复现步骤

```bat
set PATH=C:\Users\Wang\.cargo\bin;D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
cd /d D:\kanbun-kakikudashi

:: 1. 构建前端（含 /health 轮询）
cd frontend && npx vite build && cd ..

:: 2. 打包 sidecar（约 3.5 分钟）
python -m PyInstaller --noconfirm kanbun_sidecar.spec

:: 3. 验收（需已有 sidecar 在跑）
dist\kanbun-sidecar\kanbun-sidecar.exe          :: 另开一个窗口
python tools\day6_sidecar_e2e.py 8000
python tools\day6_ocr_probe.py 8000
python tools\day6_offline_audit.py
python tools\day6_pyz_audit.py

:: 4. 暂存到 Tauri resources，构建壳（LTO，约 25 分钟）
python tools\day6_stage_sidecar.py
cd frontend\src-tauri && cargo build --release
cd target\release && kanbun-kakikudashi.exe
```

---

## 9. 需要用户拍板的事

1. **NSIS 安装包**要不要做？做的话需要一个能联网的环境（下载 NSIS 插件）。
   命令是 `npx @tauri-apps/cli@2 build`（不带 `--no-bundle`）。
2. **493.4 MB 的体积**能不能接受？如果不能，唯一的大头是 qkana 词典
   （247 MB），只能改成「首次运行下载」，但那违反「断网能跑」的要求。
3. **22 秒引擎加载**要不要优化？可选方案是 sidecar 常驻（开机自启），
   但那是「安装成服务」的形态，属于产品决策。
4. `__KANBUN_API_BASE__` 注入路径（§7.2）要不要补实现+测试，还是直接删掉
   这段死代码？

---

## 10. 本轮改动的文件

新增：
- `sidecar_entry.py` — sidecar 入口
- `kanbun_sidecar.spec` — PyInstaller 配置
- `frontend/src/vite-env.d.ts` — `import.meta.env` 类型
- `tests/test_web_mount.py` — 4 个用例，锁住 `/` 的分流行为
- `tools/day6_sidecar_e2e.py` — 端到端验收（6 项）
- `tools/day6_ocr_probe.py` — 真实图片 OCR 验证
- `tools/day6_offline_audit.py` — 断网能力审计（12 项）
- `tools/day6_import_audit2.py` — AST 抽 import
- `tools/day6_pyz_audit.py` — PYZ 内容审计（17 项）
- `tools/day6_stage_sidecar.py` — 产物 → Tauri resources
- `tools/day6_startup_time.py` — 冷启动计时
- `tools/day6_sizes.py` — 体积汇总
- `tools/day6_size_probe.py`、`day6_engine_layout.py`、`day6_check_cors.py`、
  `day6_show_fetch.py`、`day6_ocr_site_size.py`、`day6_sidecar_size.py` —
  探查用脚本

修改：
- `backend/main.py` — `_WEB_DIST` 分流、`_mount_web()`、`KANBUN_LAZY_ENGINE`、
  `/health` 加 `engine_error`
- `frontend/src/App.tsx` — `apiBase()`、`/health` 轮询、引擎状态提示
- `frontend/src-tauri/src/main.rs` — 重写：setup 里起 sidecar、读端口、External URL、Exit 清理
- `frontend/src-tauri/tauri.conf.json` — `windows: []`、CSP、resources
- `.gitignore` — `frontend/src-tauri/sidecar/`、`build/`、`dist/`
