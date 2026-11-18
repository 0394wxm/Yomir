# -*- coding: utf-8 -*-
"""day6_size_probe.py — D6 前提：算清楚「随壳打包」到底要背多少东西。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def du(path):
    if not os.path.exists(path):
        return None
    tot = n = 0
    for dp, _, fs in os.walk(path):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(dp, f))
                n += 1
            except OSError:
                pass
    return {"files": n, "mb": round(tot / 1048576.0, 1)}


def main():
    items = []
    items.append(("ocr_runtime (OCR 模型+代码)", os.path.join(ROOT, "ocr_runtime")))
    items.append(("backend", os.path.join(ROOT, "backend")))
    items.append(("frontend/dist", os.path.join(ROOT, "frontend", "dist")))
    items.append(("src-tauri/target/release exe",
                  os.path.join(ROOT, "frontend", "src-tauri", "target", "release",
                               "kanbun-kakikudashi.exe")))

    import udkundoku
    items.append(("udkundoku 包", os.path.dirname(os.path.abspath(udkundoku.__file__))))

    try:
        import unidic2ud
        items.append(("unidic2ud 包", os.path.dirname(os.path.abspath(unidic2ud.__file__))))
    except Exception as e:
        items.append(("unidic2ud 包", "import 失败: %r" % (e,)))

    # MeCab 词典 / 模型
    for cand in ("mecab-kanbun", "unidic"):
        for base in (sys.prefix, os.path.dirname(sys.executable), ROOT):
            p = os.path.join(base, cand)
            if os.path.isdir(p):
                items.append((cand, p))

    # NDL OCR 的 site-packages（onnxruntime 等）
    ocr_site = os.environ.get("KANBUN_OCR_SITE", r"D:\dlkotenocr-lite\site-packages")
    items.append(("OCR site-packages (外部)", ocr_site))

    print("%-34s %10s %10s" % ("路径", "文件数", "MB"))
    print("-" * 58)
    total = 0.0
    for label, path in items:
        if not isinstance(path, str):
            print("%-34s %s" % (label, path))
            continue
        if os.path.isfile(path):
            mb = round(os.path.getsize(path) / 1048576.0, 1)
            print("%-34s %10d %10.1f" % (label, 1, mb))
            continue
        d = du(path)
        if d is None:
            print("%-34s %10s %10s  (不存在)" % (label, "-", "-"))
            continue
        print("%-34s %10d %10.1f" % (label, d["files"], d["mb"]))
        total += d["mb"]
    print("-" * 58)
    print("可打包部分合计约 %.1f MB（不含 site-packages 与 Python 解释器）" % total)

    print("\nPython 解释器:", os.path.getsize(sys.executable) / 1048576.0, "MB")
    for mod in ("fastapi", "uvicorn", "pydantic", "PIL", "numpy"):
        try:
            m = __import__(mod)
            p = os.path.dirname(os.path.abspath(m.__file__))
            d = du(p)
            print("  %-10s %8.1f MB  %s" % (mod, d["mb"], p))
        except Exception as e:
            print("  %-10s %s" % (mod, e))


if __name__ == "__main__":
    main()
