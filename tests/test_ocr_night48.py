# -*- coding: utf-8 -*-
"""test_ocr_night48.py — NIGHT48 窄框判据的否证结论钉成回归门。

Night48 只测不改，产出是**三条几何路线全部失败的证据**。本文件把结论钉死，
防止将来有人再提「窄框=噪音」而不先看这些数字。

事实（47 页 filter_off + 当前判据）：
  窄框定义: w < 0.6×主栏宽 且 縦框（不含已被上部/页脚滤掉的）
  窄框总数 1118 / 40 页；其中 1047 (94%) 能配成对 = 双行割注（正文）
  未配对 71 / 30 页

否证的三条路线：
  R1 「窄框 = 噪音」         → 会删 1118 框，其中 1047 是割注（正文注）
  R2 「未配对窄框 = 噪音」   → 71 框里 C4 割注 29 个，且 C5 混有真正文
  R3 「未配对且贴页边」      → 命中 16/71，其中全高割注 5 个（误伤 31%）

T1 窄框数与配对数钉死（1118 / 1047）
T2 割注成对率 94%：证明「窄」在本版是版式特征不是噪音特征
T3 未配对 71 框里 C4（割注）>= 25 个
T4 p044 两个 Night44 漏滤框确实未配对（它们是手写，非割注）
T5 页脚带判据无漏滤：dy>0 的保留框 = 0
T6 生产代码零改动（ocr_layout 里没有窄框判据常量）
"""
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFF = os.path.join(ROOT, "eval", "night44_full", "filter_off")
EV48 = os.path.join(ROOT, "eval", "night48_thin_verdict.json")
EV48U = os.path.join(ROOT, "eval", "night48_classify.json")
EV48P = os.path.join(ROOT, "eval", "night48_p044_probe.json")


def _need(path):
    if not os.path.exists(path):
        pytest.skip("Night48 证据未生成: %s" % os.path.basename(path))
    return json.load(open(path, encoding="utf-8"))


def test_t1_thin_and_paired_pinned():
    """T1: 窄框 1118，配对 1047（数字钉死）。"""
    d = _need(EV48)
    assert d["tot_thin"] == 1118, d["tot_thin"]
    assert d["tot_paired"] == 1047, d["tot_paired"]


def test_t2_pair_rate_is_94pct():
    """T2: 94% 的窄框能配对 → 「窄」是本版割注版式特征。"""
    d = _need(EV48)
    rate = d["tot_paired"] / float(d["tot_thin"])
    assert 0.93 <= rate <= 0.95, rate


def test_t3_unpaired_contains_real_warichu():
    """T3: 未配对 71 框里仍有 >=25 个是割注（真正文）→ 未配对也不能当噪音。"""
    d = _need(EV48U)
    assert d["n"] == 71, d["n"]
    n_w = sum(1 for r in d["rows"] if r["cls"] == "C4_warichu")
    assert n_w >= 25, n_w


def test_t4_p044_two_boxes_are_unpaired():
    """T4: Night44 记录的 p044 两框确实未配对（手写書き入れ，非割注）。"""
    d = _need(EV48U)
    texts = {r["text"] for r in d["rows"] if r["page"] == "p044"}
    assert any(t.startswith("一元条同不出旨") for t in texts), texts
    assert any(t.startswith("大金表主") for t in texts), texts


def test_t5_footer_band_has_no_leak():
    """T5: 页脚带无漏滤 —— 保留框里 dy>0 的 = 0。"""
    d = _need(EV48P)
    leak = [r for r in d["all_near"] if r["dy"] > 0]
    assert len(leak) == 0, leak[:3]


def test_t6_no_thin_criterion_in_production():
    """T6: 生产代码零改动 —— ocr_layout 里没有任何窄框/配对判据。"""
    p = os.path.join(ROOT, "backend", "ocr_layout.py")
    src = open(p, encoding="utf-8").read()
    assert "NIGHT48" not in src, "NIGHT48 不应进生产代码（只测不改）"
    assert not re.search(r"w_rel|THIN_W|paired", src), "窄框判据不应上线"
