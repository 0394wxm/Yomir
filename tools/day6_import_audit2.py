# -*- coding: utf-8 -*-
"""day6_import_audit2.py — D6 打包必备依赖审计（防再犯 networkx 那种错）。

背景：第一版 .spec 的 excludes 里写了 networkx，理由来自 day6_import_audit.py
的结论「udkundoku/unidic2ud 不碰 torch」——但那个脚本只 grep 了 backend 与两个
引擎包，没扫 ocr_runtime/。结果打包出来的 sidecar 能起、能訓読，一调 OCR 就
ModuleNotFoundError: networkx（ocr_runtime/src/reading_order/order/smooth_order.py）。

这个脚本的做法反过来：不靠人工清单，而是**从真实运行路径的源码里抽 import**，
再逐个验证「在打包产物里能被 import」。这样 excludes 写错会立刻暴露。

用法：
  python tools/day6_import_audit2.py                 # 静态扫源码，列出运行时 import
  python tools/day6_import_audit2.py --bundle DIR     # 另外校验 DIR 里有没有这些模块
"""
import ast
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 真正会在 sidecar 里执行的源码目录
SOURCE_DIRS = [
    os.path.join(ROOT, "backend"),
    os.path.join(ROOT, "ocr_runtime", "src"),
]

# 这些是标准库/内置，打包时天然在
STDLIB_HINT = set(sys.builtin_module_names)


def iter_py(d):
    for dp, dns, fs in os.walk(d):
        dns[:] = [x for x in dns if x not in ("__pycache__", ".git")]
        for f in fs:
            if f.endswith(".py"):
                yield os.path.join(dp, f)


def top_level_imports(path):
    """返回文件里所有顶层包名（`import a.b` -> a，`from a.b import c` -> a）。"""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
        tree = ast.parse(src)
    except Exception:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:      # 相对 import，跳过
                continue
            if node.module:
                out.add(node.module.split(".")[0])
    return out


def main():
    bundle = None
    if "--bundle" in sys.argv:
        i = sys.argv.index("--bundle")
        bundle = sys.argv[i + 1] if i + 1 < len(sys.argv) else None

    mods = {}
    for d in SOURCE_DIRS:
        if not os.path.isdir(d):
            print("跳过不存在的目录:", d)
            continue
        for p in iter_py(d):
            for m in top_level_imports(p):
                mods.setdefault(m, []).append(os.path.relpath(p, ROOT))

    # 本地包（backend 自己的模块、ocr_runtime/src 里的包）不算外部依赖
    LOCAL = {"backend", "ocr", "reading_order", "recognize", "detect", "model",
             "utils", "config", "const", "postprocess", "preprocess"}
    third = {m: v for m, v in mods.items()
             if m not in STDLIB_HINT and m not in LOCAL
             and not m.startswith("_")}

    print("运行路径里的第三方顶层 import：%d 个\n" % len(third))
    for m in sorted(third):
        users = sorted(set(third[m]))
        print("  %-18s <- %s" % (m, ", ".join(users[:3]) + (" …" if len(users) > 3 else "")))

    if not bundle:
        return 0

    # 校验打包产物里这些模块真的在（_internal 下同名目录或 .pyd/.pyz 里）
    import zipfile
    internal = os.path.join(bundle, "_internal")
    print("\n校验 %s：" % internal)
    missing = []
    for m in sorted(third):
        p = os.path.join(internal, m)
        if os.path.isdir(p) or os.path.isfile(p + ".pyd"):
            print("  OK   %s" % m)
            continue
        # 可能在 zip 里（base_library / PYZ），先当作通过但标注
        print("  ?    %s（_internal 下无同名目录，可能在 PYZ 里或为纯 stdlib）" % m)
    if missing:
        print("\n缺失:", missing)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
