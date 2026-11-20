# -*- coding: utf-8 -*-
"""test_ocr_night45.py — NIGHT45 列单元内并列主栏重排的不变式测试。

守护 `backend/ocr_layout.reorder_main_slots` / `main_column_keys` 的语义，
以及 47 页归档上的实测结论（I5 主栏列对颠倒 2→1，其中正文 1→0）。

数据：eval/night44_full/filter_on/*.json（Night44 全本 filter=ON 归档）。
缺归档时整体 skip（与 test_ocr_night44.py 同策略）。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import (  # noqa: E402
    MAIN_COL_OVERLAP, main_column_keys, reorder_main_slots,
)

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")


def _boxes(*specs):
    """specs: (x, y, w, h) → 带 index 的框列表。"""
    return [{"x": x, "y": y, "w": w, "h": h, "index": i}
            for i, (x, y, w, h) in enumerate(specs)]


# --- 纯单元级测试（不依赖归档）------------------------------------------

def test_no_main_keys_is_identity():
    """没有主栏框 → 顺序逐位不变。"""
    items = _boxes((100, 50, 20, 160), (80, 50, 20, 160), (60, 50, 20, 160))
    assert reorder_main_slots(items, set()) == items


def test_single_main_box_is_identity():
    """只有一个主栏框 → 无从重排，顺序不变。"""
    items = _boxes((100, 50, 20, 160), (80, 50, 50, 570))
    keys = {(80, 50, 50, 570)}
    assert reorder_main_slots(items, keys) == items


def test_stacked_main_boxes_untouched():
    """同列上下堆叠的主栏框（x 全重叠）不触发重排。"""
    items = _boxes((100, 50, 50, 300), (100, 360, 50, 300))
    keys = {(100, 50, 50, 300), (100, 360, 50, 300)}
    assert reorder_main_slots(items, keys) == items


def test_parallel_main_columns_reordered_right_to_left():
    """两个并列主栏被 y 噪声判反时，按右缘 x 右→左纠正。"""
    # 左列 x=100（y=215），右列 x=160（y=217）——y 序把左列排在前面（错）
    items = _boxes((100, 215, 50, 570), (160, 217, 50, 570))
    keys = {(100, 215, 50, 570), (160, 217, 50, 570)}
    out = reorder_main_slots(items, keys)
    assert [b["x"] for b in out] == [160, 100]


def test_already_correct_order_untouched():
    """已经右→左正确时不改动（返回同一对象内容）。"""
    items = _boxes((160, 217, 50, 570), (100, 215, 50, 570))
    keys = {(100, 215, 50, 570), (160, 217, 50, 570)}
    assert reorder_main_slots(items, keys) == items


def test_non_main_slots_stay_in_place():
    """非主栏框（头注/割注）的槽位逐位不变，只有主栏框换槽。"""
    # 槽位：0=头注A, 1=左主栏, 2=头注B, 3=右主栏
    items = _boxes((170, 50, 20, 160),   # 0 头注 A
                   (100, 215, 50, 570),  # 1 左主栏
                   (150, 60, 20, 160),   # 2 头注 B
                   (160, 217, 50, 570))  # 3 右主栏
    keys = {(100, 215, 50, 570), (160, 217, 50, 570)}
    out = reorder_main_slots(items, keys)
    # 主栏槽位仍是 1 和 3，但内容互换
    assert out[0] is items[0] and out[2] is items[2]
    assert out[1]["x"] == 160 and out[3]["x"] == 100


def test_permutation_and_multiset_preserved():
    """输出必须是输入的置换（长度、多重集、对象身份都不变）。"""
    items = _boxes((170, 50, 20, 160), (100, 215, 50, 570),
                   (150, 60, 20, 160), (160, 217, 50, 570))
    keys = {(100, 215, 50, 570), (160, 217, 50, 570)}
    out = reorder_main_slots(items, keys)
    assert len(out) == len(items)
    assert sorted(id(b) for b in out) == sorted(id(b) for b in items)


# --- 47 页归档上的回归测试 ----------------------------------------------

@pytest.fixture(scope="module")
def pages():
    if not os.path.isdir(FULL):
        pytest.skip("Night44 filter=ON 归档缺失")
    out = []
    for fn in sorted(os.listdir(FULL)):
        if fn.endswith(".json"):
            with open(os.path.join(FULL, fn), encoding="utf-8") as f:
                out.append(json.load(f))
    if not out:
        pytest.skip("Night44 filter=ON 归档为空")
    return out


def _main_cols(boxes):
    from backend.ocr_layout import _main_group

    def ov_x(a, b):
        lo = max(a["x"], b["x"])
        hi = min(a["x"] + a["w"], b["x"] + b["w"])
        return max(0, hi - lo) / max(1, min(a["w"], b["w"]))

    _miban, main = _main_group([dict(b) for b in boxes])
    if not main:
        return []
    mk = {(b["x"], b["y"], b["w"], b["h"]) for b in main}
    mi = [i for i, b in enumerate(boxes)
          if (b["x"], b["y"], b["w"], b["h"]) in mk]
    cols = []
    for i in sorted(mi, key=lambda i: -(boxes[i]["x"] + boxes[i]["w"])):
        b = boxes[i]
        for c in cols:
            if any(ov_x(b, boxes[j]) >= MAIN_COL_OVERLAP for j in c):
                c.append(i)
                break
        else:
            cols.append([i])
    cols.sort(key=lambda c: -max(boxes[i]["x"] + boxes[i]["w"] for i in c))
    return cols


def _prod_order(boxes):
    from tools.night45_cluster_proto import build_units
    main_keys = main_column_keys(boxes)
    units = build_units(boxes)
    for u in units:
        if u["kind"] == "col":
            u["items"] = sorted(u["items"], key=lambda t: t["y"])
            u["items"] = reorder_main_slots(u["items"], main_keys)
        else:
            u["items"] = sorted(u["items"], key=lambda t: -t["x"])
    units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
    idx = []
    for u in units:
        idx.extend(b["index"] for b in u["items"])
    return idx


def test_archive_order_is_permutation(pages):
    """每页重排结果都是 [0, n) 的置换。"""
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        idx = _prod_order(boxes)
        assert sorted(idx) == list(range(len(boxes))), p["page"]


def test_archive_changes_exactly_one_page(pages):
    """47 页里只有 p021 的顺序发生变化（最小修复的硬指标）。"""
    from tools.night45_cluster_proto import order_v1
    changed = []
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        if _prod_order(boxes) != order_v1(boxes):
            changed.append(p["page"])
    assert changed == ["p021"], changed


def test_archive_i5_body_inversions_zero(pages):
    """主栏列对颠倒：正文（p021）修好；只剩 p017 的手写批注。"""
    bad = {}
    for p in pages:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        cols = _main_cols(boxes)
        if len(cols) < 2:
            continue
        pos = {i: k for k, i in enumerate(_prod_order(boxes))}
        n = 0
        for k in range(len(cols) - 1):
            if max(pos[i] for i in cols[k]) > min(pos[i] for i in cols[k + 1]):
                n += 1
        if n:
            bad[p["page"]] = n
    assert bad == {"p017": 1}, bad


def test_archive_p021_known_fix(pages):
    """p021：右列（x=1135）必须排在左列（x=1081）之前。"""
    p = next(x for x in pages if x["page"] == "p021")
    boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
    idx = _prod_order(boxes)
    pos = {i: k for k, i in enumerate(idx)}
    right = next(i for i, b in enumerate(boxes)
                 if b["x"] == 1135 and b["h"] > 500)
    left = next(i for i, b in enumerate(boxes)
                if b["x"] == 1081 and b["h"] > 500)
    assert pos[right] < pos[left], (pos[right], pos[left])
    assert "天下之無道也" in p["lines"][right]
    assert "木鐸" in p["lines"][left]


def test_main_column_keys_subset_of_boxes(pages):
    """main_column_keys 必须只包含页内真实存在的框。"""
    for p in pages[:10]:
        boxes = [dict(b, index=i) for i, b in enumerate(p["line_boxes"])]
        if len(boxes) < 4:
            continue
        keys = main_column_keys(boxes)
        have = {(b["x"], b["y"], b["w"], b["h"]) for b in boxes}
        assert keys <= have, p["page"]
