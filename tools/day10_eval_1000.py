# -*- coding: utf-8 -*-
"""day10_eval_1000.py — D10：1000 条评测（规则引擎 + guwenbert 离线对比）。

严格约束：
  * **只写 eval/day10_results_1000.json 和 eval/day10_guwenbert_1000.json**，
    不覆盖任何已有评测归档（night21/22/26/31...）。
  * 规则引擎走进程内 TestClient（与 run_eval_1000 同模式，monkeypatch save_kundoku 不写库）。
  * guwenbert 走 tools/run_eval_guwenbert 的加载器（离线：HF_HUB_OFFLINE=1）。
  * 统计：总体 / 分档（≤20、21-40、41-60、>60）/ 分文体（論語 vs 故事）。

用法：
  python tools/day10_eval_1000.py --engine rule
  python tools/day10_eval_1000.py --engine guwenbert
  python tools/day10_eval_1000.py --engine both
"""
import argparse
import collections
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
EV = os.path.join(ROOT, "eval")

GOLDEN = os.path.join(EV, "golden_1000.json")


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


def bucket_of(h):
    n = len(norm(h))
    if n <= 20:
        return "≤20字"
    if n <= 40:
        return "21-40字"
    if n <= 60:
        return "41-60字"
    return ">60字"


def genre_of(url):
    u = (url or "").lower()
    if "rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    if "/keibu/" in u:
        return "経部"
    return "その他"


def summarize(results, label):
    ok = [r for r in results if r.get("edit_distance") is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n if n else None
    print("\n=== %s ===" % label)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.2f"
          % (n, len(results) - n, exact, n, avg if avg is not None else -1))

    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)

    print("\n%-10s %5s %9s %7s" % ("分档", "n", "avgDist", "精确"))
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        rs = by_b.get(b, [])
        if rs:
            print("%-10s %5d %9.2f %7d"
                  % (b, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                     sum(1 for x in rs if x["exact_match"])))

    print("\n%-10s %5s %9s %7s" % ("文体", "n", "avgDist", "精确"))
    for g, rs in sorted(by_g.items(), key=lambda kv: -len(kv[1])):
        print("%-10s %5d %9.2f %7d"
              % (g, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                 sum(1 for x in rs if x["exact_match"])))

    print("\n文体 × 分档 avgDist（n）:")
    print("%-8s %-10s %-10s %-10s %-10s" % ("", "≤20字", "21-40字", "41-60字", ">60字"))
    for g in ["論語", "故事", "その他"]:
        if g not in by_g:
            continue
        cells = []
        for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
            rs = [x for x in by_g[g] if bucket_of(x["hakubun"]) == b]
            cells.append("%.2f(%d)" % (sum(x["edit_distance"] for x in rs) / len(rs), len(rs))
                         if rs else "-")
        print("%-8s %-10s %-10s %-10s %-10s" % (g, *cells))

    cross = {}
    for g, rs_g in by_g.items():
        for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
            rs = [x for x in rs_g if bucket_of(x["hakubun"]) == b]
            if rs:
                cross["%s|%s" % (g, b)] = {
                    "n": len(rs),
                    "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                }

    return {
        "label": label,
        "n": n,
        "errors": len(results) - n,
        "exact": exact,
        "avg_edit_distance": round(avg, 3) if avg is not None else None,
        "by_bucket": {b: {"n": len(rs),
                          "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                          "exact": sum(1 for x in rs if x["exact_match"])}
                      for b, rs in by_b.items()},
        "by_genre": {g: {"n": len(rs),
                         "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                         "exact": sum(1 for x in rs if x["exact_match"])}
                     for g, rs in by_g.items()},
        "cross": cross,
    }


def run_rule(golden):
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
                    "edit_distance": levenshtein(a, b),
                    "exact_match": a == b,
                })
                if i % 100 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(golden), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real
    return results


def run_guwenbert(golden, limit=0):
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import run_eval_guwenbert as rg

    eng = rg.build_engine(None)
    items = golden[:limit] if limit else golden
    results = []
    t0 = time.time()
    for i, g in enumerate(items, 1):
        t1 = time.time()
        try:
            kk = rg.kundoku_line(eng, g["hakubun"])
            err = ""
        except Exception as e:
            kk, err = "", repr(e)
        a, b = norm(kk), norm(g["expected_kakikudashi"])
        results.append({
            "id": g["id"], "source_url": g.get("source_url", ""),
            "hakubun": g["hakubun"],
            "expected_kakikudashi": g["expected_kakikudashi"],
            "udkundoku_kakikudashi": kk,
            "edit_distance": levenshtein(a, b) if not err else None,
            "exact_match": (a == b) if not err else False,
            "error": err,
            "elapsed_sec": round(time.time() - t1, 2),
        })
        if i % 20 == 0:
            done = [r for r in results if r["edit_distance"] is not None]
            print("  %d/%d avgDist %.2f (%.0fs)"
                  % (i, len(items), sum(r["edit_distance"] for r in done) / len(done), time.time() - t0),
                  flush=True)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["rule", "guwenbert", "both"], default="rule")
    ap.add_argument("--limit", type=int, default=0, help="guwenbert 只跑前 N 条（冒烟）")
    arg = ap.parse_args()

    with open(GOLDEN, encoding="utf-8") as f:
        golden = json.load(f)
    print("golden_1000: %d 条" % len(golden), flush=True)

    summary = {}
    if arg.engine in ("rule", "both"):
        res = run_rule(golden)
        s = summarize(res, "规则引擎（当前生产线）1000 条")
        summary["rule"] = s
        out = os.path.join(EV, "day10_results_1000.json")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"total": len(res), "exact_match_count": s["exact"],
                       "avg_edit_distance": s["avg_edit_distance"],
                       "summary": s, "results": res}, f, ensure_ascii=False, indent=1)
        print("written:", out, flush=True)

    if arg.engine in ("guwenbert", "both"):
        res = run_guwenbert(golden, arg.limit)
        s = summarize(res, "guwenbert（离线）%d 条" % len(res))
        summary["guwenbert"] = s
        out = os.path.join(EV, "day10_guwenbert_1000.json")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"total": len(res), "exact_match_count": s["exact"],
                       "avg_edit_distance": s["avg_edit_distance"],
                       "summary": s, "results": res}, f, ensure_ascii=False, indent=1)
        print("written:", out, flush=True)

    if len(summary) == 2:
        r, g = summary["rule"], summary["guwenbert"]
        print("\n=== 规则引擎 vs guwenbert ===")
        print("avgDist  %.2f vs %.2f  (差 %+.2f)"
              % (r["avg_edit_distance"], g["avg_edit_distance"],
                 g["avg_edit_distance"] - r["avg_edit_distance"]))
        print("精确     %d vs %d" % (r["exact"], g["exact"]))
        with open(os.path.join(EV, "day10_compare_1000.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
