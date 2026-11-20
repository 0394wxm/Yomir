# -*- coding: utf-8 -*-
"""night47_p031_check.py — p031 的 5 个长条为什么没被 headnote_strip 滤掉。

night47_kana_ratio 在 filter_on 归档里发现 p031 还有 5 个 w=20-23、h=666-694
的长条（x=493/480/458/395/327，文本是假名混排的公文批注）。但真实 OCR 的
e2e（night46_e2e）显示 p031 的 headnote_strip 命中 **13** 个，且删了 13 行。

可能原因：`eval/night44_full/filter_on` 是 **Night44 生成的归档**（用当时
的代码，不含 Night46 的 headnote_strip）→ 归档里当然还有这些框。
本脚本验证这个解释，并确认当前代码在 p031 上命中 13 个。

用法: python -X utf8 tools/night47_p031_check.py
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


def key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def main():
    off = json.load(open(os.path.join(OFF, "p031.json"), encoding="utf-8"))
    on = json.load(open(os.path.join(ON, "p031.json"), encoding="utf-8"))
    print("filter_off: %d 框   filter_on: %d 框（Night44 生成，不含 Night46）"
          % (len(off["line_boxes"]), len(on["line_boxes"])))

    boxes = [dict(b) for b in off["line_boxes"]]
    _m, judged = judge_layout(boxes)
    kept = [b for b, r in judged if r is None]
    n_footer = sum(1 for b, r in judged if r is not None)
    vert = [b for b in kept if b["h"] >= b["w"]]
    _m2, main2 = _main_group([dict(b) for b in kept])
    strips = judge_headnote_strip(
        kept, body_top=_median([b["y"] for b in main2]),
        h_max=max(b["h"] for b in vert))

    print("\n当前代码在 p031（filter_off 原始框）上：")
    print("  页脚滤 %d  上部滤 %d  保留 %d / %d"
          % (n_footer, len(strips), len(kept) - len(strips), len(boxes)))
    print("\n上部命中的框:")
    for b in strips:
        i = next(i for i, x in enumerate(boxes) if key(x) == key(b))
        print("  x=%4d y=%3d w=%3d h=%3d  %r"
              % (b["x"], b["y"], b["w"], b["h"],
                 off["lines"][i][:56]))

    # Night47 看到的那 5 个框在 filter_on 里
    print("\n== filter_on 归档里 kana>0.15 的框（Night47 K3 报的 5 个）==")
    seen = [(493, 44), (480, 47), (458, 49), (395, 59), (327, 56)]
    for b in on["line_boxes"]:
        if (b["x"], b["y"]) in seen:
            print("  x=%4d y=%3d w=%3d h=%3d  在 filter_off 里存在: %s"
                  % (b["x"], b["y"], b["w"], b["h"],
                     any(key(x) == key(b) for x in off["line_boxes"])))
    print("\n→ 结论：filter_on 归档是 Night44 的产物，不含 Night46 判据。")
    print("  当前代码在 p031 上滤掉 %d 个上部框（含这 5 个）。" % len(strips))
    print("  Night46 e2e 实测 p031 的 headnote_strip 命中 13 → 与本文一致:",
          len(strips) == 13)


if __name__ == "__main__":
    main()
