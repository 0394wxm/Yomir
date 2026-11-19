# -*- coding: utf-8 -*-
"""day10_merge_1000.py — D10：组装 eval/golden_1000.json = 500 基础 + 500 新增。

新增来源（全部来自 kanbun.info 文本对，不碰图片）：
  1. eval/golden_rongo_full.json（Night 32 論語全量 498 章）中不在基础集里的
  2. eval/day10_new_entries.json（本次从故事页抓的）

去重规则：按 hakubun 文本去重。基础 500 条**原样保留**（含它自身的 25 条内部重复，
那是历史事实，不改评测集）；新增部分不得与基础或彼此重复。

输出：
  eval/golden_1000.json        1000 条
  eval/golden_1000_stats.json  分档 × 文体统计
  eval/day10_merge_report.json 组装对账明细
"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def load(name):
    with open(os.path.join(EV, name), encoding="utf-8") as f:
        return json.load(f)


def bucket_of(h):
    n = len(h)
    if n <= 20:
        return "≤20字"
    if n <= 40:
        return "21-40字"
    if n <= 60:
        return "41-60字"
    return ">60字"


def genre_of(url, entry):
    u = (url or "").lower()
    if "rongo" in u or entry.get("pian") is not None:
        return "論語"
    if "/koji/" in u:
        return "故事"
    if "/keibu/" in u:
        return "経部"
    return "その他"


def main():
    base = load("golden.json")
    rongo = load("golden_rongo_full.json")
    parallel = load("kanbun_parallel.json")
    crawled = load("day10_new_entries.json")

    seen = {x["hakubun"] for x in base}
    ids = {x["id"] for x in base}
    new = []
    src_counts = collections.Counter()

    def add(x, src, prefix=""):
        h = x["hakubun"]
        if not h or h in seen:
            return False
        eid = prefix + x["id"]
        if eid in ids:
            eid = "n-" + eid
            if eid in ids:
                return False
        seen.add(h)
        ids.add(eid)
        new.append({
            "id": eid,
            "source_url": x.get("source_url", ""),
            "hakubun": h,
            "expected_kakikudashi": x["expected_kakikudashi"],
            "origin": src,
        })
        src_counts[src] += 1
        return True

    # 1. 論語全量（Night 32，498 章，全部 kanbun.info/keibu 文本对）
    for x in sorted(rongo, key=lambda y: y["id"]):
        add(x, "rongo_full")

    # 2. 全站平行语料（Night 28，1705 对，全部 kanbun.info/koji 文本对）
    for x in sorted(parallel, key=lambda y: y["id"]):
        if len(new) >= 500:
            break
        add(x, "parallel", prefix="p-")

    # 3. 本次抓到的故事页（若仍不足）
    for x in crawled:
        if len(new) >= 500:
            break
        add(x, "koji_crawl", prefix="c-")

    print("新增组成:", dict(src_counts), flush=True)
    print("新增合计 %d / 目标 500" % len(new), flush=True)

    combined = base + new
    # 去掉 origin 字段：golden_1000 与 golden 保持同构
    combined_out = [{k: v for k, v in x.items() if k != "origin"} for x in combined]

    with open(os.path.join(EV, "golden_1000.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(combined_out, f, ensure_ascii=False, indent=2)

    # 统计
    buckets = collections.Counter()
    genres = collections.Counter()
    cross = collections.Counter()
    for x in combined_out:
        b = bucket_of(x["hakubun"])
        g = genre_of(x["source_url"], x)
        buckets[b] += 1
        genres[g] += 1
        cross["%s|%s" % (g, b)] += 1

    stats = {
        "total": len(combined_out),
        "base": len(base),
        "new": len(new),
        "new_by_source": dict(src_counts),
        "uniq_ids": len({x["id"] for x in combined_out}),
        "uniq_hakubun": len({x["hakubun"] for x in combined_out}),
        "base_internal_dups": len(base) - len({x["hakubun"] for x in base}),
        "by_bucket": dict(buckets),
        "by_genre": dict(genres),
        "cross": dict(cross),
    }
    with open(os.path.join(EV, "golden_1000_stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("total %d | uniq id %d | uniq hakubun %d（基础内部重复 %d）"
          % (stats["total"], stats["uniq_ids"], stats["uniq_hakubun"],
             stats["base_internal_dups"]), flush=True)
    print("分档:", dict(buckets), flush=True)
    print("文体:", dict(genres), flush=True)
    for k in sorted(cross):
        print("  %-14s %d" % (k, cross[k]), flush=True)


if __name__ == "__main__":
    main()
