# -*- mode: python ; coding: utf-8 -*-
"""kanbun_sidecar.spec — D6: 把 Python 后端打成 Tauri sidecar。

选 onedir 不选 onefile：onefile 每次启动要把几百 MB 解压到 %TEMP%，
Celeron 上要几十秒且窗口白屏。onedir 启动快，NSIS 压缩后体积差别不大。

第一版 946.8MB，体积分析（tools/day6_sidecar_size.py）发现两处不该有的：
  - torch 295.2MB（torch_cpu.dll 一个文件）：**运行时不 import torch**
    （tools/day6_import_audit.py 证明 udkundoku/unidic2ud 都不碰 torch），
    纯属 PyInstaller 顺着 site-packages 里的 hook 误收集。
  - qkana_official.zip.part 30MB：下载残留，不是运行时数据。
剔除后重新统计见 REPORT_DAY6.md。

随包内容：
  sidecar_entry.py    入口（自选空闲端口，打印 KANBUN_PORT=<n>）
  backend/            后端包
  frontend_dist/      构建好的前端（后端托管，同源，免 CORS）
  udkundoku/          引擎代码
  unidic2ud/          引擎代码 + 模型（download/qkana 248MB，必须）
  ocr_runtime/        OCR 模型与代码（121MB）
  ocr_site/           OCR 的运行时依赖（只挑真正要的 4 个包，约 100MB）

不含：D:\\dlkotenocr-lite\\site-packages 里的 flet/sympy/networkx/reportlab
（那是官方 GUI 的依赖，sidecar 不需要）。
"""
import os

ROOT = os.path.abspath(os.path.dirname(SPEC))

datas = []
_excluded_dirs = {"__pycache__", ".git", "node_modules"}


def add_tree(src, dest, skip_ext=(".pyc",), keep=None):
    """把目录整棵塞进去。keep: 可选过滤函数(相对路径)->bool。"""
    if not os.path.isdir(src):
        print("[spec] 跳过不存在的目录: %s" % src)
        return 0
    n = 0
    for dp, dns, fs in os.walk(src):
        dns[:] = [d for d in dns if d not in _excluded_dirs]
        rel = os.path.relpath(dp, src)
        target = dest if rel == "." else os.path.join(dest, rel)
        for f in fs:
            if any(f.endswith(e) for e in skip_ext):
                continue
            relf = os.path.normpath(os.path.join(rel, f)) if rel != "." else f
            if keep is not None and not keep(relf):
                continue
            datas.append((os.path.join(dp, f), target))
            n += 1
    print("[spec] %-46s -> %-22s %5d files" % (src, dest, n))
    return n


# ---- 后端 / 前端 ----
add_tree(os.path.join(ROOT, "backend"), "backend")
add_tree(os.path.join(ROOT, "frontend", "dist"), "frontend_dist")

# ---- 引擎 ----
for pkg in ("udkundoku", "unidic2ud"):
    try:
        mod = __import__(pkg)
        p = os.path.dirname(os.path.abspath(mod.__file__))
        # 下载残留 .part / .zip 不入包
        add_tree(p, pkg, skip_ext=(".pyc", ".part", ".zip", ".tmp"))
    except Exception as e:
        print("[spec] 引擎包 %s 失败: %r" % (pkg, e))

# ---- udkanbun：PyInstaller 只收 .py，数据文件必须手动塞 ----
# 缺 mecabrc 时 MeCab 初始化直接 RuntimeError（[ifs] no such file or directory）。
# 需要 mecabrc + mecab-kanbun/ + ud-kanbun.udpipe（共 23.6MB）；
# supar-kanbun/ 是 442MB 的 guwenbert 模型，udkundoku.load() 传 model=None
# 走 ud-kanbun.udpipe，用不到它。
try:
    from PyInstaller.utils.hooks import collect_data_files
    _udk = collect_data_files("udkanbun", excludes=["supar-kanbun/**"])
    datas += _udk
    print("[spec] udkanbun 数据 %d 个文件（已排除 supar-kanbun）" % len(_udk))
except Exception as e:
    print("[spec] udkanbun 数据失败: %r" % e)

# ---- OCR 模型与代码 ----
# skip samples/：12.3MB 的示例图，纯素材，运行时不读。
add_tree(os.path.join(ROOT, "ocr_runtime"), "ocr_runtime",
         skip_ext=(".pyc", ".part", ".zip", ".tmp"),
         keep=lambda rel: not rel.replace("\\", "/").startswith("samples/"))

# ---- OCR 运行时依赖（只挑 onnxruntime/PIL/lxml 及其必须的 .libs）----
# 注意：numpy 不在这里。PyInstaller 已经顺着 import 链把 numpy 打进 _internal，
# 而冻结导入器（FrozenImporter 在 sys.meta_path 里）优先于 sys.path 末尾的
# ocr_site，所以 ocr_site/numpy 永远是死重量（两份合计 ~40MB）。
OCR_SITE = os.environ.get("KANBUN_OCR_SITE", r"D:\dlkotenocr-lite\site-packages")
OCR_KEEP = ("onnxruntime", "PIL", "lxml",
            "flatbuffers", "packaging")
if os.path.isdir(OCR_SITE):
    for name in OCR_KEEP:
        add_tree(os.path.join(OCR_SITE, name), os.path.join("ocr_site", name))
else:
    print("[spec] 警告: OCR site 不存在（%s），打包后将无法 OCR" % OCR_SITE)

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "backend.main", "backend.db", "backend.llm", "backend.kundoku_rules",
    "backend.glossary_lexicon", "backend.glossary_lexicon_extra",
    "backend.ocr_engine",
    "unidic2ud", "udkundoku",
]

# 明确排除：这些在运行路径里一次都没 import（见 day6_import_audit.py）
# 注意 networkx **不能**排除：OCR 的阅读顺序排序用它
# （ocr_runtime/src/reading_order/order/smooth_order.py: import networkx as nx），
# 去掉后 /api/ocr 会在 OCREngine() 构造时 ModuleNotFoundError。
# 第一版排掉它是因为当时只 grep 了 backend/，漏了 ocr_runtime/。
# unidic / unidic_lite 必须排除：mecab-python3 的 Tagger 在 __init__ 里无条件
# `import unidic` → fallback `import unidic_lite` 只为拿 DICDIR。这两个包一旦
# 被打进来（纯 py 文件在，词典数据不在），import 不会抛 ImportError 而是抛
# FileNotFoundError('...\\unidic_lite\\dicdir\\version')，Tagger 初始化当场崩。
# 我们始终显式传 -r mecabrc -d unidic2ud/download/qkana，本来就用不到它们。
excludes = [
    "unidic", "unidic_lite",
    "torch", "torchvision", "torchaudio", "transformers", "tokenizers",
    "hf_xet", "huggingface_hub", "safetensors", "accelerate",
    "sympy", "reportlab", "flet", "matplotlib", "scipy",
    "pandas", "IPython", "pytest", "tkinter", "notebook", "jupyter",
    "torch.utils.tensorboard",
    # 后端运行路径里一个都没用（backend/ 与 ocr_runtime/ 全量 grep 无命中），
    # 是 PyInstaller 顺着依赖图收进来的：nltk 0.7MB、emoji 的 unicode_codes 4.3MB。
    "nltk", "emoji", "IPython.core",
]

a = Analysis(
    [os.path.join(ROOT, "sidecar_entry.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="kanbun-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,          # 必须保留 stdout：Rust 侧要读 KANBUN_PORT=
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="kanbun-sidecar",
)
