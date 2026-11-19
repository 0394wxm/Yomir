# -*- coding: utf-8 -*-
"""day16_build_golden_2000.py — D16：在 golden_1000 基础上扩到 2000 条。

约束（任务书）：
  * expected 一字不改：全部来自 kanbun.info 页面的 <div class="yomi02|yomi03"> 原文，
    脚本只做「剥 ruby/标签 + 去空白」，不做任何替换。
  * 去重：新增部分按 hakubun（空白归一）与 golden_1000 已有白文去重；
    新增内部也去重。golden_1000 自身的 25 条内部重复原样保留（D10 遗留，不动）。
  * golden_1000 前 1000 条**原样字节保留**在 2000 条前部。

来源优先级（先平行语料=任务书点名，再新栏目大学/孝経，最后截断补抓）：
  1. parallel        — eval/kanbun_parallel.json 中不在 golden_1000 的白文
  2. classics        — 大学 daigaku* + 孝経 kokyo*（D16 新抓）
  3. parallel_extra  — 平行语料被「每页 10 对」上限截断的页面剩余对（D16 补抓）

产物：eval/golden_2000.json + eval/golden_2000_stats.json
"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
SRC_ORDER = ["parallel", "classics", "parallel_extra"]
TARGET_NEW = 1000


def load(n):
    with open(os.path.join(EV, n), encoding="utf-8") as f:
        return json.load(f)


def genre_of(url):
    u = (url or "").lower()
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


def bucket_of(hb):
    n = len(hb)
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def main():
    base = load("golden_1000.json")
    pool = load("day16_pool.json")
    pool.sort(key=lambda r: (SRC_ORDER.index(r["_src"]) if r["_src"] in SRC_ORDER else 99,
                             r["id"]))

    seen_hb = {x["hakubun"].strip() for x in base}
    seen_id = {x["id"] for x in base}
    new = []
    skipped = collections.Counter()
    for r in pool:
        if len(new) >= TARGET_NEW:
            break
        hb = r["hakubun"].strip()
        exp = (r.get("expected_kakikudashi") or "").strip()
        if not hb or not exp:
            skipped["empty"] += 1
            continue
        if hb in seen_hb:
            skipped["dup_hakubun"] += 1
            continue
        rid = r["id"]
        if rid in seen_id:
            skipped["dup_id"] += 1
            continue
        seen_hb.add(hb)
        seen_id.add(rid)
        new.append({"id": rid, "source_url": r["source_url"],
                    "hakubun": hb, "expected_kakikudashi": exp})

    print("base %d | pool %d | picked %d | skipped %s"
          % (len(base), len(pool), len(new), dict(skipped)), flush=True)
    if len(new) < TARGET_NEW:
        print("!! 不足 %d（实得 %d）—— 如实记录，不补重复条目" % (TARGET_NEW, len(new)),
              flush=True)

    combined = [{"id": x["id"], "source_url": x.get("source_url", ""),
                 "hakubun": x["hakubun"],
                 "expected_kakikudashi": x["expected_kakikudashi"]} for x in base] + new

    out = os.path.join(EV, "golden_2000.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    b = collections.Counter(bucket_of(x["hakubun"]) for x in combined)
    g = collections.Counter(genre_of(x["source_url"]) for x in combined)
    cross = collections.Counter("%s|%s" % (genre_of(x["source_url"]), bucket_of(x["hakubun"]))
                                for x in combined)
    nb = collections.Counter(bucket_of(x["hakubun"]) for x in new)
    ng = collections.Counter(genre_of(x["source_url"]) for x in new)
    ncross = collections.Counter("%s|%s" % (genre_of(x["source_url"]), bucket_of(x["hakubun"]))
                                 for x in new)
    stats = {
        "total": len(combined), "base": len(base), "new": len(new),
        "uniq_ids": len({x["id"] for x in combined}),
        "uniq_hakubun": len({x["hakubun"] for x in combined}),
        "by_bucket": dict(b), "by_genre": dict(g), "cross": dict(cross),
        "new_by_bucket": dict(nb), "new_by_genre": dict(ng), "new_cross": dict(ncross),
        "new_by_src": dict(collections.Counter(r["_src"] for r in pool[:0])) or {},
        "base_internal_dups": len(base) - len({x["hakubun"] for x in base}),
        "skipped": dict(skipped),
    }
    # 实际入库的来源分布
    src_of_id = {r["id"]: r["_src"] for r in pool}
    stats["new_by_src"] = dict(collections.Counter(src_of_id[x["id"]] for x in new))
    with open(os.path.join(EV, "golden_2000_stats.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\n=== golden_2000 ===", flush=True)
    print("total %d | uniq ids %d | uniq hakubun %d"
          % (stats["total"], stats["uniq_ids"], stats["uniq_hakubun"]), flush=True)
    print("分档:", dict(b), flush=True)
    print("文体:", dict(g), flush=True)
    print("新增来源:", stats["new_by_src"], flush=True)
    print("新增分档:", dict(nb), flush=True)
    print("新增文体:", dict(ng), flush=True)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
