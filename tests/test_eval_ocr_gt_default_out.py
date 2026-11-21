# -*- coding: utf-8 -*-
"""test_eval_ocr_gt_default_out.py — N66: eval_ocr_gt.py 默认输出不得覆盖已跟踪归档。

背景（Night 66 第 3 次踩坑后修复）：tools/eval_ocr_gt.py 的 OUT 常量曾指向
已跟踪的 eval/night36_cer.json，且不带第 2 个位置参数时以它为默认输出 →
任何不带参数的重跑都会覆盖冻结的 Night36 CER 归档。Night 66 起默认输出改到
未跟踪的 eval/night36_cer.tmp；只有显式把 eval/night36_cer.json 作为第 2 参数
传入才允许写该文件。
"""
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "eval_ocr_gt", os.path.join(ROOT, "tools", "eval_ocr_gt.py"))
eval_ocr_gt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_ocr_gt)

FROZEN = os.path.join(ROOT, "eval", "night36_cer.json")


def test_default_out_is_not_tracked_night36_cer_json():
    """默认输出路径不得是已跟踪的 eval/night36_cer.json（显式传第 2 参数才允许写）。"""
    out = eval_ocr_gt.OUT
    assert out != FROZEN, "默认输出仍指向已跟踪归档 eval/night36_cer.json"
    assert os.path.basename(out) != "night36_cer.json", \
        "默认输出文件名仍是 night36_cer.json（会覆盖冻结归档）"
