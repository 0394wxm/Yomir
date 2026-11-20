# -*- coding: utf-8 -*-
"""night57_compare.py — N57 统计补充：旧2000(post-G) vs day17(F) vs 新增1000。"""
import collections
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def bucket_of(hb):
    n = len(norm(hb))
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


d17 = json.load(io.open(r"D:\kanbun-kakikudashi\eval\day17_results_2000.json", encoding="utf-8"))
r3k = json.load(io.open(r"D:\kanbun-kakikudashi\eval\night57_results_3000.json", encoding="utf-8"))
rows = r3k["results"]
old = [r for r in rows[:2000] if r["edit_distance"] is not None]
new = [r for r in rows[2000:] if r["edit_distance"] is not None]

d17_map = {r["id"]: r["edit_distance"] for r in d17["results"]}
old_avg = sum(r["edit_distance"] for r in old) / len(old)
new_avg = sum(r["edit_distance"] for r in new) / len(new)
d17_avg = sum(v for v in d17_map.values()) / len(d17_map)
print("前2000(post-G) avgDist %.3f | day17(F) %.3f | Δ(G) %+.3f"
      % (old_avg, d17_avg, old_avg - d17_avg))
print("新增1000      avgDist %.3f" % new_avg)

# 分档 × {前2000, 新增1000}
for label, rs in (("前2000", old), ("新增1000", new)):
    c = collections.defaultdict(list)
    for r in rs:
        c[bucket_of(r["hakubun"])].append(r["edit_distance"])
    print("%s 分档: " % label + "  ".join(
        "%s %.3f(%d)" % (b, sum(v) / len(v), len(v)) for b, v in
        (("≤20字", c["≤20字"]), ("21-40字", c["21-40字"]),
         ("41-60字", c["41-60字"]), (">60字", c[">60字"])) if v))

# 新增段的来源拆分
src = collections.defaultdict(list)
for r in new:
    u = (r.get("source_url") or "").lower()
    if "/syubu/shikyo" in u:
        src["詩経"].append(r["edit_distance"])
    elif "/syubu/" in u:
        src["漢詩"].append(r["edit_distance"])
    else:
        src["平行剩余(故事)"].append(r["edit_distance"])
for k, v in src.items():
    print("新增 %s n=%d avgDist %.3f" % (k, len(v), sum(v) / len(v)))

# 前2000 逐条 G 效应分布
diff_up = sum(1 for r in old if r["id"] in d17_map and r["edit_distance"] < d17_map[r["id"]])
diff_dn = sum(1 for r in old if r["id"] in d17_map and r["edit_distance"] > d17_map[r["id"]])
print("前2000 里 G 使 %d 条改善 / %d 条变差 / %d 条持平（vs day17）"
      % (diff_up, diff_dn, len(old) - diff_up - diff_dn))
