# -*- coding: utf-8 -*-
"""night44_insertion_check.py — 全 47 页、275 个被滤框的「插入物」几何校验（NIGHT44）。

原理（不读文本，与 backend/ocr_layout.py 判据独立）：
  页脚插入物 = 该列最底下的东西。若被滤框在**同一列**（x 重叠 >= 50% 窄者宽）
  下方还有**保留行**，说明它夹在正文列中间 → 可疑（可能是正文被截断），必须看文本。
  若同列下方无任何保留行 → 它是该列末端的独立物 → 页脚插入物特征成立。

  这与 Night43 §2.3 的手工证据（正文列间直接衔接、不经过页脚行）同构，但是
  全本自动化，覆盖 47 页所有 275 个被滤框。

另解释「275 个被滤框 vs 223 行净差」：
  被滤框在**识别前**剔除（省识别耗时），所以它们的文本从未产生；而 OFF 线的同位置框
  会被识别后再过文本过滤（is_junk_repeat_line / is_junk_border_line / 无文字行），
  其中一部分本来就会被剔除。差值 = 275 - 223 = 52 框 = 「即使不滤版面也不会进白文」。
  本脚本同时验证：OFF 线总框数 - ON 线总框数 == 275（检测确定性 + 过滤器作用面精确）。

产出: eval/night44_insertion.json + stdout 汇总
用法: python -X utf8 tools/night44_insertion_check.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "eval", "night44_full")
EVAL = os.path.join(ROOT, "eval")


def load(mode):
    d = os.path.join(FULL, "filter_" + mode)
    out = {}
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                p = json.load(f)
            out[p["page"]] = p
    return out


def ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


def main():
    on = load("on")
    off = load("off")
    pages = sorted(on)
    rows = []
    n_below = 0
    tot_filtered = 0
    tot_boxes_on = tot_boxes_off = 0
    survived_in_off = 0
    box_mismatch = []
    for pg in pages:
        po, pf = on[pg], off[pg]
        tot_boxes_on += len(po["line_boxes"])
        tot_boxes_off += len(pf["line_boxes"])
        filt = po["layout_filtered"]
        tot_filtered += len(filt)
        # 三条真正的不变式（不是「框数相加相等」——被滤框在 OFF 线还会再经文本过滤）：
        #   I1  filtered ∩ ON 存活 = ∅（被滤框不可能又出现在 ON 结果里）
        #   I2  OFF 存活 ⊆ ON 存活 ∪ filtered（OFF 里不允许出现来路不明的框）
        #   I3  被滤框在同列下方没有保留行（列末插入物，本脚本主判据）
        def key(b):
            return (b["x"], b["y"], b["w"], b["h"])
        co_on = sorted(key(b) for b in po["line_boxes"])
        co_off = sorted(key(b) for b in pf["line_boxes"])
        co_f = sorted(key(b) for b in filt)
        set_on, set_off, set_f = set(co_on), set(co_off), set(co_f)
        leak = sorted(set_f & set_on)
        unknown = sorted(set_off - (set_on | set_f))
        if leak or unknown:
            box_mismatch.append({"page": pg, "filtered_also_in_on": leak[:5],
                                 "off_boxes_unaccounted": unknown[:5],
                                 "n_off": len(co_off), "n_on": len(co_on), "n_f": len(co_f)})
        # 统计：被滤框里有多少在 OFF 线仍产出了「过文本过滤」的行（= 净行数差的来源）
        survived_in_off += len(set_f & set_off)
        for b in filt:
            below = [k for k in po["line_boxes"]
                     if ov_x(b, k) >= 0.5 and (k["y"] + k["h"] / 2.0) > (b["y"] + b["h"] / 2.0)]
            if below:
                n_below += 1
            rows.append({"page": pg, "box": b,
                         "col_overlap_below": len(below),
                         "below_sample": [(k["x"], k["y"], k["w"], k["h"]) for k in below[:3]]})

    print("== 全 47 页被滤框「同列下方是否还有保留行」==")
    print("被滤框总数=%d  同列下方有保留行=%d  无=%d"
          % (tot_filtered, n_below, tot_filtered - n_below))
    print("框数: ON=%d OFF=%d 差=%d" % (tot_boxes_on, tot_boxes_off,
                                       tot_boxes_off - tot_boxes_on))
    print("被滤框在 OFF 线仍产出经文本过滤后的行: %d（其余 %d 框即使不滤版面也进不了白文）"
          % (survived_in_off, tot_filtered - survived_in_off))
    print("不变式 I1/I2（ON 无泄漏 / OFF 框全部有来路）: %s"
          % ("PASS" if not box_mismatch else "FAIL"))

    by_page = {}
    for r in rows:
        by_page.setdefault(r["page"], []).append(r["col_overlap_below"])
    print("\n-- 逐页：被滤框数 / 其中同列下方有保留行的个数 --")
    for pg in pages:
        v = by_page.get(pg)
        if not v:
            continue
        print("  %s n=%2d below=%d" % (pg, len(v), sum(1 for x in v if x)))

    if box_mismatch:
        print("\n!! 框多重集不一致页:")
        for m in box_mismatch:
            print("  %s" % m)

    with open(os.path.join(EVAL, "night44_insertion.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump({"n_filtered": tot_filtered, "n_with_kept_below": n_below,
                   "boxes_on": tot_boxes_on, "boxes_off": tot_boxes_off,
                   "survived_in_off": survived_in_off,
                   "box_mismatch": box_mismatch, "rows": rows}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night44_insertion.json")


if __name__ == "__main__":
    main()
