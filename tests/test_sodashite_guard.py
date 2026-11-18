# -*- coding: utf-8 -*-
"""NIGHT22 Rule C'（带护栏复活）的单元测试。

背景：NIGHT5 Rule C（て而して→て）无护栏，NIGHT7 因经典句「顧みて而して他を言う」
撤销；NIGHT22 以 500 条语料重新量化后带护栏复活（REPORT_NIGHT22.md）。
护栏：て 的前 2 字是「顧み」时不删。
"""
from backend.kundoku_rules import style_fix, style_dedup_shite_soshite_guarded


def test_te_sodashite_removed():
    """最常见的 て而して（活用连接）→ て；ふ→う 先行（思ふ→思う）。"""
    assert style_fix("君子は恵なりて而して費さず") == "君子は恵なりて費さず"
    assert style_fix("見て而して思ふ") == "見て思う"


def test_shite_sodashite_removed():
    """して而して（archive 里 73 处，kana 前置最多形态）→ して。"""
    assert style_fix("して而して言ふ") == "して言う"


def test_guard_kotomite_kept():
    """护栏：顧みて而して 保留（经典句 王顧左右而言他 的训读）。"""
    s = "王は左右を顧みて而して他を言う"
    assert style_fix(s) == s
    assert style_fix("顧みて而して他を言う") == "顧みて而して他を言う"


def test_kana_not_te_untouched():
    """kana 前置但不是 て（に/は/より等）不动——规则范围只到 て而して。"""
    assert style_fix("俄に而して") == "俄に而して"
    assert style_fix("人は而して") == "人は而して"


def test_punct_and_bos_untouched():
    """标点/句首的 而して 不动（8 条 expected 含而して 的都是这类）。"""
    assert style_fix("而して鷸其肉を啄む") == "而して鷸其肉を啄む"
    assert style_fix("天の道なり。而して世の常なり") == "天の道なり。而して世の常なり"


def test_interplay_modern_kana():
    """ふ→う 与新规则共存：言ふ→言う 先行，う不是て所以而して保留。"""
    assert style_fix("言ふ而して") == "言う而して"


def test_multiple_occurrences():
    """同句多处的 而して：非护栏处删、护栏处留。"""
    assert style_fix("見て而して行き、顧みて而して言う") == "見て行き、顧みて而して言う"


def test_no_false_positive_on_plain_sodashite():
    """孤立而して（前置既非て也非顧み）不变。"""
    assert style_dedup_shite_soshite_guarded("而して") == "而して"
    assert style_dedup_shite_soshite_guarded("天は積気のみ") == "天は積気のみ"
