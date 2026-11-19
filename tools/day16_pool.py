# -*- coding: utf-8 -*-
"""day16_pool.py — 汇总所有可用来源，去重后统计可新增条目数。

来源：
  1. eval/kanbun_parallel.json        （平行语料 1705 行，已抓全站 1130 页，每页前 10 对）
  2. eval/day16_recap 补抓            （被 10 对上限截断的页面剩余对，见 day16_recap_extra）
  3. eval/day16_classics.json         （大学 130 + 孝経 219，新栏目）
  4. 論語剩余 1 章 rongo1125
去重键：hakubun（空白归一后）。base = golden_1000 的全部 hakubun。
"""
import collections
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


def load(n):
    p = os.path.join(EV, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def norm_hb(s):
    return re.sub(r"\s+", "", s or "").strip()


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", "", s)
    s = COUNTER_RX.sub("", s)
    return s.strip()


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def fetch(u, tries=3, timeout=35):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                          timeout=timeout).read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 + i * 2)
    print("[FAIL] %r" % (last,), flush=True)
    return ""


def main():
    g1 = load("golden_1000.json")
    base_hb = {norm_hb(x["hakubun"]) for x in g1}
    print("golden_1000: %d 行 / %d 唯一白文" % (len(g1), len(base_hb)), flush=True)

    pool = {}   # hakubun -> row
    stats = collections.Counter()

    def add(row, src):
        hb = norm_hb(row.get("hakubun"))
        if not hb:
            stats[src + ":empty"] += 1
            return
        if hb in base_hb:
            stats[src + ":dup_base"] += 1
            return
        if hb in pool:
            stats[src + ":dup_pool"] += 1
            return
        row["_src"] = src
        pool[hb] = row
        stats[src + ":ok"] += 1

    # 1) 平行语料
    par = load("kanbun_parallel.json")
    for r in par:
        add(dict(r), "parallel")

    # 2) 平行语料被 10 对上限截断的页面，补抓剩余对
    per_page = collections.Counter(x["source_url"] for x in par)
    capped = [u for u, n in per_page.items() if n >= 10]
    print("\n补抓被截断页面 %d 个 ..." % len(capped), flush=True)
    for u in capped:
        page = fetch(u)
        if not page:
            continue
        for i, (g, y) in enumerate(PAIR_RX.findall(page), start=1):
            hb, yk = strip_white(g), strip_yomi(y)
            if not hb or not yk or "（" in hb or "）" in hb:
                continue
            pid = u.rsplit("/", 1)[-1][:-5]
            add({"id": "%s-x%d" % (pid, i), "source_url": u,
                 "hakubun": hb, "expected_kakikudashi": yk}, "parallel_extra")
        time.sleep(0.2)

    # 3) 大学 + 孝経
    for r in load("day16_classics.json"):
        add(dict(r), "classics")

    # 4) 論語剩余
    for r in load("golden_rongo_full.json"):
        add(dict(r), "rongo_full")
    t = fetch("https://kanbun.info/keibu/rongo1125.html")
    if t:
        for i, (g, y) in enumerate(PAIR_RX.findall(t), start=1):
            hb, yk = strip_white(g), strip_yomi(y)
            if hb and yk and "（" not in hb and "）" not in hb:
                add({"id": "rongo1125-%d" % i, "source_url":
                     "https://kanbun.info/keibu/rongo1125.html",
                     "hakubun": hb, "expected_kakikudashi": yk}, "rongo_gap")

    # 5) 其余旧语料（day10 新增、golden_rongo）
    for r in load("day10_new_entries.json"):
        add(dict(r), "day10")
    for r in load("golden_rongo.json"):
        add(dict(r), "rongo_117")

    print("\n=== 来源统计 ===", flush=True)
    for k in sorted(stats):
        print("  %-28s %d" % (k, stats[k]), flush=True)
    print("\n可新增唯一白文合计: %d" % len(pool), flush=True)

    out = os.path.join(EV, "day16_pool.json")
    json.dump(list(pool.values()), open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
