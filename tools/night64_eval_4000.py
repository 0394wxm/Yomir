# -*- coding: utf-8 -*-
"""night64_eval_4000.py — N64：规则引擎全跑 4000 条（D/E/F/G/H/I 全链 + SHINJITAI 147+99 对）。

night60_eval_4000.py 同款机制（TestClient 完整后端链，monkeypatch save_kundoku）。
确定性对照：全 4000 条输出 vs night60 归档——Rule I/SHINJITAI 未触及的行应逐行一致，
触及行 = 离线模拟预测的改写行（night64_compare.py 逐位核对）。
输出 eval/night64_results_4000.json。
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
                if i % 250 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(items), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    arg = ap.parse_args()

    golden = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    items = golden[arg.start:arg.end or None]
    print("golden_4000: %d 条，本次跑 [%d:%d) 共 %d 条"
          % (len(golden), arg.start, arg.end or len(golden), len(items)), flush=True)

    res = run_rule(items)
    label = "规则引擎 %d 条（下标 %d-%d，D/E/F/G/H/I 全链 + SHINJITAI 147+99 对）" % (
        len(items), arg.start, arg.end or len(golden))
    s = summarize(res, label)

    # 确定性对照：全 4000 条 vs night60 归档——Rule I 未触及行应逐行一致，
    # 触及行数应与离线模拟的改写行数一致（逐位核对在 night64_compare.py）
    if arg.start == 0 and len(res) >= 4000:
        n60 = json.load(open(os.path.join(EV, "night60_results_4000.json"),
                             encoding="utf-8"))["results"]
        old = {r["id"]: r.get("udkundoku_kakikudashi") for r in n60}
        diff = []
        for r in res:
            o = old.get(r["id"])
            if o is not None and r["udkundoku_kakikudashi"] is not None \
                    and norm(o) != norm(r["udkundoku_kakikudashi"]):
                diff.append(r["id"])
        print("\n=== 确定性对照 ===", flush=True)
        print("全 4000 条 vs night60 归档 输出文本不同行数: %d（应 = 模拟改写 656）"
              % len(diff), flush=True)
        s["diff_rows_vs_n60"] = len(diff)
        s["changed_ids_sample"] = diff[:20]

        err = [(r["id"], (r.get("error") or "")[:60]) for r in res
               if r.get("udkundoku_kakikudashi") is None]
        print("error 行: %d %s" % (len(err), [e[0] for e in err]), flush=True)
        s["errors_detail"] = [e[0] for e in err]

    out = os.path.join(EV, "night64_results_4000.json")
    json.dump({"total": len(res), "summary": s, "results": res},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
