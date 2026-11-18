# -*- coding: utf-8 -*-
"""compare_day5.py — D5：人工标注 50 条 vs tools/classify_errors.py 输出。

指标（逐类 + 整体）：
  * 逐条「完全一致」：分类器给出的类别集合 == 人工类别集合；
  * 逐条「有交集」：至少命中一个人工类别；
  * 每类 precision / recall（以人工为基准）；
  * overall micro P/R/F1 与 per-label F1。

不修改分类器（D5 明令）。
"""
import collections
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from day5_manual_labels import MANUAL, NOTES  # noqa: E402


def main():
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3_classified.json"), encoding="utf-8") as f:
        cls = json.load(f)
    auto = {e["id"]: set(c for c in e["cats"] if c != "EXACT") for e in cls["per_entry"]}

    ids = list(MANUAL)
    print("对照 %d 条（人工标注 vs 分类器）" % len(ids))
    print()

    exact = 0
    overlap = 0
    rows = []
    for rid in ids:
        man = set(MANUAL[rid])
        got = auto.get(rid, set())
        eq = man == got
        ov = bool(man & got)
        exact += eq
        overlap += ov
        missing = sorted(man - got)
        extra = sorted(got - man)
        rows.append((rid, sorted(man), sorted(got), eq, missing, extra))

    print("=== 逐条结果（只列不一致的） ===")
    for rid, man, got, eq, missing, extra in rows:
        if eq:
            continue
        print("%-14s 人工=%s" % (rid, ",".join(man)))
        print("%-14s 自动=%s" % ("", ",".join(got) or "（空）"))
        if missing:
            print("   漏标(miss): %s" % ",".join(missing))
        if extra:
            print("   多标(false): %s" % ",".join(extra))
        print()

    print("=== 整体 ===")
    n = len(ids)
    print("完全一致：%d/%d = %.0f%%" % (exact, n, 100.0 * exact / n))
    print("至少命中一类：%d/%d = %.0f%%" % (overlap, n, 100.0 * overlap / n))

    # per-label
    labels = ["助词错", "切分错", "动词活用错", "旧字体", "专名错", "其他"]
    print()
    print("=== 逐类（人工为基准） ===")
    print("%-10s %6s %6s %6s %8s %8s %8s" % ("类", "TP", "FP", "FN", "P", "R", "F1"))
    tp_all = fp_all = fn_all = 0
    for lb in labels:
        tp = sum(1 for rid in ids if lb in MANUAL[rid] and lb in auto.get(rid, set()))
        fp = sum(1 for rid in ids if lb not in MANUAL[rid] and lb in auto.get(rid, set()))
        fn = sum(1 for rid in ids if lb in MANUAL[rid] and lb not in auto.get(rid, set()))
        p = 100.0 * tp / (tp + fp) if tp + fp else 0.0
        r = 100.0 * tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        if tp + fp + fn:
            print("%-10s %6d %6d %6d %7.0f%% %7.0f%% %7.0f%%" % (lb, tp, fp, fn, p, r, f1))
        tp_all += tp
        fp_all += fp
        fn_all += fn
    p = 100.0 * tp_all / (tp_all + fp_all) if tp_all + fp_all else 0.0
    r = 100.0 * tp_all / (tp_all + fn_all) if tp_all + fn_all else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    print("%-10s %6d %6d %6d %7.0f%% %7.0f%% %7.0f%%" % ("micro", tp_all, fp_all, fn_all, p, r, f1))

    # 输出 JSON 供报告引用
    out = os.path.join(ROOT, "eval", "day5_classifier_vs_manual.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({
            "n": n, "exact": exact, "overlap": overlap,
            "rows": [{"id": r[0], "manual": r[1], "auto": r[2], "identical": r[3],
                      "miss": r[4], "false": r[5], "note": NOTES.get(r[0], "")} for r in rows],
            "labels": labels,
            "micro": {"tp": tp_all, "fp": fp_all, "fn": fn_all,
                      "precision": round(p, 1), "recall": round(r, 1), "f1": round(f1, 1)},
        }, f, ensure_ascii=False, indent=2)
    print("\nwritten:", out)


if __name__ == "__main__":
    main()
