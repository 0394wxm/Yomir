# -*- coding: utf-8 -*-
"""test_ocr_night46.py — NIGHT46 上部手写长条过滤的不变式。

判据（backend.ocr_layout.judge_headnote_strip）：
  縦框 且 y + STRIP_TOP_OFFSET <= body_top 且 h >= STRIP_H_FRAC*h_max
其中 body_top = median(主栏 y)，用稳健量避开 p012/p017 的离群长条污染。

本文件把「47 页实测」的结论钉成回归门：
  T1 判据在 47 页归档上命中 62 框 / 18 页（数量钉死）
  T2 命中框全部 y 早于主栏 y 中位数至少 100px（判据定义自检）
  T3 命中框全部是縦框且长过 0.5*hmax
  T4 与页脚带判据零重叠（两带不相交）
  T5 body_top 用中位数而非 min：p012/p017 的 body_top 在 209-256 内
  T6 GT 8 页上命中 0 个正文行（唯一命中是 '}' 界框，Night6 已记录）
  T7 判据是纯几何：不读文本（用打乱文本的框跑，结果不变）
  T8 关掉 KANBUN_OCR_LAYOUT_FILTER 时不调用（源码级开关检查）
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")


def _pages():
    out = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                out.append(json.load(f))
    return out


@pytest.fixture(scope="module")
def pages():
    return _pages()


@pytest.fixture(scope="module")
def layout():
    from backend import ocr_layout
    return ocr_layout


def _body_top_and_hmax(layout, boxes):
    _m, main = layout._main_group([dict(b) for b in boxes])
    if not main:
        return None, None
    vert = [b for b in boxes if b["h"] >= b["w"]]
    return layout._median([b["y"] for b in main]), max(b["h"] for b in vert)


def test_hit_count_is_pinned(pages, layout):
    """T1: 47 页命中 62 框 / 18 页。"""
    total = 0
    hit_pages = 0
    for p in pages:
        boxes = p["line_boxes"]
        if len(boxes) < 4:
            continue
        bt, hm = _body_top_and_hmax(layout, boxes)
        if bt is None:
            continue
        hits = layout.judge_headnote_strip(boxes, body_top=bt, h_max=hm)
        total += len(hits)
        hit_pages += 1 if hits else 0
    assert total == 62, total
    assert hit_pages == 18, hit_pages


def test_hits_are_above_body_top(pages, layout):
    """T2: 命中框 y 至少比 body_top 早 STRIP_TOP_OFFSET。"""
    for p in pages:
        boxes = p["line_boxes"]
        if len(boxes) < 4:
            continue
        bt, hm = _body_top_and_hmax(layout, boxes)
        if bt is None:
            continue
        for b in layout.judge_headnote_strip(boxes, body_top=bt, h_max=hm):
            assert b["y"] + layout.STRIP_TOP_OFFSET <= bt


def test_hits_are_vertical_and_long(pages, layout):
    """T3: 命中框必是縦框且 h >= STRIP_H_FRAC*h_max。"""
    for p in pages:
        boxes = p["line_boxes"]
        if len(boxes) < 4:
            continue
        bt, hm = _body_top_and_hmax(layout, boxes)
        if bt is None:
            continue
        for b in layout.judge_headnote_strip(boxes, body_top=bt, h_max=hm):
            assert b["h"] >= b["w"]
            assert b["h"] >= layout.STRIP_H_FRAC * hm


def test_zero_overlap_with_footer_band(pages, layout):
    """T4: 与 judge_layout 的页脚带判据零重叠。"""
    for p in pages:
        boxes = [dict(b) for b in p["line_boxes"]]
        if len(boxes) < 4:
            continue
        bt, hm = _body_top_and_hmax(layout, boxes)
        if bt is None:
            continue
        strips = {(b["x"], b["y"], b["w"], b["h"])
                  for b in layout.judge_headnote_strip(boxes, body_top=bt,
                                                       h_max=hm)}
        _m, judged = layout.judge_layout(boxes)
        foot = {(b["x"], b["y"], b["w"], b["h"])
                for b, r in judged if r is not None}
        assert not (strips & foot), p["page"]


def test_body_top_is_median_not_min(pages, layout):
    """T5: body_top 用中位数 → p012/p017 落在 209-256，而非 min 的 36/38。"""
    for p in pages:
        if p["page"] not in ("p012", "p017"):
            continue
        bt, _hm = _body_top_and_hmax(layout, p["line_boxes"])
        assert 200 <= bt <= 260, (p["page"], bt)


def test_gt_pages_have_no_body_hits(layout):
    """T6: GT 8 页上不命中任何正文行（唯一命中是 '}' 界框）。"""
    path = os.path.join(ROOT, "eval", "night36_ocr_lines.json")
    gt = json.load(open(path, encoding="utf-8"))["results"]
    bad = []
    for r in gt:
        boxes = r["lines"]
        if not boxes:
            continue
        bt, hm = _body_top_and_hmax(layout, boxes)
        if bt is None:
            continue
        for b in layout.judge_headnote_strip(boxes, body_top=bt, h_max=hm):
            txt = r["lines"][boxes.index(b)]["text"].strip()
            if txt != "}":
                bad.append((r["pid"], r["page"], txt[:30]))
    assert bad == [], bad


def test_criterion_is_text_blind(pages, layout):
    """T7: 判据只看几何——把文本换成随机串，命中集合不变。"""
    for p in pages[:12]:
        boxes = [dict(b) for b in p["line_boxes"]]
        if len(boxes) < 4:
            continue
        bt, hm = _body_top_and_hmax(layout, boxes)
        if bt is None:
            continue
        a = {(b["x"], b["y"], b["w"], b["h"])
             for b in layout.judge_headnote_strip(boxes, body_top=bt, h_max=hm)}
        b2 = [dict(b, text="\u0000" * 20) for b in boxes]
        c = {(x["x"], x["y"], x["w"], x["h"])
             for x in layout.judge_headnote_strip(b2, body_top=bt, h_max=hm)}
        assert a == c


def test_switch_documented_in_engine():
    """T8: 引擎源码里 headnote_strip 只在 KANBUN_OCR_LAYOUT_FILTER 分支内调用。"""
    src = open(os.path.join(ROOT, "backend", "ocr_engine.py"),
               encoding="utf-8").read()
    assert "judge_headnote_strip" in src
    assert "headnote_strip" in src
    # 开关字符串必须出现在同一函数体内
    i = src.index("judge_headnote_strip(")
    j = src.rindex("KANBUN_OCR_LAYOUT_FILTER", 0, i)
    assert j > 0 and i - j < 2000
