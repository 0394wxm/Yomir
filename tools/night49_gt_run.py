# -*- coding: utf-8 -*-
"""night49_gt_run.py — GT 门：产品流跑 8 张 GT 页，CER 必须与 Night44 基线逐位相同。

与 tools/night44_gt_run.py 相同流程，只改输出路径（不覆盖 Night44 归档），
并额外打印「改前/改后顺序」的差异页（供报告引用）。

用法:
    python -X utf8 tools/night49_gt_run.py                          # 缺省（行为不变）
    python -X utf8 tools/night49_gt_run.py --out eval/night51_gt_lines.json
                                                                    # 写指定文件（NIGHT51 起）
产出: eval/night49_gt_lines.json（缺省）；传 --out 时写指定文件、不碰缺省归档
后续: python -X utf8 tools/eval_ocr_gt.py eval/night49_gt_lines.json eval/night49_gt_cer.json

NIGHT51: 新增 --out。缺省输出仍是 eval/night49_gt_lines.json（与 Night49 逐位
一致，不改变任何既有调用方）；夜班跑门时传 --out 指到当夜文件，避免每次都
覆盖已跟踪的 Night49 归档（Night50 待拍板②）。
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("KANBUN_OCR_LAYOUT_FILTER", "1")

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "gt44", os.path.join(ROOT, "tools", "night44_gt_run.py"))
gt44 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gt44)

gt44.OUT = os.path.join(ROOT, "eval", "night49_gt_lines.json")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="GT 门：8 张 GT 页产品流（缺省输出 eval/night49_gt_lines.json，行为不变）")
    ap.add_argument("--out", default=None, metavar="PATH",
                    help="输出 JSON 路径，相对路径以仓库根为基准；"
                         "不传 = eval/night49_gt_lines.json（原行为不变）")
    arg = ap.parse_args()
    if arg.out:
        gt44.OUT = arg.out if os.path.isabs(arg.out) else os.path.join(ROOT, arg.out)
    gt44.main()
