# -*- coding: utf-8 -*-
"""night49_order_final.py — 割注在**最终扁平阅读顺序**里排得对不对（正确指标）。

上一版 night49_warichu_order.py 的 Q1「两半是否在同一列单元」是**错指标**：
割注两半的 x 区间互不相交（并排），按 `overlap_x = inter/min(w)` 必然 < 0.4，
本来就该落在两个不同单元。用「同列 + 右先 + 连续」当合格线，分母 488 里
281 判不合格，但那是指标定义错，不是代码错。

本脚本改用**唯一有意义的指标**：在最终扁平输出顺序里，
**割注对的右半（x 大）是否排在左半（x 小）之前**。

数据源：eval/night44_full/filter_off/*.json 的 `line_boxes` **已经是生产
`_cluster_order` 排好序的结果**（night44_fullrun 直接存 recognize_bytes 返回值）。
所以「位置比较」直接等于产品输出顺序，不需要复刻排序器。
（复刻自检 43/47 页恒等、p021 错位 2 个，本脚本不依赖复刻。）

另外用 filter_on 归档做一次交叉核对：两条线框集合不同但相对顺序应当一致，
若右先率相同则结论稳健。

只测量，不改代码。
产出: eval/night49_order_final.json
用法: python -X utf8 tools/night49_order_final.py
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
ON = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night49_order_final.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def find_pairs(thin, wmed):
    """Night48 的成对判据（保持与之前可比）：并排 + y 重合 + 合计宽≈主栏宽。

    返回 [(right, left)]，right 的 x 更大。
    """
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
            pairs.append((r, l))
            break
    return pairs


def pairs_for_page(q, apply_filter):
    """返回 (pairs, kept_boxes, order_of_kept)。

    order_of_kept: kept 框在归档输出顺序中的位置列表（升序）。
    归档 line_boxes 已按最终顺序排列，所以下标就是输出位置。
    """
    bx = [dict(b) for b in q["line_boxes"]]
    if len(bx) < 4:
        return None
    ki = list(range(len(bx)))
    if apply_filter:
        _mi, jd = judge_layout(bx)
        ki = [i for i, (_b, r) in enumerate(jd) if r is None]
        kp = [bx[i] for i in ki]
        vt = [b for b in kp if b["h"] >= b["w"]]
        if not vt:
            return None
        hm = max(b["h"] for b in vt)
        _m3, mn = _main_group([dict(b) for b in kp])
        if not mn:
            return None
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
        return None
    _m2, mn = _main_group([dict(b) for b in kp])
    if not mn:
        return None
    wmed = _median([b["w"] for b in mn])
    if wmed <= 0:
        return None
    thin = []
    for i in ki:
        b = bx[i]
        if b["w"] / float(wmed) < 0.6 and b["h"] >= b["w"]:
            thin.append(dict(b, index=i))
    prs = find_pairs(thin, wmed)
    return prs, bx, ki


def measure(directory, apply_filter, label):
    per_page = []
    tot = right_first = 0
    exceptions = []
    detail = []
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(directory, fn), encoding="utf-8"))
        r = pairs_for_page(q, apply_filter)
        if not r:
            continue
        prs, bx, ki = r
        if not prs:
            continue
        # 位置 = 归档顺序里的下标；相对顺序与是否先滤掉别框无关
        n_page = len(prs)
        n_ok = 0
        for rt, lf in prs:
            pr, pl = rt["index"], lf["index"]
            ok = pr < pl
            if ok:
                n_ok += 1
            dist = pl - pr
            rec = {"page": q["page"],
                   "right": {"pos": pr, "x": rt["x"], "y": rt["y"],
                             "w": rt["w"], "h": rt["h"],
                             "text": q["lines"][pr][:40]},
                   "left": {"pos": pl, "x": lf["x"], "y": lf["y"],
                            "w": lf["w"], "h": lf["h"],
                            "text": q["lines"][pl][:40]},
                   "right_first": ok, "dist": dist}
            detail.append(rec)
            if not ok:
                exceptions.append(rec)
        tot += n_page
        right_first += n_ok
        per_page.append({"page": q["page"], "pairs": n_page, "right_first": n_ok})

    print("\n== [%s] 割注对在最终扁平顺序里：右半是否先于左半 ==" % label)
    print("  合计 %d 对，右先 %d (%.2f%%)"
          % (tot, right_first, 100.0 * right_first / max(1, tot)))
    bad_pages = [p for p in per_page if p["right_first"] < p["pairs"]]
    print("  有例外的页: %d / %d" % (len(bad_pages), len(per_page)))
    for p in bad_pages:
        print("    %s %d/%d" % (p["page"], p["right_first"], p["pairs"]))
    if exceptions:
        print("\n  == 例外逐条 ==")
        for e in exceptions:
            print("  %s 右(pos=%d x=%d) %r"
                  % (e["page"], e["right"]["pos"], e["right"]["x"],
                     e["right"]["text"]))
            print("     %s 左(pos=%d x=%d) %r  dist=%d"
                  % (" " * len(e["page"]), e["left"]["pos"], e["left"]["x"],
                     e["left"]["text"], e["dist"]))
    return {"tot": tot, "right_first": right_first,
            "per_page": per_page, "exceptions": exceptions,
            "detail": detail}


def main():
    off = measure(OFF, True, "filter_off + 离线版面过滤（生产口径框集）")
    on = measure(ON, False, "filter_on 归档（生产默认输出，交叉核对）")

    print("\n== 交叉核对 ==")
    print("  off线 %d/%d = %.2f%%    on线 %d/%d = %.2f%%"
          % (off["right_first"], off["tot"],
             100.0 * off["right_first"] / max(1, off["tot"]),
             on["right_first"], on["tot"],
             100.0 * on["right_first"] / max(1, on["tot"])))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"off": off, "on": on}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_order_final.json")


if __name__ == "__main__":
    main()
