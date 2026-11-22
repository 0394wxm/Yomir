# -*- coding: utf-8 -*-
"""night78_kokyo.py — kokyo09-5 死行前缀归属＋空 got 行计数＋现代副词小族计数。只读。"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EV = r"D:\kanbun-rulel\eval"

p = json.load(open(EV + r"\night78_probe.json", encoding="utf-8"))
recs = p["kotonna"]["records"]
out = []
for r in recs:
    if r["id"] in ("kokyo09-5", "kowokaete-4"):
        out.append("%s runs=%s guard=%s" % (r["id"], r["got_runs"], r["guard"]))
        out.append("  got: " + r["got"])
        out.append("  exp: " + r["exp"])
        out.append("  hb : " + r["hb"])

doc = json.load(open(EV + r"\night73_results_8165.json", encoding="utf-8"))
empty = [x["id"] for x in doc["results"] if x.get("udkundoku_kakikudashi") == ""]
out.append("empty-got rows: %d %s" % (len(empty), ", ".join(empty[:20])))
rows = [x for x in doc["results"] if x.get("udkundoku_kakikudashi") is not None]


def cnt(w):
    g = sum(1 for x in rows if w in re.sub(r"\s+", "", x["udkundoku_kakikudashi"]))
    e = sum(1 for x in rows if w in re.sub(r"\s+", "", x["expected_kakikudashi"]))
    return "got %d exp %d" % (g, e)


for w in ["しばしば", "屢", "ほとんど", "殆", "はいよいよ", "いよいよ", "弥", "やや",
          "稍", "たま", "偶", "なんぞ", "胡", "することなかれ", "すことなかれ",
          "うことなかれ", "なることなかれ", "きことなかれ", "ることなかれ", "ことなかれ",
          "なら", "こそ", "ともあれ"]:
    out.append("%s: %s" % (w, cnt(w)))

open(EV + r"\_n78_kokyo.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("written eval/_n78_kokyo.txt")
