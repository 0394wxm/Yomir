# -*- coding: utf-8 -*-
"""day10_crawl.py — 带缓存的 kanbun.info 文本对抓取器（D10 用）。

只抓文本（genbun01 / yomi02），不碰图片。
页面缓存到 %TEMP%\\kanbun_cache\\<pid>.html，重跑不再重复请求。
诊断：每页记录 pairs 数、被过滤原因计数，最后输出汇总，方便判断命中率。

用法：
  python tools/day10_crawl.py --discover-only
  python tools/day10_crawl.py --target-new 500
"""
import argparse
import collections
import html as html_mod
import json
import os
import re
import sys
import tempfile
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(ROOT, "eval", "golden.json")
CACHE = os.path.join(tempfile.gettempdir(), "kanbun_cache")

UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}

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


def cache_path(url):
    key = re.sub(r"[^a-z0-9]+", "_", url.lower())
    return os.path.join(CACHE, key[-120:] + ".html")


def fetch(url, tries=3, timeout=25, use_cache=True):
    cp = cache_path(url)
    if use_cache and os.path.exists(cp) and os.path.getsize(cp) > 500:
        with open(cp, encoding="utf-8", errors="replace") as f:
            return f.read(), "cache"
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                txt = r.read().decode("utf-8", errors="replace")
            os.makedirs(CACHE, exist_ok=True)
            with open(cp, "w", encoding="utf-8", newline="\n") as f:
                f.write(txt)
            return txt, "net"
        except Exception as e:
            last = e
            time.sleep(1.5 + i * 2)
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


def discover(use_cache=True):
    pages, seen = [], set()
    for cat in CATEGORY_PAGES:
        try:
            txt, src = fetch(cat, use_cache=use_cache)
        except Exception as e:
            print("[CAT-SKIP] %-20s %r" % (cat.rsplit("/", 1)[-1], e), flush=True)
            continue
        n0 = len(pages)
        for m in re.finditer(r'href="(?:\.\./koji/)?([a-z0-9_]+)\.html"', txt):
            pid = m.group(1)
            if pid.startswith("koji00") or pid in ("koji", "index") or pid in seen:
                continue
            seen.add(pid)
            pages.append((pid, "https://kanbun.info/koji/%s.html" % pid))
        print("[CAT] %-20s +%-4d (%s)" % (cat.rsplit("/", 1)[-1], len(pages) - n0, src), flush=True)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover-only", action="store_true")
    ap.add_argument("--target-new", type=int, default=500)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--limit-pages", type=int, default=0)
    arg = ap.parse_args()
    uc = not arg.no_cache

    with open(GOLDEN, encoding="utf-8") as f:
        base = json.load(f)
    seen_hakubun = {x["hakubun"] for x in base}
    seen_ids = {x["id"] for x in base}
    print("基础集 %d 条（uniq hakubun %d）" % (len(base), len(seen_hakubun)), flush=True)

    pages = discover(uc)
    print("发现故事页 %d 个" % len(pages), flush=True)
    if arg.discover_only:
        with open(os.path.join(ROOT, "eval", "day10_pages.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump([{"id": p, "url": u} for p, u in pages], f, ensure_ascii=False, indent=1)
        return

    if arg.limit_pages:
        pages = pages[:arg.limit_pages]

    new = []
    diag = collections.Counter()
    t0 = time.time()
    for pi, (pid, url) in enumerate(pages, 1):
        if len(new) >= arg.target_new:
            break
        try:
            page, src = fetch(url, use_cache=uc)
        except Exception as e:
            diag["fetch_fail"] += 1
            print("[%4d/%4d] %-22s FETCH-FAIL %r" % (pi, len(pages), pid, e), flush=True)
            continue
        pairs = PAIR_RX.findall(page)
        if not pairs:
            diag["no_pair"] += 1
            continue
        n0 = len(new)
        for i, (genbun, yomi) in enumerate(pairs, start=1):
            hakubun = strip_white(genbun)
            kakikudashi = strip_yomi(yomi)
            if not hakubun or not kakikudashi:
                diag["empty"] += 1
                continue
            if "（" in hakubun or "）" in hakubun:
                diag["paren"] += 1
                continue
            if hakubun in seen_hakubun:
                diag["dup"] += 1
                continue
            eid = "%s-%d" % (pid, i)
            if eid in seen_ids:
                diag["dup_id"] += 1
                continue
            seen_hakubun.add(hakubun)
            seen_ids.add(eid)
            new.append({"id": eid, "source_url": url, "hakubun": hakubun,
                        "expected_kakikudashi": kakikudashi})
            diag["ok"] += 1
        if len(new) > n0:
            print("[%4d/%4d] %-22s +%d (new %d, %.0fs)"
                  % (pi, len(pages), pid, len(new) - n0, len(new), time.time() - t0), flush=True)

    print("\n=== 抓取诊断 ===", flush=True)
    for k, v in diag.most_common():
        print("  %-12s %d" % (k, v), flush=True)
    print("新增 %d 条（目标 %d），用时 %.0fs" % (len(new), arg.target_new, time.time() - t0), flush=True)

    out = os.path.join(ROOT, "eval", "day10_new_entries.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(new, f, ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
