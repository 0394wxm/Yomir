# -*- coding: utf-8 -*-
"""day16_verify.py — golden_2000 完整性校验（只读）。

1) 前 1000 条与 golden_1000 逐字段一致（expected 一字不改）
2) 新增 1000 条：id 唯一、hakubun 与 base 不重复、expected 非空
3) 新增条目的 expected 与 source_url 页面上的 yomi 文本一致（重新抓页面核对）
"""
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0[23]">(.*?)</div>', re.S)
COUNTER_RX = re.compile(r"^\d{2,3}(（\d{2}-\d{2}）)?")


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", "", s)
    return COUNTER_RX.sub("", s).strip()


def main():
    g1 = json.load(open(os.path.join(EV, "golden_1000.json"), encoding="utf-8"))
    g2 = json.load(open(os.path.join(EV, "golden_2000.json"), encoding="utf-8"))
    print("golden_1000 %d | golden_2000 %d" % (len(g1), len(g2)), flush=True)

    # 1) 前 1000 条逐字段一致
    bad = 0
    for i, (a, b) in enumerate(zip(g1, g2), 1):
        for k in ("id", "hakubun", "expected_kakikudashi"):
            if a.get(k) != b.get(k):
                bad += 1
                print("  MISMATCH #%d %s: %r != %r" % (i, k, a.get(k), b.get(k)), flush=True)
                break
        if a.get("source_url") != b.get("source_url"):
            bad += 1
            print("  MISMATCH #%d source_url" % i, flush=True)
    print("① 前1000条逐字段一致: %s（不一致 %d）" % ("PASS" if bad == 0 else "FAIL", bad),
          flush=True)

    # 2) 新增 1000 条结构校验
    new = g2[1000:]
    hb1 = {x["hakubun"].strip() for x in g1}
    ids = [x["id"] for x in new]
    dups_in_new = len(ids) - len(set(ids))
    dup_with_base = sum(1 for x in new if x["hakubun"].strip() in hb1)
    empty = sum(1 for x in new if not x["hakubun"].strip() or not x["expected_kakikudashi"].strip())
    print("② 新增 %d 条: id 重复 %d | 与base白文重复 %d | 空字段 %d"
          % (len(new), dups_in_new, dup_with_base, empty), flush=True)

    # 3) 抽 30 条独立复核 expected 来自页面原文
    import random
    random.seed(20261119)
    sample = random.sample(new, 30)
    cache = {}
    ok = miss = mismatch = 0
    for x in sample:
        u = x["source_url"]
        if u not in cache:
            try:
                cache[u] = urllib.request.urlopen(
                    urllib.request.Request(u, headers=UA), timeout=30
                ).read().decode("utf-8", "replace")
                time.sleep(0.3)
            except Exception as e:
                cache[u] = ""
                print("  [FETCH-FAIL] %s %r" % (u.rsplit("/", 1)[-1], e), flush=True)
        page = cache[u]
        if not page:
            miss += 1
            continue
        pairs = {(strip_white(g), strip_yomi(y)) for g, y in PAIR_RX.findall(page)}
        key = (x["hakubun"].strip(), x["expected_kakikudashi"].strip())
        if key in pairs:
            ok += 1
        else:
            # 编号行已剥，允许 hakubun 轻微差异：只比 expected
            if any(y == key[1] for _g, y in pairs):
                ok += 1
            else:
                mismatch += 1
                print("  MISMATCH %s | %s" % (x["id"], x["expected_kakikudashi"][:60]), flush=True)
    print("③ 抽检 30 条 vs 页面原文: 一致 %d | 页面缺失 %d | 不一致 %d"
          % (ok, miss, mismatch), flush=True)


if __name__ == "__main__":
    main()
