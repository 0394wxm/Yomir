# -*- coding: utf-8 -*-
"""night60_scrape_left.py — N60：补抓 kanbun.info /syubu/ 剩余栏目成对文本。

N57 的抓取器凑满 1100 对即停（shikyo 102 + shijin 999），歴代/唐詩選内容页从未
访问、shijin 索引也有剩页。本夜任务书口径：来源只取 /syubu/ 剩余栏目
（唐詩選 toushisen_*、歴代 reki_*、詩人別 shijin_* 未抓完的页）。

解析与 N57 完全同款（genbun01 + yomi02/03 相邻对；剥 ruby/标签+去空白；
expected 一字不改）。去重：hakubun 不与 golden_3000 重复、不与本批重复；
缓冲目标 1200 对（建库时再裁到 1000）。
产物 eval/night60_scraped_left.json。
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
TARGET_PAIRS = 1200

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0[23]">(.*?)</div>', re.S)

SHIJIN_IDX = ["shijin_%s" % x for x in ("a", "ka", "sa", "ta", "ha", "ma", "ya", "ra")]
REKI_IDX = ["reki_%s" % x for x in ("banto", "chuto", "gen", "gi", "gokan", "hokuso",
                                    "kin", "kodai", "min", "naibokucho", "nanso",
                                    "seito", "shin01", "shin02", "shoto", "zenkan")]
NAV_PREFIXES = ("index", "sitemap", "kanshi", "reki_", "shijin_", "toushisen000",
                "shikyo000", "koji", "rongo", "about", "miscellaneous", "shochu")


def get(u, tries=3, timeout=30):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                          timeout=timeout).read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 + i * 2)
    print("[FAIL] %-40s %r" % (u.rsplit("/", 1)[-1], last), flush=True)
    return ""


def strip_white(s):
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^\d{2,3}(（\d{2}-\d{2}）)?", "", s)
    return s.strip()


def strip_yomi(s):
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def links_of(idx):
    t = get("https://kanbun.info/" + idx)
    if not t:
        return []
    out = []
    for m in re.finditer(r'href="((?:\.\./syubu/|\.\./koji/)?([a-z0-9_]+)\.html)"', t):
        name = m.group(2)
        if any(name.startswith(p) for p in NAV_PREFIXES):
            continue
        if name not in out:
            out.append(name)
    return out


def main():
    # 已抓过的页（N57 缓冲 + golden_3000 里出现过的 kanbun.info URL）
    prev_pages = set()
    for p in json.load(open(os.path.join(EV, "night57_scraped_syubu.json"),
                            encoding="utf-8")):
        prev_pages.add(p["source_url"].rsplit("/", 1)[-1].rsplit(".", 1)[0])
    golden = json.load(open(os.path.join(EV, "golden_3000.json"), encoding="utf-8"))
    seen_hb = {g["hakubun"].strip() for g in golden}
    for g in golden:
        u = g.get("source_url", "")
        if "/syubu/" in u:
            prev_pages.add(u.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    print("已抓/已入 golden 的 /syubu/ 页 %d 个" % len(prev_pages), flush=True)

    # 发现：shijin 剩页 → toushisen 内容页 → reki 内容页（shikyo 已全部抓过，跳过）
    pages = []
    seen_pg = set()

    def add(names, tag):
        for n in names:
            if n not in seen_pg and n not in prev_pages:
                seen_pg.add(n)
                pages.append((n, tag))

    for idx in SHIJIN_IDX:
        add(links_of("syubu/%s.html" % idx), "syubu_shijin")
    print("[discover] shijin 剩页 → %d" % len(pages), flush=True)
    n0 = len(pages)
    for name in links_of("syubu/toushisen000.html"):
        add([name], "syubu_toushisen")
    print("[discover] +toushisen → %d（+%d）" % (len(pages), len(pages) - n0), flush=True)
    n0 = len(pages)
    for idx in REKI_IDX:
        add(links_of("syubu/%s.html" % idx), "syubu_reki")
    print("[discover] +reki → %d（+%d）" % (len(pages), len(pages) - n0), flush=True)

    pairs = []
    pages_done = 0
    t0 = time.time()
    for name, src in pages:
        if len(pairs) >= TARGET_PAIRS:
            break
        t = get("https://kanbun.info/syubu/%s.html" % name)
        pages_done += 1
        if not t:
            continue
        n_pairs = len(pairs)
        for i, (g, y) in enumerate(PAIR_RX.findall(t), start=1):
            hb, yk = strip_white(g), strip_yomi(y)
            if not hb or not yk or "（" in hb or "）" in hb:
                continue
            if hb in seen_hb:
                continue
            seen_hb.add(hb)
            pairs.append({"id": "%s-%d" % (name, i),
                          "source_url": "https://kanbun.info/syubu/%s.html" % name,
                          "hakubun": hb, "expected_kakikudashi": yk,
                          "_src": src})
        if len(pairs) != n_pairs:
            print("  %-24s +%2d → %4d (%.0fs)"
                  % (name, len(pairs) - n_pairs, len(pairs), time.time() - t0), flush=True)
        time.sleep(0.4)

    by_src = {}
    for p in pairs:
        by_src[p["_src"]] = by_src.get(p["_src"], 0) + 1
    print("\n抓取完成：页 %d / 对 %d / %.0fs | 来源 %s"
          % (pages_done, len(pairs), time.time() - t0, by_src), flush=True)
    out = os.path.join(EV, "night60_scraped_left.json")
    json.dump(pairs, open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
