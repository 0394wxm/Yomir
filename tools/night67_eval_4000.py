# -*- coding: utf-8 -*-
"""night67_eval_4000.py — N67⑬：golden_4000 全量重跑（D/E/F/G/H/I 全链 + SHINJITAI 246 对
+ ⑬ AUX「應,v,助動詞,必要,*」runtime 补丁）。

night64_eval_4000.py 同款机制（TestClient 完整后端链，monkeypatch save_kundoku）。
确定性对照 vs night64_results_4000.json：
  * 补丁前已可解析的 3998 行：输出应逐行一致（diff=0，补丁不搅动任何既有行）；
  * 补丁前 error 的 2 行（toushisen135-12 / toushisen043-16）：应恢复出訓読（error 2→0），
    且不得新增其他 error。
输出 eval/night67_results_4000.json（schema 与 night64_results_4000.json 相同）。
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

N64_FIX_EXPECT = ["toushisen043-16", "toushisen135-12"]  # sorted


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
    golden = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    print("golden_4000: %d 条（⑬ AUX 應补丁后全量重跑）" % len(golden), flush=True)

    res = run_rule(golden)
    s = summarize(res, "规则引擎 4000 条（D/E/F/G/H/I 全链 + SHINJITAI 246 对 + ⑬ AUX 應补丁）")

    # 确定性对照 vs night64_results_4000.json
    n64 = json.load(open(os.path.join(EV, "night64_results_4000.json"),
                         encoding="utf-8"))["results"]
    old = {r["id"]: r for r in n64}
    diff_resolved = []   # 双方都有输出但文本不同（预期 0）
    fixed = []           # n64 error → n67 有输出（预期恰好 2 行）
    still_err = []       # n67 仍 error（预期 0）
    for r in res:
        o = old.get(r["id"])
        if r["udkundoku_kakikudashi"] is None:
            still_err.append(r["id"])
            continue
        if o is not None and o.get("udkundoku_kakikudashi") is None:
            fixed.append(r["id"])
        elif o is not None and \
                norm(o["udkundoku_kakikudashi"]) != norm(r["udkundoku_kakikudashi"]):
            diff_resolved.append(r["id"])
    print("\n=== 确定性对照 vs night64_results_4000.json ===", flush=True)
    print("既有可解析行输出文本不同行数: %d（预期 0）" % len(diff_resolved), flush=True)
    print("error→恢复 行: %d %s" % (len(fixed), sorted(fixed)), flush=True)
    print("本跑仍 error 行: %d %s（预期 0）" % (len(still_err), still_err), flush=True)
    s["diff_rows_vs_n64_resolved"] = diff_resolved
    s["fixed_rows_vs_n64"] = sorted(fixed)
    s["still_error"] = still_err
    s["errors_detail"] = still_err
    for r in res:
        if r["id"] in fixed:
            print("  %-18s dist=%d exact=%s | exp=%r" % (
                r["id"], r["edit_distance"], r["exact_match"],
                r["expected_kakikudashi"]), flush=True)
            print("      got=%r" % r["udkundoku_kakikudashi"], flush=True)

    out = os.path.join(EV, "night67_results_4000.json")
    json.dump({"total": len(res), "summary": s, "results": res},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
