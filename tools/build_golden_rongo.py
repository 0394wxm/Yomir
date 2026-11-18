# -*- coding: utf-8 -*-
"""
build_golden_rongo.py — 从 Web漢文大系 論語部抓 白文+書き下し文 成对文本，
生成 eval/golden_rongo.json（Night 23：分文体评测的数据落地，Night 21 §5 顺延项）。

页面结构（tools/night23_probe_rongo*.py 实测）：
  篇索引 rongo01.html .. rongo20.html（20 篇）
  章节页 rongo0101.html 等（篇+章 4 位数），每页一对：
    <div class="genbun01">001（01-01）<br/>子曰、學而…</div>
    <div class="yomi03"><ruby>子<rp>（</rp><rt>し</rt>…</div>
  注意是 yomi03（論語部），故事部是 yomi02；genbun01 带编号行要剥掉。

每条: { id, source_url, pian, hakubun, expected_kakikudashi }
只抓取事实文本，不改写 expected 来凑 UD-Kundoku 输出。
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
COUNTER_RX = re.compile(r"^\d{3}（\d{2}-\d{2}）")
PAIR_RX = re.compile(
    r'<div class="genbun01">(.*?)</div>\s*<div class="yomi03">(.*?)</div>',
    re.S,
)
CHAPTER_RX = re.compile(r'href="(?:\.\./keibu/)?(rongo(\d{2})(\d{2}))\.html"')


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_retry(url, attempts=3):
    for i in range(attempts):
        try:
            return fetch(url)
        except Exception as e:
            print("[RETRY] %s attempt %d: %r" % (url.rsplit("/", 1)[-1], i + 1, e))
            time.sleep(3)
    return None


def strip_white(s: str) -> str:
    s = re.sub(r"〔[^〕]*〕", "", s)
    s = TAG_RX.sub("", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", "", s)
    s = COUNTER_RX.sub("", s)  # 剥「001（01-01）」编号行（strip 后已无空白，贴在正文前）
    return s.strip()


def strip_yomi(s: str) -> str:
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html.unescape(s)
    s = re.sub(r"[\r\n\t]+", "", s)
    return s.strip()


def main():
    per_pian = int(os.environ.get("RONGO_PER_PIAN", "6"))
    pian_range = range(1, 21)

    # 1) 篇索引 → 章节页清单（按篇分组，篇内按章排序）
    pian_chapters = {}
    for pian in pian_range:
        idx_url = "https://kanbun.info/keibu/rongo%02d.html" % pian
        txt = fetch_retry(idx_url)
        if not txt:
            print("[SKIP] index rongo%02d" % pian)
            continue
        found = set()
        for m in CHAPTER_RX.finditer(txt):
            pid, p, c = m.group(1), int(m.group(2)), int(m.group(3))
            if p == pian:  # 只要本篇的章页（索引里会混其它篇的引用）
                found.add((pid, c))
        chapters = sorted(found, key=lambda t: t[1])[:per_pian]
        pian_chapters[pian] = chapters
        print("[IDX] pian %02d: %d chapters on page, taking %d" % (pian, len(found), len(chapters)))
        time.sleep(0.2)

    # 2) 章节页抓取
    entries = []
    fail = 0
    for pian in pian_range:
        for pid, _c in pian_chapters.get(pian, []):
            url = "https://kanbun.info/keibu/%s.html" % pid
            page = fetch_retry(url)
            if not page:
                fail += 1
                continue
            pairs = PAIR_RX.findall(page)
            if not pairs:
                print("[SKIP] %s: no genbun01/yomi03 pair" % pid)
                fail += 1
                continue
            for i, (genbun, yomi) in enumerate(pairs, start=1):
                hakubun = strip_white(genbun)
                kakikudashi = strip_yomi(yomi)
                if not hakubun or not kakikudashi:
                    continue
                if "（" in hakubun or "）" in hakubun:  # 正文混入注记（编号行已剥）
                    print("[SKIP] %s-%d: paren in hakubun" % (pid, i))
                    continue
                entries.append({
                    "id": "%s-%d" % (pid, i),
                    "source_url": url,
                    "pian": pian,
                    "hakubun": hakubun,
                    "expected_kakikudashi": kakikudashi,
                })
            time.sleep(0.2)
    print("total entries:", len(entries), "fetch failures:", fail)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    out_name = args[0] if args else "golden_rongo.json"
    out_path = os.path.join(ROOT, "eval", out_name)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("written:", out_path)


if __name__ == "__main__":
    main()
