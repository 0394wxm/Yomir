# -*- coding: utf-8 -*-
"""test_rule_f_kana_kanji.py — D17: Rule F（假名→汉字，第二批）的回归测试。

数据依据（eval/day17_*.json，2000 条，基线 avgDist 21.218 = Rule E 之后）：

    候选          白文含字&输出有假名(A)  白文无字&输出有假名(C)   Δ      改善/变差
    また→亦た            85                    68              -0.051   85/0
    いかん→如何          28                     0              -0.024   25/0
    べし→可し            49                     5              -0.026   41/0
    べく→可く             7                     3              -0.002    3/0

组合（tools/day17_combo.py + day17_boundary.py 逐条核对，真函数）：
    改写 158 / avgDist 21.218 → 21.116（**-0.102**） / 改善 147 / **变差 0** / 持平 1853
    幂等 2000/2000；语料外 13 条探针（白文=输入本身）全部一字不动。

被拒绝（变差 > 0，一律不上线）：また→又（1 变差）、べき→可き（4）、べから→可から（4）。

本文件锁住：
  1. 表结构：4 条，护栏含词形首字
  2. 词形是 expected 的真实形态（亦た/如何/可し/可く）
  3. 白文含字 → 替换；白文不含 → 一字不动
  4. 词界护栏：またたく/またがり/またしても 等不被拆
  5. 幂等
  6. 与 Rule E 叠加（两张表不互相干扰）
  7. Rule F 的词表与 E 分开（F_LONGER_WORDS 独立）
  8. 旧入口 style_fix 不受影响
  9. 语料原句
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    F_KANA_TO_KANJI,
    F_LONGER_WORDS,
    E_KANA_TO_KANJI,
    E_LONGER_WORDS,
    style_fix,
    style_fix_with_hakubun,
    style_kana_to_kanji,
    style_kana_to_kanji_f,
)


def test_table_shape():
    """4 条；每条 (假名, 词形, 护栏元组)；护栏字必须出现在替换词形里。

    注：Rule E 的 5 条都是「首字=护栏」，但 F 里 いかん→如何 的 何 在第二位
    （白文写「如之何」/「如何」，汉字是 何 不是 如），所以判据放宽到「出现在词形中」。
    """
    assert len(F_KANA_TO_KANJI) == 4
    for kana, repl, guard in F_KANA_TO_KANJI:
        assert isinstance(kana, str) and kana
        assert isinstance(repl, str) and repl
        assert isinstance(guard, tuple) and guard
        assert any(g in repl for g in guard), "护栏字必须出现在替换词形里"


def test_word_forms_match_expected_shapes():
    """词形必须是 expected 里实际出现的形态，不是裸汉字。"""
    forms = {kana: repl for kana, repl, _g in F_KANA_TO_KANJI}
    assert forms["また"] == "亦た"      # expected: 亦た 41+32+8+…；裸亦 很少
    assert forms["いかん"] == "如何"    # expected: 如何（熟语）
    assert forms["べし"] == "可し"      # expected: 可し 19+16+…
    assert forms["べく"] == "可く"      # expected: 可く（連用形）


def test_replaces_when_hakubun_has_char():
    """白文含对应汉字 → 全部按词形替换。"""
    assert style_kana_to_kanji_f("また", "亦") == "亦た"
    assert style_kana_to_kanji_f("いかん", "何") == "如何"
    assert style_kana_to_kanji_f("べし", "可") == "可し"
    assert style_kana_to_kanji_f("べく", "可") == "可く"


def test_no_change_when_hakubun_lacks_char():
    """白文不含对应汉字 → 一个假名都不动（白文护栏）。"""
    assert style_kana_to_kanji_f("また", "又") == "また"
    assert style_kana_to_kanji_f("いかん", "如") == "いかん"
    assert style_kana_to_kanji_f("べし", "無") == "べし"
    assert style_kana_to_kanji_f("べく", "非") == "べく"


def test_partial_guard_only_affects_matching_entry():
    """一条白文只含「可」时，只有 べし/べく 被改，また/いかん 不动。"""
    text = "またいかんべしべく"
    out = style_kana_to_kanji_f(text, "可")
    assert "また" in out and "いかん" in out
    assert "可し" in out and "可く" in out


def test_word_boundary_guard_protects_longer_words():
    """更长词（またたく/またがり/またしても/またと/またの）整段不动。"""
    for w in ("またたく", "またがり", "またがる", "またぎ", "またぐ",
              "またたき", "またしても", "またと", "またの"):
        assert style_kana_to_kanji_f(w, "亦") == w, "更长词被拆: %s" % w


def test_word_boundary_does_not_block_legit_cases():
    """后面是汉字/标点/句末时要替换。"""
    assert style_kana_to_kanji_f("また、然り", "亦") == "亦た、然り"
    assert style_kana_to_kanji_f("亦また", "亦") == "亦亦た"
    assert style_kana_to_kanji_f("また。", "亦") == "亦た。"


def test_idempotent():
    """应用两次结果不变。"""
    for text, hb in (("またいかんべしべく", "亦何可可"), ("また最初にまた", "亦")):
        once = style_kana_to_kanji_f(text, hb)
        twice = style_kana_to_kanji_f(once, hb)
        assert once == twice


def test_composes_with_rule_e():
    """Rule E 与 Rule F 叠加互不破坏（各自的护栏独立判断）。"""
    # 白文同时含 亦 与 皆：E 改 みな→皆，F 改 また→亦た
    out = style_fix_with_hakubun("みなまた", "皆亦")
    assert "皆" in out and "亦た" in out
    # 只有亦：E 不动（無皆），F 动
    out2 = style_fix_with_hakubun("みなまた", "亦")
    assert "みな" in out2 and "亦た" in out2
    # 只有皆：E 动，F 不动
    out3 = style_fix_with_hakubun("みなまた", "皆")
    assert "皆" in out3 and "また" in out3


def test_longer_word_tables_are_separate():
    """F_LONGER_WORDS 与 E_LONGER_WORDS 是两张独立的表，F 的新词不污染 E。"""
    assert F_LONGER_WORDS is not E_LONGER_WORDS
    assert set(F_LONGER_WORDS) == {k for k, _r, _g in F_KANA_TO_KANJI}
    # E 的 5 条必须与 D14 版本完全一致（不能被 D17 改动）
    e_forms = {kana: repl for kana, repl, _g in E_KANA_TO_KANJI}
    assert e_forms == {"みな": "皆", "すでに": "既に", "なお": "猶お",
                       "あに": "豈に", "ただ": "唯だ"}


def test_old_style_fix_unaffected():
    """旧入口 style_fix（无白文）不做 Rule F。"""
    assert style_fix("またいかんべしべく") == "またいかんべしべく"


def test_empty_hakubun_keeps_word_boundary_guard():
    """空白文：白文护栏不生效（纯函数语义，与 Rule E 一致），但词界护栏仍在。"""
    assert style_kana_to_kanji_f("またたく間に", "") == "またたく間に"
    assert style_kana_to_kanji_f("また", "") == "亦た"


def test_real_sentences_from_corpus():
    """语料原句（来自 day17_inspect.py 的实例）。"""
    # 河東凶、亦然。→ expected: 河東凶なるも、亦た然り。
    assert style_kana_to_kanji_f("河の東は凶なり、また然り。", "河東凶、亦然。") == \
        "河の東は凶なり、亦た然り。"
    # 天王曰、流可枕、石可漱乎 → expected: 流れは枕す可く、石は漱ぐ可きか
    assert style_kana_to_kanji_f("流して枕するべし、石は漱ぐべしや。", "王曰、流可枕、石可漱乎") \
        == "流して枕する可し、石は漱ぐ可しや。"
    # 天生德於予。桓魋其如予何 → expected: 桓魋其れ予を如何せん
    assert style_kana_to_kanji_f("桓魋は其予のいかん。", "子曰、天生德於予。桓魋其如予何。") == \
        "桓魋は其予の如何。"


def test_classic_sentence_still_intact():
    """经典句在白文=自身时不动（现代和文/语料外安全网）。"""
    for t in ("吾十有五而志于学", "学而時習之", "また明日会いましょう",
              "またいとこ", "いかんせん", "べくして", "べき論"):
        assert style_kana_to_kanji_f(t, t) == t, "语料外被改: %s" % t
