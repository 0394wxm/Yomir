# -*- coding: utf-8 -*-
"""night79_ruby.py — N79 ③ 深查：語料出处页（kanbun.info）の振り仮名で読みを確定する。

N76 §3.5 の方法の night79 版。argv で語を渡すと、golden_8165 の書き下し文に
その語を含む行（最大 3 行）の source_url を取得し、<ruby>〜<rt> ペアを抽出、
対象語の漢字を含むペアを出力する（語の読みが語料作者自身の ruby で取れる＝最強証拠）。

用法: python -I tools/night79_ruby.py 而る後 而ち 所以 ...
出力: 標準出力（UTF-8）＋ eval/night79_ruby_cache/<word>.txt（全 ruby ペア落盘）
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")
OUTDIR = os.path.join(EV, "night79_ruby_cache")
os.makedirs(OUTDIR, exist_ok=True)

RX = re.compile(r"<ruby>(.*?)<rp>.*?<rt>(.*?)</rt>", re.S)


def safe_name(w):
    return "".join(ch if ch.isascii() else ("x%04x" % ord(ch)) for ch in w)[:40]


def fetch_ruby(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
    return RX.findall(html)


def main():
    words = sys.argv[1:]
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    report = []
    for w in words:
        wchars = set(w) - set("されるときにをはがの")
        rows = []
        for g in golden:
            kkd = re.sub(r"\s+", "", g.get("expected_kakikudashi", ""))
            if w in kkd:
                rows.append(g)
        report.append("######## %s : corpus lines=%d" % (w, len(rows)))
        pairs_all = []
        for g in rows[:3]:
            url = g.get("source_url", "")
            if not url:
                report.append("  %s: no source_url" % g.get("id", ""))
                continue
            try:
                pairs = fetch_ruby(url)
                time.sleep(0.4)
            except Exception as ex:
                report.append("  %s (%s): FAIL %s" % (g.get("id", ""), url, ex))
                continue
            report.append("  %s (%s): %d ruby pairs" % (g.get("id", ""), url, len(pairs)))
            pairs_all.append("=== %s (%s) ===" % (g.get("id", ""), url))
            for base, rt in pairs:
                base, rt = base.strip(), rt.strip()
                pairs_all.append("%s=%s" % (base, rt))
                if any(ch in base for ch in wchars):
                    report.append("    %s=%s" % (base, rt))
        path = os.path.join(OUTDIR, safe_name(w) + ".txt")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(pairs_all) + "\n")
    print("\n".join(report))
    print("\nweblio batch progress:", len(os.listdir(os.path.join(EV, "night79_dict_cache"))))


if __name__ == "__main__":
    main()
