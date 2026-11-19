# -*- coding: utf-8 -*-
"""day16_guwenbert_new.py — D16：guwenbert 只跑新增 1000 条（离线）对比。

用 D10 的加载器（tools/run_eval_guwenbert.py，HF_HUB_OFFLINE=1），
只跑 golden_2000 的 [1000:2000] 段，避免重跑旧 1000 条（旧结果已有 day10_guwenbert_1000.json）。
输出 eval/day16_guwenbert_new1000.json。

用法：python tools/day16_guwenbert_new.py [--limit N]
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=1000)
    arg = ap.parse_args()

    golden = json.load(open(os.path.join(EV, "golden_2000.json"), encoding="utf-8"))
    items = golden[arg.offset:]
    if arg.limit:
        items = items[:arg.limit]
    print("新增段 [%d:] 共 %d 条" % (arg.offset, len(items)), flush=True)

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import run_eval_guwenbert as rg

    t_init = time.time()
    eng = rg.build_engine(None)
    print("engine built in %.1fs" % (time.time() - t_init), flush=True)

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
            "edit_distance": lev(a, b) if not err else None,
            "exact_match": (a == b) if not err else False,
            "error": err,
            "elapsed_sec": round(time.time() - t1, 2),
        })
        if i % 50 == 0:
            done = [r for r in results if r["edit_distance"] is not None]
            print("  %d/%d avgDist %.2f (%.0fs)"
                  % (i, len(items), sum(r["edit_distance"] for r in done) / len(done),
                     time.time() - t0), flush=True)

    ok = [r for r in results if r["edit_distance"] is not None]
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / len(ok) if ok else None
    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
    summary = {
        "label": "guwenbert 新增段 %d 条" % len(ok),
        "n": len(ok), "errors": len(results) - len(ok), "exact": exact,
        "avg_edit_distance": round(avg, 3) if avg else None,
        "by_bucket": {b: {"n": len(rs), "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                          "exact": sum(1 for x in rs if x["exact_match"])}
                      for b, rs in by_b.items()},
        "by_genre": {g: {"n": len(rs), "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                         "exact": sum(1 for x in rs if x["exact_match"])}
                     for g, rs in by_g.items()},
    }
    print("\n=== guwenbert 新增 %d 条 ===" % len(ok), flush=True)
    print("OK %d / error %d | 精确 %d | avgDist %.3f"
          % (len(ok), len(results) - len(ok), exact, avg if avg else -1), flush=True)
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        d = summary["by_bucket"].get(b)
        if d:
            print("  %-8s n=%4d avg %6.2f exact %d" % (b, d["n"], d["avg"], d["exact"]), flush=True)
    for g, d in summary["by_genre"].items():
        print("  %-6s n=%4d avg %6.2f exact %d" % (g, d["n"], d["avg"], d["exact"]), flush=True)

    out = os.path.join(EV, "day16_guwenbert_new1000.json")
    json.dump({"total": len(results), "summary": summary, "results": results},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
