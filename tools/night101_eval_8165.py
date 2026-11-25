# -*- coding: utf-8 -*-
"""night101_eval_8165.py — Night 101 合并夜（night98-report → master）の golden_8165 全量真跑回归（TestClient 完整后端链）。

机制复用 night100_eval_8165.py（N93/N95/N97/N100 合并夜型：基线＝合并带入归档・全行 diff=0 断言）。
扩充归档（NIGHT_ARTIFACTS 非登记・默认口径は golden_4000 のまま＝N82 以降惯例）。
合并後の真跑出力は night100_results_8165.json（N100 归档）と**全行逐位一致**：
  - 全 8165 行 udkundoku_kakikudashi 一字不変（报告-only 夜＝引擎零改动・Rule T 3 条
    は既に master 生效済み・night98-report 分支は backend 一字未碰）；
  - avgDist 13.469／exact 30／error 0（＝night100 归档值）。
不一致 → 先查实现，绝不改 expected（EXIT 2）。

输出 eval/night101_results_8165.json（扩充归档）。
用法: python -I tools/night101_eval_8165.py
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

EXPECT = {"avg": 13.469, "exact": 30, "errors": 0}  # night100_results_8165.json 归档值（全行逐位一致门）


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
    base = json.load(open(os.path.join(EV, "night100_results_8165.json"),
                          encoding="utf-8"))["results"]
    assert len(golden) == 8165 and len(base) == 8165
    assert [g["id"] for g in golden] == [b["id"] for b in base], "golden 与 night100 归档行序不一致"
    old = {b["id"]: b for b in base}
    print("golden_8165 %d | 基线 night100_results_8165.json（avgDist %.3f / exact %d / error %d）"
          " | 合并夜全行逐位对照" % (len(golden), 13.469, 30, 0), flush=True)

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

    # ---- 与 night100 归档全行逐位对照 ----
    diff_rows = [r["id"] for r in results
                 if norm(r["udkundoku_kakikudashi"] or "") != norm(old[r["id"]]["udkundoku_kakikudashi"] or "")]

    print("\n=== night101_eval_8165（合并夜・扩充归档・vs night100 归档全行逐位） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg), flush=True)
    print("与 night100 归档不一致行 %d 行（合并夜门＝0）" % (len(diff_rows),), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg is None or avg > EXPECT["avg"]:
        fails.append("avgDist %.3f > N100 归档 %.3f（全行逐位一致门）" % (avg, EXPECT["avg"]))
    if diff_rows:
        fails.append("与 night100 归档不一致行 %d: %s" % (len(diff_rows), diff_rows[:8]))
    if fails:
        print("\n[FAIL] night100 归档逐位一致断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_8165 真跑＝night100 归档全行逐位一致（avgDist %.3f / exact %d / error 0 / "
          "diff 0 行——报告-only 分支合并・Rule T 3 条维持 master 版）"
          % (avg, exact), flush=True)

    out = os.path.join(EV, "night101_results_8165.json")
    json.dump({
        "total": len(results),
        "summary": {
            "label": "night101 merge regression vs night100 archive (report-only night98-report merged, engine untouched, bit-identical)",
            "n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
            "changed_ids_vs_n100": sorted(diff_rows),
            "expect": EXPECT,
        },
        "results": results,
    }, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
