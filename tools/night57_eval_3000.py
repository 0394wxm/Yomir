# -*- coding: utf-8 -*-
"""night57_eval_3000.py — N57：规则引擎全跑 3000 条（day16_eval_2000.py 同款机制）。

走真实 TestClient（完整后端链，Rule D/E/F/G 全在），
monkeypatch save_kundoku 避开 D: 盘 fsync。
支持 --start/--end 断点；附带「前 2000 条 vs day17 真机归档」的确定性对照
（差异行应恰为 Rule G 的 136 条改写行）。
输出 eval/night57_results_3000.json。
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
    if "/syubu/shikyo" in u:
        return "詩経"
    if "/syubu/" in u:
        return "漢詩"
    if "/keibu/daigaku" in u:
        return "大学"
    if "/keibu/kokyo" in u:
        return "孝経"
    if "/keibu/rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    return "その他"


def summarize(results, label):
    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n if n else None
    print("\n=== %s ===" % label, flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f"
          % (n, len(results) - n, exact, n, avg if avg is not None else -1), flush=True)
    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
    print("\n%-10s %5s %9s %7s" % ("分档", "n", "avgDist", "精确"), flush=True)
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        rs = by_b.get(b, [])
        if rs:
            print("%-10s %5d %9.3f %7d"
                  % (b, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                     sum(1 for x in rs if x["exact_match"])), flush=True)
    print("\n%-10s %5s %9s %7s" % ("文体", "n", "avgDist", "精确"), flush=True)
    for g, rs in sorted(by_g.items(), key=lambda kv: -len(kv[1])):
        print("%-10s %5d %9.3f %7d"
              % (g, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                 sum(1 for x in rs if x["exact_match"])), flush=True)
    print("\n文体 × 分档 avgDist（n）:", flush=True)
    print("%-8s %-14s %-14s %-14s %-14s" % ("", "≤20字", "21-40字", "41-60字", ">60字"),
          flush=True)
    for g in ["故事", "論語", "大学", "孝経", "詩経", "漢詩"]:
        if g not in by_g:
            continue
        cells = []
        for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
            rs = [x for x in by_g[g] if bucket_of(x["hakubun"]) == b]
            cells.append("%.2f(%d)" % (sum(x["edit_distance"] for x in rs) / len(rs), len(rs))
                         if rs else "-")
        print("%-8s %-14s %-14s %-14s %-14s" % (g, *cells), flush=True)
    return {
        "label": label, "n": n, "errors": len(results) - n, "exact": exact,
        "avg_edit_distance": round(avg, 3) if avg is not None else None,
        "by_bucket": {b: {"n": len(rs), "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                          "exact": sum(1 for x in rs if x["exact_match"])}
                      for b, rs in by_b.items()},
        "by_genre": {g: {"n": len(rs), "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                         "exact": sum(1 for x in rs if x["exact_match"])}
                     for g, rs in by_g.items()},
    }


def run_rule(items):
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    results = []
    t0 = time.time()
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, g in enumerate(items, 1):
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
                if i % 200 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(items), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    arg = ap.parse_args()

    golden = json.load(open(os.path.join(EV, "golden_3000.json"), encoding="utf-8"))
    items = golden[arg.start:arg.end or None]
    print("golden_3000: %d 条，本次跑 [%d:%d) 共 %d 条"
          % (len(golden), arg.start, arg.end or len(golden), len(items)), flush=True)

    res = run_rule(items)
    label = "规则引擎 %d 条（下标 %d-%d，Rule D/E/F/G 全链）" % (
        len(items), arg.start, arg.end or len(golden))
    s = summarize(res, label)

    # 前 2000 条 vs day17 真机归档（F 基线）的确定性对照
    if arg.start == 0 and len(res) >= 2000:
        d17 = json.load(open(os.path.join(EV, "day17_results_2000.json"), encoding="utf-8"))
        old = {r["id"]: r["udkundoku_kakikudashi"] for r in d17["results"]}
        diff = []
        for r in res[:2000]:
            o = old.get(r["id"])
            if o is not None and r["udkundoku_kakikudashi"] is not None \
                    and norm(o) != norm(r["udkundoku_kakikudashi"]):
                diff.append(r["id"])
        print("\n=== 前 2000 条 vs day17 归档（Rule G 增量对照）===", flush=True)
        print("输出文本不同行数: %d（预期 = Rule G 改写 136 条）" % len(diff), flush=True)
        s["g_diff_rows_vs_day17"] = len(diff)

    out = os.path.join(EV, "night57_results_3000.json")
    json.dump({"total": len(res), "summary": s, "results": res},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
