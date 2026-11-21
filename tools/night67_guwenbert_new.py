# -*- coding: utf-8 -*-
"""night67_guwenbert_new.py — N67⑲：guwenbert 只跑 golden_<N> ⑲ 新增段（离线）。

night62_guwenbert_new.py 同款机制（tools/run_eval_guwenbert.py，HF_HUB_OFFLINE=1），
offset 默认 7908（⑲ paren 新增段）。与 backend/main.py ⑬ 同款 AUX runtime 补丁在
本进程同样生效（guwenbert 路径与规则路径共享 kundoku 翻译层，N62 §5 已实证同行同败），
保证两路同口径。输出 eval/night67_guwenbert_new<N>.json。

用法：python tools/night67_guwenbert_new.py [--limit N] [--offset 7908] [--golden xxx.json]
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=7908)
    ap.add_argument("--golden", default=None)
    arg = ap.parse_args()

    fn = arg.golden or pick_golden()
    golden = json.load(open(os.path.join(EV, fn), encoding="utf-8"))
    items = golden[arg.offset:]
    if arg.limit:
        items = items[:arg.limit]
    print("%s ⑲新增段 [%d:] 共 %d 条" % (fn, arg.offset, len(items)), flush=True)

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import run_eval_guwenbert as rg

    # N67⑬: 与 backend/main.py 同款 AUX runtime 补丁（guwenbert 路径共享 kundoku 翻译层）
    import udkundoku.auxiliary as _aux_mod  # noqa: E402
    _aux_mod.AUX["應,v,助動詞,必要,*"] = _aux_mod.AUX["須,v,助動詞,必要,*"]
    print("⑬ AUX runtime 补丁在场：應,v,助動詞,必要,*", flush=True)

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
                  % (i, len(items),
                     sum(r["edit_distance"] for r in done) / len(done) if done else -1,
                     time.time() - t0), flush=True)

    ok = [r for r in results if r["edit_distance"] is not None]
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / len(ok) if ok else None
    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    by_s = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
        by_s[section_of(r.get("source_url", ""))].append(r)
    summary = {
        "label": "guwenbert ⑲新增段 %d 条" % len(ok),
        "n": len(ok), "errors": len(results) - len(ok), "exact": exact,
        "avg_edit_distance": round(avg, 3) if avg else None,
        "by_bucket": {b: {"n": len(rs),
                          "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                          "exact": sum(1 for x in rs if x["exact_match"])}
                      for b, rs in by_b.items()},
        "by_genre": {g: {"n": len(rs),
                         "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                         "exact": sum(1 for x in rs if x["exact_match"])}
                     for g, rs in by_g.items()},
        "by_section": {g: {"n": len(rs),
                           "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                           "exact": sum(1 for x in rs if x["exact_match"])}
                       for g, rs in by_s.items()},
    }
    print("\n=== guwenbert ⑲新增 %d 条 ===" % len(ok), flush=True)
    print("OK %d / error %d | 精确 %d | avgDist %.3f"
          % (len(ok), len(results) - len(ok), exact, avg if avg else -1), flush=True)
    for b in ["≤20字", "21-40字", "41-60字", ">60字"]:
        d = summary["by_bucket"].get(b)
        if d:
            print("  %-8s n=%4d avg %6.2f exact %d" % (b, d["n"], d["avg"], d["exact"]),
                  flush=True)
    for g, d in summary["by_genre"].items():
        print("  %-6s n=%4d avg %6.2f exact %d" % (g, d["n"], d["avg"], d["exact"]),
              flush=True)

    n_total = len(golden)
    out = os.path.join(EV, "night67_guwenbert_new%d.json" % (n_total - arg.offset))
    json.dump({"golden": fn, "offset": arg.offset, "total": len(results),
               "summary": summary, "results": results},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
