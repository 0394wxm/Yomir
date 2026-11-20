# -*- coding: utf-8 -*-
"""night49_residual_check.py — 验证改后残余的 7 对是否全是伪配对（非并排割注）。

对每一对报：
  dy_top = L.y - R.y
  y 重叠率 = overlap_y / min(h)
  是否满足 A_strict 判据（gap<0.15*wmed ∧ |dy_top|<=0.05*h ∧ |Δh|<=0.15*h）

用法: python -X utf8 tools/night49_residual_check.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

F = os.path.join(ROOT, "eval", "night49_final.json")


def ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def main():
    d = json.load(open(F, encoding="utf-8"))
    exc = d["off"]["exc_after"]
    print("== 改后残余 %d 对：是否并排割注 ==" % len(exc))
    print("%-6s %-8s %-8s %-8s %-7s %-6s %s"
          % ("page", "dy_top", "y重叠率", "Δh/h", "gap/w", "严格?", "右半文本"))
    n_strict = 0
    for e in exc:
        page = e["page"]
        q = json.load(open(os.path.join(sim.OFF, page + ".json"),
                           encoding="utf-8"))
        kept, _bx, _q = sim.page_kept(q)
        byxy = {(it["x"], it["y"]): it for it in kept}
        r = byxy.get((e["r"]["x"], e["r"]["y"]))
        l = byxy.get((e["l"]["x"], e["l"]["y"]))
        if not (r and l):
            print("  %s 框未找到" % page)
            continue
        tyo = ov(r["y"], r["y"] + r["h"], l["y"], l["y"] + l["h"])
        yrat = tyo / max(1, min(r["h"], l["h"]))
        dy = l["y"] - r["y"]
        dh = abs(r["h"] - l["h"]) / max(r["h"], l["h"])
        gap = min(abs(r["x"] - (l["x"] + l["w"])),
                  abs(l["x"] - (r["x"] + r["w"])))
        wmed = sim._median([it["w"] for it in kept
                            if it["w"] > 0.6 * max(b["w"] for b in kept)])
        strict = (abs(dy) <= 0.05 * max(r["h"], l["h"])
                  and dh <= 0.15)
        if strict:
            n_strict += 1
        print("%-6s %+8d %8.2f %8.2f %7.2f %-6s %r"
              % (page, dy, yrat, dh, gap / max(1.0, wmed),
                 "是" if strict else "否", e["r"]["text"][:26]))
    print("\n  其中满足「顶端对齐+等高」（真并排割注）的对数: %d / %d"
          % (n_strict, len(exc)))


if __name__ == "__main__":
    main()
