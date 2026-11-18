# -*- coding: utf-8 -*-
"""day6_import_audit.py — 谁把 torch 拖进来的？

D6 打包发现 sidecar 946.8MB，其中 torch_cpu.dll 295MB。
sidecar 只需要 udkundoku + MeCab + FastAPI，本不该有 torch。
这里逐个 import 关键模块，看 sys.modules 里什么时候出现 torch。

【教训，2026-11-18】本脚本最初只扫 backend/ 与 udkundoku/unidic2ud，据此把
networkx 写进了 .spec 的 excludes —— 结果打包出来的 sidecar 可以訓読、一调
/api/ocr 就 ModuleNotFoundError（ocr_runtime/src/reading_order/order/
smooth_order.py 用它）。**扫 import 必须覆盖真正会跑的源码目录**，所以现在
SOURCE_DIRS 里加上了 ocr_runtime/src。新的通用版见 day6_import_audit2.py。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SOURCE_DIRS = ("backend", "ocr_runtime/src")


def has_torch():
    return any(m == "torch" or m.startswith("torch.") for m in sys.modules)


def main():
    print("初始 torch:", has_torch())

    import udkundoku
    print("import udkundoku 后 torch:", has_torch())

    import unidic2ud
    print("import unidic2ud 后 torch:", has_torch())

    mods = sorted(m for m in sys.modules if m.startswith(("torch", "transformers", "tokenizers", "hf_xet")))
    print("相关模块数:", len(mods))
    for m in mods[:20]:
        print("  ", m)

    # 再看源码里 import 了什么（backend + OCR 运行时，两个都会在 sidecar 里跑）
    p = os.path.dirname(os.path.abspath(udkundoku.__file__))
    print("\nudkundoku 源文件里的关键 import:")
    for fn in sorted(os.listdir(p)):
        if not fn.endswith(".py"):
            continue
        t = open(os.path.join(p, fn), encoding="utf-8", errors="replace").read()
        hits = [k for k in ("torch", "transformers", "tokenizers", "guwenbert", "unidic2ud",
                            "MeCab", "fugashi", "spacy", "ufal") if k in t]
        if hits:
            print("  %-24s %s" % (fn, hits))

    print("\n运行路径（%s）里的重量级 import:" % " + ".join(SOURCE_DIRS))
    KEYS = ("torch", "transformers", "networkx", "matplotlib", "cv2", "scipy",
            "pandas", "PIL", "lxml", "onnxruntime", "tqdm", "yaspin", "yaml")
    for d in SOURCE_DIRS:
        base = os.path.join(ROOT, d.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for dp, dns, fs in os.walk(base):
            dns[:] = [x for x in dns if x != "__pycache__"]
            for f in fs:
                if not f.endswith(".py"):
                    continue
                pth = os.path.join(dp, f)
                t = open(pth, encoding="utf-8", errors="replace").read()
                hits = [k for k in KEYS if ("import %s" % k) in t or ("from %s" % k) in t]
                if hits:
                    print("  %-46s %s" % (os.path.relpath(pth, ROOT), hits))


if __name__ == "__main__":
    main()
