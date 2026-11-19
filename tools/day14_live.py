# -*- coding: utf-8 -*-
"""day14_live.py — D14 真机验证：Rule E 上线后 1000 条完整复跑。

走真实 TestClient + 完整后端路径（含 style_fix_with_hakubun -> Rule E），
monkeypatch save_kundoku 避免 D: 盘 fsync 拖慢（只影响写库，不影响训读结果）。

与离线（tools/day14_boundary.py）比对：avgDist 必须逐位一致，否则说明
「规则写进 backend/」与「模拟脚本」有偏差。

输出 eval/day14_results_1000.json。
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
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    with open(os.path.join(EV, "golden_1000.json"), encoding="utf-8") as f:
        golden = json.load(f)
    print("golden_1000: %d 条" % len(golden), flush=True)

    # 旧基线（D11 真机结果），用于对比
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        prev = {r["id"]: r for r in json.load(f)["results"]}
    print("D11 基线：avgDist %.3f" % (sum(r["edit_distance"] for r in prev.values()
                                          if r["edit_distance"] is not None)
                                      / len(prev)), flush=True)

    results = []
    t0 = time.time()
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, g in enumerate(golden, 1):
                r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                if r.status_code != 200:
                    results.append({"id": g["id"], "hakubun": g["hakubun"],
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
                if i % 200 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(golden), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n
    print("\n=== Rule E 真机 1000 条 ===")
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f"
          % (n, len(results) - n, exact, n, avg))

    # 与 D11 基线逐条比对
    better = worse = same = 0
    worse_ids = []
    for r in ok:
        p = prev.get(r["id"])
        if not p or p["edit_distance"] is None:
            continue
        if r["edit_distance"] < p["edit_distance"]:
            better += 1
        elif r["edit_distance"] > p["edit_distance"]:
            worse += 1
            worse_ids.append(r["id"])
        else:
            same += 1
    print("对比 D11 基线：改善 %d / 变差 %d / 持平 %d%s"
          % (better, worse, same, ("  变差:%s" % ",".join(worse_ids[:8])) if worse else ""))

    import collections
    by_b = collections.defaultdict(list)
    for r in ok:
        L = len(norm(r["hakubun"]))
        by_b["≤20" if L <= 20 else ("21-40" if L <= 40 else ("41-60" if L <= 60 else ">60"))].append(r)
    for b in ["≤20", "21-40", "41-60", ">60"]:
        rs = by_b.get(b, [])
        if rs:
            print("  %-6s n=%4d avgDist %6.2f  精确 %d"
                  % (b, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                     sum(1 for x in rs if x["exact_match"])))

    out = {"total": len(results), "exact_match_count": exact,
           "avg_edit_distance": round(avg, 3),
           "vs_day11": {"better": better, "worse": worse, "same": same,
                        "worse_ids": worse_ids[:50]},
           "results": results}
    with open(os.path.join(EV, "day14_results_1000.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("written: eval/day14_results_1000.json", flush=True)


if __name__ == "__main__":
    main()
