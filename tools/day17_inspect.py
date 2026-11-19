# -*- coding: utf-8 -*-
"""day17_inspect.py — D17：逐条看候选的 got vs expected，确认改写方向。

打印每类候选的若干实例：白文片段 / expected / got / 假名出现位置。
只读。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def show(rows, kana, guard_chars, limit=4, tag=""):
    print("\n===== %s  (假名 %r, 白文含 %s) =====" % (tag, kana, "/".join(guard_chars)),
          flush=True)
    n = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        if kana not in got:
            continue
        if guard_chars and not any(g in hb for g in guard_chars):
            continue
        i = got.find(kana)
        print("  id=%s" % r["id"], flush=True)
        print("    hb  %s" % hb[:70], flush=True)
        print("    exp %s   ← 含目标字: %s" % (exp[:70],
              [c for c in guard_chars if c in exp]), flush=True)
        print("    got ...%s...  [pos %d]" % (got[max(0, i - 18):i + 22], i), flush=True)
        n += 1
        if n >= limit:
            break
    print("  （共展示 %d 条）" % n, flush=True)


def main():
    doc = json.load(open(os.path.join(EV, "day16_results_2000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    show(rows, "また", ("亦",), 4, "また→亦た")
    show(rows, "また", ("又",), 4, "また→又")
    show(rows, "いかん", ("何",), 4, "いかん→如何")
    show(rows, "べき", ("可",), 5, "べき→可き")
    show(rows, "べし", ("可",), 4, "べし→可し")
    show(rows, "べから", ("可",), 4, "べから→可から")

    # なし 的情况：exp 有 莫し 而 got 是 無し 的例子
    print("\n===== 莫：exp 有莫、got 有無し =====", flush=True)
    n = 0
    for r in rows:
        exp = norm(r["expected_kakikudashi"])
        got = norm(r["udkundoku_kakikudashi"])
        if "莫" in exp and "無し" in got:
            print("  id=%s" % r["id"], flush=True)
            print("    hb  %s" % norm(r["hakubun"])[:70], flush=True)
            print("    exp %s" % exp[:70], flush=True)
            print("    got %s" % got[:70], flush=True)
            n += 1
            if n >= 4:
                break
    print("  （共展示 %d 条）" % n, flush=True)


if __name__ == "__main__":
    main()
