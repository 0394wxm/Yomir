# -*- coding: utf-8 -*-
"""night49_gt_sim.py — GT 门离线模拟：8 张 GT 页在新排序下的行序变化。

GT 的 CER 是按 line_no 对齐的，所以只要「框 → 文本」配对不变，CER 就不变。
但 CER 评估里还有 cluster_ocr（按 x 聚类拼接整列），列内 y 序改变会改变
拼接文本的字符顺序 → 可能影响 CER。本脚本实测：

  1) 用 filter_off 归档里 8 张 GT 页的框与文本，跑改前/改后两种顺序
  2) 报告：行级文本是否变化（按框坐标配对）
  3) 报告：按 eval_ocr_gt.cluster_ocr 口径的整列拼接文本是否变化
  4) 若变化，列出变化的列

注意：GT 页样张在 ocr_runtime/samples/batch20，与 11892692 全本页图不是同一份；
本脚本只做**排序层面的**影响分析（用归档框与文本），不重跑 OCR。

用法: python -X utf8 tools/night49_gt_sim.py
产出: eval/night49_gt_sim.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.argv = [sys.argv[0]]
import importlib.util  # noqa: E402

from backend.ocr_layout import (  # noqa: E402
    main_column_keys, reorder_main_slots, reorder_warichu_slots,
)

spec = importlib.util.spec_from_file_location(
    "sim", os.path.join(ROOT, "tools", "night49_simulate.py"))
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
OUT = os.path.join(ROOT, "eval", "night49_gt_sim.json")

# GT 8 页（stem → 全本归档页名映射见下）
GT_STEMS = [
    "ndl_11892692_R0000003", "ndl_11892692_R0000004", "ndl_11892692_R0000005",
    "ndl_1033232_R0000003", "ndl_10301438_R0000002", "ndl_10301438_R0000003",
    "ndl_781192_R0000003", "ndl_781193_R0000003",
]


def order_of(kept, use_new):
    units = sim.cluster_units([dict(b) for b in kept])
    mk = main_column_keys([dict(b) for b in kept])
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            if use_new:
                u["items"] = reorder_warichu_slots(u["items"])
            u["items"] = reorder_main_slots(u["items"], mk)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    out = []
    for u in units:
        out.extend(it["index"] for it in u["items"])
    return out


def cluster_cols(lines):
    """复刻 eval_ocr_gt.cluster_ocr（gap=14）的列拼接，返回列文本列表。"""
    PUNCT = None
    cols = []
    for l in sorted(lines, key=lambda t: -(t["x"] + t["w"] / 2.0)):
        cx = l["x"] + l["w"] / 2.0
        if cols and abs(cx - cols[-1]["cx_last"]) < 14:
            cols[-1]["members"].append(l)
            cols[-1]["cx_last"] = cx
        else:
            cols.append({"cx_last": cx, "members": [l]})
    out = []
    for c in cols:
        c["members"].sort(key=lambda t: t["y"])
        out.append("".join(m["text"] for m in c["members"]))
    return out


def main():
    manifest = {}
    mp = os.path.join(ROOT, "ocr_runtime", "samples", "batch20", "manifest.json")
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as f:
            manifest = {m["file"]: m for m in json.load(f)}

    # 全本归档页 → GT stem 的映射：用 night44_gt_lines.json 的 file 字段
    gt_lines_path = os.path.join(ROOT, "eval", "night44_gt_lines.json")
    stem_pages = {}
    if os.path.exists(gt_lines_path):
        g = json.load(open(gt_lines_path, encoding="utf-8"))
        for r in g["results"]:
            stem = r["file"].rsplit(".", 1)[0]
            # page 字段是 "p012" 之类
            stem_pages[stem] = r.get("page")

    print("== GT 页 → 全本归档页 ==")
    print("  %s" % (stem_pages or "（缺 night44_gt_lines.json，跳过逐页模拟）"))

    rows = []
    n_line_text_changed = 0
    n_col_changed = 0
    for stem, page in sorted(stem_pages.items()):
        if not page:
            continue
        p = os.path.join(OFF, page + ".json")
        if not os.path.exists(p):
            continue
        q = json.load(open(p, encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, _bx, q = r
        before = order_of(kept, False)
        after = order_of(kept, True)
        if before == after:
            rows.append({"stem": stem, "page": page, "changed": False})
            continue
        byidx = {it["index"]: it for it in kept}
        # 行文本按框坐标配对：同一框的文本在两次顺序里不变（文本不随顺序变），
        # 但**输出序列**变了。CER 按 line_no 对齐，所以只要框集合不变，
        # 行级 CER 不变。真正可能变的是 cluster_ocr 的列拼接文本。
        lb = [dict(byidx[i], text=q["lines"][i]) for i in before]
        la = [dict(byidx[i], text=q["lines"][i]) for i in after]
        cb = cluster_cols(lb)
        ca = cluster_cols(la)
        same_cols = (cb == ca)
        if not same_cols:
            n_col_changed += 1
        # 逐行序列差异
        tb = [x["text"] for x in lb]
        ta = [x["text"] for x in la]
        if tb != ta:
            n_line_text_changed += 1
        rows.append({"stem": stem, "page": page, "changed": True,
                     "cols_same": same_cols,
                     "n_cols_before": len(cb), "n_cols_after": len(ca),
                     "col_diff": None if same_cols else [
                         {"before": b, "after": a}
                         for b, a in zip(cb, ca) if b != a][:6]})

    print("\n== 结果 ==")
    print("  行序列有变化的 GT 页: %d / %d" % (n_line_text_changed, len(rows)))
    print("  列拼接文本有变化的 GT 页: %d / %d" % (n_col_changed, len(rows)))
    for r in rows:
        if r.get("changed") and not r.get("cols_same", True):
            print("\n  %s (%s) 列拼接有变化:" % (r["stem"], r["page"]))
            for d in (r["col_diff"] or []):
                print("    改前: %r" % d["before"][:60])
                print("    改后: %r" % d["after"][:60])

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"rows": rows, "line_changed": n_line_text_changed,
                   "col_changed": n_col_changed}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night49_gt_sim.json")


if __name__ == "__main__":
    main()
