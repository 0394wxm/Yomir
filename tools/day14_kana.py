# -*- coding: utf-8 -*-
"""day14_kana.py — D14 第三步：kana->kanji 候选的 1:1 对应检查。

思路（Rule D 的推广）：
  expected 把某词写成汉字 Y，引擎写成假名 X。
  如果 got 里 Y 几乎不出现、而 X 出现次数与 expected 里 Y 的次数接近，
  就说明这是一个**系统性的一对一映射**，可以做替换规则。

对每个候选 (X 假名串 -> Y 汉字) 输出：
  exp_Y  expected 里 Y 的次数
  got_Y  输出里 Y 的次数        （越小越好：说明引擎不用这个汉字）
  got_X  输出里 X 的次数
  exp_X  expected 里 X 的次数     （越大越危险：说明 expected 也用它）
  ratio  got_X / exp_Y           （接近 1 表示一对一）

输出 eval/day14_kana.json。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


# (假名串, 汉字, 说明)
CANDIDATES = [
    ("また", "亦", "副词「也」"),
    ("また", "又", "副词「又」"),
    ("みな", "皆", "副词「皆」"),
    ("すでに", "既", "副词「既」"),
    ("ただ", "唯", "副词「唯」"),
    ("なお", "猶", "副词「犹」"),
    ("なかれ", "勿", "禁止「勿」"),
    ("なかれ", "毋", "禁止「毋」"),
    ("あに", "豈", "反语「岂」"),
    ("いやしくも", "苟", "假定「苟」"),
    ("いずくんぞ", "焉", "疑问「焉」"),
    ("なんぞ", "焉", "疑问「焉」"),
    ("ごとし", "如", "比况「如」"),
    ("ごとく", "如", "比况「如」"),
    ("ごとく", "若", "比况「若」"),
    ("およそ", "凡", "副词「凡」"),
    ("たとひ", "縦", "假定「縦」"),
    ("もし", "若", "假定「若」"),
    ("ここに", "茲", "指示「茲」"),
    ("すなはち", "即", "即「即」"),
    ("すなわち", "即", "即「即」"),
]


def main():
    with open(os.path.join(EV, "day11_results_1000.json"), encoding="utf-8") as f:
        doc = json.load(f)
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    got_all = "".join(norm(r["udkundoku_kakikudashi"]) for r in rows)
    exp_all = "".join(norm(r["expected_kakikudashi"]) for r in rows)
    print("语料：got %d 字 / exp %d 字（%d 条）\n" % (len(got_all), len(exp_all), len(rows)),
          flush=True)

    print("%-12s %-4s %6s %6s %6s %6s %7s" %
          ("kana", "kanji", "exp_Y", "got_Y", "got_X", "exp_X", "ratio"), flush=True)
    out = []
    for kana, kanji, note in CANDIDATES:
        exp_y = exp_all.count(kanji)
        got_y = got_all.count(kanji)
        got_x = got_all.count(kana)
        exp_x = exp_all.count(kana)
        ratio = round(got_x / exp_y, 3) if exp_y else None
        print("%-12s %-4s %6d %6d %6d %6d %7s" %
              (kana, kanji, exp_y, got_y, got_x, exp_x, ratio), flush=True)
        out.append({"kana": kana, "kanji": kanji, "note": note, "exp_kanji": exp_y,
                    "got_kanji": got_y, "got_kana": got_x, "exp_kana": exp_x,
                    "ratio": ratio})

    # 再扫一遍：哪些 2 字假名串在 exp 里几乎不出现而在 got 里很多
    print("\n=== 2-3 字假名串：got 多 / exp 少（top 30） ===", flush=True)
    kana_re = re.compile(r"[\u3041-\u309f\u30a0-\u30ff]{2,3}")
    gc = collections.Counter(kana_re.findall(got_all))
    ec = collections.Counter(kana_re.findall(exp_all))
    ranked = [(s, n, ec.get(s, 0)) for s, n in gc.items() if n >= 15 and ec.get(s, 0) * 4 < n]
    ranked.sort(key=lambda x: -(x[1] - x[2]))
    for s, n, e in ranked[:30]:
        print("  %-6s got %4d  exp %4d  (ratio %.2f)" % (s, n, e, e / n), flush=True)

    with open(os.path.join(EV, "day14_kana.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"candidates": out, "kana_got_heavy": ranked[:60]}, f,
                  ensure_ascii=False, indent=1)
    print("\nwritten: eval/day14_kana.json", flush=True)


if __name__ == "__main__":
    main()
