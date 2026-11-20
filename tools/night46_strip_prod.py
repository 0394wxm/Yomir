# -*- coding: utf-8 -*-
"""night46_strip_prod.py — 生产实现（judge_headnote_strip）与离线调查的等价性。

调查脚本（night46_strip_safety.py）是独立实现的判据；生产代码
（backend/ocr_layout.judge_headnote_strip + ocr_engine 的调用顺序）是另一份。
本脚本用**生产函数**在 filter_off 原始框上重跑，验证：
  E1 命中数 = 62 框 / 18 页（与调查一致）
  E2 命中框集合与调查逐框相同
  E3 页脚过滤 → 上部过滤 的顺序下，两判据仍零重叠
  E4 最终保留框数 = 1770（1832 - 62）
  E5 行序：过滤前后（在保留框上）主栏列对顺序不变

产出: eval/night46_strip_prod.json
用法: python -X utf8 tools/night46_strip_prod.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    _main_group, _median, judge_headnote_strip, judge_layout,
)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
ON = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT = os.path.join(ROOT, "eval", "night46_strip_prod.json")
SURVEY = os.path.join(ROOT, "eval", "night46_strip_safety.json")


def key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def load(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                p = json.load(f)
            out[p["page"]] = p
    return out


def main():
    off = load(OFF)
    on = load(ON)
    survey = json.load(open(SURVEY, encoding="utf-8"))
    expect = {}
    for r in survey["pages"]:
        expect[r["page"]] = {key(b) for b in r["hits"]}

    rows = []
    tot = 0
    tot_footer = 0
    mism = []
    for pg in sorted(off):
        p = off[pg]
        boxes = [dict(b) for b in p["line_boxes"]]
        if len(boxes) < 4:
            continue
        # 生产顺序：先页脚，再上部
        _m, judged = judge_layout(boxes, None, None)
        footer = [b for b, r in judged if r is not None]
        kept = [b for b, r in judged if r is None]
        vert = [b for b in kept if b["h"] >= b["w"]]
        strips = []
        if vert:
            _m2, main2 = _main_group([dict(b) for b in kept])
            if main2:
                strips = judge_headnote_strip(
                    kept, body_top=_median([b["y"] for b in main2]),
                    h_max=max(b["h"] for b in vert))
        sk = {key(b) for b in strips}
        tot += len(strips)
        tot_footer += len(footer)
        exp = expect.get(pg, set())
        got = sk
        if exp != got:
            mism.append({"page": pg,
                         "survey_only": [list(k) for k in exp - got],
                         "prod_only": [list(k) for k in got - exp]})
        rows.append({"page": pg, "n": len(boxes), "footer": len(footer),
                     "strips": len(strips), "keep": len(kept) - len(strips),
                     "overlap_footer_strip":
                         len({key(b) for b in footer} & sk),
                     "match_survey": exp == got})

    print("== 生产实现 vs 离线调查 ==")
    print("页数 %d   页脚被滤 %d   上部被滤 %d   保留 %d"
          % (len(rows), tot_footer, tot, sum(r["keep"] for r in rows)))
    print("调查预期: 页脚 223 / 上部 62 / 保留 1770（filter_off 原始 2056 框）")
    print("逐页命中集合不一致的页: %s" % (mism or "无"))
    print("页脚与上部同时命中的框: %d（应为 0）"
          % sum(r["overlap_footer_strip"] for r in rows))
    print("框数: 原始 %d → 保留 %d（删 %d）"
          % (sum(r["n"] for r in rows), sum(r["keep"] for r in rows),
             sum(r["n"] - r["keep"] for r in rows)))

    print("\n== 逐页 ==")
    for r in rows:
        if r["strips"] or r["footer"]:
            print("  %s n=%3d 页脚 %2d 上部 %2d 保留 %3d  %s"
                  % (r["page"], r["n"], r["footer"], r["strips"], r["keep"],
                     "OK" if r["match_survey"] else "MISMATCH"))

    ok = (not mism
          and sum(r["overlap_footer_strip"] for r in rows) == 0
          and tot == 62 and tot_footer == 223)
    print("\n== %s ==" % ("PASS：生产实现与调查逐框一致" if ok else "FAIL"))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"ok": ok, "total_footer": tot_footer,
                   "total_strips": tot, "mismatch": mism, "pages": rows},
                  f, ensure_ascii=False, indent=1)
    print("[written] eval/night46_strip_prod.json")


if __name__ == "__main__":
    main()
