# -*- coding: utf-8 -*-
"""night46_e2e_verify.py — 复核 e2e 结果的「内容守恒 + 顺序合理性」。

e2e 用 is_subsequence 判「只删不加」，但删框发生在聚列之前，列单元结构会变
→ 顺序会变，子序列判据过严（Night43 的页脚过滤就有同样性质）。

本脚本改判：
  V1 内容守恒：ON 的行多重集 == OFF 的行多重集 − 被删行多重集
  V2 被删行数 == headnote_strip + footer_band 命中数（按多重集计）
  V3 被删行里有多少是「正文」（用 GT 8 页的正文行文本做参照集）
  V4 保留行的相对顺序变化量（Kendall tau 距离 / 对数）
  V5 被删行是否全部含手写批注特征（「候」「御」「様」「にて」「ゟ」等）
       —— 只作辅助观察，不作判据

用法: python -X utf8 tools/night46_e2e_verify.py
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

E2E = os.path.join(ROOT, "eval", "night46_e2e.json")
OUT = os.path.join(ROOT, "eval", "night46_e2e_verify.json")

# 手写公文批注的字符特征（辅助观察，非判据）
HAND_MARKS = ["候", "御", "様", "ゟ", "にて", "之儀", "以上", "村", "兵衛",
              "右", "左", "申", "可", "致"]


def kendall_inversions(a, b):
    """b 相对 a 的顺序反转对数（只在共同元素上算）。"""
    idx = {x: i for i, x in enumerate(a)}
    common = [x for x in b if x in idx]
    inv = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            if idx[common[i]] > idx[common[j]]:
                inv += 1
    return inv, len(common)


def main():
    d = json.load(open(E2E, encoding="utf-8"))
    rows = []
    for r in d["pages"]:
        on, off = r["on_text"], r["off_text"]
        dels = r["deleted_lines"]
        # V1 内容守恒
        co, cf, cd = Counter(on), Counter(off), Counter(dels)
        expect = cf - cd
        v1 = co == expect
        # V2 计数
        n_reason = r["reasons"].get("headnote_strip", 0) + \
            r["reasons"].get("footer_band", 0)
        v2 = len(dels) == n_reason
        # V3 手写特征
        n_hand = sum(1 for x in dels
                     if any(m in x for m in HAND_MARKS))
        # V4 顺序变化
        inv, ncom = kendall_inversions(off, on)
        rows.append({
            "page": r["page"], "off": len(off), "on": len(on),
            "deleted": len(dels), "n_reason": n_reason,
            "v1_content_conserved": v1, "v2_count_match": v2,
            "n_deleted_with_hand_marks": n_hand,
            "kendall_inv": inv, "n_common": ncom,
            "inv_rate": round(inv / max(1, ncom * (ncom - 1) / 2), 4),
            "missing": [list(k) for k in (expect - co)],
            "extra": [list(k) for k in (co - expect)],
        })

    print("== e2e 复核 ==")
    print("page   OFF  ON  删  理由数  内容守恒  计数一致  手写特征  顺序反转/总对")
    for r in rows:
        print("%s  %3d %3d  %2d   %3d     %-6s   %-6s    %2d/%2d     %3d/%4d (%.1f%%)"
              % (r["page"], r["off"], r["on"], r["deleted"], r["n_reason"],
                 "YES" if r["v1_content_conserved"] else "NO",
                 "YES" if r["v2_count_match"] else "NO",
                 r["n_deleted_with_hand_marks"], r["deleted"],
                 r["kendall_inv"], r["n_common"],
                 100.0 * r["inv_rate"]))

    print("\n== 结论 ==")
    print("内容守恒: %s" % ("全部 PASS" if all(r["v1_content_conserved"] for r in rows)
                            else "有 FAIL"))
    for r in rows:
        if not r["v1_content_conserved"]:
            print("  %s 缺 %s 多 %s" % (r["page"], r["missing"], r["extra"]))
    print("计数一致（删行数 = 理由数）: %s"
          % ("全部 PASS" if all(r["v2_count_match"] for r in rows) else
             [r["page"] for r in rows if not r["v2_count_match"]]))
    print("被删行含手写特征: %d / %d（%.0f%%）"
          % (sum(r["n_deleted_with_hand_marks"] for r in rows),
             sum(r["deleted"] for r in rows),
             100.0 * sum(r["n_deleted_with_hand_marks"] for r in rows)
             / max(1, sum(r["deleted"] for r in rows))))
    print("顺序反转率（保留行）: %s"
          % ", ".join("%s %.1f%%" % (r["page"], 100 * r["inv_rate"])
                      for r in rows))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"hand_marks": HAND_MARKS, "pages": rows}, f,
                  ensure_ascii=False, indent=1)
    print("\n[written] eval/night46_e2e_verify.json")


if __name__ == "__main__":
    main()
