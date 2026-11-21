# -*- coding: utf-8 -*-
"""night62_probe_site.py — N62：盘点 kanbun.info 全站剩余可抓文本对资源（v2，真实入口）。

入口 = 首页导航实测：keibu/rongo00.html（論語）/ koji/koji.html（故事名言）/
syubu/kanshi.html（漢詩）/ miscellaneous/miscellaneous.html（その他）。
两层爬链：栏目索引 → 其链接的全部页面（子索引再展开一层）。
配对模式沿用 N57/N60：genbun01 + yomi02/03 相邻对（koji/keibu/syubu 均实测成立）。
只读不写库，输出 eval/night62_probe.txt / night62_probe.json。
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
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0[23]">(.*?)</div>', re.S)

NAV = ("index", "sitemap", "about", "kanshi", "boshu", "pagetop", "css/", "js/", "images/")


def get(u, tries=3, timeout=30):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                          timeout=timeout).read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 + i * 2)
    print("[FAIL] %s %r" % (u, last), flush=True)
    return ""


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^\d{2,3}(（\d{2}-\d{2}）)?", "", s)
    return s.strip()


def strip_yomi(s):
    s = re.sub(r"<rt>.*?</rt>", "", s, flags=re.S)
    s = re.sub(r"<rp>.*?</rp>", "", s, flags=re.S)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def norm_href(base_dir, h):
    """返回 (section, pagename) 或 None（外链/资源）。"""
    if h.startswith(("http", "//", "#", "css/", "js/", "images/", "mailto")):
        return None
    m = re.fullmatch(r"(?:\.\./)?([a-z0-9]+)/([a-z0-9_]+)\.html", h)
    if m:
        return (m.group(1), m.group(2))
    m = re.fullmatch(r"([a-z0-9_]+)\.html", h)
    if m:
        return (base_dir, m.group(1))
    return None


def links_from(url, base_dir):
    t = get(url)
    out = []
    for m in re.finditer(r'href="([^"]+)"', t):
        p = norm_href(base_dir, m.group(1))
        if p and p not in out:
            out.append(p)
    return out


def main():
    lines = []

    def log(s):
        lines.append(s)
        print(s, flush=True)

    # 已见页 + 已见白文
    seen_pages, seen_hb = set(), set()
    for x in json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8")):
        u = x.get("source_url", "")
        if u:
            seen_pages.add(u.rsplit("/", 1)[-1].rsplit(".", 1)[0])
        seen_hb.add(x["hakubun"].strip())
    for fn in ("night57_scraped_syubu.json", "night60_scraped_left.json"):
        for x in json.load(open(os.path.join(EV, fn), encoding="utf-8")):
            u = x.get("source_url", "")
            if u:
                seen_pages.add(u.rsplit("/", 1)[-1].rsplit(".", 1)[0])
            seen_hb.add(x["hakubun"].strip())
    log("已见页 %d、已见白文 %d" % (len(seen_pages), len(seen_hb)))

    try:
        sm = get("https://kanbun.info/sitemap.xml")
        log("sitemap.xml: %d bytes, 开头 %r" % (len(sm), sm[:120]))
    except Exception as e:
        log("sitemap.xml 异常 %r" % e)

    # 两层爬链
    ENTRIES = [("keibu", "rongo00"), ("koji", "koji"), ("syubu", "kanshi"),
               ("miscellaneous", "miscellaneous")]
    known_indexes = set()
    all_pages = {}          # (sec,name) -> raw_pairs count（抓过的页）
    fetch_count = 0
    t0 = time.time()
    frontier = list(ENTRIES)
    seen_fetch = set(ENTRIES)
    hop = 0
    while frontier and hop < 3:
        hop += 1
        nxt = []
        for sec, name in frontier:
            url = "https://kanbun.info/%s/%s.html" % (sec, name)
            t = get(url)
            fetch_count += 1
            time.sleep(0.3)
            if not t:
                all_pages[(sec, name)] = -1
                continue
            n_raw = len(PAIR_RX.findall(t))
            all_pages[(sec, name)] = n_raw
            ls = links_from(url, sec)
            new_links = []
            for p in ls:
                if p not in seen_fetch:
                    seen_fetch.add(p)
                    new_links.append(p)
            # 非内容页（0 对）多半是索引/导航，展开下一层；内容页不再展开
            if n_raw == 0:
                nxt.extend(new_links)
                for p in new_links:
                    known_indexes.add(p)
            else:
                # 内容页里的链接只登记不展开（除非未知栏目）
                for p in new_links:
                    if p[0] == "miscellaneous":
                        nxt.append(p)
                        seen_fetch.add(p)
        frontier = nxt
        log("hop%d: 累计抓 %d 页，前沿 %d" % (hop, fetch_count, len(frontier)))

    # 统计
    by_sec = {}
    for (sec, name), n_raw in all_pages.items():
        d = by_sec.setdefault(sec, {"pages": 0, "with_pairs": 0, "fresh": 0,
                                    "fresh_with_pairs": 0, "raw_pairs_sum": 0})
        d["pages"] += 1
        if n_raw > 0:
            d["with_pairs"] += 1
            d["raw_pairs_sum"] += n_raw
        if name not in seen_pages:
            d["fresh"] += 1
            if n_raw > 0:
                d["fresh_with_pairs"] += 1
    log("\n=== 站点盘点（抓 %d 页 / %.0fs）===" % (fetch_count, time.time() - t0))
    for sec, d in sorted(by_sec.items()):
        log("%-14s 页 %4d | 有对页 %4d | raw 对合计 %5d | 剩页 %4d（其中有对 %4d）"
            % (sec, d["pages"], d["with_pairs"], d["raw_pairs_sum"], d["fresh"],
               d["fresh_with_pairs"]))

    # 剩页里的密度抽样（每栏目 3 页）
    log("\n=== 剩页密度抽样 ===")
    sampled = []
    for sec in sorted(by_sec):
        fresh_wp = [(s, n) for (s, n), r in all_pages.items()
                    if s == sec and n > 0 and n not in sampled
                    and n not in seen_pages] if False else [
            (s, n) for (s, n), r in all_pages.items()
            if s == sec and r > 0 and n not in seen_pages]
        for s, n in fresh_wp[:3]:
            url = "https://kanbun.info/%s/%s.html" % (s, n)
            t = get(url)
            good = 0
            for g, y in PAIR_RX.findall(t):
                hb, yk = strip_white(g), strip_yomi(y)
                if hb and yk and "（" not in hb and "）" not in hb and hb not in seen_hb:
                    good += 1
                    seen_hb.add(hb)
            log("  %s/%s: 新可用 %d 对" % (s, n, good))
            sampled.append(n)
            time.sleep(0.3)

    out = {"seen_pages": len(seen_pages), "seen_hb": len(seen_hb),
           "fetched": fetch_count,
           "by_sec": by_sec,
           "fresh_names": {sec: sorted(n for (s, n) in all_pages
                                       if s == sec and n not in seen_pages)
                           for sec in by_sec},
           "sampled": sampled}
    json.dump(out, open(os.path.join(EV, "night62_probe.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    with open(os.path.join(EV, "night62_probe.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("written: eval/night62_probe.txt / night62_probe.json", flush=True)


if __name__ == "__main__":
    main()
