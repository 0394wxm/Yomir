# -*- coding: utf-8 -*-
"""night62_scrape_10k.py — N62：kanbun.info 全站剩页文本对抓取（sitemap 盘点口径）。

夜62任务书：golden_4000 + 6000 新对，/syubu/ 剩约 270 页优先，其余栏目补。
实测盘点（night62_inventory.py）：全站剩页 1279，推算新对 ~3100 < 6000。
本脚本把剩页**全部**抓完（syubu → shibu02 → syubu02 → shibu01 → koji → keibu →
history → miscellaneous），产物求全求实：

  * 每条带 _quality：ok / paren（白文含（），N57 起按约定拒绝；本夜只标记不丢，
    是否启用留给用户拍板）；expected 空的对不入库。
  * 去重只对 golden_4000 白文（3975 唯一）+ 本批内重复；池文件（day16/N57/N60）
    的剩余对**不算已用**，留给建库脚本统一合并去重。
  * 断点续跑：eval/night62_scrape_10k_state.json 记已抓页，重跑自动续。

产物 eval/night62_scraped_10k.json + night62_scrape_10k.txt。
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

PRIORITY = ["syubu", "shibu02", "syubu02", "shibu01", "koji", "keibu",
            "history", "miscellaneous"]
DELAY = 0.35
CKPT_EVERY = 20


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
    s = re.sub(r"<rt>.*?</rt>", "", s, flags=re.S)
    s = re.sub(r"<rp>.*?</rp>", "", s, flags=re.S)
    s = TAG_RX.sub("", s)
    s = html_mod.unescape(s)
    return re.sub(r"[\r\n\t]+", "", s).strip()


def load_state():
    st_p = os.path.join(EV, "night62_scrape_10k_state.json")
    if os.path.exists(st_p):
        st = json.load(open(st_p, encoding="utf-8"))
        return st, st_p
    return {"done": []}, st_p


def main():
    inv = json.load(open(os.path.join(EV, "night62_inventory.json"), encoding="utf-8"))
    g4 = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    g4_hb = {x["hakubun"].strip() for x in g4}
    print("golden_4000 白文唯一 %d 条（去重基准）" % len(g4_hb), flush=True)

    st, st_p = load_state()
    done = set(st.get("done", []))
    pair_p = os.path.join(EV, "night62_scraped_10k.json")
    pairs = []
    if os.path.exists(pair_p):
        pairs = json.load(open(pair_p, encoding="utf-8"))
        print("续跑：已有 %d 对、已抓 %d 页" % (len(pairs), len(done)), flush=True)
    batch_hb = {p["hakubun"] for p in pairs}

    queue = []
    for sec in PRIORITY:
        for name in inv["fresh_names"].get(sec, []):
            queue.append((sec, name))
    print("待抓剩页 %d（已抓 %d）" % (len(queue) - len(done), len(done)), flush=True)

    lines = []
    t0 = time.time()
    pages_done = 0
    stat = {"ok": 0, "paren": 0, "dup_golden": 0, "dup_batch": 0,
            "paren_dup_golden": 0, "paren_dup_batch": 0, "empty": 0}
    sec_stat = {}
    for sec, name in queue:
        key = "%s/%s" % (sec, name)
        if key in done:
            continue
        t = get("https://kanbun.info/%s/%s.html" % (sec, name))
        pages_done += 1
        d = sec_stat.setdefault(sec, {"pages": 0, "ok": 0, "paren": 0})
        if not t:
            d["pages"] += 1
            continue
        d["pages"] += 1
        n_add = 0
        for i, (g, y) in enumerate(PAIR_RX.findall(t), start=1):
            hb, yk = strip_white(g), strip_yomi(y)
            if not hb or not yk:
                stat["empty"] += 1
                continue
            q = "paren" if ("（" in hb or "）" in hb) else "ok"
            if hb in g4_hb:
                stat["paren_dup_golden" if q == "paren" else "dup_golden"] += 1
                continue
            if hb in batch_hb:
                stat["paren_dup_batch" if q == "paren" else "dup_batch"] += 1
                continue
            batch_hb.add(hb)
            pairs.append({"id": "%s-%d" % (name, i),
                          "source_url": "https://kanbun.info/%s/%s.html" % (sec, name),
                          "hakubun": hb, "expected_kakikudashi": yk,
                          "_src": sec, "_quality": q})
            stat[q] += 1
            d[q] += 1
            n_add += 1
        done.add(key)
        if n_add or stat["ok"] + stat["paren"] == n_add:
            lines.append("%-16s %-24s +%d (ok+%d paren+%d) 累计 ok %d paren %d (%.0fs)"
                         % (sec, name, n_add, d["ok"], d["paren"],
                            stat["ok"], stat["paren"], time.time() - t0))
            print(lines[-1], flush=True)
        if pages_done % CKPT_EVERY == 0:
            json.dump(pairs, open(pair_p, "w", encoding="utf-8", newline="\n"),
                      ensure_ascii=False, indent=1)
            json.dump({"done": sorted(done)}, open(st_p, "w", encoding="utf-8",
                                                   newline="\n"), ensure_ascii=False, indent=1)
            print("[ckpt] %d 页 / %d 对 (%.0fs)" % (len(done), len(pairs), time.time() - t0),
                  flush=True)
        time.sleep(DELAY)

    json.dump(pairs, open(pair_p, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    json.dump({"done": sorted(done)}, open(st_p, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)

    print("\n=== 抓取完成：页 %d / 对 %d（ok %d + paren %d）/ %.0fs ==="
          % (len(done), len(pairs), stat["ok"], stat["paren"], time.time() - t0), flush=True)
    for sec, d in sec_stat.items():
        print("  %-14s 页 %4d | ok %4d | paren %4d"
              % (sec, d["pages"], d["ok"], d["paren"]), flush=True)
    print("拒绝：dup_golden %d / dup_batch %d / paren_dup_golden %d / paren_dup_batch %d / empty %d"
          % (stat["dup_golden"], stat["dup_batch"], stat["paren_dup_golden"],
             stat["paren_dup_batch"], stat["empty"]), flush=True)
    lines.append("=== 抓取完成：页 %d / 对 %d（ok %d + paren %d）/ %.0fs ==="
                 % (len(done), len(pairs), stat["ok"], stat["paren"], time.time() - t0))
    lines.append("拒绝：" + json.dumps(stat, ensure_ascii=False))
    with open(os.path.join(EV, "night62_scrape_10k.txt"), "a", encoding="utf-8",
              newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("written:", pair_p, flush=True)


if __name__ == "__main__":
    main()
