# -*- coding: utf-8 -*-
"""night57_build_golden_3000.py — N57：在 golden_2000 基础上扩到 3000 条。

约束（任务书）：
  * 来源只取 kanbun.info 文本对：平行语料剩余（day16_pool 里 31 条 parallel_extra）
    + 新栏目 /syubu/（詩経 shikyo_*、漢詩詩人別、歴代；night57_scrape_syubu.py 产物）。
  * expected 一字不改：抓取器只做「剥 ruby/标签 + 去空白」，不做任何替换。
  * 去重：按 hakubun（strip 归一）与 golden_2000 已有白文去重，来源内部也去重。
  * golden_2000 前 2000 条**原样字节保留**在 3000 条前部（逐条 dict 相等 + 顺序一致）。

产物：eval/golden_3000.json + eval/golden_3000_stats.json
"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
SRC_ORDER = ["parallel_extra", "syubu_shikyo", "syubu_shijin", "syubu_reki", "syubu_toushisen"]
TARGET_NEW = 1000


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


def bucket_of(hb):
    n = len(hb)
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def main():
    base = json.load(open(os.path.join(EV, "golden_2000.json"), encoding="utf-8"))
    pool_old = json.load(open(os.path.join(EV, "day16_pool.json"), encoding="utf-8"))
    pool_new = json.load(open(os.path.join(EV, "night57_scraped_syubu.json"), encoding="utf-8"))

    used_hb = {x["hakubun"].strip() for x in base}
    used_id = {x["id"] for x in base}
    pool = []
    for r in pool_old:
        if r.get("_src") == "parallel_extra":
            pool.append({"id": r["id"], "source_url": r["source_url"],
                         "hakubun": r["hakubun"].strip(),
                         "expected_kakikudashi": (r.get("expected_kakikudashi") or "").strip(),
                         "_src": "parallel_extra"})
    for r in pool_new:
        pool.append({"id": r["id"], "source_url": r["source_url"],
                     "hakubun": r["hakubun"].strip(),
                     "expected_kakikudashi": (r.get("expected_kakikudashi") or "").strip(),
                     "_src": r["_src"]})
    pool.sort(key=lambda r: (SRC_ORDER.index(r["_src"]) if r["_src"] in SRC_ORDER else 99,
                             r["id"]))

    seen_hb, seen_id = set(used_hb), set(used_id)
    new, skipped = [], collections.Counter()
    for r in pool:
        if len(new) >= TARGET_NEW:
            break
        hb, exp = r["hakubun"], r["expected_kakikudashi"]
        if not hb or not exp:
            skipped["empty"] += 1
            continue
        if hb in seen_hb:
            skipped["dup_hakubun"] += 1
            continue
        if r["id"] in seen_id:
            skipped["dup_id"] += 1
            continue
        seen_hb.add(hb)
        seen_id.add(r["id"])
        new.append({"id": r["id"], "source_url": r["source_url"], "hakubun": hb,
                    "expected_kakikudashi": exp})

    print("base %d | pool %d | picked %d | skipped %s"
          % (len(base), len(pool), len(new), dict(skipped)), flush=True)
    if len(new) < TARGET_NEW:
        print("!! 不足 %d（实得 %d）—— 如实记录，不补重复条目" % (TARGET_NEW, len(new)),
              flush=True)

    combined = [{"id": x["id"], "source_url": x.get("source_url", ""),
                 "hakubun": x["hakubun"],
                 "expected_kakikudashi": x["expected_kakikudashi"]} for x in base] + new

    # 硬断言：前 2000 条与 golden_2000 逐条相等且顺序一致
    assert combined[:len(base)] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in base], \
        "golden_2000 前缀被改动！"
    assert len(combined) == len(base) + len(new)
    assert len({x["id"] for x in combined}) == len(combined), "id 有重复"

    out = os.path.join(EV, "golden_3000.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    b = collections.Counter(bucket_of(x["hakubun"]) for x in combined)
    g = collections.Counter(genre_of(x["source_url"]) for x in combined)
    nb = collections.Counter(bucket_of(x["hakubun"]) for x in new)
    ng = collections.Counter(genre_of(x["source_url"]) for x in new)
    src_cnt = collections.Counter()
    src_of = {r["id"]: r["_src"] for r in pool}
    for x in new:
        src_cnt[src_of.get(x["id"], "?")] += 1
    stats = {
        "total": len(combined), "base": len(base), "new": len(new),
        "uniq_ids": len({x["id"] for x in combined}),
        "uniq_hakubun": len({x["hakubun"] for x in combined}),
        "by_bucket": dict(b), "by_genre": dict(g),
        "new_by_bucket": dict(nb), "new_by_genre": dict(ng), "new_by_src": dict(src_cnt),
        "skipped": dict(skipped),
        "base_internal_dups": len(base) - len({x["hakubun"] for x in base}),
    }
    with open(os.path.join(EV, "golden_3000_stats.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\n=== golden_3000 ===", flush=True)
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
