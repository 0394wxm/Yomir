# -*- coding: utf-8 -*-
"""night49_safety_audit.py — 修法的安全边界审计。

对全本 47 页，枚举所有**被实际重排的 y 槽**，报告：
  S1 槽内出现 x 重叠 > 0.5 的框对（= 可能上下堆叠或重复检测）有多少个槽
      → 这些是第一顺位风险：重排会改变它们的相对顺序
  S2 槽内框的尺寸极端情况（h 很小，< 10px，意味着几何上可能上下相接）
  S3 每个风险槽的具体内容，逐槽列出

判定标准：如果 S1 全部是「几乎完全重合的重复检测框」（IoU 高、x/y 都接近），
那么重排只是交换两个几乎相同的框，对阅读无影响。

用法: python -X utf8 tools/night49_safety_audit.py
产出: eval/night49_safety_audit.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

from backend.ocr_layout import WARICHU_TOL  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OUT = os.path.join(ROOT, "eval", "night49_safety_audit.json")


def ovr(a, b):
    inter = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"])
                - max(a["x"], b["x"]))
    return inter / max(1, min(a["w"], b["w"]))


def iou(a, b):
    ix = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    inter = ix * iy
    ua = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / max(1.0, ua)


def slots_of(items, tol):
    items = sorted(items, key=lambda t: t["y"])
    out = []
    i, n = 0, len(items)
    while i < n:
        j = i + 1
        anchor = items[i]["y"]
        while j < n and abs(items[j]["y"] - anchor) <= tol:
            j += 1
        out.append((items[i:j], i, j))
        i = j
    return out


def main():
    n_slots = 0
    n_reordered = 0
    risky = []
    tiny = []
    for fn in sorted(os.listdir(sim.OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, _bx, q = r
        units = sim.cluster_units([dict(b) for b in kept])
        for ui, u in enumerate(units):
            if u["kind"] != "col":
                continue
            for run, _i0, _i1 in slots_of(u["items"], WARICHU_TOL):
                if len(run) < 2:
                    continue
                n_slots += 1
                by_x = sorted(run, key=lambda t: -(t["x"] + t["w"]))
                if by_x == sorted(run, key=lambda t: t["y"]):
                    continue  # 重排是恒等，不算
                n_reordered += 1
                worst = None
                for a in range(len(run)):
                    for b in range(a + 1, len(run)):
                        o = ovr(run[a], run[b])
                        if o > 0.5:
                            if worst is None or o > worst[0]:
                                worst = (o, iou(run[a], run[b]), a, b)
                if worst:
                    risky.append({
                        "page": q["page"], "unit": ui,
                        "ov": round(worst[0], 3),
                        "iou": round(worst[1], 3),
                        "members": [{"x": it["x"], "y": it["y"],
                                     "w": it["w"], "h": it["h"],
                                     "text": q["lines"][it["index"]][:38]}
                                    for it in run],
                    })
                for it in run:
                    if it["h"] < 10:
                        tiny.append({"page": q["page"], "h": it["h"],
                                     "text": q["lines"][it["index"]][:30]})

    print("== 安全审计（全本 47 页）==")
    print("  多框 y 槽: %d，其中实际发生重排的: %d" % (n_slots, n_reordered))
    print("  S1 槽内含 x 重叠 > 0.5 框对的槽: %d" % len(risky))
    for r in risky:
        print("    %s unit#%d 最大重叠=%.2f 对应IoU=%.2f"
              % (r["page"], r["unit"], r["ov"], r["iou"]))
        for m in r["members"]:
            print("       x=%4d y=%4d w=%3d h=%3d %r"
                  % (m["x"], m["y"], m["w"], m["h"], m["text"]))
    print("\n  S2 槽内 h<10px 的框: %d %s" % (len(tiny), tiny[:10]))

    # 判定
    dup_like = [r for r in risky if r["iou"] >= 0.5]
    other = [r for r in risky if r["iou"] < 0.5]
    print("\n== 判定 ==")
    print("  其中 IoU>=0.5（几乎重合的重复检测，重排无阅读影响）: %d" % len(dup_like))
    print("  IoU<0.5（需人工判断）: %d" % len(other))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"tol": WARICHU_TOL, "slots": n_slots,
                   "reordered": n_reordered, "risky": risky,
                   "tiny": tiny, "dup_like": len(dup_like),
                   "needs_review": len(other)}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_safety_audit.json")


if __name__ == "__main__":
    main()
