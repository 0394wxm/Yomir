# -*- coding: utf-8 -*-
"""recalc_distances.py — 就地把结果文件的 exact/edit_distance 重算成空白归一化口径（NIGHT4）。

背景：got 里句读换行是显示产物，旧口径把它们算进编辑距离（475 条噪声块）。
本脚本读取 results 里已有的原始输出，重新归一化比较，覆盖写回。
用法: python -X utf8 tools/recalc_distances.py eval/night4_results_baseline.json [...]
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.run_eval import levenshtein  # noqa: E402


def main():
    for p in sys.argv[1:]:
        full = p if os.path.isabs(p) else os.path.join(ROOT, p)
        with open(full, encoding="utf-8") as f:
            d = json.load(f)
        exact = 0
        for r in d["results"]:
            got = re.sub(r"\s+", "", r.get("udkundoku_kakikudashi", ""))
            exp = re.sub(r"\s+", "", r["expected_kakikudashi"])
            r["udkundoku_kakikudashi_norm"] = got
            r["exact_match"] = got == exp
            r["edit_distance"] = levenshtein(got, exp)
            if r["exact_match"]:
                exact += 1
        d["exact_match_count"] = exact
        dists = [r["edit_distance"] for r in d["results"]]
        d["avg_edit_distance"] = round(sum(dists) / len(dists), 2) if dists else 0
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("%s: exact %d/%d avgDist %.2f" % (os.path.basename(full), exact, len(d["results"]), d["avg_edit_distance"]))


if __name__ == "__main__":
    main()
