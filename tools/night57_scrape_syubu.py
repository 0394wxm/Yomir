# -*- coding: utf-8 -*-
"""night57_scrape_syubu.py — N57：抓 kanbun.info 新栏目（/syubu/ 詩経・漢詩）成对文本。

D16 的任务书口径复用：「expected 一字不改——全部来自页面 <div class="yomi02|yomi03">
原文，脚本只做剥 ruby/标签 + 去空白，不做任何替换」。

来源（sitemap 实测，均为 golden_2000 未覆盖的新栏目）：
  * 詩経 shikyo_*（reki_kodai 等歴代索引链接，経文气质）→ _src=syubu_shikyo
  * 詩人別索引 shijin_{a,ka,sa,ta,ha,ma,ya,ra} → 内容页 _src=syubu_shijin
  * 歴代索引 reki_* 的其它内容页 → _src=syubu_reki
  * 唐詩選 toushisen_v*（多为书籍介绍页，0 对则自然跳过）→ _src=syubu_toushisen

页面结构与 D16 抓的大学/孝経一致（genbun01 + yomi02/yomi03 相邻对）。
带缓存（抓过的页写进输出文件）、重试、限速 0.4s。
产物 eval/night57_scraped_syubu.json（目标 1100 对缓冲）。
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
TARGET_PAIRS = 1100

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0[23]">(.*?)</div>', re.S)


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


def links_of(idx, exclude_prefixes):
    t = get("https://kanbun.info/" + idx)
    if not t:
        return []
    out = []
    for m in re.finditer(r'href="((?:\.\./syubu/|\.\./koji/)?([a-z0-9_]+)\.html)"', t):
        name = m.group(2)
        if any(name.startswith(p) for p in exclude_prefixes):
            continue
        if name not in out:
            out.append(name)
    return out


def discover():
    """返回 [(page_name, src_tag)]（去重，shikyo 优先，其次 shijin，再歴代/唐詩選）。"""
    shijin_idx = ["shijin_%s" % x for x in ("a", "ka", "sa", "ta", "ha", "ma", "ya", "ra")]
    reki_idx = ["reki_%s" % x for x in ("banto", "chuto", "gen", "gi", "gokan", "hokuso",
                                        "kin", "kodai", "min", "naibokucho", "nanso",
                                        "seito", "shin01", "shin02", "shoto", "zenkan")]
    nav_prefixes = ("index", "sitemap", "kanshi", "reki_", "shijin_", "toushisen000",
                    "shikyo000", "koji", "rongo", "about", "miscellaneous", "shochu")
    out, seen = [], set()

    # 1. 詩経：全部 reki_* 索引里出现的 shikyo_* 页
    for idx in reki_idx:
        for name in links_of("syubu/%s.html" % idx, nav_prefixes):
            if name.startswith("shikyo") and name not in seen:
                seen.add(name)
                out.append((name, "syubu_shikyo"))
    n_shikyo = len(out)
    print("[discover] shikyo 页 %d" % n_shikyo, flush=True)

    # 2. 詩人別内容页
    for idx in shijin_idx:
        for name in links_of("syubu/%s.html" % idx, nav_prefixes):
            if name not in seen:
                seen.add(name)
                out.append((name, "syubu_shijin"))
    print("[discover] +shijin → %d（shijin %d）" % (len(out), len(out) - n_shikyo), flush=True)

    # 3. 歴代/唐詩選 索引里的其它内容页（toushisen_v* 等）
    for idx in ["toushisen000.html"] + ["%s.html" % i for i in reki_idx]:
        for name in links_of("syubu/" + idx, nav_prefixes):
            if name not in seen:
                seen.add(name)
                out.append((name, "syubu_reki"))
    print("[discover] +reki/toushisen → %d" % len(out), flush=True)
    return out


def main():
    pages = discover()
    pairs = []
    seen_hb = set()
    g2k = {x["hakubun"].strip() for x in json.load(
        open(os.path.join(EV, "golden_2000.json"), encoding="utf-8"))}
    seen_hb |= g2k
    pages_done = 0
    t0 = time.time()
    for name, src in pages:
        if len(pairs) >= TARGET_PAIRS:
            break
        t = get("https://kanbun.info/syubu/%s.html" % name)
        pages_done += 1
        if not t:
            continue
        n0 = len(pairs)
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
        if len(pairs) != n0:
            print("  %-24s +%2d → %4d (%.0fs)"
                  % (name, len(pairs) - n0, len(pairs), time.time() - t0), flush=True)
        time.sleep(0.4)

    print("\n抓取完成：页 %d / 对 %d / %.0fs" % (pages_done, len(pairs), time.time() - t0),
          flush=True)
    by_src = {}
    for p in pairs:
        by_src[p["_src"]] = by_src.get(p["_src"], 0) + 1
    print("来源分布:", by_src, flush=True)
    out = os.path.join(EV, "night57_scraped_syubu.json")
    json.dump(pairs, open(out, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
