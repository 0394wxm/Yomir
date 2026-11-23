# -*- coding: utf-8 -*-
"""night82_compact.py - N82 helper: shrink digest files to judgment tables
（night80_compact.py の night82 版）。

Keeps breadcrumb tail, dictionary section heads, reading lines and one or two
definition lines per entry; cuts Wikipedia/Wiktionary body entirely (page with
no real dictionary region gets a [no-real-dict-region] marker). HTTP404 entries
collapse to a single line. Output: eval/night82_compact_<start>.txt (UTF-8 CRLF).

Usage: python tools/night82_compact.py <start_rank>
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

WIKI_HEADS = ("ウィキペディア", "Wiktionary", "ウィクショナリー", "ウィキペディア小見出し辞書")
JUNK = ("索引トップ", "用語の索引", "ランキング", "凡例", "カテゴリー", "出典:",
        "この記事で示されている", "ご存知の方は", "関連することわざ", "関連する慣用句",
        "関連する英語表現")


def shrink(header, body):
    out = [header]
    status = "OK" if "status=OK" in header else ("HTTP404" if "HTTP404" in header else "?")
    deflines = 0
    for l in body:
        s = l.strip()
        if not s:
            continue
        if s.startswith("corpus:"):
            out.append("  corpus: " + s[7:].strip()[: (60 if status == "HTTP404" else 130)])
            continue
        if not s.startswith("|") or status == "HTTP404":
            continue
        c = s[1:].strip()
        if c.startswith("Weblio 辞書 >"):
            out.append("  [src] " + c.split(" > ")[-1][:70])
            continue
        if c.startswith(WIKI_HEADS):
            out.append("  [wikibody-cut] " + c[:20])
            break
        if "読み方：" in c or "読み方:" in c:
            out.append("  [read] " + c[:120])
            continue
        if any(c.startswith(j) for j in JUNK):
            continue
        if deflines < 2:
            out.append("  def: " + c[:120])
            deflines += 1
    if not any(x.startswith("  [src]") for x in out):
        out.append("  [no-real-dict-region]")
    return "\n".join(out)


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    src = os.path.join(EV, "night82_digest_%03d.txt" % start)
    text = open(src, encoding="utf-8").read()
    parts = re.split(r"\r?\n===", text)
    blocks = []
    for p in parts[1:]:
        lines = p.splitlines()
        header = "[" + lines[0].strip()
        blocks.append(shrink(header, lines[1:]))
    dst = os.path.join(EV, "night82_compact_%03d.txt" % start)
    with open(dst, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\r\n\r\n".join(blocks) + "\r\n")
    print("compact %d..%d written: %s (entries=%d)" % (start, start + len(blocks) - 1, dst, len(blocks)),
          flush=True)


if __name__ == "__main__":
    main()
