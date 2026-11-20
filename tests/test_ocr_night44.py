# -*- coding: utf-8 -*-
"""test_ocr_night44.py — NIGHT44：全本 filter=ON/OFF 对照的不变式（纯离线，不跑 OCR）。

验证 Night43 版面过滤在**真实全本归档**上的行为契约（数据来自 eval/night44_full/）：
  * 被滤框必须是列末插入物（同列下方无保留行）
  * ON 线不得出现被滤框（无泄漏）
  * OFF 线不得出现来路不明的框
  * 被滤框在 OFF 线能产出文本的条数 = 净行数差（口径自洽）

这些断言把「275 vs 223」的口径钉死，防止后续改动把差额悄悄吃掉。
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "eval", "night44_full")


def _load(mode):
    d = os.path.join(FULL, "filter_" + mode)
    if not os.path.isdir(d):
        pytest.skip("night44 归档不存在（先跑 tools/night44_fullrun.py）")
    out = {}
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                p = json.load(f)
            out[p["page"]] = p
    return out


def _key(b):
    return (b["x"], b["y"], b["w"], b["h"])


def _ov_x(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo) / max(1, min(a["w"], b["w"]))


@pytest.fixture(scope="module")
def data():
    return _load("on"), _load("off")


def test_all_47_pages_present(data):
    on, off = data
    assert len(on) == 47 and len(off) == 47
    assert sorted(on) == sorted(off)


def test_filtered_boxes_never_leak_into_on(data):
    on, _ = data
    for pg, p in on.items():
        set_on = {_key(b) for b in p["line_boxes"]}
        for b in p["layout_filtered"]:
            assert _key(b) not in set_on, "%s: 被滤框又出现在结果里 %r" % (pg, b)


def test_off_boxes_all_accounted_for(data):
    on, off = data
    for pg in on:
        allowed = {_key(b) for b in on[pg]["line_boxes"]} | \
                  {_key(b) for b in on[pg]["layout_filtered"]}
        for b in off[pg]["line_boxes"]:
            assert _key(b) in allowed, "%s: OFF 线出现来路不明的框 %r" % (pg, b)


def test_filtered_boxes_are_column_tails(data):
    """被滤框 = 列末插入物：同列（x 重叠≥50%）下方不得还有保留行。"""
    on, _ = data
    for pg, p in on.items():
        for b in p["layout_filtered"]:
            cy = b["y"] + b["h"] / 2.0
            below = [k for k in p["line_boxes"]
                     if _ov_x(b, k) >= 0.5 and (k["y"] + k["h"] / 2.0) > cy]
            assert not below, "%s: 被滤框 x=%d y=%d 同列下方还有 %d 行" % (
                pg, b["x"], b["y"], len(below))


def test_line_delta_matches_off_text_lines(data):
    """净行数差 == 被滤框中在 OFF 线仍产出文本的个数（口径自洽）。"""
    on, off = data
    tot_delta = tot_survived = 0
    for pg in on:
        n_on, n_off = on[pg]["line_count"], off[pg]["line_count"]
        tot_delta += n_off - n_on
        set_off = {_key(b) for b in off[pg]["line_boxes"]}
        tot_survived += sum(1 for b in on[pg]["layout_filtered"]
                            if _key(b) in set_off)
    assert tot_delta == tot_survived
    assert tot_delta > 0


def test_no_page_lost_more_than_half(data):
    """单页删除量不超过 50%（防止判据突然变激进把整页吃掉）。"""
    on, off = data
    for pg in on:
        n_on, n_off = on[pg]["line_count"], off[pg]["line_count"]
        if n_off:
            assert n_on >= 0.5 * n_off, "%s: ON %d / OFF %d 删太多" % (pg, n_on, n_off)


def test_gt_pages_unfiltered_except_known(data):
    """8 张 GT 页中，11892692 三页（GT 主体 41 行）零过滤；10301438_R2 的 6 个被滤框
    已由 tools/night44_gt_impact.py 证明不与任何 GT 行相交（no-gt 6/6）。"""
    on, _ = data
    # 11892692 全本里 p003/p004/p005 = R3/R4/R5
    for pg in ("p003", "p004", "p005"):
        assert len(on[pg]["layout_filtered"]) == 0, "%s 不应有过滤" % pg
