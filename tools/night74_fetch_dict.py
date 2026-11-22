# -*- coding: utf-8 -*-
"""night74_fetch_dict.py — N74 ③ 逐条校对的取数器（GET-only，限速，断点续跑）。

对词库 500 条词形逐条抓 www.weblio.jp/content/<word>（含古語辞典/大辞泉/Wiktionary
等聚合），抽可见文本的「词典条目区」存 eval/night74_dict_cache/<idx3>.txt。
- 每个 GET 间隔 0.7s（礼貌限速；对 N71 的 CPU 零增量——纯网络等待）。
- 404 / 传输异常 / 无条目页都如实记录 status，不猜不编。
- 已有 <idx3>.txt 且含 URL 行的条目跳过（断点续跑）。
- kotobank.jp 全站 403（反爬拒绝），本夜记「来源不可达」，不再逐条重试。
用法: python -I tools/night74_fetch_dict.py [limit]   （limit 省略 = 全部 500）
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402

OUTDIR = os.path.join(ROOT, "eval", "night74_dict_cache")
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

MAXTEXT = 4000  # 条目区截断（控制后续人工阅读成本）


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
    """词条区 = 从第一个词典名行到「辞書ショートカット」前；找不到就从面包屑起。"""
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
    """返回 (status, final_url, bytes_n, region_text)。"""
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


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    n_done = n_skip = 0
    for i, e in enumerate(GLOSSARY_LEXICON):
        if i >= limit:
            break
        w = e.get("word", "")
        path = os.path.join(OUTDIR, "%03d.txt" % i)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                head = f.readline()
            if head.startswith("# URL"):
                n_skip += 1
                continue
        status, final_url, nbytes, region = fetch_one(w)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# URL %s\n# word %s\n# status %s bytes=%d\n\n" % (final_url, w, status, nbytes))
            f.write(region[:MAXTEXT] if region else "(no region)")
        n_done += 1
        if n_done % 25 == 0:
            print("fetched %d (idx %d, word_ok=%s, status=%s)" % (n_done, i, status == "OK", status), flush=True)
        time.sleep(0.7)
    print("done fetched=%d skipped=%d" % (n_done, n_skip))


if __name__ == "__main__":
    main()
