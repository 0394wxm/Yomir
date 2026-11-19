# -*- coding: utf-8 -*-
"""day10_build_golden_1000.py — D10：把评测集扩到 1000 条（500 基础 + 500 新增）。

约束：
  * 只抓 kanbun.info 的**文本对**（genbun01 / yomi02），全程不碰图片。
  * **不动 eval/golden.json**（D2 验收门的比对基准）。
  * 500 条基础 = 现有 golden.json 原样（不增不减不改）。
  * 新增 500 条 = 从 kanbun.info 其它页面抓，且与「基础 500 + 已收新增」按
    hakubun 文本去重（golden 自身有 25 条内部重复，保留；新增部分不再重复）。
  * 输出 eval/golden_1000.json，并写一份分档/文体统计 eval/golden_1000_stats.json。

用法：python tools/day10_build_golden_1000.py [--target-new 500]
"""
import argparse
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, "eval", "golden.json")
OUT = os.path.join(ROOT, "eval", "golden_1000.json")
STATS = os.path.join(ROOT, "eval", "golden_1000_stats.json")

UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}

# 站点分区：故事页(koji) / 論語(rongo) / 名言(meigen) / 漢詩? 先探这三类
CATEGORY_PAGES = [
    "https://kanbun.info/koji/koji00a.html",
    "https://kanbun.info/koji/koji00ka.html",
    "https://kanbun.info/koji/koji00sa.html",
    "https://kanbun.info/koji/koji00ta.html",
    "https://kanbun.info/koji/koji00na.html",
    "https://kanbun.info/koji/koji00ha.html",
    "https://kanbun.info/koji/koji00ma.html",
    "https://kanbun.info/koji/koji00ya.html",
    "https://kanbun.info/koji/koji00ra.html",
    "https://kanbun.info/koji/koji00wa.html",
    "https://kanbun.info/koji/koji00rongo.html",
]

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi02">(.*?)</div>', re.S)


def fetch(url, tries=2, timeout=20):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(1 + i)
    raise last


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"\s+", "", s).strip()


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def discover():
    """从分类页收集故事页 id（与 build_golden 相同的发现逻辑）。"""
    pages = []
    seen = set()
    for cat in CATEGORY_PAGES:
        try:
            txt = fetch(cat)
        except Exception as e:
            print("[CAT-SKIP] %s: %r" % (cat.rsplit("/", 1)[-1], e))
            continue
        n0 = len(pages)
        for m in re.finditer(r'href="(?:\.\./koji/)?([a-z0-9_]+)\.html"', txt):
            pid = m.group(1)
            if pid.startswith("koji00") or pid in ("koji", "index") or pid in seen:
                continue
            seen.add(pid)
            pages.append((pid, "https://kanbun.info/koji/%s.html" % pid))
        print("[CAT] %-18s +%d" % (cat.rsplit("/", 1)[-1], len(pages) - n0))
    return pages


def genre_of(url):
    u = url.lower()
    if "rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    if "/meigen/" in u:
        return "名言"
    if "/kanbun/" in u:
        return "漢文"
    return "その他"


def bucket_of(hakubun):
    n = len(hakubun)
    if n <= 20:
        return "≤20字"
    if n <= 40:
        return "21-40字"
    if n <= 60:
        return "41-60字"
    return ">60字"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-new", type=int, default=500)
    ap.add_argument("--per-page", type=int, default=99)
    arg = ap.parse_args()

    with open(GOLDEN, encoding="utf-8") as f:
        base = json.load(f)
    print("基础集 golden.json: %d 条" % len(base))

    # 去重种子：基础集全部 hakubun（含其内部重复，只用来挡新增）
    seen_hakubun = {x["hakubun"] for x in base}
    seen_ids = {x["id"] for x in base}

    pages = discover()
    print("发现故事页 %d 个" % len(pages), flush=True)

    new = []
    for pi, (pid, url) in enumerate(pages, 1):
        if len(new) >= arg.target_new:
            break
        try:
            page = fetch(url)
        except Exception as e:
            print("[SKIP] %s: %r" % (pid, e), flush=True)
            continue
        pairs = PAIR_RX.findall(page)
        if not pairs:
            continue
        n0 = len(new)
        for i, (genbun, yomi) in enumerate(pairs, start=1):
            if len(new) >= arg.target_new:
                break
            if i > arg.per_page:
                break
            hakubun = strip_white(genbun)
            kakikudashi = strip_yomi(yomi)
            if not hakubun or not kakikudashi:
                continue
            if "（" in hakubun or "）" in hakubun:  # 混入读音注记
                continue
            if hakubun in seen_hakubun:  # 去重
                continue
            eid = "%s-%d" % (pid, i)
            if eid in seen_ids:
                eid = "%s-n%d" % (pid, i)
                if eid in seen_ids:
                    continue
            seen_hakubun.add(hakubun)
            seen_ids.add(eid)
            new.append({"id": eid, "source_url": url, "hakubun": hakubun,
                        "expected_kakikudashi": kakikudashi})
        print("[%d/%d] %-22s +%d (new %d)"
              % (pi, len(pages), pid, len(new) - n0, len(new)), flush=True)

    print("\n新增 %d 条（目标 %d）" % (len(new), arg.target_new), flush=True)
    combined = base + new

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    # 统计（分档 × 文体）
    from collections import Counter
    buckets = Counter()
    genres = Counter()
    cross = Counter()
    for x in combined:
        b = bucket_of(x["hakubun"])
        g = genre_of(x["source_url"])
        buckets[b] += 1
        genres[g] += 1
        cross["%s|%s" % (g, b)] += 1
    stats = {
        "total": len(combined),
        "base": len(base),
        "new": len(new),
        "uniq_ids": len({x["id"] for x in combined}),
        "uniq_hakubun": len({x["hakubun"] for x in combined}),
        "by_bucket": dict(buckets),
        "by_genre": dict(genres),
        "cross": dict(cross),
        "base_dups_internal": len(base) - len({x["hakubun"] for x in base}),
        "new_dup_with_base": 0,  # 构造保证
    }
    with open(STATS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("分档:", dict(buckets))
    print("文体:", dict(genres))
    print("written:", OUT)
    print("written:", STATS)


if __name__ == "__main__":
    main()
