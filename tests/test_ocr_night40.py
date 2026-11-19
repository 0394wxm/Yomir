# -*- coding: utf-8 -*-
"""test_ocr_night40.py — NIGHT40：界框数字垃圾行 + cluster 排序 box 对齐。"""
from backend.ocr_postfix import is_junk_border_line
from backend.ocr_engine import OCREngine


def test_border_junk_lines():
    assert is_junk_border_line("一一一一一一二二二二一二二二二二")  # 781193 实形态
    assert is_junk_border_line("一二二二二二二二二二、、一二")      # 781193 混句读形态
    assert is_junk_border_line("一二一二一二一二")
    assert not is_junk_border_line("十一月十一日")      # 合法日期（含月/日/十）
    assert not is_junk_border_line("一二三")            # 短行不拦
    assert not is_junk_border_line("一甲二乙")          # 非纯一二
    assert not is_junk_border_line("")
    assert not is_junk_border_line("一一一")            # 纯一串归 NIGHT39 规则


def test_cluster_order_syncs_boxes_and_lines():
    """Night40 bugfix：cluster 重排后 lines 与 line_boxes 必须仍配对
    （此前只重排 resultlines，boxes 留在原序）。"""
    import numpy as np

    eng = OCREngine.__new__(OCREngine)  # 不触发模型加载
    eng._np = np  # _cluster_order 只用到 self._np
    boxes = [
        {"x": 100, "y": 10, "w": 30, "h": 200, "index": 0},
        {"x": 200, "y": 10, "w": 30, "h": 200, "index": 1},
        {"x": 300, "y": 10, "w": 30, "h": 200, "index": 2},
    ]
    # _cluster_order 返回列序（右→左）索引
    idx = eng._cluster_order([dict(b) for b in boxes])
    resultlines = ["L0", "L1", "L2"]
    # 复现 recognize_bytes 的重排逻辑
    rl = [resultlines[i] for i in idx]
    bx = [boxes[i] for i in idx]
    # 每个文本的行框必须就是该文本自己的框（x 与内容编号一致）
    for t, b in zip(rl, bx):
        assert t == "L%d" % (b["x"] // 100 - 1), (t, b)
