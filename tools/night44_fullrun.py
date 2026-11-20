# -*- coding: utf-8 -*-
"""night44_fullrun.py — 47 页全本 filter=ON / filter=OFF 对照重跑（NIGHT44 主体）。

Night43 §7 遗留项 3：「全本重跑 book.md 前，先用 KANBUN_OCR_LAYOUT_FILTER=0 跑一遍对照，
量化白文行数差」。本脚本一次跑完**两条**处理线，产出可直接对照的归档：

  A 线 filter=ON （新默认）  → eval/night44_full/filter_on/
  B 线 filter=OFF（Night42 行为）→ eval/night44_full/filter_off/

每页落盘 {page}.json：{"page", "lines", "line_boxes", "layout_filtered",
"junk_filtered", "ocr_sec", "text"}。**不训读**（训读在 book.md 层，与本夜判据无关，
且 47 页训读要 63s+；行数差不需要它）。页图用 Night42 的下载缓存（不入库）。

断点续跑：已存在的 {page}.json 直接跳过（--fresh 强制重跑）。
单页失败记 ERROR 继续（不中断整本）。

用法: python -X utf8 tools/night44_fullrun.py [--fresh] [--pages p014,p015]
产出: eval/night44_full/ + eval/night44_full/summary.json
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PAGES_DIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT_ROOT = os.path.join(ROOT, "eval", "night44_full")

# **关键**：环境变量在 recognize_bytes 内读，必须在调用前设置。
# 两条线共用一个引擎实例（模型加载 ~20s，只付一次）。
MODES = [("on", "1"), ("off", "0")]


def main():
    args = sys.argv[1:]
    fresh = "--fresh" in args
    only = None
    if "--pages" in args:
        only = set(args[args.index("--pages") + 1].split(","))

    from backend.ocr_engine import get_engine
    t0 = time.time()
    engine = get_engine()
    print("[engine] load %.1fs" % (time.time() - t0), flush=True)

    pages = sorted(f[:-4] for f in os.listdir(PAGES_DIR) if f.endswith(".jpg"))
    if only:
        pages = [p for p in pages if p in only]
    print("[plan] %d pages x %d modes" % (len(pages), len(MODES)), flush=True)

    summary = {}
    for name, flag in MODES:
        d = os.path.join(OUT_ROOT, "filter_" + name)
        os.makedirs(d, exist_ok=True)
        os.environ["KANBUN_OCR_LAYOUT_FILTER"] = flag
        print("\n=== line %s (KANBUN_OCR_LAYOUT_FILTER=%s) ===" % (name, flag), flush=True)
        n_done = n_skip = n_err = 0
        t_line = time.time()
        for pg in pages:
            dst = os.path.join(d, pg + ".json")
            if os.path.exists(dst) and not fresh:
                n_skip += 1
                continue
            with open(os.path.join(PAGES_DIR, pg + ".jpg"), "rb") as f:
                data = f.read()
            t1 = time.time()
            try:
                r = engine.recognize_bytes(data)
            except Exception as e:
                n_err += 1
                print("[%s/%s] ERROR %r" % (name, pg, e), flush=True)
                continue
            sec = time.time() - t1
            n_done += 1
            with open(dst, "w", encoding="utf-8", newline="\n") as f:
                json.dump({"page": pg, "mode": name,
                           "lines": r["lines"], "line_boxes": r["line_boxes"],
                           "line_count": r["line_count"],
                           "layout_filtered": r["layout_filtered"],
                           "junk_filtered": r["junk_filtered"],
                           "ocr_sec": round(sec, 1), "text": r["text"]},
                          f, ensure_ascii=False, indent=1)
            print("[%s/%s] %.1fs lines=%d layout=%d junk=%d"
                  % (name, pg, sec, r["line_count"], len(r["layout_filtered"]),
                     r["junk_filtered"]), flush=True)
            # 逐页进度落盘，中途被杀也能看出跑到哪
            with open(os.path.join(OUT_ROOT, "progress_%s.txt" % name), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("%s %d done %d skip %d err %.1fs\n"
                        % (pg, n_done, n_skip, n_err, time.time() - t_line))
        summary[name] = {"done": n_done, "skip": n_skip, "err": n_err,
                         "sec": round(time.time() - t_line, 1)}
        print("--- line %s: %s" % (name, json.dumps(summary[name])), flush=True)

    with open(os.path.join(OUT_ROOT, "summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "pages_dir": PAGES_DIR, "modes": summary}, f,
                  ensure_ascii=False, indent=1)
    print("\n[done] %s" % json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
