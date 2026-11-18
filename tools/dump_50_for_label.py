# -*- coding: utf-8 -*-
"""dump_50_for_label.py — 导出 D5 人工标注用的 50 条（分类器结果 + got/expected 对齐）。

抽样规则（可复现）：night5_results_full_v3.json 的 200 条按 id 排序后取第 1,5,9,...（等距 4），
共 50 条。这样覆盖全部语料而不是只看前 50 条。

输出 eval/day5_label_50.tsv（id / 分类器判定 / got / expected）
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        rows = json.load(f)["results"]
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3_classified.json"), encoding="utf-8") as f:
        cls = json.load(f)
    cats = {e["id"]: e["cats"] for e in cls["per_entry"]}

    rows = sorted(rows, key=lambda r: r["id"])
    idx = list(range(0, len(rows), 4))[:50]
    pick = [rows[i] for i in idx]

    out = os.path.join(ROOT, "eval", "day5_label_50.tsv")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("id\tclassifier\tgot\texpected\n")
        for r in pick:
            got = r.get("udkundoku_kakikudashi_norm") or r.get("udkundoku_kakikudashi", "")
            fh.write("%s\t%s\t%s\t%s\n" % (r["id"], ",".join(cats.get(r["id"], [])), got, r["expected_kakikudashi"]))
    print("抽样 %d 条（等距 4，按 id 排序），written: %s" % (len(pick), out))
    for r in pick[:5]:
        print(" ", r["id"], cats.get(r["id"]))


if __name__ == "__main__":
    main()
