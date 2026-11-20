# -*- coding: utf-8 -*-
"""test_rule_g_kana_kanji.py — N55: Rule G（假名→汉字，第三批）的回归测试。

数据依据（eval/night55_sim.json，2000 条，基线 avgDist 21.116 = Rule F 之后真机）：

    候选              白文护栏   改写条   Δ        改善/变差
    また→又           又         44     -0.040   36/0   ← D17 遗留#1（1 变差已消）
    ゆゑん→所以        所以       30     -0.033   29/0
    いはゆる→所謂      所謂       23     -0.044   23/0
    たがいに→相        相        43     -0.084   43/0

组合（tools/night55_boundary.py 真函数逐条核对，与模拟逐位一致）：
    改写 136 / avgDist 21.116 → 20.916（**-0.200**） / 改善 127 / **变差 0**
    幂等 2000/2000；语料外 9 条探针全部一字不动。

维持拒绝（N55 逐条核因，见 REPORT_NIGHT55.md §4）：べき→可き（4 变差）、
べから→可から（4 变差）——expected 自身写假名 べき/べからず，运行时无信号可分。
ために→為に 0 条命中 → 不收。

本文件锁住：
  1. 表结构：4 条，护栏出现在替换词形里
  2. 词形是 expected/挖掘的真实形态
  3. 白文含字 → 替换；白文不含 → 一字不动（ゆゑん 的护栏是二字序列）
  4. 词界护栏：また 的 9 个长词不被拆
  5. 幂等
  6. 与 Rule F 分工：白文含亦 → F 吃掉 また，G 的又规则不再命中；含又 → G 接手
  7. G/F/E 三张长词表独立；また 一项 F/G 共享同一常量
  8. 旧入口 style_fix 不受影响
  9. 语料原句 / 语料外探针
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    G_KANA_TO_KANJI,
    G_LONGER_WORDS,
    F_KANA_TO_KANJI,
    F_LONGER_WORDS,
    E_KANA_TO_KANJI,
    E_LONGER_WORDS,
    style_fix,
    style_fix_with_hakubun,
    style_kana_to_kanji_g,
)


def test_table_shape():
    """4 条；护栏字（或序列）出现在替换词形里。"""
    assert len(G_KANA_TO_KANJI) == 4
    for kana, repl, guard in G_KANA_TO_KANJI:
        assert isinstance(kana, str) and kana
        assert isinstance(repl, str) and repl
        assert isinstance(guard, tuple) and guard
        assert any(g in repl for g in guard), "护栏必须出现在替换词形里"


def test_word_forms_match_expected_shapes():
    """词形必须是挖掘到的 expected 形态（裸又 / 所以 / 所謂 / 相）。"""
    forms = {kana: repl for kana, repl, _g in G_KANA_TO_KANJI}
    assert forms["また"] == "又"          # expected 又 56 次（又た 4 次为少数派）
    assert forms["ゆゑん"] == "所以"      # engine 写 ゆゑん 的地方 expected 写 所以
    assert forms["いはゆる"] == "所謂"    # engine 写 いはゆる 的地方 expected 写 所謂
    assert forms["たがいに"] == "相"      # engine 写 たがいに 的地方 expected 写 相


def test_replaces_when_hakubun_has_guard():
    """白文含护栏 → 替换。"""
    assert style_kana_to_kanji_g("また", "又") == "又"
    assert style_kana_to_kanji_g("ゆゑん", "所以") == "所以"
    assert style_kana_to_kanji_g("いはゆる", "所謂") == "所謂"
    assert style_kana_to_kanji_g("たがいに", "相") == "相"


def test_no_change_when_hakubun_lacks_guard():
    """白文不含护栏 → 一字不动。ゆゑん 的护栏是二字序列，单字「所」不触发。"""
    assert style_kana_to_kanji_g("また", "亦") == "また"        # 亦 归 F
    assert style_kana_to_kanji_g("ゆゑん", "所") == "ゆゑん"
    assert style_kana_to_kanji_g("ゆゑん", "以") == "ゆゑん"
    assert style_kana_to_kanji_g("いはゆる", "所") == "いはゆる"
    assert style_kana_to_kanji_g("たがいに", "与") == "たがいに"


def test_word_boundary_guard_protects_longer_words():
    """また 的 9 个长词整段不动（与 F 共享同一清单）。"""
    for w in ("またたく", "またがり", "またがる", "またぎ", "またぐ",
              "またたき", "またしても", "またと", "またの"):
        assert style_kana_to_kanji_g(w, "又") == w, "更长词被拆: %s" % w


def test_word_boundary_does_not_block_legit_cases():
    assert style_kana_to_kanji_g("また、然り", "又") == "又、然り"
    assert style_kana_to_kanji_g("また。", "又") == "又。"
    assert style_kana_to_kanji_g("はまた誰をか", "又") == "は又誰をか"


def test_idempotent():
    for text, hb in (("またゆゑんたがいに", "又所以相"),
                     ("また最初にまた", "又")):
        once = style_kana_to_kanji_g(text, hb)
        twice = style_kana_to_kanji_g(once, hb)
        assert once == twice


def test_division_of_labor_with_rule_f():
    """F（また→亦た，护栏 亦）与 G（また→又，护栏 又）按白文分工。

    live 链序 = F 先 G 后：白文含亦 → F 先把 また 吃成 亦た，G 的又规则不再命中；
    白文含又 → F 不动，G 接手；两者都有 → F 赢（G 变 no-op）。
    """
    # 只有又：G 改
    out = style_fix_with_hakubun("また思いを寄す", "又")
    assert "又思い" in out and "また" not in out
    # 只有亦：F 改，G 无また可改
    out2 = style_fix_with_hakubun("また思いを寄す", "亦")
    assert "亦た思い" in out2
    # 两者都有：F 先吃掉，输出与只有亦时相同（G no-op）
    out3 = style_fix_with_hakubun("また思いを寄す", "亦又")
    assert out3 == out2
    # 白文都无：全不动
    out4 = style_fix_with_hakubun("また思いを寄す", "無所")
    assert "また" in out4


def test_longer_word_tables_are_separate_and_share_mata():
    """G/F/E 三张表独立；G 的 また 长词与 F 引用同一常量（值恒等）。"""
    assert G_LONGER_WORDS is not F_LONGER_WORDS
    assert G_LONGER_WORDS is not E_LONGER_WORDS
    assert set(G_LONGER_WORDS) == {k for k, _r, _g in G_KANA_TO_KANJI}
    assert G_LONGER_WORDS["また"] == F_LONGER_WORDS["また"]
    assert G_LONGER_WORDS["また"] == ("またたく", "またがり", "またがる", "またぎ",
                                      "またぐ", "またたき", "またしても", "またと",
                                      "またの")
    # E 的 5 条必须与 D14 版本完全一致（不能被 N55 改动）
    e_forms = {kana: repl for kana, repl, _g in E_KANA_TO_KANJI}
    assert e_forms == {"みな": "皆", "すでに": "既に", "なお": "猶お",
                       "あに": "豈に", "ただ": "唯だ"}


def test_d17_rejected_candidates_stay_rejected():
    """D17 拒绝的 べき/べから 不许借 N55 回来（N55 复核仍各 4 变差）。"""
    g_kana = {kana for kana, _r, _g in G_KANA_TO_KANJI}
    assert "べき" not in g_kana and "べから" not in g_kana and "ために" not in g_kana


def test_old_style_fix_unaffected():
    assert style_fix("またゆゑんたがいに") == "またゆゑんたがいに"


def test_empty_hakubun_keeps_word_boundary_guard():
    """空白文：白文护栏不生效（纯函数语义，与 E/F 一致），但词界护栏仍在。"""
    assert style_kana_to_kanji_g("またがる", "") == "またがる"
    assert style_kana_to_kanji_g("また", "") == "又"
    assert style_kana_to_kanji_g("ゆゑん", "") == "所以"


def test_real_sentences_from_mining():
    """语料原句形态（来自 eval/night55_mine.json 的实例片段）。"""
    # 又 56/0：exp「…之を労す。又誰をか怨まん。」got また
    assert style_kana_to_kanji_g("之を労す。また誰をか怨まん。", "労す可きを択びて之を労す。又焉をか怨まん。") == \
        "之を労す。又誰をか怨まん。"
    # 所以：exp「る所以な」got「るゆゑん」（frags ゆゑん×15）
    assert style_kana_to_kanji_g("其れゆゑんなり。", "其の所以なり。") == "其れ所以なり。"
    # 所謂：exp「いはゆる」→ 所謂（frags いはゆる×14）
    assert style_kana_to_kanji_g("いはゆる君子は", "所謂君子は") == "所謂君子は"
    # 相：exp「相視る」got「たがいに視る」（frags たがいに×18）
    assert style_kana_to_kanji_g("たがいに視ること勿れ。", "相視ること勿れ。") == "相視ること勿れ。"


def test_classic_sentence_still_intact():
    """经典句/语料外在白文=自身时不动。"""
    for t in ("吾十有五而志于学", "学而時習之", "また明日会いましょう",
              "またいとこ", "ゆゑん深し", "いはゆる古典", "たがいに手を携う"):
        assert style_kana_to_kanji_g(t, t) == t, "语料外被改: %s" % t
