# -*- coding: utf-8 -*-
"""day6_pyz_audit.py — 验证「excludes 没排掉运行时要的模块」。

对 PyInstaller 产物的真实内容做判定：
  1. 读 PYZ-00.pyz 的目录表（纯 Python 模块都在里面，不是 _internal 下的目录）；
  2. 读 _internal 下的原生包目录（.pyd/dll 形态）；
  3. 拿运行时源码里 import 的第三方模块去对，缺一个就报 FAIL。

v1 的错误做法是只看 _internal 有没有同名目录，于是 networkx（在 PYZ 里）
被误判为「可能不在」，而真正被 excludes 排掉的 matplotlib 也是同一种判法
看不出来。这里直接问 PYZ「你到底装了哪些包」。

用法：python tools/day6_pyz_audit.py [dist/kanbun-sidecar]
"""
import marshal
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 运行路径（backend + ocr_runtime/src）真正 import 的第三方顶层模块。
# 由 tools/day6_import_audit2.py 生成；带 lazy import，只统计会执行到的。
REQUIRED = {
    "fastapi": "后端",
    "pydantic": "后端",
    "starlette": "后端",
    "uvicorn": "后端",
    "sqlite3": "stdlib",
    "numpy": "OCR",
    "PIL": "OCR",
    "lxml": "OCR",
    "onnxruntime": "OCR",
    "yaml": "OCR (PyYAML)",
    "networkx": "OCR 阅读顺序",     # 曾经被误排除，导致 /api/ocr 崩
    "tqdm": "OCR ndl_parser 顶层",
    "udkundoku": "訓読",
    "unidic2ud": "訓読",
    "udkanbun": "訓読",
    "MeCab": "訓読",
    "ufal": "訓読 (ufal.udpipe)",
}

# 明确「只用在 CLI / 可视化里，不进运行路径」的，列出来备查
NOT_REQUIRED = {
    "matplotlib": "ndl_parser.summary() 画图，识别路径不调用",
    "cv2": "ndl_parser 里的 show/dump 辅助函数，识别路径不调用",
    "yaspin": "reading_order/utils/file.py 的 collect_files，后端不调用",
    "nltk": "无引用",
    "emoji": "无引用",
    "torch": "无引用（D6 体积优化的主目标）",
}


def pyz_modules(pyz):
    """PyInstaller 的 PYZ 是 zlib 归档；用 importer 读目录表最可靠。"""
    sys.path.insert(0, os.path.dirname(pyz))
    from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader
    arch = ZlibArchiveReader(pyz)
    names = set(arch.toc.keys())
    return names


def main():
    bundle = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "kanbun-sidecar")
    internal = os.path.join(bundle, "_internal")
    pyz = os.path.join(ROOT, "build", "kanbun_sidecar", "PYZ-00.pyz")
    print("bundle:", bundle)
    print("pyz:", pyz, os.path.isfile(pyz))

    names = pyz_modules(pyz) if os.path.isfile(pyz) else set()
    tops = set()
    for n in names:
        tops.add(n.split(".")[0])
    print("PYZ 里模块数: %d，顶层包数: %d" % (len(names), len(tops)))

    native = set()
    if os.path.isdir(internal):
        for d in os.listdir(internal):
            if d.endswith((".pyd", ".dll")):
                continue
            native.add(d)
        for d in os.listdir(internal):
            if d.endswith(".pyd"):
                native.add(d.split(".")[0])
        # ocr_site/ 是「随包的另一套 site-packages」，sidecar_entry 会把它
        # 整个加进 sys.path，所以 ocr_site/<pkg> 等价于顶层 <pkg>。
        ocr_site = os.path.join(internal, "ocr_site")
        if os.path.isdir(ocr_site):
            for d in os.listdir(ocr_site):
                if not d.endswith((".pyd", ".dll", ".dist-info")):
                    native.add(d)

    def has(mod):
        return mod in tops or any(n.startswith(mod + ".") for n in names) or mod in native

    fails = []
    print("\n必需模块：")
    for mod, why in sorted(REQUIRED.items()):
        ok = has(mod)
        print("  %-14s %-4s %s" % (mod, "OK" if ok else "MISS", why))
        if not ok:
            fails.append(mod)

    print("\n刻意排除（运行路径不需要）：")
    for mod, why in sorted(NOT_REQUIRED.items()):
        present = has(mod)
        print("  %-14s %-12s %s" % (mod, "在包里!" if present else "已排除", why))

    print()
    if fails:
        print("FAIL 缺模块: %s" % fails)
        return 1
    print("PASS: 运行路径所需模块全部在包里")
    return 0


if __name__ == "__main__":
    sys.exit(main())
