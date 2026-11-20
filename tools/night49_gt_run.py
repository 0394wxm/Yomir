# -*- coding: utf-8 -*-
"""night49_gt_run.py — GT 门：产品流跑 8 张 GT 页，CER 必须与 Night44 基线逐位相同。

与 tools/night44_gt_run.py 相同流程，只改输出路径（不覆盖 Night44 归档），
并额外打印「改前/改后顺序」的差异页（供报告引用）。

用法: python -X utf8 tools/night49_gt_run.py
产出: eval/night49_gt_lines.json
后续: python -X utf8 tools/eval_ocr_gt.py eval/night49_gt_lines.json eval/night49_gt_cer.json
"""
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
    gt44.main()
