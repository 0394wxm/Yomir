# -*- coding: utf-8 -*-
"""night36_view.py — GT 抄录用取图工具：从 3000px 高清原图裁出查看区域（NIGHT36）。

只裁图片，不调用 recognizer、不读写任何 OCR 识别文本。
用法:
  python tools/night36_view.py <stem> [--box x y w h] [--line N] [--pad P] [--rot]
                                [--scale S] [--name out.png]
  stem   : 如 ndl_11892692_R0000003（gt36_hr 下的文件名去 .jpg）
  --line : 用 gt36/<stem>/boxes.json 的 line_no 框（按 1400→3000 比例换算）
  --box  : 直接给 3000px 图上的像素框
  --rot  : 顺时针旋转 90 度（竖行转横排，便于细看）
产出: eval/ocr_samples/gt36_view/<stem>[_<name>].png
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HR = os.path.join(ROOT, "eval", "ocr_samples", "gt36_hr")
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
OUT = os.path.join(ROOT, "eval", "ocr_samples", "gt36_view")


def get_box(args):
    if "--box" in args:
        i = args.index("--box")
        return tuple(int(v) for v in args[i + 1:i + 5])
    if "--line" in args:
        i = args.index("--line")
        line_no = int(args[i + 1])
        stem = args[0]
        with open(os.path.join(GT36, stem, "boxes.json"), encoding="utf-8") as f:
            b = json.load(f)
        line = next(l for l in b["lines"] if l["line_no"] == line_no)
        return (line["x"], line["y"], line["w"], line["h"])
    return None


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    stem = args[0]
    src = os.path.join(HR, stem + ".jpg")
    from PIL import Image

    im = Image.open(src)
    box = get_box(args)
    if box:
        # --line 走 1400px 坐标系，--box 走 3000px 坐标系
        if "--line" in args:
            scale = im.width / 1400.0
            x, y, w, h = [int(round(v * scale)) for v in box]
        else:
            x, y, w, h = box
    else:
        x, y, w, h = 0, 0, im.width, im.height
    if "--pad" in args:
        p = int(args[args.index("--pad") + 1])
        x, y = max(0, x - p), max(0, y - p)
        w = min(im.width - x, w + 2 * p)
        h = min(im.height - y, h + 2 * p)
    crop = im.crop((x, y, x + w, y + h))
    if "--scale" in args:
        s = float(args[args.index("--scale") + 1])
        crop = crop.resize((int(crop.width * s), int(crop.height * s)), Image.LANCZOS)
    if "--rot" in args:
        crop = crop.transpose(Image.ROTATE_90)  # 逆时针 90 度：竖行首字转到左侧，从左往右读
    os.makedirs(OUT, exist_ok=True)
    name = "crop"
    if "--name" in args:
        name = args[args.index("--name") + 1]
    dst = os.path.join(OUT, "%s_%s.png" % (stem, name))
    crop.save(dst)
    print("[ok]", dst, crop.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
