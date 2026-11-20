# -*- coding: utf-8 -*-
"""night46_e2e.py — 上部手写长条过滤的端到端验证（真实 OCR）。

对 6 页跑真实 OCR（生产引擎 recognize_bytes），对比
KANBUN_OCR_LAYOUT_FILTER=1（新代码，含 headnote_strip）与 =0（全不过滤）：
  * 逐页行数、被删行文本、reason 计数
  * 「只删不加」：ON 的行序列必须是 OFF 的子序列
  * 被删行与离线几何命中的框是否一一对应（文本级复核）

产出: eval/night46_e2e.json
用法: python -X utf8 tools/night46_e2e.py
"""
import json
import os
import sys
import time
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IMGDIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT = os.path.join(ROOT, "eval", "night46_e2e.json")
PAGES = ["p007", "p012", "p014", "p017", "p020", "p031"]


def run(engine, path, filter_on):
    os.environ["KANBUN_OCR_LAYOUT_FILTER"] = "1" if filter_on else "0"
    os.environ["KANBUN_OCR_ORDER"] = "cluster"
    with open(path, "rb") as f:
        data = f.read()
    t0 = time.time()
    res = engine.recognize_bytes(data)
    return {
        "sec": round(time.time() - t0, 1),
        "lines": res.get("lines", []),
        "filtered": res.get("layout_filtered", []),
    }


def is_subsequence(small, big):
    it = iter(big)
    return all(x in it for x in small)


def main():
    from backend.ocr_engine import get_engine
    engine = get_engine()
    out = {"pages": []}
    for pg in PAGES:
        path = os.path.join(IMGDIR, pg + ".jpg")
        if not os.path.exists(path):
            print("[skip] %s 无样张" % pg)
            continue
        on = run(engine, path, True)
        off = run(engine, path, False)
        reasons = Counter(b.get("reason") for b in on["filtered"])
        # 被删行 = OFF 行多重集 - ON 行多重集
        c = Counter(on["lines"])
        dels = []
        for ln in off["lines"]:
            if c[ln] > 0:
                c[ln] -= 1
            else:
                dels.append(ln)
        subseq = is_subsequence(on["lines"], off["lines"])
        out["pages"].append({
            "page": pg,
            "on_lines": len(on["lines"]), "off_lines": len(off["lines"]),
            "deleted": len(off["lines"]) - len(on["lines"]),
            "reasons": dict(reasons), "is_subsequence": subseq,
            "sec_on": on["sec"], "sec_off": off["sec"],
            "deleted_lines": dels,
            "on_text": on["lines"], "off_text": off["lines"],
        })
        print("%s  OFF %2d → ON %2d 行（删 %d）  %s  子序列=%s  %.0fs/%.0fs"
              % (pg, len(off["lines"]), len(on["lines"]),
                 len(off["lines"]) - len(on["lines"]),
                 dict(reasons), subseq, on["sec"], off["sec"]), flush=True)

    print("\n== 被删行明细 ==")
    for r in out["pages"]:
        print("\n--- %s  删 %d 行 ---" % (r["page"], len(r["deleted_lines"])))
        for d in r["deleted_lines"]:
            print("    %r" % d[:70])

    print("\n== 汇总 ==")
    print("总删行 %d" % sum(r["deleted"] for r in out["pages"]))
    print("headnote_strip 命中 %d / footer_band 命中 %d"
          % (sum(r["reasons"].get("headnote_strip", 0) for r in out["pages"]),
             sum(r["reasons"].get("footer_band", 0) for r in out["pages"])))
    print("所有页「只删不加」= %s"
          % all(r["is_subsequence"] for r in out["pages"]))
    print("行数与几何命中一致的页: %s"
          % [r["page"] for r in out["pages"]
             if r["deleted"] == r["reasons"].get("headnote_strip", 0)
             + r["reasons"].get("footer_band", 0)])

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_e2e.json")


if __name__ == "__main__":
    main()
