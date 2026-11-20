# -*- coding: utf-8 -*-
"""night49_sweep.py — TOL 敏感性扫描（复用 night49_simulate 的测量逻辑）。

用法: python -X utf8 tools/night49_sweep.py
产出: eval/night49_sweep.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]  # 避免 night49_simulate 读 argv
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OUT = os.path.join(ROOT, "eval", "night49_sweep.json")


def run(tol):
    pq = json.load(open(os.path.join(ROOT, "eval", "night49_pair_quality.json"),
                        encoding="utf-8"))
    strict = {}
    for x in pq["A_strict"]["rows"]:
        strict.setdefault(x["page"], []).append(
            ((x["r"]["x"], x["r"]["y"]), (x["l"]["x"], x["l"]["y"])))

    tot = okb = oka = 0
    perm = 0
    changed = 0
    regress = []
    for fn in sorted(os.listdir(sim.OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, bx, q = r
        before = sim.order_for(kept, False, tol)
        after = sim.order_for(kept, True, tol)
        if sorted(before) != sorted(after):
            raise SystemExit("invariant broken %s" % q["page"])
        nch = sum(1 for a, b in zip(before, after) if a != b)
        if nch:
            changed += 1
            perm += nch
        keys = strict.get(q["page"], [])
        if not keys:
            continue
        byxy = {(it["x"], it["y"]): it for it in kept}
        pairs = [(byxy[a], byxy[b]) for a, b in keys
                 if a in byxy and b in byxy]
        if not pairs:
            continue
        b_ok = sim.measure_right_first(before, kept, pairs)
        a_ok = sim.measure_right_first(after, kept, pairs)
        tot += len(pairs)
        okb += b_ok
        oka += a_ok
        if a_ok < b_ok:
            regress.append({"page": q["page"], "n": len(pairs),
                            "before": b_ok, "after": a_ok})
    return {"tol": tol, "pairs": tot, "before": okb, "after": oka,
            "changed_pages": changed, "perm_changes": perm,
            "regressions": regress}


def main():
    rows = []
    print("%-5s %6s %9s %9s %8s %9s" % ("TOL", "对数", "改前右先", "改后右先",
                                        "变页", "位置变"))
    for tol in (2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 30):
        r = run(tol)
        rows.append(r)
        print("%-5d %6d %8.1f%% %8.1f%% %8d %9d"
              % (tol, r["pairs"],
                 100.0 * r["before"] / max(1, r["pairs"]),
                 100.0 * r["after"] / max(1, r["pairs"]),
                 r["changed_pages"], r["perm_changes"]))
        if r["regressions"]:
            print("      退化: %s" % r["regressions"])
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_sweep.json")


if __name__ == "__main__":
    main()
