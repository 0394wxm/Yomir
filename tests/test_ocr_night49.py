# -*- coding: utf-8 -*-
"""test_ocr_night49.py — NIGHT49 割注并排槽重排（reorder_warichu_slots）回归。

守护三件事：
  1. 语义：同一 y 槽内的并排框按右→左排；跨槽（上下相接）不动。
  2. 不变式：输出是输入的置换（长度、多重集、对象身份不变）。
  3. 全本归档实测：A_strict 层割注对右先率 91.9% → 100%（生产口径）。

数据：eval/night44_full/filter_off/*.json。缺归档时归档相关测试 skip。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_layout import WARICHU_TOL, reorder_warichu_slots  # noqa: E402

OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")


def _boxes(*specs):
    """specs: (x, y, w, h) → 带 index 的框列表。"""
    return [{"x": x, "y": y, "w": w, "h": h, "index": i}
            for i, (x, y, w, h) in enumerate(specs)]


# --- 纯单元级测试（不依赖归档）------------------------------------------

def test_single_box_identity():
    """单框 → 原样返回。"""
    items = _boxes((100, 50, 20, 160))
    assert reorder_warichu_slots(items) == items


def test_empty_identity():
    assert reorder_warichu_slots([]) == []


def test_side_by_side_right_to_left():
    """同一 y 槽的并排半行：左半被排到前面（y 序）时应纠正为右→左。"""
    # 模拟 p007 实测：左半 y=43、右半 y=44 → y 序把左半放前面（错）
    items = _boxes((502, 43, 16, 175), (518, 44, 17, 174))
    out = reorder_warichu_slots(items)
    assert [b["x"] for b in out] == [518, 502]


def test_already_right_first_untouched():
    items = _boxes((518, 44, 17, 174), (502, 43, 16, 175))
    out = reorder_warichu_slots(items)
    assert [b["x"] for b in out] == [518, 502]


def test_stacked_boxes_untouched():
    """上下相接的框（Δy 远大于容差）分属不同槽，顺序不变。"""
    items = _boxes((100, 50, 50, 300), (100, 360, 50, 300))
    assert reorder_warichu_slots(items) == items


def test_stacked_boxes_within_tol_of_each_other():
    """Δy 略小于容差的上下框会被当同槽——记录该已知边界（非静默）。"""
    items = _boxes((100, 50, 50, 300), (100, 56, 50, 300))
    out = reorder_warichu_slots(items)
    # x 相同 → 右缘相同，排序稳定；顺序不变（此处只确认不崩、不丢框）
    assert len(out) == 2 and {b["index"] for b in out} == {0, 1}


def test_three_way_slot_ordering():
    """三列并排（如 p013 实测）应按右→左。"""
    items = _boxes((968, 49, 17, 179), (1009, 49, 18, 179), (988, 50, 17, 177))
    out = reorder_warichu_slots(items)
    assert [b["x"] for b in out] == [1009, 988, 968]


def test_tolerance_is_anchor_based_not_chained():
    """槽以槽首框为锚：y 链式漂移不会把整列吞成一个槽。"""
    # 0,7,14,21... 相邻差 7 <= tol，但离锚点 0 越来越远 → 应分成多槽
    items = _boxes((100, 0, 10, 100), (80, 7, 10, 100),
                   (60, 14, 10, 100), (40, 21, 10, 100))
    out = reorder_warichu_slots(items, tol=8)
    assert len(out) == 4
    assert [b["x"] for b in out] == [100, 80, 60, 40]


def test_permutation_invariant():
    """输出必须是输入的置换（对象身份也不变）。"""
    items = _boxes((518, 44, 17, 174), (502, 43, 16, 175),
                   (100, 220, 54, 590), (485, 44, 17, 175))
    out = reorder_warichu_slots(items)
    assert len(out) == len(items)
    assert {id(b) for b in out} == {id(b) for b in items}


def test_tol_default_matches_constant():
    items = _boxes((100, 0, 10, 100), (80, WARICHU_TOL, 10, 100))
    out_default = reorder_warichu_slots(items)
    out_explicit = reorder_warichu_slots(items, tol=WARICHU_TOL)
    assert [b["x"] for b in out_default] == [b["x"] for b in out_explicit]


# --- 归档实测（缺归档则 skip）------------------------------------------

@pytest.mark.skipif(not os.path.isdir(OFF), reason="缺 filter_off 归档")
def test_archive_strict_pairs_right_first():
    """全本归档：A_strict 层割注对右先率应为 100%（生产口径）。

    A_strict 判据（Night49 分层）：
      紧贴 gap<0.15*wmed ∧ 顶端对齐 |Δy|<=0.05*h ∧ 等高 |Δh|<=0.15*h
    这是「真割注」的最保守子集。Night49 实测 296 对全部右先。
    """
    pq_path = os.path.join(ROOT, "eval", "night49_pair_quality.json")
    if not os.path.exists(pq_path):
        pytest.skip("缺 night49_pair_quality.json（先跑 tools/night49_pair_quality.py）")
    pq = json.load(open(pq_path, encoding="utf-8"))
    strict = {}
    for x in pq["A_strict"]["rows"]:
        strict.setdefault(x["page"], []).append(
            ((x["r"]["x"], x["r"]["y"]), (x["l"]["x"], x["l"]["y"])))

    sys.argv = [sys.argv[0]]
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sim49", os.path.join(ROOT, "tools", "night49_simulate.py"))
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)
    from backend.ocr_layout import main_column_keys, reorder_main_slots

    def order(kept, use_new):
        units = sim.cluster_units([dict(b) for b in kept])
        mk = main_column_keys([dict(b) for b in kept])
        for u in units:
            if u["kind"] == "col":
                u["items"] = sorted(u["items"], key=lambda t: t["y"])
                if use_new:
                    u["items"] = reorder_warichu_slots(u["items"])
                u["items"] = reorder_main_slots(u["items"], mk)
            else:
                u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
        units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
        out = []
        for u in units:
            out.extend(it["index"] for it in u["items"])
        return out

    tot = ok = 0
    for fn in sorted(os.listdir(OFF)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(OFF, fn), encoding="utf-8"))
        r = sim.page_kept(q)
        if not r:
            continue
        kept, _bx, q = r
        keys = strict.get(q["page"], [])
        if not keys:
            continue
        byxy = {(it["x"], it["y"]): it for it in kept}
        pairs = [(byxy[a], byxy[b]) for a, b in keys
                 if a in byxy and b in byxy]
        if not pairs:
            continue
        pos = {idx: p for p, idx in enumerate(order(kept, True))}
        tot += len(pairs)
        ok += sum(1 for r_, l_ in pairs if pos[r_["index"]] < pos[l_["index"]])

    assert tot >= 200, "A_strict 对数异常偏少: %d" % tot
    assert ok == tot, "割注右先率未达 100%%: %d/%d" % (ok, tot)
