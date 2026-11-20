# -*- coding: utf-8 -*-
"""night56_analysis.py — N56：大学/孝経 avgDist 偏低的归因（分档 × 文体交叉 + 反事实分解）。

问题（D16 §3.3 遗留）：大学 14.926 / 孝経 9.442 vs 故事 21.780 —— 是短句占比高，
还是文体本身好读？

方法（不改任何生产代码，只读归档）：
  1. 复算 day17 真机归档的分档/文体表（口径与 day16_split_stats.py 完全一致）；
  2. 分档 × 文体交叉表（同档跨文体对比才是可信的，D16 §3.2 的教训）；
  3. **反事实分解**：把 大学/孝経 各行按所在分档套用「故事的同档均值」，
     得到「假如大学/孝経的难度 = 故事（按档）」的假设 avgDist。
     实际 avgDist 与假设 avgDist 的差 = 文体效应；假设值与故事整体均值的差
     里由档位分布解释的部分 = 构成效应。
输出 eval/night56_analysis.json + stdout。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

BUCKETS = ["≤20字", "21-40字", "41-60字", ">60字"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def bucket_of(hb):
    n = len(norm(hb))
    return BUCKETS[0] if n <= 20 else BUCKETS[1] if n <= 40 else BUCKETS[2] if n <= 60 else BUCKETS[3]


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
    golden = {r["id"]: r for r in json.load(open(os.path.join(EV, "golden_2000.json"),
                                                encoding="utf-8"))}
    doc = json.load(open(os.path.join(EV, "day17_results_2000.json"), encoding="utf-8"))
    rows = []
    for r in doc["results"]:
        if r.get("edit_distance") is None:
            continue
        g = golden[r["id"]]
        rows.append({
            "id": r["id"], "dist": r["edit_distance"],
            "bucket": bucket_of(g["hakubun"]), "genre": genre_of(g.get("source_url", "")),
            "exact": bool(r.get("exact_match")),
        })
    n = len(rows)
    total = sum(r["dist"] for r in rows)
    print("样本 %d 条（day17 真机，Rule F）| avgDist %.3f | 精确 %d"
          % (n, total / n, sum(r["exact"] for r in rows)), flush=True)

    # 1. 复算 D17 §7.2 的分文体（应与 REPORT_DAY17 §7.2 一致）
    print("\n=== 1. 分文体复算（对照 REPORT_DAY17 §7.2）===", flush=True)
    by_g = collections.defaultdict(list)
    for r in rows:
        by_g[r["genre"]].append(r)
    genre_avg = {}
    for g, rs in sorted(by_g.items(), key=lambda kv: -len(kv[1])):
        a = sum(r["dist"] for r in rs) / len(rs)
        genre_avg[g] = a
        print("  %-6s n=%4d avgDist %8.3f 精确 %d"
              % (g, len(rs), a, sum(r["exact"] for r in rs)), flush=True)

    # 2. 分档 × 文体交叉表
    print("\n=== 2. 分档 × 文体 avgDist（同档跨文体对比）===", flush=True)
    cell = collections.defaultdict(list)
    for r in rows:
        cell[(r["bucket"], r["genre"])].append(r)
    print("  %-9s" % "分档" + "".join("%12s" % g for g in ["故事", "論語", "大学", "孝経"]),
          flush=True)
    cross = {}
    for b in BUCKETS:
        line = "  %-9s" % b
        for g in ["故事", "論語", "大学", "孝経"]:
            rs = cell.get((b, g), [])
            if rs:
                a = sum(r["dist"] for r in rs) / len(rs)
                cross[(b, g)] = {"n": len(rs), "avg": round(a, 3)}
                line += "%12s" % ("%.3f(%d)" % (a, len(rs)))
            else:
                cross[(b, g)] = {"n": 0, "avg": None}
                line += "%12s" % "-"
        print(line, flush=True)
    # 各文体档位构成
    print("\n  各文体档位构成（行内 %）:", flush=True)
    for g in ["故事", "論語", "大学", "孝経"]:
        rs = by_g[g]
        c = collections.Counter(r["bucket"] for r in rs)
        print("    %-6s n=%4d | " % (g, len(rs)) +
              " ".join("%s %d(%0.0f%%)" % (b, c.get(b, 0), 100.0 * c.get(b, 0) / len(rs))
                       for b in BUCKETS), flush=True)

    # 3. 反事实分解
    print("\n=== 3. 反事实分解（构成效应 vs 文体效应）===", flush=True)
    story_by_bucket = {b: cross[(b, "故事")]["avg"] for b in BUCKETS
                       if cross[(b, "故事")]["n"] >= 20}
    print("  故事同档均值（n≥20 才做基准）:", {b: story_by_bucket[b] for b in story_by_bucket},
          flush=True)
    decomp = {}
    for g in ["大学", "孝経", "論語"]:
        rs = by_g[g]
        actual = genre_avg[g]
        # 反事实：每行换成所在档的故事均值
        used = [r for r in rs if r["bucket"] in story_by_bucket]
        cf = sum(story_by_bucket[r["bucket"]] for r in used) / len(used)
        # 文体效应 = 实际 - 反事实（负 = 比故事同档更容易）
        genre_effect = actual - cf
        # 构成效应 = 反事实 - 故事整体
        comp_effect = cf - genre_avg["故事"]
        decomp[g] = {"actual": round(actual, 3), "counterfactual_as_story": round(cf, 3),
                     "genre_effect": round(genre_effect, 3),
                     "composition_effect_vs_story": round(comp_effect, 3),
                     "n_used": len(used), "n_total": len(rs)}
        print("  %-4s 实际 %7.3f | 若按故事同档 %7.3f | 文体效应 %+7.3f | 构成效应 %+7.3f (n=%d)"
              % (g, actual, cf, genre_effect, comp_effect, len(used)), flush=True)

    # 4. 孝経/大学 短句占比 + 极短句精确
    print("\n=== 4. 精确命中的长度分布 ===", flush=True)
    for r in rows:
        if r["exact"]:
            print("  %-22s %-4s %s" % (r["id"], r["genre"], r["bucket"]), flush=True)

    out = {
        "n": n, "avg": round(total / n, 3),
        "genre_avg": {g: round(v, 3) for g, v in genre_avg.items()},
        "cross": {"%s|%s" % k: v for k, v in cross.items()},
        "decomposition": decomp,
    }
    json.dump(out, open(os.path.join(EV, "night56_analysis.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/night56_analysis.json", flush=True)


if __name__ == "__main__":
    main()
