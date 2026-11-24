# -*- coding: utf-8 -*-
"""night88_eval_4000.py — N88 零规则夜：golden_4000 全量真跑阴性回归
（TestClient 完整后端链）。

机制复用 night85/86/87_eval_4000.py。本夜 Rule P 零收录（kundoku_rules.py 一字未改），
golden_4000 的 kakikudashi 输出必须与 night87_results_4000.json **逐位一致**：
每行 kakikudashi 相同、avgDist 13.491 / exact 24 / error 0。不一致 → 先查实现，
绝不改 expected（EXIT 2）。

输出 eval/night88_results_4000.json（阴性证明归档；零规则夜＝NIGHT_ARTIFACTS
不登记、accept 88 走 N69/N74/N76 报告-only 先例 skip=eval_integrity）。
用法: python -I tools/night88_eval_4000.py
"""
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

EXPECT = {"avg": 13.491, "exact": 24, "errors": 0}  # night87_results_4000.json 链尾值


def norm(s):
    return re.sub(r"\s+", "", s or "")


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    golden = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(EV, "night87_results_4000.json"),
                          encoding="utf-8"))["results"]
    assert len(golden) == 4000 and len(base) == 4000
    assert [g["id"] for g in golden] == [b["id"] for b in base], "golden 与 night87 归档行序不一致"
    old = {b["id"]: b for b in base}
    print("golden_4000 %d | 基线 night87_results_4000.json（avgDist %.3f / exact %d / error %d）"
          % (len(golden), EXPECT["avg"], EXPECT["exact"], EXPECT["errors"]), flush=True)

    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    results = []
    t0 = time.time()
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, g in enumerate(golden, 1):
                r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                if r.status_code != 200:
                    results.append({"id": g["id"], "source_url": g.get("source_url", ""),
                                    "hakubun": g["hakubun"],
                                    "expected_kakikudashi": g["expected_kakikudashi"],
                                    "udkundoku_kakikudashi": None,
                                    "edit_distance": None, "exact_match": False,
                                    "error": repr(r.text)[:200]})
                    continue
                got = r.json().get("kakikudashi", "")
                a, b = norm(got), norm(g["expected_kakikudashi"])
                results.append({
                    "id": g["id"], "source_url": g.get("source_url", ""),
                    "hakubun": g["hakubun"],
                    "expected_kakikudashi": g["expected_kakikudashi"],
                    "udkundoku_kakikudashi": got,
                    "edit_distance": lev(a, b),
                    "exact_match": a == b,
                })
                if i % 2000 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(golden), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = round(sum(r["edit_distance"] for r in ok) / n, 3) if n else None
    errors = len(results) - n

    # 逐位对照 night87 归档（零规则夜：全行必须一致）
    diff_ids = []
    for r in results:
        o = old[r["id"]]
        if norm(r["udkundoku_kakikudashi"] or "") != norm(o["udkundoku_kakikudashi"] or ""):
            diff_ids.append(r["id"])

    print("\n=== night88_eval_4000（零规则夜：kundoku_rules.py 一字未改） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg), flush=True)
    print("与 night87 归档输出不一致行: %d %s" % (len(diff_ids), diff_ids[:10]), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg != EXPECT["avg"]:
        fails.append("avgDist %.3f != %.3f" % (avg, EXPECT["avg"]))
    if diff_ids:
        fails.append("输出与 night87 归档不一致 %d 行: %s" % (len(diff_ids), diff_ids[:8]))
    if fails:
        print("\n[FAIL] 逐位一致断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_4000 与 night87 归档逐位一致（avgDist %.3f / exact %d / error 0 / 输出差异 0 行）"
          % (avg, exact), flush=True)

    out = os.path.join(EV, "night88_results_4000.json")
    json.dump({
        "total": len(results),
        "summary": {
            "label": "night88 zero-rule regression vs night87 archive (Rule P: 0 rules accepted; "
                     "kundoku_rules.py untouched)",
            "n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
            "diff_ids_vs_n87": diff_ids,
            "expect": EXPECT,
        },
        "results": results,
    }, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
