# -*- coding: utf-8 -*-
"""night62_build_golden.py — N62：golden_4000 + 在手池剩 + 全站剩页抓取 → golden_<N>.json。

方案A（用户拍板 2026-11-21）：扩到约束内上限，**不设目标截断**；文件按实数命名。
任务书「/syubu/ 剩约 270 页优先，其余栏目补」→ 来源并入优先序：
  1) night57_scraped_syubu.json 池剩（N57 抓过、未入 golden 的干净对）
  2) night60_scraped_left.json 池剩
  3) night62_scraped_10k.json（全站剩页，_quality=ok；**paren 对不启用**——
     N57 起的质量约定不改，只把数量记进报告挂拍板）
去重：与 golden_4000 白文（3975 唯一）+ 本批内重复；expected 一字不改。
硬断言：前 4000 条与 golden_4000 逐条相等且顺序一致。
产物 eval/golden_<N>.json + golden_<N>_stats.json。
"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


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
    base = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    used_hb = {x["hakubun"].strip() for x in base}
    used_id = {x["id"] for x in base}

    pools = [("night57_scraped_syubu.json", "night57"),
             ("night60_scraped_left.json", "night60"),
             ("night62_scraped_10k.json", "night62_fresh")]

    new, skipped = [], collections.Counter()
    paren_excluded = 0
    seen_hb, seen_id = set(used_hb), set(used_id)
    for fn, tag in pools:
        for r in json.load(open(os.path.join(EV, fn), encoding="utf-8")):
            hb = (r.get("hakubun") or "").strip()
            exp = (r.get("expected_kakikudashi") or "").strip()
            if not hb or not exp:
                skipped["empty"] += 1
                continue
            if "（" in hb or "）" in hb:
                paren_excluded += 1
                continue
            if hb in seen_hb:
                skipped["dup_hakubun"] += 1
                continue
            if r["id"] in seen_id:
                skipped["dup_id"] += 1
                continue
            seen_hb.add(hb)
            seen_id.add(r["id"])
            new.append({"id": r["id"], "source_url": r.get("source_url", ""),
                        "hakubun": hb, "expected_kakikudashi": exp,
                        "_src": r.get("_src", tag)})

    total = len(base) + len(new)
    combined = [{"id": x["id"], "source_url": x.get("source_url", ""),
                 "hakubun": x["hakubun"],
                 "expected_kakikudashi": x["expected_kakikudashi"]} for x in base] + \
               [{k: v for k, v in x.items() if k != "_src"} for x in new]

    # 硬断言：前 4000 条与 golden_4000 逐条相等且顺序一致
    assert combined[:len(base)] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in base], \
        "golden_4000 前缀被改动！"
    assert len(combined) == total
    assert len({x["id"] for x in combined}) == total, "id 有重复"

    name = "golden_%d.json" % total
    with open(os.path.join(EV, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    b = collections.Counter(bucket_of(x["hakubun"]) for x in combined)
    g = collections.Counter(genre_of(x["source_url"]) for x in combined)
    nb = collections.Counter(bucket_of(x["hakubun"]) for x in new)
    ng = collections.Counter(genre_of(x["source_url"]) for x in new)
    sec = collections.Counter(x["_src"].split("/")[0] if "/" in x["_src"] else x["_src"]
                              for x in new)
    src_tag = collections.Counter()
    for x in new:
        u = x["source_url"].lower()
        if "/shibu02/" in u:
            src_tag["shibu02"] += 1
        elif "/shibu01/" in u:
            src_tag["shibu01"] += 1
        elif "/syubu02/" in u:
            src_tag["syubu02"] += 1
        elif "/syubu/" in u:
            src_tag["syubu"] += 1
        elif "/koji/" in u:
            src_tag["koji"] += 1
        elif "/keibu/" in u:
            src_tag["keibu"] += 1
        else:
            src_tag["night57/60池剩"] += 1

    stats = {
        "total": total, "base": len(base), "new": len(new),
        "uniq_ids": total,
        "uniq_hakubun": len({x["hakubun"] for x in combined}),
        "by_bucket": dict(b), "by_genre": dict(g),
        "new_by_bucket": dict(nb), "new_by_genre": dict(ng),
        "new_by_src_section": dict(sec), "new_by_src_tag": dict(src_tag),
        "paren_excluded_not_enabled": paren_excluded,
        "skipped": dict(skipped),
        "decision": "方案A：扩到约束内上限（kanbun.info 剩余干净文本对全部并入，"
                    "无目标截断）；golden_4000 前缀逐条断言不变",
    }
    with open(os.path.join(EV, "golden_%d_stats.json" % total), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\n=== %s ===" % name)
    print("base %d | 池剩+剩页新增 %d | skipped %s | paren 未启用 %d"
          % (len(base), len(new), dict(skipped), paren_excluded))
    print("total %d | uniq hakubun %d" % (total, stats["uniq_hakubun"]))
    print("分档:", dict(b))
    print("文体:", dict(g))
    print("新增分档:", dict(nb))
    print("新增文体:", dict(ng))
    print("新增来源(栏目):", dict(sec))
    print("written:", os.path.join(EV, name))


if __name__ == "__main__":
    main()
