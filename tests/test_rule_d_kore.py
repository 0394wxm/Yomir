# -*- coding: utf-8 -*-
"""test_rule_d_kore.py — D11 Rule D（これ→之）的锁定测试。

覆盖：
  1. 白文含「之」→ 替换生效
  2. 白文不含「之」→ 一个都不动（护栏）
  3. 空 hakubun → 不加护栏（纯函数行为，供离线模拟用）
  4. 经典句/既有规则不受影响
  5. 多个「これ」全部替换
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.kundoku_rules import (  # noqa: E402
    style_fix,
    style_fix_with_hakubun,
    style_kore_to_shi,
)


def test_kore_replaced_when_hakubun_has_shi():
    """白文有「之」→ 这 れ 换成 之。"""
    assert style_kore_to_shi("学びて時にこれを習う", "学而時習之") == "学びて時に之を習う"


def test_kore_kept_when_hakubun_has_no_shi():
    """白文无「之」→ 原样保留（护栏）。"""
    s = "これを以て観る"
    assert style_kore_to_shi(s, "觀其所由") == s


def test_kore_all_occurrences_replaced():
    """多个 これ 全部替换。"""
    assert style_kore_to_shi("これを知りこれを好む", "知之好之") == "之を知り之を好む"


def test_kore_no_hakubun_means_no_guard():
    """hakubun 为空时按纯函数处理（离线模拟/直接调用）。"""
    assert style_kore_to_shi("これを見る") == "之を見る"


def test_style_fix_with_hakubun_orders_rules():
    """D11 入口：ふ→う、は曰く、Rule C'、Rule D 依次生效且互不破坏。"""
    out = style_fix_with_hakubun("子は曰く、これを学ぶ、見て而して思ふ", "子曰、學之、見而思")
    assert "子曰く" in out          # は曰く 删除
    assert "之を学ぶ" in out        # Rule D
    assert "見て思う" in out        # Rule C' + ふ→う


def test_style_fix_with_hakubun_guard_from_real_hakubun():
    """白文里没有之的原句，即便输出有 これ 也不改（语料外安全网）。"""
    s = "これぞ天の道なり"
    assert style_fix_with_hakubun(s, "此天道也") == s


def test_style_fix_unchanged_for_rule_d():
    """旧入口 style_fix 不调用 Rule D（无白文），行为保持 NIGHT22 原样。"""
    assert style_fix("これを学ぶ") == "これを学ぶ"
    assert style_fix("顧みて而して他を言う") == "顧みて而して他を言う"


def test_classic_sentence_still_intact():
    """经典句锁定（既有约定不被 D11 破坏）。"""
    assert style_fix("王は左右を顧みて而して他を言う") == "王は左右を顧みて而して他を言う"
