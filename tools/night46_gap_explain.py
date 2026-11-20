# -*- coding: utf-8 -*-
"""night46_gap_explain.py — 差值来源的最终核对（引擎行级后处理）。

上一步假设「空串」不成立。真正的机制在 ocr_engine.recognize_bytes 的
keep 过滤（L341-344）：识别结果若
  * 空串
  * 含 "□□□" / "、、、"
  * 不含假名或汉字（纯 ASCII/符号）
  * is_junk_repeat_line（同字重复 ≥3）
  * is_junk_border_line（仅 一/二 组成 ≥6 字）
就会被剔除，不产生输出行。被滤框若落进这些类，就**不会减少行数**。

本脚本对 OFF 结果的「被滤框对应行」逐个套这五个判据，核对差值。
做法：OFF 的 boxes 与 lines 一一对应；找出与 layout_filtered 几何键相同的框，
取它的行文本，跑 keep 判据。

用法: python -X utf8 tools/night46_gap_explain.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IMGDIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT = os.path.join(ROOT, "eval", "night46_gap_explain.json")
PAGES = ["p012", "p014", "p017"]


def key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def main():
    from backend.ocr_engine import (
        get_engine, is_junk_border_line, is_junk_repeat_line,
    )
    eng = get_engine()
    patterns = ["□□□", "、、、"]

    def has_text(s):
        return any(("\u3040" <= c <= "\u30ff") or ("\u3400" <= c <= "\u9fff")
                   or ("\u4e00" <= c <= "\u4dbf") for c in s)

    def would_keep(s):
        return bool(s) and not any(p in s for p in patterns) and has_text(s) \
            and not is_junk_repeat_line(s) and not is_junk_border_line(s)

    rows = []
    for pg in PAGES:
        os.environ["KANBUN_OCR_LAYOUT_FILTER"] = "0"
        os.environ["KANBUN_OCR_ORDER"] = "cluster"
        path = os.path.join(IMGDIR, pg + ".jpg")
        with open(path, "rb") as f:
            off = eng.recognize_bytes(f.read())
        os.environ["KANBUN_OCR_LAYOUT_FILTER"] = "1"
        with open(path, "rb") as f:
            on = eng.recognize_bytes(f.read())
        filtered = {key(b) for b in on["layout_filtered"]}
        # OFF 的 boxes 与 lines 一一对应
        pairs = list(zip(off["line_boxes"], off["lines"]))
        hit = [(b, t) for b, t in pairs if key(b) in filtered]
        # 注意：ON 的 layout_filtered 里有些框在 OFF 已被 junk 剔除，不在 pairs 里
        n_not_in_off = len(filtered) - len(hit)
        n_dropped_by_keep = sum(1 for _b, t in hit if not would_keep(t))
        rows.append({
            "page": pg, "n_filtered": len(filtered),
            "n_present_in_off": len(hit),
            "n_absent_from_off": n_not_in_off,
            "n_deleted_rows": len(off["lines"]) - len(on["lines"]),
            "n_short_circuited": n_dropped_by_keep,
            "detail": [{"text": t[:40], "kept": would_keep(t)} for _b, t in hit],
        })
        print("%s  被滤 %2d  在OFF行里 %2d  不在OFF行 %2d  实际删行 %2d  "
              "短接 %2d"
              % (pg, len(filtered), len(hit), n_not_in_off,
                 len(off["lines"]) - len(on["lines"]), n_dropped_by_keep))
        print("   账目: 删行 = 在OFF行里 - 短接 → %d - %d = %d（实际 %d）"
              % (len(hit), n_dropped_by_keep,
                 len(hit) - n_dropped_by_keep,
                 len(off["lines"]) - len(on["lines"])))
        for d in rows[-1]["detail"]:
            if not d["kept"]:
                print("      短接行: %r" % d["text"])

    print("\n== 结论 ==")
    ok = all(r["n_deleted_rows"] == r["n_present_in_off"] - r["n_short_circuited"]
             for r in rows)
    print("账目闭合（删行 = 在OFF行里 - 短接）: %s" % ("YES" if ok else "NO"))
    print("不在 OFF 行里的被滤框（已被 junk 前置剔除）合计: %d"
          % sum(r["n_absent_from_off"] for r in rows))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"pages": rows}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_gap_explain.json")


if __name__ == "__main__":
    main()
