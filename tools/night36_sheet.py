# -*- coding: utf-8 -*-
"""night36_sheet.py — GT 抄录用拼版图：把多行 crop 纵向拼成一张标注图（NIGHT36）。

红线：不调用 recognizer、不读写任何 OCR 识别文本。
用法: python tools/night36_sheet.py <stem> <line_no...|all> [--scale S] [--per N] [--pad P]
  all = boxes.json 全部行（junk 行标签带 *，供参考）
  每张拼版图默认叠 2 行（--per N）；行框是 1400px 坐标系，自动换算到高清图
产出: eval/ocr_samples/gt36_view/<stem>_sheet<k>.png
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HR = os.path.join(ROOT, "eval", "ocr_samples", "gt36_hr")
GT36 = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
OUT = os.path.join(ROOT, "eval", "ocr_samples", "gt36_view")


def argval(args, flag, default):
    if flag in args:
        return args[args.index(flag) + 1]
    return default


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    stem = args[0]
    scale = float(argval(args, "--scale", "0.75"))
    per = int(argval(args, "--per", "2"))
    pad = int(argval(args, "--pad", "10"))
    flags = ("--scale", "--per", "--pad")
    pos = []
    skip_next = False
    for a in args[1:]:
        if skip_next:
            skip_next = False
            continue
        if a in flags:
            skip_next = True
            continue
        if a.startswith("--"):
            continue
        pos.append(a)

    from PIL import Image, ImageDraw

    with open(os.path.join(GT36, stem, "boxes.json"), encoding="utf-8") as f:
        b = json.load(f)
    im = Image.open(os.path.join(HR, stem + ".jpg"))
    s = im.width / 1400.0

    if "all" in pos:
        nums = [l["line_no"] for l in b["lines"]]
    else:
        nums = [int(x) for x in pos]
    by_no = {l["line_no"]: l for l in b["lines"]}

    cells = []
    for n in nums:
        l = by_no[n]
        x = max(0, int(l["x"] * s) - pad)
        y = max(0, int(l["y"] * s) - pad)
        w = min(im.width - x, int(l["w"] * s) + 2 * pad)
        h = min(im.height - y, int(l["h"] * s) + 2 * pad)
        c = im.crop((x, y, x + w, y + h))
        if "--v" not in args:  # --v: 竖列原样（字正立、自上而下），多列横向并排
            if c.height > c.width:  # 竖行列：默认逆时针转 90 度（首字到左侧）；--cw 顺时针
                rot = Image.ROTATE_270 if "--cw" in args else Image.ROTATE_90
                c = c.transpose(rot)
        if "--gray" in args:
            from PIL import ImageOps
            c = ImageOps.grayscale(c)
            c = ImageOps.autocontrast(c, cutoff=1)
            c = c.convert("RGB")
        c = c.resize((max(1, int(c.width * scale)), max(1, int(c.height * scale))), Image.LANCZOS)
        cells.append((n, bool(l["junk"]), c))

    os.makedirs(OUT, exist_ok=True)
    label_h = 22
    k = 0
    if "--v" in args:
        per = len(cells)  # --v 模式下一张图放全部列
        W = sum(c.width + 10 for _, _, c in cells) + 8
        H = max(label_h + c.height for _, _, c in cells) + 10
        sheet = Image.new("RGB", (W, H), (225, 225, 225))
        d = ImageDraw.Draw(sheet)
        x = 8
        for n, junk, c in cells:
            d.text((x, 3), "L%02d%s" % (n, "*" if junk else ""), fill=(180, 0, 0))
            sheet.paste(c, (x, label_h))
            x += c.width + 10
        tag = "vL%d-%d" % (nums[0], nums[-1])
        dst = os.path.join(OUT, "%s_%s.png" % (stem, tag))
        sheet.save(dst)
        print("[ok]", tag, sheet.size, "lines:", ",".join(str(n) for n, _, _ in cells))
        return 0
    for i in range(0, len(cells), per):
        group = cells[i:i + per]
        W = max(c.width for _, _, c in group) + 8
        H = sum(label_h + c.height + 6 for _, _, c in group) + 6
        sheet = Image.new("RGB", (W, H), (225, 225, 225))
        d = ImageDraw.Draw(sheet)
        y = 4
        for n, junk, c in group:
            d.text((6, y + 3), "L%02d%s" % (n, "*" if junk else ""), fill=(180, 0, 0))
            sheet.paste(c, (4, y + label_h))
            y += label_h + c.height + 6
        k += 1
        dst = os.path.join(OUT, "%s_sheet%d.png" % (stem, k))
        sheet.save(dst)
        print("[ok] sheet%d" % k, sheet.size, "lines:", ",".join(str(n) for n, _, _ in group))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
