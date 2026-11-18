# -*- coding: utf-8 -*-
"""
run_eval_1000.py — Night 26：eval/golden_1000.json 逐条过当前生产线引擎。

与 run_eval_rongo.py 同一模式（进程内 TestClient、monkeypatch save_kundoku 不写库）。
输出 eval/night26_results_full.json（自报 total / exact_match_count 供验收门核对）。
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def norm(s):
    return re.sub(r"\s+", "", s)


def levenshtein(a, b):
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
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    with open(os.path.join(ROOT, "eval", "golden_1000.json"), encoding="utf-8") as f:
        golden = json.load(f)
    print("golden_1000 entries:", len(golden))

    results = []
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, g in enumerate(golden, start=1):
                r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                if r.status_code != 200:
                    results.append({"id": g["id"], "hakubun": g["hakubun"],
                                    "expected_kakikudashi": g["expected_kakikudashi"],
                                    "udkundoku_kakikudashi": None, "error": repr(r.text)[:200]})
                    continue
                got = r.json().get("kakikudashi", "")
                a, b = norm(got), norm(g["expected_kakikudashi"])
                results.append({
                    "id": g["id"], "source_url": g["source_url"],
                    "hakubun": g["hakubun"],
                    "expected_kakikudashi": g["expected_kakikudashi"],
                    "udkundoku_kakikudashi": got,
                    "edit_distance": levenshtein(a, b),
                    "exact_match": a == b,
                })
                if i % 100 == 0:
                    print("  %d/%d" % (i, len(golden)))
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r.get("edit_distance") is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    print("\n=== 1000 条基线（当前生产线，Rule C' 后）===")
    print("engine OK %d / error %d  精确匹配 %d/%d  avgDist %.2f"
          % (n, len(results) - n, exact, n, sum(r["edit_distance"] for r in ok) / n if n else -1))

    buckets = {"<=20": [], "20-40": [], ">40": []}
    for r in ok:
        ln = len(norm(r["hakubun"]))
        buckets["<=20" if ln <= 20 else ("20-40" if ln <= 40 else ">40")].append(r)
    for b, rs in buckets.items():
        if rs:
            print("  %-6s n=%4d avgDist %6.2f  精确 %d" % (
                b, len(rs), sum(r["edit_distance"] for r in rs) / len(rs),
                sum(1 for r in rs if r["exact_match"])))

    # 与 500 条官方归档的稳定性对照（前 500 id 交集）
    with open(os.path.join(ROOT, "eval", "night22_results_full.json"), encoding="utf-8") as f:
        n22 = {r["id"]: r for r in json.load(f)["results"]}
    common = [r for r in ok if r["id"] in n22]
    if common:
        d26 = sum(r["edit_distance"] for r in common) / len(common)
        d22 = sum(n22[r["id"]]["edit_distance"] for r in common) / len(common)
        print("\n与 night22 归档交集 %d 条：avgDist %.2f vs %.2f（应相等，引擎确定性）"
              % (len(common), d26, d22))

    out = {"total": len(results), "exact_match_count": exact,
           "avg_edit_distance": round(sum(r["edit_distance"] for r in ok) / n, 3) if n else None,
           "results": results}
    out_path = os.path.join(ROOT, "eval", "night26_results_full.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("written:", out_path)


if __name__ == "__main__":
    main()
