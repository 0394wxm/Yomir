# -*- coding: utf-8 -*-
"""night48_thin_verdict.py — 窄框判据的判决：这本书是双行割注本。

night48_thin_sweep 显示 w < 0.6×主栏宽 的保留框有 1118 个 / 40 页，
w_rel 中位 0.35、p75 0.38，且 0.40-0.60 区间并不空（184 框）。

本脚本检验一个更根本的假设：**这些窄框不是噪音，是割注（双行注）**。
若成立，则任何「窄框=噪音」的判据都会误删注解。

检验方法（纯几何，不看文本）：
  1) 窄框是否**成对出现**（同一 x 带内两框并排，宽各约主栏宽的一半）？
     割注在版面上是「一列宽 = 两行窄注」，所以窄框应成对、y 范围高度重合。
  2) 窄框对的高度是否与相邻正文列相当（割注常与正文等高）？
  3) 全本窄框 x 分布：是否与主栏列 x 交错（割注嵌在正文列之间）？

同时给出一个关键的负面证据：**p044 那两个框**（Night44 记为漏滤）
在成对检验下是否成立为割注？若不是，说明它们是别的东西（手写書き入れ）。

只测量，不改代码。
产出: eval/night48_thin_verdict.json
用法: python -X utf8 tools/night48_thin_verdict.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    _main_group, _median, judge_headnote_strip, judge_layout,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night48_thin_verdict.json")


def ov(a0, a1, b0, b1):
    lo = max(a0, b0)
    hi = min(a1, b1)
    return max(0.0, hi - lo)


def main():
    pages = []
    for fn in sorted(os.listdir(OFF)):
        if fn.endswith(".json"):
            pages.append(json.load(open(os.path.join(OFF, fn), encoding="utf-8")))

    per_page = []
    tot_thin = 0
    tot_paired = 0
    tot_hclose = 0
    pairs = []

    for q in pages:
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        _mi, jd = judge_layout(bx)
        ki = [i for i, (b, r) in enumerate(jd) if r is None]
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
        wmed = _median([b["w"] for b in mn])
        if wmed <= 0:
            continue
        xlo = min(b["x"] for b in mn)
        xhi = max(b["x"] + b["w"] for b in mn)

        thin = []
        for i in ki:
            b = bx[i]
            if (b["x"], b["y"], b["w"], b["h"]) in skk:
                continue
            if b["w"] / float(wmed) < 0.6 and b["h"] >= b["w"]:
                thin.append((b, q["lines"][i]))

        n_paired = 0
        n_hclose = 0
        for a_i, (a, ta) in enumerate(thin):
            best = None
            for b_i, (b, tb) in enumerate(thin):
                if a_i == b_i:
                    continue
                # 并排：x 区间不重叠但相邻（间隙 < 1.2*主栏宽），y 高度重合
                if ov(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"]) > 0:
                    continue
                gap = min(abs(a["x"] - (b["x"] + b["w"])),
                          abs(b["x"] - (a["x"] + a["w"])))
                if gap > 1.2 * wmed:
                    continue
                yo = ov(a["y"], a["y"] + a["h"], b["y"], b["y"] + b["h"])
                if yo < 0.7 * min(a["h"], b["h"]):
                    continue
                # 两框宽度都窄，合起来约等于主栏宽
                if a["w"] + b["w"] + gap > 1.35 * wmed:
                    continue
                best = b
                break
            if best is not None:
                n_paired += 1
                if abs(a["h"] - best["h"]) <= 0.15 * max(a["h"], best["h"]):
                    n_hclose += 1
                if len(pairs) < 60:
                    pairs.append({
                        "page": q["page"],
                        "a": {"x": a["x"], "y": a["y"], "w": a["w"],
                              "h": a["h"], "text": ta[:40]},
                        "b": {"x": best["x"], "y": best["y"], "w": best["w"],
                              "h": best["h"],
                              "text": next((t2[:40] for b2, t2 in thin
                                            if b2 is best), "")},
                    })
        tot_thin += len(thin)
        tot_paired += n_paired
        tot_hclose += n_hclose
        if thin:
            per_page.append({
                "page": q["page"], "n_thin": len(thin),
                "n_paired": n_paired, "n_hclose": n_hclose,
                "in_main_x": sum(1 for b, _t in thin
                                 if xlo <= b["x"] <= xhi),
            })

    print("== 窄框成对检验（并排 + y 重合 + 合计宽≈主栏宽）==")
    print("窄框总数 %d，能配成对的 %d (%.0f%%)，其中高度接近的 %d (%.0f%%)"
          % (tot_thin, tot_paired,
             100.0 * tot_paired / max(1, tot_thin),
             tot_hclose, 100.0 * tot_hclose / max(1, tot_thin)))

    print("\n== 逐页（只列有窄框的页）==")
    print("%-5s %7s %8s %8s %9s" % ("page", "窄框", "成对", "高接近", "在栏x内"))
    for r in per_page:
        print("%-5s %7d %8d %8d %9d"
              % (r["page"], r["n_thin"], r["n_paired"], r["n_hclose"],
                 r["in_main_x"]))

    print("\n== 成对样本（前 25）==")
    for p in pairs[:25]:
        print("  %s  A(x=%d y=%d w=%d h=%d) %r"
              % (p["page"], p["a"]["x"], p["a"]["y"], p["a"]["w"],
                 p["a"]["h"], p["a"]["text"]))
        print("        B(x=%d y=%d w=%d h=%d) %r"
              % (p["b"]["x"], p["b"]["y"], p["b"]["w"], p["b"]["h"],
                 p["b"]["text"]))

    print("\n== p044 两个 Night44 记录的漏滤框 ==")
    for tgt in ("一元条同不出旨", "大金表主"):
        found = [p for p in pairs
                 if p["a"]["text"].startswith(tgt)
                 or p["b"]["text"].startswith(tgt)]
        print("  %r → 成对? %s" % (tgt, "YES" if found else "NO"))
        for p in found:
            print("     %s A=%r B=%r"
                  % (p["page"], p["a"]["text"], p["b"]["text"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"tot_thin": tot_thin, "tot_paired": tot_paired,
                   "tot_hclose": tot_hclose, "per_page": per_page,
                   "pairs": pairs}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night48_thin_verdict.json")


if __name__ == "__main__":
    main()
