# -*- coding: utf-8 -*-
"""night80_weblio.py — N80 ③ 逐条研究の取数器（N74 fetch_dict の night79 版）。

eval/night80_candidates.json の候補（頻度順）を input に、
www.weblio.jp/content/<word> 聚合ページを GET し、可視テキストの「辞書条目区」を
eval/night80_dict_cache/cand_<rank3>_<word>.txt に保存する。
- GET 間隔 0.7s（礼儀レート制限。N71 は OCR で満负荷——CPU 増分ゼロ、純网络待ち）。
- 404 / 伝送異常 / 無条目ページは status にありのまま記録（推測しない）。
- キャッシュ済み（# URL 行あり）はスキップ＝断点再開。
- kotobank.jp は 403 反爬、goo はタイムアウト（N74 実測）——本夜は再試行しない。
用法: python -I tools/night80_weblio.py <start_rank> [count]   （rank は 0 始まり）
"""
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")
OUTDIR = os.path.join(EV, "night80_dict_cache")
os.makedirs(OUTDIR, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.8,en;q=0.7",
    "Connection": "close",
}

MAXTEXT = 4000  # 条目区截断（N74 と同じ）


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        elif tag in ("p", "div", "li", "tr", "br", "h1", "h2", "h3", "h4", "table", "ul", "dt", "dd"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        elif tag in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "table", "ul", "dt", "dd"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def visible_text(html):
    p = Visible()
    p.feed(html)
    lines = []
    for ln in "".join(p.parts).splitlines():
        ln = ln.strip()
        if ln:
            lines.append(ln)
    return lines


def cut_region(lines):
    """词条区 = 从第一个词典名行到「辞書ショートカット」前（N74 と同じ）。"""
    dictnames = (
        "デジタル大辞泉", "精選版 日本国語大辞典", "古語辞典", "日本語古語辞典",
        "Weblio古語辞典", "故事ことわざの辞典", " Wiktionary日本語版",
        "Wiktionary日本語版", "日本語WordNet", "ウィキペディア小見出し辞書",
        "Weblio日本語例文用例辞書", "故事ことわざ辞典",
    )
    start = end = None
    for i, ln in enumerate(lines):
        if start is None and any(ln == d or ln.startswith(d) for d in dictnames):
            start = i
        if ln == "辞書ショートカット":
            end = i
            break
    if start is None:
        for i, ln in enumerate(lines):
            if ln.startswith("Weblio 辞書 >"):
                start = i
                break
    if start is None:
        start = 0
    if end is None or end <= start:
        end = min(start + 120, len(lines))
    return "\n".join(lines[start:end])


def fetch_one(w):
    url = "https://www.weblio.jp/content/" + urllib.parse.quote(w.strip())
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
            body = resp.read()
        status = "OK"
    except urllib.error.HTTPError as e:
        return ("HTTP%d" % e.code, url, 0, "")
    except Exception as e:
        return ("ERR:%s" % type(e).__name__, url, 0, "")
    html = body.decode("utf-8", "replace")
    lines = visible_text(html)
    region = cut_region(lines)
    if "の意味や使い方" not in " ".join(lines[:3]) and len(region) < 80:
        status = "NO_CONTENT"
    return (status, resp.geturl(), len(body), region)


def cand_path(rank, word):
    safe = "".join(ch if ch.isascii() or ch.isalnum() else "_" for ch in word)[:24]
    return os.path.join(OUTDIR, "cand_%03d_%s.txt" % (rank, safe or "noname"))


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    cands = json.load(open(os.path.join(EV, "night80_candidates.json"),
                           encoding="utf-8"))["candidates"]
    batch = cands[start:start + count]
    n_done = n_skip = 0
    for j, c in enumerate(batch):
        rank = start + j
        w = c["word"]
        path = cand_path(rank, w)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                head = f.readline()
            if head.startswith("# URL"):
                n_skip += 1
                continue
        status, final_url, nbytes, region = fetch_one(w)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# URL %s\n# rank %d word %s freq %d\n# status %s bytes=%d\n\n"
                    % (final_url, rank, w, c.get("freq", 0), status, nbytes))
            f.write(region[:MAXTEXT] if region else "(no region)")
        n_done += 1
        if n_done % 10 == 0:
            print("fetched %d (rank %d, %s, status=%s)" % (n_done, rank, status == "OK", status),
                  flush=True)
        time.sleep(0.7)
    print("done fetched=%d skipped=%d (rank %d..%d)" % (n_done, n_skip, start, start + len(batch) - 1),
          flush=True)


if __name__ == "__main__":
    main()
