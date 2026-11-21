# -*- coding: utf-8 -*-
"""night62_eval_10k.py — N62：规则引擎全跑 golden_<N>（方案A全量）。

night60_eval_4000.py 同款机制（TestClient 完整后端链，monkeypatch save_kundoku，
D/E/F/G/H 全链 + SHINJITAI）。确定性对照：前 4000 条输出 vs night60 归档应逐行
一致（引擎确定性 + 规则未变 → diff=0）；新增段 = golden[4000:]。
breakdown：长度档 × 文体（沿用历史 genre_of 口径保证可比）+ 栏目（URL 路径段）
补充表（shibu02 等新栏目在历史文体口径下归「その他」，栏目表如实分开记）。

用法：python tools/night62_eval_10k.py [--golden golden_7430.json]
默认自动挑 eval/ 下编号最大的 golden_<n>.json（n>4000）。
输出 eval/night62_results_<N>.json + night62_eval.txt。
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


def section_of(url):
    m = re.search(r"kanbun\.info/([a-z0-9_]+)/", (url or "").lower())
    return m.group(1) if m else "?"


def pick_golden():
    best = None
    for fn in os.listdir(EV):
        m = re.fullmatch(r"golden_(\d+)\.json", fn)
        if m and int(m.group(1)) > 4000:
            n = int(m.group(1))
            if best is None or n > best[0]:
                best = (n, fn)
    if not best:
        raise SystemExit("eval/ 下没有 n>4000 的 golden_<n>.json，先跑 night62_build_golden.py")
    return best[1]


def table(rows, keyfn, keys_order=None):
    by = collections.defaultdict(list)
    for r in rows:
        by[keyfn(r)].append(r)
    return by, keys_order


def summarize(results, label):
    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n if n else None
    print("\n=== %s ===" % label, flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f"
          % (n, len(results) - n, exact, n, avg if avg is not None else -1), flush=True)
    buckets = ["≤20字", "21-40字", "41-60字", ">60字"]
    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    by_s = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
        by_s[section_of(r.get("source_url", ""))].append(r)
    print("\n%-10s %5s %9s %7s" % ("分档", "n", "avgDist", "精确"), flush=True)
    for b in buckets:
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
    grid = {}
    for g in sorted(by_g, key=lambda k: -len(by_g[k])):
        cells = []
        for b in buckets:
            rs = [x for x in by_g[g] if bucket_of(x["hakubun"]) == b]
            cells.append("%.2f(%d)" % (sum(x["edit_distance"] for x in rs) / len(rs), len(rs))
                         if rs else "-")
            if rs:
                grid["%s|%s" % (g, b)] = {
                    "n": len(rs),
                    "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                    "exact": sum(1 for x in rs if x["exact_match"])}
        print("%-8s %-14s %-14s %-14s %-14s" % (g, *cells), flush=True)
    print("\n栏目补充表（历史文体口径下 shibu02 等归「その他」）：", flush=True)
    for s, rs in sorted(by_s.items(), key=lambda kv: -len(kv[1])):
        print("  %-14s %5d %9.3f %7d"
              % (s, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                 sum(1 for x in rs if x["exact_match"])), flush=True)
    return {
        "label": label, "n": n, "errors": len(results) - n, "exact": exact,
        "avg_edit_distance": round(avg, 3) if avg is not None else None,
        "by_bucket": {b: {"n": len(by_b[b]),
                          "avg": round(sum(x["edit_distance"] for x in by_b[b]) / len(by_b[b]), 3),
                          "exact": sum(1 for x in by_b[b] if x["exact_match"])}
                      for b in buckets if by_b.get(b)},
        "by_genre": {g: {"n": len(rs),
                         "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                         "exact": sum(1 for x in rs if x["exact_match"])}
                     for g, rs in by_g.items()},
        "by_section": {s: {"n": len(rs),
                           "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                           "exact": sum(1 for x in rs if x["exact_match"])}
                       for s, rs in by_s.items()},
        "grid_genre_bucket": grid,
    }


def run_rule(items):
    import logging
    logging.getLogger("httpx2").setLevel(logging.WARNING)
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
                if i % 500 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(items), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    arg = ap.parse_args()

    fn = arg.golden or pick_golden()
    golden = json.load(open(os.path.join(EV, fn), encoding="utf-8"))
    items = golden[arg.start:arg.end or None]
    print("%s: %d 条，本次跑 [%d:%d) 共 %d 条"
          % (fn, len(golden), arg.start, arg.end or len(golden), len(items)), flush=True)

    res = run_rule(items)
    s = summarize(res, "规则引擎 %d 条（%s [0:%d)，D/E/F/G/H 全链 + SHINJITAI）"
                  % (len(res), fn, len(golden)))

    # 确定性对照：前 4000 条 vs night60 归档（引擎/规则未变 → 应逐行一致）
    if arg.start == 0 and len(res) >= 4000:
        n60 = json.load(open(os.path.join(EV, "night60_results_4000.json"),
                             encoding="utf-8"))["results"]
        old = {r["id"]: r.get("udkundoku_kakikudashi") for r in n60}
        diff = []
        for r in res[:4000]:
            o = old.get(r["id"])
            if o is not None and r["udkundoku_kakikudashi"] is not None \
                    and norm(o) != norm(r["udkundoku_kakikudashi"]):
                diff.append(r["id"])
        missing = [r["id"] for r in res[:4000] if r["id"] not in old]
        print("\n=== 确定性对照 ===", flush=True)
        print("前 4000 条 vs night60 归档 输出文本不同行数: %d（预期 0）；归档缺行 %d"
              % (len(diff), len(missing)), flush=True)
        s["diff_rows_vs_n60"] = len(diff)
        s["missing_in_n60"] = missing

        # 新增段（4000+）单独摘要
        new_res = res[4000:]
        s_new = summarize(new_res, "新增段（[%d:%d)，%d 条）"
                          % (4000, len(golden), len(new_res)))
        s["new_segment"] = s_new
        new_err = [(r["id"], r.get("error")) for r in new_res
                   if r.get("udkundoku_kakikudashi") is None]
        print("新增段 error 行: %d %s" % (len(new_err), [e[0] for e in new_err][:20]),
              flush=True)
        s["new_segment_errors"] = [e[0] for e in new_err]

    n_total = len(golden)
    out = os.path.join(EV, "night62_results_%d.json" % n_total)
    json.dump({"golden": fn, "total": len(res), "summary": s, "results": res},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
