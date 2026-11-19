# -*- coding: utf-8 -*-
"""day17_live.py — D17 真机验证：Rule F 上线后 2000 条完整复跑。

走真实 TestClient + 完整后端路径（含 Rule D/E/F）。
与离线（tools/day17_boundary.py）比对：avgDist 必须逐位一致。
同时与 day16 的 2000 条基线逐条比对改善/变差。
输出 eval/day17_results_2000.json。
"""
import collections
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


def bucket_of(hb):
    n = len(norm(hb))
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def genre_of(url):
    u = (url or "").lower()
    if "/keibu/daigaku" in u:
        return "大学"
    if "/keibu/kokyo" in u:
        return "孝経"
    if "/keibu/rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    return "その他"


def main():
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    golden = json.load(open(os.path.join(EV, "golden_2000.json"), encoding="utf-8"))
    prev = {r["id"]: r for r in json.load(
        open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))["results"]}
    print("golden_2000: %d 条 | 基线 avgDist %.3f"
          % (len(golden), sum(x["edit_distance"] for x in prev.values()) / len(prev)),
          flush=True)

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
                if i % 400 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(golden), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n
    print("\n=== Rule F 真机 2000 条 ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f"
          % (n, len(results) - n, exact, n, avg), flush=True)

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
    print("对比 day16 基线（Rule E）：改善 %d / 变差 %d / 持平 %d%s"
          % (better, worse, same, ("  变差:%s" % ",".join(worse_ids[:8])) if worse else ""),
          flush=True)

    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
    print("\n%-8s %5s %9s %6s" % ("分档", "n", "avgDist", "精确"), flush=True)
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        rs = by_b.get(b, [])
        if rs:
            print("%-8s %5d %9.3f %6d"
                  % (b, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                     sum(1 for x in rs if x["exact_match"])), flush=True)
    print("\n%-8s %5s %9s %6s" % ("文体", "n", "avgDist", "精确"), flush=True)
    for g, rs in sorted(by_g.items(), key=lambda kv: -len(kv[1])):
        print("%-8s %5d %9.3f %6d"
              % (g, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                 sum(1 for x in rs if x["exact_match"])), flush=True)

    out = {"total": len(results), "exact_match_count": exact,
           "avg_edit_distance": round(avg, 3),
           "vs_day16": {"better": better, "worse": worse, "same": same,
                        "worse_ids": worse_ids[:50]},
           "results": results}
    json.dump(out, open(os.path.join(EV, "day17_results_2000.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written: eval/day17_results_2000.json", flush=True)


if __name__ == "__main__":
    main()
