# -*- coding: utf-8 -*-
"""night36_xcols.py — 把碎掉的行框按 x 聚类还原成整列裁剪图（NIGHT36，仅几何，不碰 OCR 文本）。

用法: python tools/night36_xcols.py <stem> [--gap G] [--scale S] [--pad P]
  取 boxes.json 全部行框，按 x 中心聚类（间距<G 视为同一列），每列从高清原图
  裁 x.min-P .. x.max+w+P、y.min-P .. y.max+h+P 的整列图，列号从右到左排 k1,k2...
产出: eval/ocr_samples/gt36_view/<stem>_xc<k>_<x0>_<nboxes>.png
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HR = os.path.join(ROOT, "eval", "ocr_samples", "gt36_hr")
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
OUT = os.path.join(ROOT, "eval", "ocr_samples", "gt36_view")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    stem = args[0]
    gap = float(args[args.index("--gap") + 1]) if "--gap" in args else 55.0
    scale = float(args[args.index("--scale") + 1]) if "--scale" in args else 1.0
    pad = int(args[args.index("--pad") + 1]) if "--pad" in args else 12

    with open(os.path.join(GT36, stem, "boxes.json"), encoding="utf-8") as f:
        b = json.load(f)
    lines = sorted(b["lines"], key=lambda l: -l["x"])  # 右到左
    # 聚类：x 中心间距 < gap 合并
    cols = []
    for l in lines:
        cx = l["x"] + l["w"] / 2.0
        if cols and abs(cx - cols[-1][-1][0]) < gap:
            cols[-1].append((cx, l))
        else:
            cols.append([(cx, l)])
    from PIL import Image

    im = Image.open(os.path.join(HR, stem + ".jpg"))
    s = im.width / 1400.0
    os.makedirs(OUT, exist_ok=True)
    for k, col in enumerate(cols, 1):
        xs = [l["x"] for _, l in col]
        x0 = max(0, int(min(xs) * s) - pad)
        x1 = min(im.width, int((max(l["x"] + l["w"] for _, l in col)) * s) + pad)
        y0 = max(0, int(min(l["y"] for _, l in col) * s) - pad)
        y1 = min(im.height, int(max(l["y"] + l["h"] for _, l in col) * s) + pad)
        c = im.crop((x0, y0, x1, y1))
        c = c.resize((max(1, int(c.width * scale)), max(1, int(c.height * scale))), Image.LANCZOS)
        dst = os.path.join(OUT, "%s_xc%d_%d_%d.png" % (stem, k, int(min(xs)), len(col)))
        c.save(dst)
        print("[ok] xc%d x=%d boxes=%d size=%s -> %s" % (k, min(xs), len(col), c.size, os.path.basename(dst)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
