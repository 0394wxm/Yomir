# -*- coding: utf-8 -*-
"""night79_weblio2.py — N79 ③ 任意補查 fetcher（night79_weblio.py の自由語版）。

eval/night79_extra_queries.json の [{"word": ..., "note": ...}] を逐語
www.weblio.jp/content/<word> で取得し eval/night79_dict_cache/extra_<word>.txt に落盘。
词典の見出し語形が語料表記と異なる場合（而る後は など）の補查に使う。

用法: python -I tools/night79_weblio2.py
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
OUTDIR = os.path.join(EV, "night79_dict_cache")
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
MAXTEXT = 4000


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
    return [ln.strip() for ln in "".join(p.parts).splitlines() if ln.strip()]


def cut_region(lines):
    dictnames = (
        "デジタル大辞泉", "精選版 日本国語大辞典", "古語辞典", "日本語古語辞典",
        "Weblio古語辞典", "故事ことわざの辞典", "Wiktionary日本語版",
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


def safe_name(w):
    return "".join(ch if ch.isascii() else ("x%04x" % ord(ch)) for ch in w)[:40]


def main():
    qpath = os.path.join(EV, "night79_extra_queries.json")
    queries = json.load(open(qpath, encoding="utf-8"))
    for q in queries:
        w = q["word"]
        path = os.path.join(OUTDIR, "extra_" + safe_name(w) + ".txt")
        if os.path.exists(path):
            print("skip cached:", w)
            continue
        status, final_url, nbytes, region = fetch_one(w)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# URL %s\n# word %s note %s\n# status %s bytes=%d\n\n"
                    % (final_url, w, q.get("note", ""), status, nbytes))
            f.write(region[:MAXTEXT] if region else "(no region)")
        print("%-12s %s bytes=%d" % (status, w, nbytes), flush=True)
        time.sleep(0.7)


if __name__ == "__main__":
    main()
