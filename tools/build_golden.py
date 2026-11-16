# -*- coding: utf-8 -*-
"""
build_golden.py — 从 Web漢文大系 (kanbun.info) 抓 10 条 白文+書き下し文 成对文本，
生成 eval/golden.json。

每条: { id, source_url, hakubun, expected_kakikudashi }
- hakubun: 页面 <div class="genbun01"> 里的白文（去标签）
- expected_kakikudashi: 紧随其后的 <div class="yomi02">，剥掉 ruby 注音只留正文

只抓取事实文本，不改写 expected 来凑 UD-Kundoku 输出。
"""
import html
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# 10 个故事页（故事名言，均为古文散文；出处页内注明）
PAGES = [
    ("mujun", "https://kanbun.info/koji/mujun.html"),        # 矛盾（韓非子）
    ("dasoku", "https://kanbun.info/koji/dasoku.html"),      # 蛇足（史記）
    ("chosan", "https://kanbun.info/koji/chosan.html"),      # 朝三暮四（列子）
    ("saio", "https://kanbun.info/koji/saio.html"),          # 塞翁が馬（淮南子）
    ("shimen", "https://kanbun.info/koji/shimen.html"),      # 四面楚歌（史記）
    ("toranoi", "https://kanbun.info/koji/toranoi.html"),    # 虎の威を借る（戦国策）
    ("garyo", "https://kanbun.info/koji/garyo.html"),        # 画竜点睛（歴代名画記）
    ("shushu", "https://kanbun.info/koji/shushu.html"),      # 守株（韓非子）
    ("gojippo", "https://kanbun.info/koji/gojippo.html"),    # 五十歩百歩（孟子）
    ("keiko", "https://kanbun.info/koji/keiko.html"),        # 鶏口牛後（戦国策）
]

TAG_RX = re.compile(r"<[^>]+>")
RT_RX = re.compile(r"<rt>.*?</rt>", re.S)
RP_RX = re.compile(r"<rp>.*?</rp>", re.S)
PAIR_RX = re.compile(
    r'<div class="genbun01">(.*?)</div>\s*<div class="yomi02">(.*?)</div>',
    re.S,
)


def strip_white(s: str) -> str:
    s = re.sub(r"〔[^〕]*〕", "", s)  # 去掉编辑性方括号补充
    s = TAG_RX.sub("", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", "", s)  # 白文去掉全部空白（原页面的换行/缩进）
    return s.strip()


def strip_yomi(s: str) -> str:
    s = RT_RX.sub("", s)
    s = RP_RX.sub("", s)
    s = TAG_RX.sub("", s)
    s = html.unescape(s)
    s = re.sub(r"[\r\n\t]+", "", s)
    return s.strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "eval", "golden.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    per_page = int(os.environ.get("GOLDEN_PER_PAGE", "5"))
    entries = []
    for pid, url in PAGES:
        try:
            page = fetch(url)
        except Exception as e:
            print("[SKIP] %s: fetch failed %r" % (pid, e))
            continue
        pairs = PAIR_RX.findall(page)
        if not pairs:
            print("[SKIP] %s: no genbun01/yomi02 pairs found" % pid)
            continue
        # 每页取前 N 对干净文本（NIGHT3: 5 对/页 × 10 页 = 50 条）；
        # 白文混入读音注记（含全角括号）的丢弃
        n = 0
        for i, (genbun, yomi) in enumerate(pairs, start=1):
            if n >= per_page:
                break
            hakubun = strip_white(genbun)
            kakikudashi = strip_yomi(yomi)
            if not hakubun or not kakikudashi:
                continue
            if "（" in hakubun or "）" in hakubun:
                continue
            entries.append({
                "id": "%s-%d" % (pid, i),
                "source_url": url,
                "hakubun": hakubun,
                "expected_kakikudashi": kakikudashi,
            })
            n += 1
        print("[OK] %s: %d pairs" % (pid, n))
    print("total entries:", len(entries))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("written:", out_path)


if __name__ == "__main__":
    main()
