# -*- coding: utf-8 -*-
"""night84_collect.py — N84 空串行证据收集（只读，不跑引擎）。

从 night83_results_8165.json（N83 链尾 TestClient 全量真跑归档、与 N81 逐位一致）
提取 udkundoku_kakikudashi == "" 的全部行，输出分层统计与 ruby 尾段截取信息到
eval/night84_empty_lines.json。

根因（N84 定性）：detect_text_type 把（…）ruby 夹注内的假名计入分子、括号本身
排除出分母 → 夹注行假名占比 >0.3 被误判为假名文学文本 → kana 分流直接返回
kakikudashi=""（引擎从未被调用）。
用法: python -I tools/night84_collect.py
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

from backend.main import _ruby_tail_kanbun, detect_text_type  # noqa: E402


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    doc = json.load(open(os.path.join(EV, "night83_results_8165.json"), encoding="utf-8"))
    res = doc["results"]
    empty = [r for r in res if (r.get("udkundoku_kakikudashi") or "") == ""]

    pref = collections.Counter(re.match(r"([a-z_]+)", r["id"]).group(1) if re.match(r"([a-z_]+)", r["id"]) else "?"
                               for r in empty)
    pref_all = collections.Counter(re.match(r"([a-z_]+)", r["id"]).group(1) if re.match(r"([a-z_]+)", r["id"]) else "?"
                                   for r in res)
    lens = [len(r["hakubun"].replace("\n", "")) for r in empty]
    lens_all = [len(r["hakubun"].replace("\n", "")) for r in res]
    n_kana_branch = sum(1 for r in empty if detect_text_type(r["hakubun"]) == "kana")
    with_paren = [r for r in res if "（" in r["hakubun"] or "）" in r["hakubun"]]
    with_kana = [r for r in res if re.search(r"[ぁ-ゖー]", r["hakubun"])]

    rows = []
    no_tail = []
    for r in empty:
        tail = _ruby_tail_kanbun(r["hakubun"])
        if not tail:
            no_tail.append(r["id"])
        rows.append({
            "id": r["id"],
            "source_url": r.get("source_url", ""),
            "hakubun": r["hakubun"],
            "expected_kakikudashi": r["expected_kakikudashi"],
            "ruby_tail": tail,
            "tail_len": len(tail),
            "old_edit_distance": len(norm(r["expected_kakikudashi"])),
        })

    out = {
        "baseline": "eval/night83_results_8165.json (N83 链尾 TestClient 全量真跑归档)",
        "n_corpus": len(res),
        "n_empty": len(empty),
        "n78_reported": 249,
        "kana_branch": n_kana_branch,
        "corpus_rows_with_fullwidth_paren": len(with_paren),
        "corpus_rows_with_kana": len(with_kana),
        "empty_rows_without_ruby_tail": no_tail,
        "prefix_dist_empty": dict(pref.most_common()),
        "prefix_dist_corpus_top": dict(pref_all.most_common(12)),
        "hakubun_len_empty": {"min": min(lens), "max": max(lens), "avg": round(sum(lens) / len(lens), 1)},
        "hakubun_len_corpus": {"min": min(lens_all), "max": max(lens_all), "avg": round(sum(lens_all) / len(lens_all), 1)},
        "old_distance_sum": sum(x["old_edit_distance"] for x in rows),
        "rows": rows,
    }
    out_path = os.path.join(EV, "night84_empty_lines.json")
    json.dump(out, open(out_path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("empty rows: %d (N78 称 249) | kana 分流命中 %d | 无尾段 %d %s"
          % (len(empty), n_kana_branch, len(no_tail), no_tail[:5]))
    print("prefix (empty):", dict(pref.most_common()))
    print("hakubun len (empty): min %d max %d avg %.1f | corpus avg %.1f"
          % (min(lens), max(lens), sum(lens) / len(lens), sum(lens_all) / len(lens_all)))
    print("old distance sum: %d" % out["old_distance_sum"])
    print("written:", out_path)


if __name__ == "__main__":
    main()
