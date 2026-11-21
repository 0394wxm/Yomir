# -*- coding: utf-8 -*-
"""night62_reservoir.py — N62：盘点「已在手、无需再抓」的未入库干净文本对。

背景：sitemap 盘点显示 kanbun.info 剩余文本对 ~3100 < 6000 目标。本脚本清点
历史上各次抓取留下的缓冲池/归档里，有多少**干净、且不在 golden_4000 白文集**
的对可以直接拿来用（零抓取成本）：

  * day10_new_entries / day16_pool / day16_scraped —— Day10/16 时代的目标截断剩余
  * night57_scraped_syubu / night60_scraped_left —— N57/N60 的目标截断剩余
  * golden_rongo_full（N32 論語全量 498 章）/ golden_rongo / golden.json /
    kanbun_parallel —— 独立口径的既有归档，量一下与 golden_4000 的白文重叠

只读。产物 eval/night62_reservoir.json + 控制台表。
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

FILES = [
    "day10_new_entries.json",
    "day16_pool.json",
    "day16_scraped.json",
    "night57_scraped_syubu.json",
    "night60_scraped_left.json",
    "golden_rongo_full.json",
    "golden_rongo.json",
    "golden.json",
    "kanbun_parallel.json",
]

LIST_KEYS = ("results", "entries", "pairs", "data", "chapters", "rows", "items", "list")
HB_KEYS = ("hakubun", "genbun", "source_text", "kanbun", "hb")
EXP_KEYS = ("expected_kakikudashi", "kakikudashi", "yomi", "expected", "kundoku")


def entries_of(doc):
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict):
        for k in LIST_KEYS:
            v = doc.get(k)
            if isinstance(v, list):
                return v
    return []


def pick(e, keys):
    if not isinstance(e, dict):
        return ""
    for k in keys:
        v = e.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def bucket_of(hb):
    n = len(re.sub(r"\s+", "", hb))
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def genre_of(url):
    u = (url or "").lower()
    if "/syubu/shikyo" in u:
        return "詩経"
    if "/syubu/" in u or "/syubu02/" in u:
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


def main():
    g4 = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    g4_hb = {x["hakubun"].strip() for x in g4}
    print("golden_4000: %d 条 / 白文唯一 %d" % (len(g4), len(g4_hb)))

    rows = []
    reservoir = {}   # hb -> entry（首个来源优先）
    for fn in FILES:
        p = os.path.join(EV, fn)
        if not os.path.exists(p):
            rows.append({"file": fn, "missing": True})
            print("%-28s 缺失" % fn)
            continue
        try:
            doc = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            rows.append({"file": fn, "parse_error": repr(e)})
            print("%-28s 解析失败 %r" % (fn, e))
            continue
        es = entries_of(doc)
        n = len(es)
        clean, ok_new, paren_new, exp_missing = 0, 0, 0, 0
        for e in es:
            hb, exp = pick(e, HB_KEYS).strip(), pick(e, EXP_KEYS).strip()
            if not hb or not exp:
                exp_missing += 1
                continue
            paren = "（" in hb or "）" in hb
            if not paren:
                clean += 1
            if hb in g4_hb:
                continue
            if paren:
                paren_new += 1
            else:
                ok_new += 1
                if hb not in reservoir:
                    e2 = dict(e)
                    e2["_pool"] = fn
                    reservoir[hb] = e2
        rows.append({"file": fn, "n": n, "clean": clean, "ok_new_vs_g4": ok_new,
                     "paren_new_vs_g4": paren_new, "no_expected": exp_missing,
                     "keys_sample": sorted(es[0].keys())[:10] if es and isinstance(es[0], dict) else []})
        print("%-28s n=%5d 干净 %5d | vs g4 新 ok %5d paren %4d | 无expected %3d"
              % (fn, n, clean, ok_new, paren_new, exp_missing))

    uniq = list(reservoir.items())
    b = Counter(bucket_of(hb) for hb, _ in uniq)
    g = Counter(genre_of(e.get("source_url", "")) for _, e in uniq)
    by_pool = Counter(e.get("_pool", "?") for _, e in uniq)
    print("\n=== 在手未用干净对（去重后唯一白文） ===")
    print("合计唯一 %d 条" % len(uniq))
    print("分档:", dict(b))
    print("文体:", dict(g))
    print("来源池:", dict(by_pool))
    out = {"golden4000_uniq_hb": len(g4_hb), "files": rows,
           "reservoir_unique": len(uniq),
           "by_bucket": dict(b), "by_genre": dict(g), "by_pool": dict(by_pool)}
    json.dump(out, open(os.path.join(EV, "night62_reservoir.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written: eval/night62_reservoir.json")


if __name__ == "__main__":
    main()
