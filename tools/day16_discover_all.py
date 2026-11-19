# -*- coding: utf-8 -*-
"""day16_discover_all.py — 全站故事页发现（含 build_golden 漏掉的 わ行索引）。

只读：抓 11 个分类索引页，汇总故事页 id；与 kanbun_parallel.json 已有页面对比。
"""
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}

CATS = ["koji00a", "koji00ka", "koji00sa", "koji00ta", "koji00na",
        "koji00ha", "koji00ma", "koji00ya", "koji00ra", "koji00wa", "koji00rongo"]

LINK_RX = re.compile(r'href="(?:\.\./koji/)?([a-z0-9_]+)\.html"')


def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                  timeout=30).read().decode("utf-8", "replace")


def main():
    pages, missing_cats = [], []
    seen = set()
    for c in CATS:
        u = "https://kanbun.info/koji/%s.html" % c
        try:
            t = fetch(u)
        except Exception as e:
            missing_cats.append((c, repr(e)))
            print("[FAIL] %-14s %r" % (c, e), flush=True)
            continue
        n0 = len(pages)
        for m in LINK_RX.finditer(t):
            pid = m.group(1)
            if pid.startswith("koji00") or pid in ("koji", "index") or pid in seen:
                continue
            seen.add(pid)
            pages.append(pid)
        print("[CAT] %-14s +%d (total %d)" % (c, len(pages) - n0, len(pages)), flush=True)

    par = json.load(open(os.path.join(ROOT, "eval", "kanbun_parallel.json"), encoding="utf-8"))
    have = {x["source_url"].rsplit("/", 1)[-1][:-5] for x in par}
    print("\n站点发现 %d 页 | 平行语料已含 %d 页 | 未抓 %d 页"
          % (len(pages), len(have), len(set(pages) - have)), flush=True)
    print("未抓页面:", sorted(set(pages) - have), flush=True)
    print("语料有但站点索引没有:", len(have - set(pages)), sorted(have - set(pages))[:20], flush=True)
    out = os.path.join(ROOT, "eval", "day16_pages.json")
    json.dump(sorted(pages), open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
