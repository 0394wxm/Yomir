# -*- coding: utf-8 -*-
"""night44_append_shift.py — Night 44 的 SHIFT_LOG 条目（二进制追加，不碰旧字节）。

SHIFT_LOG.md 早期条目含非法 UTF-8 字节（Night36 §7 已记录），任何「读全文→重写」
都会失败或毁历史，故沿用 day12_append_shift.py 的 'ab' 模式并校验旧字节前缀。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N44 页脚过滤全本对照"

SECTION = u"""

- 2026-11-20 白天 | N44 页脚过滤全本对照（接手 Night43 遗留）| 先复跑 Night43 的两项只读门确认可复现（47 页仿真仍 275 框、book.md 六页删 53 行错滤 0）。**遗留项 1**：p014/p015/p044 用 `KANBUN_OCR_LAYOUT_FILTER=0` 跑产品流、离线套同一判据，**69 个被滤框逐框读过文本**——66 明确手写杂记（书信体「鈴木佐美座候以上」/人名「一同村伊勢守様」/金额「一銭壱匁」/年号「嘉永」）+ 3 个 2-4 字碎片记 ambiguous，**错滤 0**。**遗留项 3**：`tools/night44_fullrun.py` 47 页 × filter=ON/OFF 双线重跑（2993s/3298s，各 0 错误）：**OFF 线 2056 行逐页完整复现 Night42 book.md**，ON 线 1833 行，净删 223；ON 线自报 `layout_filtered` 合计 **275 与 Night43 仿真逐页吻合**。**差额口径钉死**：275 个被滤框中 223 个在 OFF 线确实产出文本（=净行数差），另 52 个即使不滤版面也被文本过滤吃掉。**新证据（本夜最重要）**：`tools/night44_insertion_check.py` 纯几何校验全部 275 个被滤框——**同列下方还有保留行的 = 0/275**，即无一夹在正文列中间，全部是列末插入物（覆盖 Night43 只验 6 页的空白）。**GT 补强**：Night43 的 GT 门走检测层、不经 `recognize_bytes`，本夜用产品流重跑 8 张 GT 页（`night44_gt_run.py`，坐标反查 canonical line_no，unmatched 0/8）→ **raw 0.3568 / norm 0.3053 与 Night41 逐位相同**；`night44_gt_impact.py` 逐框核 IoU，**被滤框触碰 GT 行 = 0**。book.md 用 ON 线重建为 `book_filter_on.md`（44/47 页），diff：白文 2056→1833、**増行 0**、書き下し同步 −223、有变化页 20/47 正好是有被滤框的页、其余 27 页零差异（基线 book.md 未动）。pytest 97→**104**（`tests/test_ocr_night44.py` 7 条不变式：无泄漏/无来路不明框/列末/口径自洽/单页删除不过半/GT 页零过滤）。accept44 **PASS**。如实记录：p014 重跑被滤框 33→24 是口径差（配对含事后被文本过滤的框）；p044 仍有 `一元条同不出旨…`(h=150) 与 `大金表主`(dy −40) 两行漏滤，属判据已知边界未修。提交 `532b064`，未推远程。
"""


def main():
    with open(PATH, "rb") as f:
        head = f.read()
    if MARK.encode("utf-8") in head:
        print("已存在 N44 段落，跳过")
        return
    before = len(head)
    with open(PATH, "ab") as f:
        f.write(SECTION.encode("utf-8"))
    after = os.path.getsize(PATH)
    print("appended: %d -> %d bytes (+%d)" % (before, after, after - before))
    print("旧字节前缀一致: %s" % (open(PATH, "rb").read(before) == head))


if __name__ == "__main__":
    main()
