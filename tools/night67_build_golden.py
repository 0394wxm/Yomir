# -*- coding: utf-8 -*-
"""night67_build_golden.py — N67⑲：启用 N62 标记未启用的 257 个 paren 对 → golden_<N>.json。

来源：eval/night62_scraped_10k.json 中 _quality=="paren" 的 257 条（白文含（），N57 质量
约定下 N62 只标记未启用；用户 2026-11-21 19:00 拍板启用 = Night 67 任务书 ⑲）。
规矩（与 night62_build_golden.py 同款 + ⑲ 专项断言）：
  * expected 一字不改：新行 4 字段与 scraped 原行逐字段相等（硬断言，任一不符即中止）；
  * 去重：新段白文（strip 口径）与 golden_7908 已有白文及本段内部不重复；id 同理
    （有冲突则 skip 并计数，文件按实数命名）；
  * 硬断言：前 7908 条与 golden_7908 逐条 dict 相等且顺序一致，且前缀序列化字节与
    golden_7908.json 文件字节完全一致。
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


def section_of(url):
    u = (url or "").lower()
    for s in ("shibu02", "shibu01", "syubu02", "keibu", "koji"):
        if "/" + s + "/" in u:
            return s
    if "/syubu/" in u:
        return "syubu"
    return "?"


def main():
    base = json.load(open(os.path.join(EV, "golden_7908.json"), encoding="utf-8"))
    scraped = json.load(open(os.path.join(EV, "night62_scraped_10k.json"), encoding="utf-8"))
    paren = [r for r in scraped if r.get("_quality") == "paren"]
    print("golden_7908: %d 条 | scraped paren 标记: %d 条" % (len(base), len(paren)), flush=True)

    used_hb = {x["hakubun"].strip() for x in base}
    used_id = {x["id"] for x in base}

    new, skipped = [], collections.Counter()
    seen_hb, seen_id = set(used_hb), set(used_id)
    for r in paren:
        hb = (r.get("hakubun") or "").strip()
        exp = (r.get("expected_kakikudashi") or "").strip()
        if not hb or not exp:
            skipped["empty"] += 1
            continue
        if hb in seen_hb:
            skipped["dup_hakubun"] += 1
            continue
        if r["id"] in seen_id:
            skipped["dup_id"] += 1
            continue
        # ⑲ 专项硬断言：expected 一字不改（与 scraped 原行逐字段相等），任一不符即中止
        assert hb == r["hakubun"].strip() and exp == r["expected_kakikudashi"].strip(), \
            "paren 对字段被改写！中止。"
        seen_hb.add(hb)
        seen_id.add(r["id"])
        new.append({"id": r["id"], "source_url": r.get("source_url", ""),
                    "hakubun": hb, "expected_kakikudashi": exp})

    combined = [{"id": x["id"], "source_url": x.get("source_url", ""),
                 "hakubun": x["hakubun"],
                 "expected_kakikudashi": x["expected_kakikudashi"]} for x in base] + new

    # 硬断言 1：前 7908 条与 golden_7908 逐条相等且顺序一致
    assert combined[:len(base)] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in base], \
        "golden_7908 前缀被改动！"
    # 硬断言 2：前缀序列化字节与 golden_7908.json 内容字节完全一致。
    # 注：工作树文件为 CRLF（git autocrlf checkout 产物，blob 本身 LF），按 LF 归一后比对。
    old_bytes = open(os.path.join(EV, "golden_7908.json"), "rb").read()
    prefix_bytes = json.dumps(combined[:len(base)], ensure_ascii=False, indent=2).encode("utf-8")
    assert prefix_bytes == old_bytes.replace(b"\r\n", b"\n"), "golden_7908.json 前缀字节不一致！"
    # 硬断言 3：新增段白文零重复（段内 + 与前缀）、id 唯一
    new_hb = [x["hakubun"] for x in new]
    assert len(new_hb) == len(set(new_hb)), "新增段内部白文重复"
    assert not (set(new_hb) & {x["hakubun"].strip() for x in base}), "新增段白文与前缀重复"
    assert len({x["id"] for x in combined}) == len(combined), "id 有重复"

    total = len(combined)
    name = "golden_%d.json" % total
    with open(os.path.join(EV, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    b = collections.Counter(bucket_of(x["hakubun"]) for x in combined)
    g = collections.Counter(genre_of(x["source_url"]) for x in combined)
    nb = collections.Counter(bucket_of(x["hakubun"]) for x in new)
    ng = collections.Counter(genre_of(x["source_url"]) for x in new)
    sec = collections.Counter(section_of(x["source_url"]) for x in new)
    stats = {
        "total": total, "base": len(base), "new": len(new),
        "paren_source_total": len(paren), "paren_enabled": len(new),
        "uniq_hakubun": len({x["hakubun"].strip() for x in combined}),
        "by_bucket": dict(b), "by_genre": dict(g),
        "new_by_bucket": dict(nb), "new_by_genre": dict(ng),
        "new_by_section": dict(sec), "skipped": dict(skipped),
        "prefix_bytes_identical": "LF 归一后逐字节一致（工作树 CRLF 为 autocrlf checkout 产物，git blob 为 LF）",
        "decision": "N67⑲：启用 N62 标记未启用的 257 个 paren 对（expected 一字不改、"
                    "前缀 7908 硬断言不变、文件按实数命名）",
    }
    with open(os.path.join(EV, "golden_%d_stats.json" % total), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\n=== %s ===" % name, flush=True)
    print("base %d | paren 启用新增 %d | skipped %s" % (len(base), len(new), dict(skipped)),
          flush=True)
    print("total %d | uniq hakubun %d" % (total, stats["uniq_hakubun"]), flush=True)
    print("新增分档:", dict(nb), flush=True)
    print("新增文体:", dict(ng), flush=True)
    print("新增栏目:", dict(sec), flush=True)
    print("written:", os.path.join(EV, name), flush=True)


if __name__ == "__main__":
    main()
