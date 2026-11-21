# -*- coding: utf-8 -*-
"""night68_eval_8165.py — N68：规则引擎全跑 golden_<N>（Rule J 上线后全量）。

night67_eval_8165.py 同款机制（TestClient 完整后端链，monkeypatch save_kundoku，
D/E/F/G/H/I/J 全链 + SHINJITAI 275 对）。确定性对照（单基准，双向断言）：
  * 全库 vs night67_results_8165.json —— 既有可解析行的输出 diff 行集合 ==
    离线组合模拟（night68_combo_changed_rows.json，configB 若先）预测改写集合 283 行，
    逐 id 双向断言（多一行/少一行都算 FAIL）；error→恢复 / 仍 error 预期 0；
  * 每个改写行 new_dist ≤ old_dist（变差 0 = 模拟门硬规则在真机复现）；
  * ⑯ 偏科分档：shibu02 长句段与漢詩短句段（漢詩文体 × ≤20字档）的改善数分开报。
用法：python tools/night68_eval_8165.py [--golden golden_8165.json]
默认自动挑 eval/ 下编号最大的 golden_<n>.json（n>4000）。
输出 eval/night68_results_<N>.json。
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


def _bias(res, old_map, diff_ids):
    """⑯ 偏科分档：diff 行按 shibu02 长句段 / 漢詩短句段 分开统计改善。"""
    segs = {"shibu02": [], "kanshi_short": [], "other": []}
    for r in res:
        if r["id"] not in diff_ids:
            continue
        if "kanbun.info/shibu02/" in (r.get("source_url") or "").lower():
            segs["shibu02"].append(r)
        elif genre_of(r.get("source_url", "")) == "漢詩" and bucket_of(r["hakubun"]) == "≤20字":
            segs["kanshi_short"].append(r)
        else:
            segs["other"].append(r)
    stats = {}
    for k, rs in segs.items():
        imp = sum(1 for r in rs
                  if r["edit_distance"] < old_map[r["id"]]["edit_distance"])
        wor = sum(1 for r in rs
                  if r["edit_distance"] > old_map[r["id"]]["edit_distance"])
        same = len(rs) - imp - wor
        stats[k] = {"n": len(rs), "improved": imp, "worsened": wor, "same": same}
        print("⑯ %-13s 改写 %3d | 改善 %3d / 变差 %d / 持平 %d"
              % (k, len(rs), imp, wor, same), flush=True)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=None)
    arg = ap.parse_args()

    fn = arg.golden or pick_golden()
    golden = json.load(open(os.path.join(EV, fn), encoding="utf-8"))
    print("%s: %d 条（Rule J 上线后全量，SHINJITAI 275 对在场）" % (fn, len(golden)), flush=True)

    res = run_rule(golden)
    s = summarize(res, "规则引擎 %d 条（%s，D/E/F/G/H/I/J 全链 + SHINJITAI 275 对）"
                  % (len(res), fn))
    n_total = len(golden)

    # 确定性对照 vs night67_results_8165.json（单基准，双向断言）
    n67 = json.load(open(os.path.join(EV, "night67_results_8165.json"), encoding="utf-8"))["results"]
    old = {r["id"]: r for r in n67}
    combo = json.load(open(os.path.join(EV, "night68_combo_changed_rows.json"), encoding="utf-8"))
    pred = {r["id"] for r in combo if r["id"] in {g["id"] for g in golden}}

    diff_ids = set()
    better, worse = [], []
    fixed, still_err = [], []
    for r in res:
        o = old.get(r["id"])
        if r["udkundoku_kakikudashi"] is None:
            still_err.append(r["id"])
            continue
        if o is not None and o.get("udkundoku_kakikudashi") is None:
            fixed.append(r["id"])
        elif o is not None and norm(o["udkundoku_kakikudashi"]) != norm(r["udkundoku_kakikudashi"]):
            diff_ids.add(r["id"])
            if r["edit_distance"] > o["edit_distance"]:
                worse.append((r["id"], o["edit_distance"], r["edit_distance"]))
            elif r["edit_distance"] < o["edit_distance"]:
                better.append(r["id"])
    same = sorted(diff_ids - set(better) - {w[0] for w in worse})
    print("\n=== 确定性对照 vs night67_results_8165.json ===", flush=True)
    print("改写行: %d（模拟预测 %d）| 改善 %d / 变差 %d / 持平 %d"
          % (len(diff_ids), len(pred), len(better), len(worse), len(same)), flush=True)
    miss = sorted(pred - diff_ids)
    extra = sorted(diff_ids - pred)
    print("预测有实跑无: %d %s" % (len(miss), miss[:10]), flush=True)
    print("实跑有预测无: %d %s" % (len(extra), extra[:10]), flush=True)
    print("error→恢复: %d | 仍 error: %d %s（预期 0）" % (len(fixed), len(still_err), still_err), flush=True)
    for i, od, nd in worse[:20]:
        print("  变差! %s %d→%d" % (i, od, nd), flush=True)
    s["check_n67"] = {"ref": "night67_results_8165.json", "diff_ids": sorted(diff_ids),
                      "predicted_ids": sorted(pred), "missing_vs_pred": miss,
                      "extra_vs_pred": extra, "improved": len(better),
                      "worsened": len(worse), "worsened_detail": worse,
                      "fixed": sorted(fixed), "still_error": still_err}
    s["bias_segments"] = _bias(res, old, diff_ids)
    s["errors_detail"] = [r["id"] for r in res if r.get("udkundoku_kakikudashi") is None]

    out = os.path.join(EV, "night68_results_%d.json" % n_total)
    json.dump({"golden": fn, "total": len(res), "summary": s, "results": res},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
