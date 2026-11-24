# -*- coding: utf-8 -*-
"""night95_eval_8165.py — N95 合并夜：golden_8165 全量真跑回归（TestClient 完整后端链）。

机制复用 night93_eval_8165.py（合并夜阴性证明型）。night94-ruleq 合入 master 后，
Rule R（ゆく→之く）在 master 生效，golden_8165 的
kakikudashi 输出必须与 eval/night94_results_8165.json **逐位一致**：
每行 kakikudashi 相同、avgDist 13.498 / exact 30 / error 0（不是 N93 合并夜的 13.500——
12 行改写随合并生效）。不一致 → 先查实现，绝不改 expected（EXIT 2）。

输出 eval/night95_results_8165.json（合并后扩充归档；NIGHT_ARTIFACTS 非登记）。
用法: python -I tools/night95_eval_8165.py
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

EXPECT = {"avg": 13.498, "exact": 30, "errors": 0}  # night94_results_8165.json 值


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
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(EV, "night94_results_8165.json"),
                          encoding="utf-8"))["results"]
    assert len(golden) == 8165 and len(base) == 8165
    assert [g["id"] for g in golden] == [b["id"] for b in base], "golden 与 night94 归档行序不一致"
    old = {b["id"]: b for b in base}
    print("golden_8165 %d | 基线 night94_results_8165.json（avgDist %.3f / exact %d / error %d）"
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

    diff_ids = []
    for r in results:
        o = old[r["id"]]
        if norm(r["udkundoku_kakikudashi"] or "") != norm(o["udkundoku_kakikudashi"] or ""):
            diff_ids.append(r["id"])

    print("\n=== night95_eval_8165（合并后・扩充归档口径） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg), flush=True)
    print("与 night94 归档输出不一致行: %d %s" % (len(diff_ids), diff_ids[:10]), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg != EXPECT["avg"]:
        fails.append("avgDist %.3f != %.3f" % (avg, EXPECT["avg"]))
    if diff_ids:
        fails.append("输出与 night94 归档不一致 %d 行: %s" % (len(diff_ids), diff_ids[:8]))
    if fails:
        print("\n[FAIL] 逐位一致断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_8165 真跑＝night94 归档逐位一致（avgDist %.3f / exact %d / error 0 / "
          "diff 0 行——Rule R 1 条在 master 生效确认・N94 13.500 から 12 行改写分改善）" % (avg, exact), flush=True)

    out = os.path.join(EV, "night95_results_8165.json")
    json.dump({
        "total": len(results),
        "summary": {
            "label": "night95 merge regression vs night94 archive (Rule R 1 rule merged to master)",
            "n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
            "diff_ids_vs_n94": diff_ids,
            "expect": EXPECT,
        },
        "results": results,
    }, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
