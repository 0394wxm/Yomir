# -*- coding: utf-8 -*-
"""night49_dup_impact.py — 重复检测框重排前后的文本影响。

safety_audit 找到 9 个槽含 x 重叠 > 0.5 的框对，其中 7 个 IoU>=0.5
（同一行被检测两次）。这 7 个槽若发生重排，会交换两个几乎相同框的位置。

本脚本对每个风险槽，打印**重排前 vs 重排后**该槽贡献的文本序列，
并判断是否产生了「阅读上可见」的差异（文本不同而非重复）。

用法: python -X utf8 tools/night49_dup_impact.py
产出: eval/night49_dup_impact.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

from backend.ocr_layout import WARICHU_TOL, reorder_warichu_slots  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

AUDIT = os.path.join(ROOT, "eval", "night49_safety_audit.json")
OUT = os.path.join(ROOT, "eval", "night49_dup_impact.json")


def main():
    aud = json.load(open(AUDIT, encoding="utf-8"))
    targets = {(r["page"], r["unit"]): r for r in aud["risky"]}

    print("== 风险槽：重排前后的槽内顺序 ==")
    out_rows = []
    n_visible = 0
    for fn in sorted(os.listdir(sim.OFF)):
        if not fn.endswith(".json"):
            continue
        page = fn[:-5]
        if not any(k[0] == page for k in targets):
            continue
        q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, _bx, q = r
        units = sim.cluster_units([dict(b) for b in kept])
        for ui, u in enumerate(units):
            if u["kind"] != "col" or (page, ui) not in targets:
                continue
            items = sorted(u["items"], key=lambda t: t["y"])
            before = [it["index"] for it in items]
            after = [it["index"] for it in reorder_warichu_slots(items,
                                                                 WARICHU_TOL)]
            # 只看这个槽的范围
            tb = [q["lines"][i] for i in before]
            ta = [q["lines"][i] for i in after]
            changed = tb != ta
            if changed:
                n_visible += 1
            print("\n  --- %s unit#%d  (文本%s) ---"
                  % (page, ui, "有变" if changed else "相同"))
            print("   改前: %s" % (tb,))
            print("   改后: %s" % (ta,))
            out_rows.append({"page": page, "unit": ui,
                             "before": tb, "after": ta,
                             "changed": changed,
                             "unit_size": len(u["items"])})

    print("\n== 汇总 ==")
    print("  风险槽 %d，其中槽内文本序列发生变化: %d" % (len(out_rows),
                                                        n_visible))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"rows": out_rows, "n_changed": n_visible}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_dup_impact.json")


if __name__ == "__main__":
    main()
