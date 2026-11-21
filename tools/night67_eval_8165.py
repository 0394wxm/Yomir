# -*- coding: utf-8 -*-
"""night67_eval_8165.py — N67⑲：规则引擎全跑 golden_<N>（⑲ paren 启用后全量）。

night62_eval_10k.py 同款机制（TestClient 完整后端链，monkeypatch save_kundoku，
D/E/F/G/H/I 全链 + SHINJITAI + ⑬ AUX 應补丁）。确定性对照（双前缀）：
  * [0:4000)  vs night64_results_4000.json —— 既有可解析行应逐行一致（diff=0），
    error→恢复 恰好 toushisen135-12 / toushisen043-16 两行；
  * [0:7908)  vs night62_results_7908.json —— 同上，error→恢复 恰好 +zasshi-2 共 3 行；
新增段 = golden[7908:]（⑲ paren 257 对），单独摘要。
用法：python tools/night67_eval_8165.py [--golden golden_8165.json]
默认自动挑 eval/ 下编号最大的 golden_<n>.json（n>4000）。
输出 eval/night67_results_<N>.json。
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
        raise SystemExit("eval/ 下没有 n>4000 的 golden_<n>.json，先跑 night67_build_golden.py")
    return best[1]


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
    print("\n栏目补充表：", flush=True)
    for s_, rs in sorted(by_s.items(), key=lambda kv: -len(kv[1])):
        print("  %-14s %5d %9.3f %7d"
              % (s_, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
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
        "by_section": {s_: {"n": len(rs),
                            "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                            "exact": sum(1 for x in rs if x["exact_match"])}
                       for s_, rs in by_s.items()},
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
                if i % 500 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(items), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real
    return results


def _check_prefix(res, end, ref_fn, tag):
    ref = json.load(open(os.path.join(EV, ref_fn), encoding="utf-8"))["results"]
    old = {r["id"]: r for r in ref}
    diff_resolved, fixed, still_err = [], [], []
    for r in res[:end]:
        o = old.get(r["id"])
        if r["udkundoku_kakikudashi"] is None:
            still_err.append(r["id"])
            continue
        if o is not None and o.get("udkundoku_kakikudashi") is None:
            fixed.append(r["id"])
        elif o is not None and \
                norm(o["udkundoku_kakikudashi"]) != norm(r["udkundoku_kakikudashi"]):
            diff_resolved.append(r["id"])
    print("\n=== 确定性对照 [0:%d) vs %s ===" % (end, ref_fn), flush=True)
    print("既有可解析行 diff: %d（预期 0）| error→恢复: %d %s | 仍 error: %d"
          % (len(diff_resolved), len(fixed), sorted(fixed), len(still_err)), flush=True)
    return {"ref": ref_fn, "end": end, "diff_resolved": diff_resolved,
            "fixed": sorted(fixed), "still_error": still_err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=None)
    arg = ap.parse_args()

    fn = arg.golden or pick_golden()
    golden = json.load(open(os.path.join(EV, fn), encoding="utf-8"))
    print("%s: %d 条（⑲ paren 启用后全量，⑬ AUX 應补丁在场）"
          % (fn, len(golden)), flush=True)

    res = run_rule(golden)
    s = summarize(res, "规则引擎 %d 条（%s，D/E/F/G/H/I 全链 + SHINJITAI + ⑬ AUX 應补丁）"
                  % (len(res), fn))
    n_total = len(golden)

    s["check_n64"] = _check_prefix(res, 4000, "night64_results_4000.json", "n64")
    if n_total >= 7908:
        s["check_n62_7908"] = _check_prefix(res, 7908, "night62_results_7908.json", "n62")

    new_res = res[7908:]
    if new_res:
        s_new = summarize(new_res, "⑲ paren 新增段（[7908:%d)，%d 条）" % (n_total, len(new_res)))
        s["new_segment"] = s_new
        new_err = [(r["id"], (r.get("error") or "")[:120]) for r in new_res
                   if r.get("udkundoku_kakikudashi") is None]
        print("新增段 error 行: %d %s" % (len(new_err), [e[0] for e in new_err][:20]),
              flush=True)
        s["new_segment_errors"] = [e[0] for e in new_err]
    s["errors_detail"] = [r["id"] for r in res if r.get("udkundoku_kakikudashi") is None]

    out = os.path.join(EV, "night67_results_%d.json" % n_total)
    json.dump({"golden": fn, "total": len(res), "summary": s, "results": res},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
