# -*- coding: utf-8 -*-
"""night49_verify.py — 生产实现 vs 离线模拟的一致性 + 不变式校验。

1) 用**生产 ocr_layout.reorder_warichu_slots** 构造顺序，与离线模拟逐页比对
   （必须完全相同，否则说明模拟没复刻生产）。
2) 校验不变式：输出是输入的置换；主栏框槽位由 reorder_main_slots 决定。
3) 报告 A_strict 层右先率（生产口径）。
4) 回退开关 KANBUN_OCR_WARICHU=0 时应等于旧行为。

用法: python -X utf8 tools/night49_verify.py
产出: eval/night49_verify.json
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
    main_column_keys, reorder_main_slots, reorder_warichu_slots,
)

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OUT = os.path.join(ROOT, "eval", "night49_verify.json")


def order_prod(kept, use_warichu):
    units = sim.cluster_units([dict(b) for b in kept])
    mk = main_column_keys([dict(b) for b in kept])
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            if use_warichu:
                u["items"] = reorder_warichu_slots(u["items"])
            u["items"] = reorder_main_slots(u["items"], mk)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    out = []
    for u in units:
        out.extend(it["index"] for it in u["items"])
    return out


def main():
    pq = json.load(open(os.path.join(ROOT, "eval", "night49_pair_quality.json"),
                        encoding="utf-8"))
    strict = {}
    for x in pq["A_strict"]["rows"]:
        strict.setdefault(x["page"], []).append(
            ((x["r"]["x"], x["r"]["y"]), (x["l"]["x"], x["l"]["y"])))

    mismatch = []
    inv_break = []
    tot = ok_on = ok_off = 0
    perm = 0
    changed = 0
    for fn in sorted(os.listdir(sim.OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(sim.OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, bx, q = r
        p_on = order_prod(kept, True)
        p_off = order_prod(kept, False)
        s_on = sim.order_for(kept, True, 8)
        if p_on != s_on:
            mismatch.append({"page": q["page"],
                             "prod": p_on[:20], "sim": s_on[:20]})
        if sorted(p_on) != sorted([it["index"] for it in kept]):
            inv_break.append(q["page"])
        nch = sum(1 for a, b in zip(p_on, p_off) if a != b)
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
        tot += len(pairs)
        ok_on += sim.measure_right_first(p_on, kept, pairs)
        ok_off += sim.measure_right_first(p_off, kept, pairs)

    print("== 生产实现 vs 离线模拟 ==")
    print("  逐页不一致: %d" % len(mismatch))
    for m in mismatch[:5]:
        print("    %s" % m["page"])
    print("  置换不变式破坏: %d %s" % (len(inv_break), inv_break))

    print("\n== A_strict 层右先率（生产口径，TOL=WARICHU_TOL=8）==")
    print("  关闭(KANBUN_OCR_WARICHU=0): %d / %d (%.1f%%)"
          % (ok_off, tot, 100.0 * ok_off / max(1, tot)))
    print("  开启(默认):                 %d / %d (%.1f%%)"
          % (ok_on, tot, 100.0 * ok_on / max(1, tot)))

    print("\n== 全本置换差异 ==")
    print("  有变化的页: %d / 47，位置变化的框: %d" % (changed, perm))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"mismatch": mismatch, "inv_break": inv_break,
                   "pairs": tot, "right_first_off": ok_off,
                   "right_first_on": ok_on, "changed_pages": changed,
                   "perm_changes": perm}, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_verify.json")


if __name__ == "__main__":
    main()
