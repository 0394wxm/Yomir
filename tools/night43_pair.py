# -*- coding: utf-8 -*-
"""night43_pair.py — 选样页跑产品流 OCR，落盘「行文本↔框」一一配对（NIGHT43 测量用）。

与 import_pid.py 完全同流（recognize_bytes：junk3 → 识别 → 文本过滤 → cluster），
lines 与 line_boxes 天然配对，供噪音行/正文列的分布统计标注。
产出: eval/night43_pair.json
用法: python -X utf8 -I tools/night43_pair.py p005 p019 p020 p033
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.ocr_engine import get_engine  # noqa: E402

PAGES_DIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT = os.path.join(ROOT, "eval", "night43_pair.json")


def main():
    pages = [a for a in sys.argv[1:] if a.startswith("p")]
    print("[plan] pair pages: %s" % ",".join(pages), flush=True)

    # 增量合并：已有 night43_pair.json 的其他页保留（p012/p017 等验证页不再重跑）
    prev = {}
    if os.path.exists(OUT) and "--fresh" not in sys.argv:
        with open(OUT, encoding="utf-8") as f:
            prev = {p["page"]: p for p in json.load(f)["pages"]}

    print("[engine] loading...", flush=True)
    t0 = time.time()
    engine = get_engine()
    print("[engine] load %.1fs" % (time.time() - t0), flush=True)

    for pg in pages:
        path = os.path.join(PAGES_DIR, pg + ".jpg")
        with open(path, "rb") as f:
            data = f.read()
        t1 = time.time()
        r = engine.recognize_bytes(data)
        sec = time.time() - t1
        pairs = []
        assert len(r["lines"]) == len(r["line_boxes"]), (pg, len(r["lines"]), len(r["line_boxes"]))
        for text, b in zip(r["lines"], r["line_boxes"]):
            pairs.append({"text": text, "x": b["x"], "y": b["y"],
                          "w": b["w"], "h": b["h"], "vert": bool(b["h"] >= b["w"])})
        print("[%s] ocr %.1fs pairs=%d junk3=%d layout=%d"
              % (pg, sec, len(pairs), r["junk_filtered"], len(r["layout_filtered"])),
              flush=True)
        prev[pg] = {"page": pg, "ocr_sec": round(sec, 1),
                    "junk3_filtered": r["junk_filtered"],
                    "layout_filtered_n": len(r["layout_filtered"]), "pairs": pairs}

    out_pages = [prev[k] for k in sorted(prev)]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_pages": len(out_pages), "pages": out_pages}, f,
                  ensure_ascii=False, indent=1)
    print("[done] written: %s (%d pages)" % (OUT, len(out_pages)), flush=True)


if __name__ == "__main__":
    main()
