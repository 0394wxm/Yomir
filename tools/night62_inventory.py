# -*- coding: utf-8 -*-
"""night62_inventory.py — N62：用 sitemap.xml 盘点 kanbun.info 全站剩余可抓文本对。

背景：v2 探针（night62_probe_site.py）的链接爬链在 hop1 中断；sitemap.xml 实测
可用（185941 bytes），本脚本改为一次性取全站 URL，按栏目分类、减去已见页
（golden_4000 + N57/N60 缓冲池），每栏目抽样 4 页估密度 → 推算可得新对总量，
判定「golden_4000 + 6000 新对」目标是否可行、各栏目要补多少。

配对模式与 N57/N60 完全同款：genbun01 + yomi02/03 相邻对，剥 ruby/标签+去空白，
expected 一字不改。只读不写库。
产物 eval/night62_inventory.txt / night62_inventory.json。

v2（本轮）：栏目改为 sitemap 动态发现（首轮漏掉了 shibu01/shibu02/syubu02/
history 四个从未访问的栏目）；抽样页记录拒绝原因（dup_seen/括号/空 expected），
各栏目样本数按剩页规模分档。
"""
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.request
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
TAG_RX = re.compile(r"<[^>]+>")
PAIR_RX = re.compile(r'<div class="genbun01">(.*?)</div>\s*<div class="yomi0[23]">(.*?)</div>', re.S)

SECTIONS = ("syubu", "koji", "keibu", "miscellaneous")


def sample_n(fresh_n):
    """抽样页数：剩页 >100 的栏目取 5，>20 取 3，其余 2。"""
    return 5 if fresh_n > 100 else (3 if fresh_n > 20 else 2)


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


def page_key(url):
    """https://kanbun.info/<sec>/<name>.html -> (sec, name)；其余返回 None。"""
    m = re.match(r"https://kanbun\.info/([a-z0-9_]+)/([a-z0-9_]+)\.html$", url)
    return (m.group(1), m.group(2)) if m else None


def main():
    lines = []

    def log(s):
        lines.append(s)
        print(s, flush=True)

    # ---- 已见页 / 已见白文（口径与 night62_probe_site.py 一致） ----
    seen, seen_hb = set(), set()
    for x in json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8")):
        k = page_key(x.get("source_url", ""))
        if k:
            seen.add(k)
        seen_hb.add(x["hakubun"].strip())
    for fn in ("night57_scraped_syubu.json", "night60_scraped_left.json"):
        for x in json.load(open(os.path.join(EV, fn), encoding="utf-8")):
            k = page_key(x.get("source_url", ""))
            if k:
                seen.add(k)
            seen_hb.add(x["hakubun"].strip())
    log("已见页 %d 个、已见白文 %d 条（golden_4000 + N57/N60 缓冲池）"
        % (len(seen), len(seen_hb)))

    # ---- sitemap 全站 URL ----
    xml = get("https://kanbun.info/sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    log("sitemap.xml %d bytes → %d 条 URL" % (len(xml), len(urls)))
    by_sec = defaultdict(list)
    root_pages = []
    for u in urls:
        k = page_key(u)
        if k:
            by_sec[k[0]].append(k[1])
        else:
            root_pages.append(u)
    for sec in sorted(by_sec):
        log("  %-14s %4d 页" % (sec, len(by_sec[sec])))
    log("  (根目录)       %4d 条: %s" % (len(root_pages), root_pages[:8]))

    # ---- 剩页（按 (sec,name) 精确去已见） ----
    fresh = {}
    for sec, names in by_sec.items():
        fresh[sec] = [n for n in names if (sec, n) not in seen]

    # ---- 每栏目抽样估密度（均匀取 2-5 页） ----
    density = {}
    dynamic_secs = [s for s in sorted(by_sec) if s not in ("sitemap",)]
    for sec in dynamic_secs:
        fl = fresh.get(sec, [])
        if not fl:
            log("\n[%s] 剩页 0（已全部抓过，全站 %d 页）" % (sec, len(by_sec[sec])))
            density[sec] = {"fresh_pages": 0, "total_pages": len(by_sec[sec])}
            continue
        k = sample_n(len(fl))
        picks = sorted({fl[min(i * len(fl) // k, len(fl) - 1)] for i in range(k)},
                       key=fl.index)
        log("\n[%s] 剩页 %d/%d，抽样 %s" % (sec, len(fl), len(by_sec[sec]),
                                           ",".join(picks)))
        raws, usables, reasons = [], [], defaultdict(int)
        for name in picks:
            t = get("https://kanbun.info/%s/%s.html" % (sec, name))
            time.sleep(0.35)
            if not t:
                log("  %s: 抓取失败" % name)
                continue
            n_raw = len(PAIR_RX.findall(t))
            good = 0
            for g, y in PAIR_RX.findall(t):
                hb, yk = strip_white(g), strip_yomi(y)
                if not hb or not yk:
                    reasons["empty"] += 1
                elif "（" in hb or "）" in hb:
                    reasons["paren"] += 1
                elif hb in seen_hb:
                    reasons["dup_seen"] += 1
                else:
                    good += 1
                    seen_hb.add(hb)
            raws.append(n_raw)
            usables.append(good)
            log("  %-24s raw 对 %2d → 新可用 %2d  拒绝 %s"
                % (name, n_raw, good, dict(reasons) if reasons else ""))
        avg = sum(usables) / len(usables) if usables else 0.0
        density[sec] = {"fresh_pages": len(fl), "total_pages": len(by_sec[sec]),
                        "sampled": picks, "raw": raws, "usable": usables,
                        "reject": dict(reasons),
                        "avg_usable_per_page": round(avg, 2),
                        "projected_pairs": int(round(avg * len(fl)))}
        log("  → 平均 %.2f 对/页 × %d 页 ≈ %d 对"
            % (avg, len(fl), density[sec]["projected_pairs"]))

    total_proj = sum(d.get("projected_pairs", 0) for d in density.values())
    total_fresh = sum(d.get("fresh_pages", 0) for d in density.values())
    log("\n=== 结论 ===")
    log("剩页合计 %d（%s）" % (total_fresh,
        ", ".join("%s %d" % (s, density[s]["fresh_pages"])
                  for s in dynamic_secs if density[s]["fresh_pages"])))
    log("推算新对合计 ≈ %d（目标 6000 + 建库裁剪余量 → 缓冲目标 6800）" % total_proj)
    log("6000 目判定: %s" % ("可行" if total_proj >= 6800 else
                             ("勉强（需压满全部栏目并接受裁剪）" if total_proj >= 6200
                              else "不足，须如实记录缺口")))

    out = {"seen_pages": len(seen), "seen_hb": len(seen_hb),
           "sitemap_urls": len(urls),
           "by_sec_total": {s: len(v) for s, v in by_sec.items()},
           "root_pages": root_pages,
           "fresh_names": {s: fresh.get(s, []) for s in sorted(by_sec)},
           "fresh_counts": {s: len(fresh.get(s, [])) for s in sorted(by_sec)},
           "density": density, "projected_pairs": total_proj}
    json.dump(out, open(os.path.join(EV, "night62_inventory.json"), "w",
                        encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    with open(os.path.join(EV, "night62_inventory.txt"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("written: eval/night62_inventory.txt / night62_inventory.json", flush=True)


if __name__ == "__main__":
    main()
