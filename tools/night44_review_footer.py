# -*- coding: utf-8 -*-
"""night44_review_footer.py — 复核页脚框最多页（p014/p015/p044）的被滤框是否真噪音（NIGHT44）。

Night43 §7 遗留项 1：47 页全本只做检测-only 仿真，其余 41 页的 275 个被滤框未看文本；
p014(33)/p015(34)/p044(29) 被滤最多，先复核这三页。

方法：
  1. 设 KANBUN_OCR_LAYOUT_FILTER=0 跑产品流 OCR（**不过滤**），拿到全部行文本 + line_boxes；
  2. 离线用 backend.ocr_layout.judge_layout 对同一批框做判定；
  3. 把被判 "footer_band" 的框的**文本**打印出来，逐框人工读：
       - 若是「插入物」特征（人名/册数/日期/书志短行，不是经文连续句）→ OK（合法滤除）
       - 若像正文（经文句子、割注）→ WRONG（错滤，硬门失败）
  4. 同时打印每个被滤框的**上下文**：同页保留行的最右列文本 + 该框左右邻列，供判断接续。

判据与过滤器完全同源（同一函数），只多了「看文本」这一步——这是复核，不是实现改变。

产出: eval/night44_footer_review.json（逐框记录，含 verdict 字段留人工填写）
用法: python -X utf8 tools/night44_review_footer.py p014 p015 p044
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 必须先关闭过滤器再 import/调用引擎（引擎在 recognize_bytes 内读环境变量）
os.environ["KANBUN_OCR_LAYOUT_FILTER"] = "0"

from backend.ocr_layout import judge_layout  # noqa: E402
from backend.ocr_engine import get_engine  # noqa: E402

PAGES_DIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT = os.path.join(ROOT, "eval", "night44_footer_review.json")


def main():
    pages = [a for a in sys.argv[1:] if a.startswith("p")] or ["p014", "p015", "p044"]
    engine = get_engine()

    # 增量合并：已复核过的页保留
    prev = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            prev = {p["page"]: p for p in json.load(f)["pages"]}

    for pg in pages:
        path = os.path.join(PAGES_DIR, pg + ".jpg")
        with open(path, "rb") as f:
            data = f.read()
        t0 = time.time()
        r = engine.recognize_bytes(data)
        sec = time.time() - t0
        assert len(r["lines"]) == len(r["line_boxes"])
        assert not r["layout_filtered"], "过滤器未被关掉：%d" % len(r["layout_filtered"])

        boxes = [dict(b, text=t) for b, t in zip(r["line_boxes"], r["lines"])]
        miban, judged = judge_layout(boxes)
        y_max = (miban["y"] + miban["h"]) if miban else None

        # 保留行按 x 降序（右→左），供「邻列」上下文
        kept = [b for b, reason in judged if reason is None]
        kept_sorted = sorted(kept, key=lambda b: -b["x"])

        recs = []
        for b, reason in judged:
            if reason is None:
                continue
            # 左右邻列：x 比被滤框大的最近一列 / x 比它小的最近一列（同一批保留行）
            right = next((k for k in kept_sorted if k["x"] > b["x"]), None)
            left = next((k for k in reversed(kept_sorted) if k["x"] < b["x"]), None)
            recs.append({
                "page": pg, "text": b["text"],
                "x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                "cy": round(b["y"] + b["h"] / 2.0),
                "dy_ymax": round(b["y"] + b["h"] / 2.0 - y_max, 1) if y_max else None,
                "reason": reason,
                "neighbor_right": right["text"] if right else None,
                "neighbor_left": left["text"] if left else None,
                "verdict": None,     # 人工填：ok_noise / wrong_body
                "note": None,
            })
        recs.sort(key=lambda r: (r["cy"], -r["x"]))

        # 漏滤面：同一页脚带上**没被滤掉**的行（cy 距 y_max 80px 内），
        # 量「召回」用——被滤框是 TP，这些若也是杂记就是 FN。
        kept_band = []
        if y_max is not None:
            for b in kept:
                cy = b["y"] + b["h"] / 2.0
                if cy >= y_max - 80:
                    kept_band.append({"text": b["text"], "x": b["x"], "y": b["y"],
                                      "w": b["w"], "h": b["h"],
                                      "cy": round(cy),
                                      "dy_ymax": round(cy - y_max, 1),
                                      "vert": b["h"] >= b["w"]})
            kept_band.sort(key=lambda r: (r["cy"], -r["x"]))

        print("== %s ocr %.1fs total=%d filtered=%d kept_in_footer_band=%d miban_y=%s y_max=%s"
              % (pg, sec, len(boxes), len(recs), len(kept_band),
                 miban["y"] if miban else None, y_max), flush=True)
        for r_ in recs:
            print("  FILTER y=%4d h=%3d x=%4d dy=%+4d  %-24r  R:%r L:%r"
                  % (r_["y"], r_["h"], r_["x"], r_["dy_ymax"] or 0,
                     r_["text"], (r_["neighbor_right"] or "")[:14],
                     (r_["neighbor_left"] or "")[:14]), flush=True)
        for r_ in kept_band:
            print("  KEPT   y=%4d h=%3d x=%4d dy=%+4d vert=%d  %r"
                  % (r_["y"], r_["h"], r_["x"], r_["dy_ymax"], r_["vert"], r_["text"]),
                  flush=True)
        prev[pg] = {"page": pg, "ocr_sec": round(sec, 1), "n_boxes": len(boxes),
                    "miban_y": miban["y"] if miban else None, "y_max": y_max,
                    "filtered": recs, "kept_in_footer_band": kept_band,
                    # 全量配对落盘：后续离线复核（改判据/改标注）零 OCR 成本
                    "all_pairs": [{"text": b["text"], "x": b["x"], "y": b["y"],
                                   "w": b["w"], "h": b["h"], "vert": b["h"] >= b["w"]}
                                  for b in boxes]}

    out_pages = [prev[k] for k in sorted(prev)]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"n_pages": len(out_pages), "pages": out_pages}, f,
                  ensure_ascii=False, indent=1)
    print("[done] written: %s" % OUT, flush=True)


if __name__ == "__main__":
    main()
