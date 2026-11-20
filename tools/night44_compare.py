# -*- coding: utf-8 -*-
"""night44_compare.py — filter=ON vs filter=OFF 全本对照（NIGHT44 主体分析）。

读 eval/night44_full/filter_{on,off}/*.json，逐页算：
  * 行数差（off - on）= 被版面过滤掉的行数
  * 逐行文本多重集差：**只在 off 里出现的行** = 被滤掉的行的文本
  * 与 Night42 基线 book.md 的同页白文行做三方差（off 线应≈book.md，验证重跑一致）
  * 分类被滤行：文本含「人名/敬称/金额/年号/册数/丁数/书信体」特征 → noise 特征；
    否则记为「需人工看」并原样列出，供报告引用

硬门：
  H1  被滤行里出现**经文/割注特征**的必须 0 或全部列明理由（本脚本只分类，不替人判断）
  H2  on 线的 layout_filtered 数必须等于 off-on 的行数差（同源判据自洽性）

产出: eval/night44_compare.json + stdout 表格
用法: python -X utf8 tools/night44_compare.py
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, "eval")
FULL = os.path.join(EVAL, "night44_full")

# 页脚杂记的**弱**文本特征（只用于分类展示，不参与任何过滤决策）
NOISE_HINTS = [
    (r"[候様殿君様御]", "敬称/书信体"),
    (r"[一二三四五六七八九十百千万廿丗〇]+[巻冊軒畝匁文銭丁ヶ所条]", "册数/数量/金额"),
    (r"(嘉永|嘉次|安政|文政|天明|寛政|享保|元禄|正徳|宝暦)", "年号"),
    (r"[銭匁文畝]", "货币/面积单位"),
]


def load_mode(mode):
    d = os.path.join(FULL, "filter_" + mode)
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                p = json.load(f)
            out[p["page"]] = p
    return out


def book_lines():
    """Night42 基线 book.md 的每页白文行（第一段代码块）。"""
    path = os.path.join(EVAL, "import_pid_11892692", "book.md")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out, page, in_block, seen = {}, None, False, False
    for l in lines:
        if l.startswith("## p"):
            page = l.split()[1]
            out[page] = []
            in_block = seen = False
            continue
        if page is None:
            continue
        if l.strip() == "```":
            if not seen:
                in_block = not in_block
                if not in_block:
                    seen = True
            continue
        if in_block and not seen:
            out[page].append(l)
    return out


def classify(text):
    hits = [why for pat, why in NOISE_HINTS if re.search(pat, text)]
    return hits


def main():
    on = load_mode("on")
    off = load_mode("off")
    base = book_lines()
    pages = sorted(set(on) | set(off))

    rows = []
    tot_on = tot_off = tot_base = 0
    tot_filtered = 0
    bad_pages = []
    hint_hit = hint_miss = 0
    for pg in pages:
        if pg not in on or pg not in off:
            bad_pages.append((pg, "missing on" if pg not in on else "missing off"))
            continue
        lo, lf = on[pg]["lines"], off[pg]["lines"]
        tot_on += len(lo)
        tot_off += len(lf)
        tot_base += len(base.get(pg, []))
        removed = list((Counter(lf) - Counter(lo)).elements())
        added = list((Counter(lo) - Counter(lf)).elements())
        tot_filtered += len(removed)
        # 自洽性：on 线自报 layout_filtered 数 vs 行数差
        n_reported = len(on[pg]["layout_filtered"])
        # 注意：被滤框仍可能被后续文本过滤（junk repeat / border）剔除，
        # 因此 layout_filtered >= 实际行数差 是正常；反过来不成立才是 bug。
        consistent = n_reported >= len(removed)
        if not consistent or added:
            bad_pages.append((pg, "reported=%d removed=%d added=%d"
                              % (n_reported, len(removed), len(added))))
        detail = []
        for t in removed:
            h = classify(t)
            if h:
                hint_hit += 1
            else:
                hint_miss += 1
            detail.append({"text": t, "hints": h})
        rows.append({"page": pg, "n_on": len(lo), "n_off": len(lf),
                     "n_base": len(base.get(pg, [])),
                     "removed": len(removed), "added": len(added),
                     "layout_filtered_reported": n_reported,
                     "removed_lines": detail})

    print("== 全本对照 filter=ON vs filter=OFF ==")
    print("pages=%d  lines: on=%d off=%d base(book.md)=%d"
          % (len(rows), tot_on, tot_off, tot_base))
    print("removed_by_layout=%d  自报 layout_filtered=%d"
          % (tot_filtered, sum(r["layout_filtered_reported"] for r in rows)))
    print("被滤行文本特征命中: 有特征=%d 无特征=%d" % (hint_hit, hint_miss))
    print("\n-- 有变化的页 --")
    for r in rows:
        if r["removed"] or r["added"] or r["n_off"] != r["n_base"]:
            print("  %s on=%3d off=%3d base=%3d removed=%3d added=%d rep=%d"
                  % (r["page"], r["n_on"], r["n_off"], r["n_base"], r["removed"],
                     r["added"], r["layout_filtered_reported"]))
    print("\n-- 无变化页数: %d --"
          % sum(1 for r in rows if not r["removed"] and not r["added"]))
    if bad_pages:
        print("\n!! 异常页:")
        for b in bad_pages:
            print("   %s %s" % b)

    # 无特征行单独列出（需人工看）
    print("\n-- 被滤行中**无**杂记文本特征者（需人工确认）--")
    n = 0
    for r in rows:
        for d in r["removed_lines"]:
            if not d["hints"]:
                n += 1
                print("  %s %r" % (r["page"], d["text"]))
    print("  合计 %d 行" % n)

    with open(os.path.join(EVAL, "night44_compare.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump({"lines_on": tot_on, "lines_off": tot_off, "lines_base": tot_base,
                   "removed_by_layout": tot_filtered,
                   "hint_hit": hint_hit, "hint_miss": hint_miss,
                   "bad_pages": bad_pages, "pages": rows}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night44_compare.json")


if __name__ == "__main__":
    main()
