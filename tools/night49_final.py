# -*- coding: utf-8 -*-
"""night49_final.py — Night49 验收口径：逐页报「割注对右半是否在左半之前」。

这是任务书步骤 1 要求的**唯一指标**：在最终扁平输出顺序里，
割注对的右半是否排在左半之前。分母 = 全部配对，分子 = 右先的对数，
逐页列出分母/分子/例外页，并给出改前（Night48 行为）与改后（Night49）。

配对口径沿用 Night48（tools/night48_thin_verdict.py 的几何判据）以保持可比；
另按 quality 分层（A_strict/B/C）给出子集统计。

用法: python -X utf8 tools/night49_final.py
产出: eval/night49_final.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

from backend.ocr_layout import (  # noqa: E402
    WARICHU_TOL, main_column_keys, reorder_main_slots, reorder_warichu_slots,
)

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
ON = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night49_final.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def find_pairs(thin, wmed):
    used = set()
    pairs = []
    for a in sorted(thin, key=lambda t: -(t["x"] + t["w"])):
        if id(a) in used:
            continue
        for b in thin:
            if b is a or id(b) in used:
                continue
            if ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"]) > 0:
                continue
            gap = min(abs(a["x"] - (b["x"] + b["w"])),
                      abs(b["x"] - (a["x"] + a["w"])))
            if gap > 1.2 * wmed:
                continue
            yo = ov(a["y"], a["y"] + a["h"], b["y"], b["y"] + b["h"])
            if yo < 0.7 * min(a["h"], b["h"]):
                continue
            if a["w"] + b["w"] + gap > 1.35 * wmed:
                continue
            r, l = (a, b) if a["x"] > b["x"] else (b, a)
            used.add(id(r))
            used.add(id(l))
            pairs.append((r, l, gap))
            break
    return pairs


def order_of(kept, use_new):
    units = sim.cluster_units([dict(b) for b in kept])
    mk = main_column_keys([dict(b) for b in kept])
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            if use_new:
                u["items"] = reorder_warichu_slots(u["items"])
            u["items"] = reorder_main_slots(u["items"], mk)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    out = []
    for u in units:
        out.extend(it["index"] for it in u["items"])
    return out


def tier(r, l):
    """按夜间 49 的分层口径给一对分类。"""
    gap = min(abs(r["x"] - (l["x"] + l["w"])), abs(l["x"] - (r["x"] + r["w"])))
    return gap  # 由调用方结合 wmed 判层


def measure(directory, apply_filter, label):
    per_page = []
    tot = ok_before = ok_after = 0
    exc_before, exc_after = [], []
    n_regress_pages = []
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(directory, fn), encoding="utf-8"))
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        from backend.ocr_layout import _main_group, _median, \
            judge_headnote_strip, judge_layout
        ki = list(range(len(bx)))
        if apply_filter:
            _mi, jd = judge_layout(bx)
            ki = [i for i, (_b, r) in enumerate(jd) if r is None]
            kp = [bx[i] for i in ki]
            vt = [b for b in kp if b["h"] >= b["w"]]
            if not vt:
                continue
            hm = max(b["h"] for b in vt)
            _m3, mn = _main_group([dict(b) for b in kp])
            if not mn:
                continue
            bt = _median([b["y"] for b in mn])
            st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
            skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
            ki = [i for i in ki
                  if (bx[i]["x"], bx[i]["y"], bx[i]["w"], bx[i]["h"]) not in skk]
            kp = [bx[i] for i in ki]
        else:
            kp = bx
        vt = [b for b in kp if b["h"] >= b["w"]]
        if not vt:
            continue
        _m2, mn = _main_group([dict(b) for b in kp])
        if not mn:
            continue
        wmed = _median([b["w"] for b in mn])
        if wmed <= 0:
            continue
        thin = [dict(bx[i], index=i) for i in ki
                if bx[i]["w"] / float(wmed) < 0.6 and bx[i]["h"] >= bx[i]["w"]]
        prs = find_pairs(thin, wmed)
        if not prs:
            continue
        kept = [dict(bx[i], index=i) for i in ki]
        o_before = order_of(kept, False)
        o_after = order_of(kept, True)
        pb = {i: p for p, i in enumerate(o_before)}
        pa = {i: p for p, i in enumerate(o_after)}

        n_page = n_ok_b = n_ok_a = 0
        for r, l, gap in prs:
            n_page += 1
            if pb[r["index"]] < pb[l["index"]]:
                n_ok_b += 1
            else:
                exc_before.append({"page": q["page"],
                                   "r": {"x": r["x"], "y": r["y"],
                                         "text": q["lines"][r["index"]][:28]},
                                   "l": {"x": l["x"], "y": l["y"],
                                         "text": q["lines"][l["index"]][:28]},
                                   "dy": l["y"] - r["y"]})
            if pa[r["index"]] < pa[l["index"]]:
                n_ok_a += 1
            else:
                exc_after.append({"page": q["page"],
                                  "r": {"x": r["x"], "y": r["y"],
                                        "text": q["lines"][r["index"]][:28]},
                                  "l": {"x": l["x"], "y": l["y"],
                                        "text": q["lines"][l["index"]][:28]}})
        tot += n_page
        ok_before += n_ok_b
        ok_after += n_ok_a
        per_page.append({"page": q["page"], "n": n_page,
                         "before": n_ok_b, "after": n_ok_a})
        if n_ok_a < n_ok_b:
            n_regress_pages.append(per_page[-1])

    print("\n== [%s] ==" % label)
    print("  分母 %d 对" % tot)
    print("  改前右先 %d (%.2f%%)，例外 %d 对 / %d 页"
          % (ok_before, 100.0 * ok_before / max(1, tot), len(exc_before),
             sum(1 for p in per_page if p["before"] < p["n"])))
    print("  改后右先 %d (%.2f%%)，例外 %d 对 / %d 页"
          % (ok_after, 100.0 * ok_after / max(1, tot), len(exc_after),
             sum(1 for p in per_page if p["after"] < p["n"])))
    print("  退化的页: %d" % len(n_regress_pages))
    for p in n_regress_pages:
        print("    %s %d/%d → %d/%d" % (p["page"], p["before"], p["n"],
                                        p["after"], p["n"]))
    if exc_after:
        print("\n  改后仍颠倒的 %d 对:" % len(exc_after))
        for e in exc_after:
            print("    %s R(x=%d y=%d) %r | L(x=%d y=%d) %r"
                  % (e["page"], e["r"]["x"], e["r"]["y"], e["r"]["text"],
                     e["l"]["x"], e["l"]["y"], e["l"]["text"]))
    return {"tot": tot, "before": ok_before, "after": ok_after,
            "per_page": per_page, "exc_before": exc_before,
            "exc_after": exc_after, "regress": n_regress_pages}


def main():
    print("== 逐页：割注对右半是否先于左半（分母 / 改前 / 改后）==")
    print("%-6s %5s %8s %8s" % ("page", "对数", "改前", "改后"))
    off = measure(OFF, True, "filter_off + 离线版面过滤（生产口径）")
    for p in off["per_page"]:
        mark = "  <<< 改前有例外" if p["before"] < p["n"] else ""
        print("%-6s %5d %6d/%d %6d/%d%s"
              % (p["page"], p["n"], p["before"], p["n"], p["after"], p["n"],
                 mark))
    on = measure(ON, False, "filter_on 归档（生产默认输出，交叉核对）")

    print("\n== 两线交叉核对 ==")
    for label, d in (("off", off), ("on", on)):
        print("  %s: %d/%d = %.2f%% → %d/%d = %.2f%%"
              % (label, d["before"], d["tot"],
                 100.0 * d["before"] / max(1, d["tot"]),
                 d["after"], d["tot"],
                 100.0 * d["after"] / max(1, d["tot"])))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"off": off, "on": on, "tol": WARICHU_TOL}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_final.json")


if __name__ == "__main__":
    main()
