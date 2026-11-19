# -*- coding: utf-8 -*-
"""test_rule_e_kana_kanji.py — D14: Rule E（假名→汉字）的回归测试。

Rule E 与 Rule D 同构：kanbun.info 的規範書き下し把汉语虚词写成汉字，
引擎写成假名。数据依据（eval/day14_*.json，1000 条，基线 avgDist 25.201）：

    字   expected  引擎输出   输出里的假名   expected 里的真实词形
    皆      36        0        みな          皆 裸 31 / 皆な 5
    既      25        0        すでに        既に 20 / 既 3 / 既にし 2
    猶      33        1        なお          猶お 29 / 猶しく 4
    豈      10        0        あに          豈に 10
    唯      17        0        ただ          唯だ 16 / 唯 1

**词形按 expected 的真实形态**，不是裸汉字替换（tools/day14_shape2.py）：
裸替只有 -0.099，按词形是 -0.153。

最终（tools/day14_final2.py 逐条核对）：改写 95 / 改善 91 / **变差 0**，
avgDist 25.201→25.048；幂等 1000/1000。

本文件锁住七件事：
  1. 白文含对应汉字 → 替换成 expected 的词形（既に/猶お/豈に/唯だ/皆）；
  2. 白文不含 → **一个假名都不动**（白文护栏）；
  3. 异体字也算（旣/既）；
  4. 词界护栏：みなす/なおす/ただいま/みんな 不被拆（假名后接假名则不动）；
  5. 幂等：应用两次结果不变；
  6. 与 Rule D 叠加互不破坏；旧入口 style_fix 不受影响；
  7. 经典句与语料外现代和文一字不动。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    E_KANA_TO_KANJI,
    style_fix,
    style_fix_with_hakubun,
    style_kana_to_kanji,
)


def test_table_shape():
    """表本身的结构：5 条、每条 (假名, 词形, 护栏元组)，且护栏含该词形的首字。"""
    assert len(E_KANA_TO_KANJI) == 5
    for kana, repl, guard in E_KANA_TO_KANJI:
        assert isinstance(kana, str) and kana
        assert isinstance(repl, str) and repl
        assert isinstance(guard, tuple) and guard
        assert repl[0] in guard, "护栏必须包含替换词形的首字"


def test_word_forms_match_expected_shapes():
    """词形必须是 expected 里实际出现的形态（不是裸汉字）。"""
    forms = {kana: repl for kana, repl, _g in E_KANA_TO_KANJI}
    assert forms["すでに"] == "既に"
    assert forms["なお"] == "猶お"
    assert forms["あに"] == "豈に"
    assert forms["ただ"] == "唯だ"
    assert forms["みな"] == "皆"


def test_all_replacements_when_hakubun_has_char():
    """白文含对应汉字 → 五条全部生效，且是带送り仮名的词形。"""
    text = "皆すでになおあにただ"
    out = style_kana_to_kanji(text, "皆既猶豈唯")
    assert out == "皆既に猶お豈に唯だ"


def test_no_change_when_hakubun_lacks_char():
    """白文不含任何对应汉字 → 一字不动（白文护栏）。"""
    text = "みな、すでに、なお、あに、ただ"
    assert style_kana_to_kanji(text, "吾十有五而志于学") == text


def test_partial_guard_only_affects_matching_entry():
    """白文只含「皆」→ 只换 みな，其余假名保持原样。"""
    assert style_kana_to_kanji("皆すでにみな", "皆之有") == "皆すでに皆"


def test_variant_kanji_ji_accepts_both_forms():
    """旣（异体）与 既 都算「白文有此字」。"""
    assert style_kana_to_kanji("すでに帰る", "旣而歸") == "既に帰る"
    assert style_kana_to_kanji("すでに帰る", "既得之") == "既に帰る"


def test_word_boundary_guard_protects_longer_words():
    """词界护栏：命中更长词清单 → 整段保持不动。"""
    # みなす（看做）不是 皆
    assert style_kana_to_kanji("之をみなす", "皆") == "之をみなす"
    # なおす（直す）
    assert style_kana_to_kanji("なおす", "猶") == "なおす"
    # ただいま
    assert style_kana_to_kanji("ただいま", "唯") == "ただいま"
    # みんな
    assert style_kana_to_kanji("みんなで行く", "皆") == "みんなで行く"


def test_adjacent_candidates_do_not_interfere():
    """回归：相邻候选词不能互相干扰。

    这是本规则第一版的真实 bug——用「后接假名就挡」做词界护栏时，
    `皆すでになおあにただ` 里 すでに 的后面正好是 なお 的「な」，
    于是 すでに 被误判为更长词而没替换，`なお` 也随之错位，二次应用还不幂等。
    改成「命中更长词清单才挡」后修复。
    """
    text = "皆すでになおあにただ"
    out = style_kana_to_kanji(text, "皆既猶豈唯")
    assert out == "皆既に猶お豈に唯だ", out
    assert style_kana_to_kanji(out, "皆既猶豈唯") == out


def test_word_boundary_does_not_block_legit_cases():
    """词界护栏不能挡掉真词：后面是汉字/标点/句末时要替换。"""
    assert style_kana_to_kanji("みな之を知る", "皆") == "皆之を知る"
    assert style_kana_to_kanji("みな。", "皆") == "皆。"
    assert style_kana_to_kanji("すでに", "既") == "既に"


def test_idempotent():
    """应用两次 == 应用一次。"""
    text = "皆すでになおあにただ"
    hb = "皆既猶豈唯"
    once = style_kana_to_kanji(text, hb)
    assert style_kana_to_kanji(once, hb) == once


def test_no_hakubun_keeps_word_boundary_guard():
    """空白文：白文护栏不生效（纯函数语义），但词界护栏仍在。

    注意：探针用两个**独立**字符串。像「みなすでに」这种 みなす/すでに 重叠的串
    有歧义（す 同时属于 みなす 和 すでに），不拿它做断言。
    """
    assert style_kana_to_kanji("之をみなす", "") == "之をみなす"   # 更长词被保护
    assert style_kana_to_kanji("すでに", "") == "既に"            # 无白文也替换


def test_real_sentence_from_corpus():
    """语料原句：子曰、唯上知與下愚不移。"""
    got = "子曰く、ただ上は下とも愚なるを知りて移さず。"
    out = style_kana_to_kanji(got, "子曰、唯上知與下愚不移。")
    assert out.startswith("子曰く、唯だ上は")


def test_composes_with_rule_d():
    """与 Rule D 叠加：これ→之 与 みな→皆 互不破坏。"""
    out = style_fix_with_hakubun("これを見る。みなこれを知る。", "此之見。皆知之。")
    assert "之を見る" in out
    assert "皆" in out
    assert "これ" not in out


def test_old_style_fix_unaffected():
    """旧入口 style_fix 不跑 Rule E（供 pytest/验收门/离线脚本按旧语义调用）。"""
    assert style_fix("みなすでに") == "みなすでに"
    assert style_fix("これを見る") == "これを見る"


def test_classic_sentence_still_intact():
    """经典句：Rule E 不许碰它（白文无这五个汉字）。"""
    out = style_fix_with_hakubun("王は左右を顧みて而して他を言う", "王顧左右而言他")
    assert out == "王は左右を顧みて而して他を言う"
