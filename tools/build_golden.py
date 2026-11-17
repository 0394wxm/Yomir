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

# 10 个故事页（故事名言，均为古文散文；出处页内注明）——Night1-3 的 10 页基础
BASE_PAGES = [
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

# Night4: 五十音分类索引页（koji00a あ行 … koji00rongo 論語），从中汇总全部故事页
CATEGORY_PAGES = [
    "https://kanbun.info/koji/koji00a.html",
    "https://kanbun.info/koji/koji00ka.html",
    "https://kanbun.info/koji/koji00sa.html",
    "https://kanbun.info/koji/koji00ta.html",
    "https://kanbun.info/koji/koji00na.html",
    "https://kanbun.info/koji/koji00ha.html",
    "https://kanbun.info/koji/koji00ma.html",
    "https://kanbun.info/koji/koji00ya.html",
    "https://kanbun.info/koji/koji00ra.html",
    "https://kanbun.info/koji/koji00rongo.html",
]


def discover_pages():
    """BASE_PAGES 优先（保证 Night1-3 的 50 条子集稳定），再从分类页发现其余故事页。"""
    import re as _re
    import time as _t
    import urllib.request as _rq

    pages = list(BASE_PAGES)
    seen = {pid for pid, _ in pages}
    for cat in CATEGORY_PAGES:
        html_txt = None
        for attempt in range(3):
            try:
                req = _rq.Request(cat, headers={"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"})
                with _rq.urlopen(req, timeout=45) as r:
                    html_txt = r.read().decode("utf-8", errors="replace")
                break
            except Exception as e:
                print("[CAT-RETRY] %s attempt %d: %r" % (cat.rsplit('/', 1)[-1], attempt + 1, e))
                _t.sleep(3)
        if not html_txt:
            print("[CAT-SKIP] %s" % cat.rsplit('/', 1)[-1])
            continue
        # 分类页链接两种形态：../koji/xxx.html（索引页）与裸 xxx.html（同目录）
        for m in _re.finditer(r'href="(?:\.\./koji/)?([a-z0-9_]+)\.html"', html_txt):
            pid = m.group(1)
            if pid.startswith("koji00") or pid in ("koji", "index") or pid in seen:
                continue
            seen.add(pid)
            pages.append((pid, "https://kanbun.info/koji/%s.html" % pid))
    print("[discover] total story pages:", len(pages))
    return pages

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
    total_cap = int(os.environ.get("GOLDEN_TOTAL", "200"))
    pages = discover_pages()
    entries = []
    for pid, url in pages:
        if len(entries) >= total_cap:
            break
        try:
            page = fetch(url)
        except Exception as e:
            print("[SKIP] %s: fetch failed %r" % (pid, e))
            continue
        pairs = PAIR_RX.findall(page)
        if not pairs:
            print("[SKIP] %s: no genbun01/yomi02 pairs found" % pid)
            continue
        # 每页取前 N 对干净文本；白文混入读音注记（含全角括号）的丢弃
        n = 0
        for i, (genbun, yomi) in enumerate(pairs, start=1):
            if n >= per_page or len(entries) >= total_cap:
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
        print("[OK] %s: %d pairs (total %d)" % (pid, n, len(entries)))
    print("total entries:", len(entries))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("written:", out_path)


if __name__ == "__main__":
    main()
