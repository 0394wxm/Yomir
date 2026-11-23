# -*- coding: utf-8 -*-
"""night74_fetch_test.py — 抓 1 页 www.weblio 看结构 + 复测 kotobank（完整浏览器头）。

输出: eval/night74_dict_cache/struct_test/ 目录
  weblio_nochi.html   原始 HTML（分析结构用）
  weblio_nochi.txt    去 script/style 后的可见文本（前 8000 字）
  kotobank_nochi.txt  补头重试的结果（状态+文本前 3000 字）
"""
import os
import ssl
import urllib.request
import urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "eval", "night74_dict_cache", "struct_test")
os.makedirs(OUTDIR, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

UA_FULL = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "ja,en-US;q=0.8,en;q=0.7",
    "Connection": "close",
}


def get(url, headers=None):
    h = dict(UA_FULL)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
        return resp.read()


class TextExtract(HTMLParser):
    """去 script/style/noscript，收集可见文本。"""

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.out = []
        self.marks = []  # h2/h3 标题（词典名）

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        if tag in ("h2", "h3", "h4"):
            self.marks.append("<%s>" % tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        if tag in ("h2", "h3", "h4"):
            self.marks.append("</%s>" % tag)
        if tag in ("p", "div", "li", "tr", "br", "h2", "h3", "h4"):
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)
            if self.marks and self.marks[-1].startswith("<"):
                self.out.append(" [MARK] ")


def fetch_nochi():
    w = urllib.parse.quote("乃ち")
    body = get("https://www.weblio.jp/content/" + w)
    html = body.decode("utf-8", "replace")
    with open(os.path.join(OUTDIR, "weblio_nochi.html"), "w", encoding="utf-8") as f:
        f.write(html)
    p = TextExtract()
    p.feed(html)
    text = "".join(p.out)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    with open(os.path.join(OUTDIR, "weblio_nochi.txt"), "w", encoding="utf-8") as f:
        f.write(text[:8000])
    print("weblio bytes=%d textlen=%d" % (len(body), len(text)))


def fetch_kotobank():
    w = urllib.parse.quote("乃ち")
    try:
        body = get("https://kotobank.jp/word/" + w)
        html = body.decode("utf-8", "replace")
        p = TextExtract()
        p.feed(html)
        text = "".join(p.out)
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        with open(os.path.join(OUTDIR, "kotobank_nochi.txt"), "w", encoding="utf-8") as f:
            f.write("STATUS=200 bytes=%d\n%s" % (len(body), text[:3000]))
        print("kotobank bytes=%d" % len(body))
    except Exception as e:
        with open(os.path.join(OUTDIR, "kotobank_nochi.txt"), "w", encoding="utf-8") as f:
            f.write("ERROR: %r" % (e,))
        print("kotobank error", repr(e))


if __name__ == "__main__":
    fetch_nochi()
    fetch_kotobank()
