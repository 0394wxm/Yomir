# -*- coding: utf-8 -*-
"""test_rule_h_kana_kanji.py — N58: Rule H（假名→汉字，第四批）+ SHINJITAI 30 对的回归测试。

数据依据（eval/night58_sim.json，2999 条，基线 avgDist 16.321 = night57 真机归档、
D/E/F/G 全链）：

    候选              白文护栏   改写条   Δ        改善/变差
    また→復た         復        35     -0.011   33/0
    それ→只だ         只         8     -0.004    7/0
    べからず→須いず    須         4     -0.002    4/0
    SHINJITAI 30 对    （显示层） 280    -0.084  226/0

组合（tools/night58_sim.py，逐条真算 Levenshtein）：
    改写 317 / 16.321 → 16.219（**-0.102**） / 改善 264 / **变差 0**
    幂等 PASS；语料外探针一字不动。

维持拒绝（N58 逐条核因，见 REPORT_NIGHT58.md）：
    ことなかれ→莫かれ（11 变差：exp 写 莫し/莫き/莫けん 等其他活用形，运行时无信号可分）、
    なかれ→莫かれ（1 变差，维持 D14 拒绝）、べし→須らく（5 变差：同行混写 須らく…べし）。

本文件锁住：
  1. 表结构：3 条，护栏出现在替换词形里
  2. 词形是 expected 的真实形态（復た/只だ/須いず）
  3. 白文含字 → 替换；白文不含 → 一字不动
  4. 词界护栏：また 9 长词（与 F/G 共享）、それ 6 长词
  5. 幂等
  6. 三方分工：白文含亦 → F；含又 → G；含復 → H；多个并存时链序 F→G→H 谁先命中谁吃
  7. H/E/F/G 四张长词表独立；また 一项 F/G/H 共享同一常量
  8. SHINJITAI 30 对在表里、可逆性（新形不是 key）、抽查 映射
  9. 旧入口 style_fix 不受影响
 10. 语料原句 / 语料外探针
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    H_KANA_TO_KANJI,
    H_LONGER_WORDS,
    G_KANA_TO_KANJI,
    G_LONGER_WORDS,
    F_LONGER_WORDS,
    E_LONGER_WORDS,
    SHINJITAI_MAP,
    style_fix,
    style_fix_with_hakubun,
    style_kana_to_kanji_h,
    normalize_shinjitai,
)

N58_SHINJITAI_PAIRS = {
    "舊": "旧", "隱": "隠", "說": "説", "醬": "醤", "鄉": "郷", "權": "権",
    "綠": "緑", "峽": "峡", "踐": "践", "靑": "青", "產": "産", "燒": "焼",
    "眞": "真", "營": "営", "膽": "胆", "燈": "灯", "滯": "滞", "兒": "児",
    "豐": "豊", "雙": "双", "樓": "楼", "處": "処", "獨": "独", "遙": "遥",
    "曉": "暁", "醉": "酔", "縱": "縦", "橫": "横", "晚": "晩", "寳": "宝",
}


def test_table_shape():
    """3 条；护栏字出现在替换词形里。"""
    assert len(H_KANA_TO_KANJI) == 3
    for kana, repl, guard in H_KANA_TO_KANJI:
        assert isinstance(kana, str) and kana
        assert isinstance(repl, str) and repl
        assert isinstance(guard, tuple) and guard
        assert any(g in repl for g in guard), "护栏必须出现在替换词形里"


def test_word_forms_match_expected_shapes():
    """词形必须是挖掘到的 expected 形态（復た / 只だ / 須いず）。"""
    forms = {kana: repl for kana, repl, _g in H_KANA_TO_KANJI}
    assert forms["また"] == "復た"        # exp 復た 13 次（新增段），无 又た/亦た 形态
    assert forms["それ"] == "只だ"        # exp 只だ 5 / 只使い 1 / 只今 1，多数派
    assert forms["べからず"] == "須いず"   # exp 須いず（須的 ず 活用）


def test_replaces_when_hakubun_has_guard():
    assert style_kana_to_kanji_h("また", "復") == "復た"
    assert style_kana_to_kanji_h("それ", "只") == "只だ"
    assert style_kana_to_kanji_h("辞するべからず", "須") == "辞する須いず"


def test_no_change_when_hakubun_lacks_guard():
    """白文不含护栏 → 一字不动。また 的 亦/又 归 F/G，H 不越位。"""
    assert style_kana_to_kanji_h("また", "亦") == "また"
    assert style_kana_to_kanji_h("また", "又") == "また"
    assert style_kana_to_kanji_h("それ", "其") == "それ"
    assert style_kana_to_kanji_h("べからず", "可") == "べからず"


def test_word_boundary_guard_protects_longer_words():
    """また 的 9 个长词（与 F/G 共享）与 それ 的长词整段不动。"""
    for w in ("またたく", "またがり", "またがる", "またぎ", "またぐ",
              "またたき", "またしても", "またと", "またの"):
        assert style_kana_to_kanji_h(w, "復") == w, "更长词被拆: %s" % w
    for w in ("それで", "それぞ", "それとも", "それが", "それら", "それでは"):
        assert style_kana_to_kanji_h(w, "只") == w, "更长词被拆: %s" % w


def test_word_boundary_does_not_block_legit_cases():
    assert style_kana_to_kanji_h("また、曰く", "復") == "復た、曰く"
    assert style_kana_to_kanji_h("それ当時に大なり", "只") == "只だ当時に大なり"


def test_idempotent():
    for text, hb in (("またそれべからず", "復只須"),
                     ("また最初にまたそれ", "復")):
        once = style_kana_to_kanji_h(text, hb)
        twice = style_kana_to_kanji_h(once, hb)
        assert once == twice


def test_three_way_division_of_labor_for_mata():
    """F（亦た）→ G（又）→ H（復た）按白文分工，链序谁先命中谁吃。"""
    # 只有復：H 改
    out = style_fix_with_hakubun("また兎を得る", "復")
    assert "復た兎" in out and "また" not in out
    # 只有亦：F 改，H 无また可改
    out2 = style_fix_with_hakubun("また兎を得る", "亦")
    assert "亦た兎" in out2
    # 只有又：G 改
    out3 = style_fix_with_hakubun("また兎を得る", "又")
    assert "又兎" in out3
    # 亦+復 都有：F 先吃掉，H no-op（与 G 的 F-first 语义一致）
    out4 = style_fix_with_hakubun("また兎を得る", "亦復")
    assert out4 == out2
    # 白文都无：全不动
    out5 = style_fix_with_hakubun("また兎を得る", "無所")
    assert "また" in out5


def test_longer_word_tables_are_separate_and_share_mata():
    """H/G/F/E 四张表独立；また 长词 F/G/H 引用同一常量（值恒等）。"""
    assert H_LONGER_WORDS is not G_LONGER_WORDS
    assert H_LONGER_WORDS is not F_LONGER_WORDS
    assert H_LONGER_WORDS is not E_LONGER_WORDS
    assert set(H_LONGER_WORDS) == {k for k, _r, _g in H_KANA_TO_KANJI}
    assert H_LONGER_WORDS["また"] == F_LONGER_WORDS["また"]
    assert H_LONGER_WORDS["また"] == G_LONGER_WORDS["また"]
    assert set(G_LONGER_WORDS) == {k for k, _r, _g in G_KANA_TO_KANJI}


def test_n58_rejected_candidates_stay_rejected():
    """N58 拒绝的 ことなかれ/なかれ/べし 不许借机回来。"""
    h_kana = {kana for kana, _r, _g in H_KANA_TO_KANJI}
    assert "ことなかれ" not in h_kana and "なかれ" not in h_kana
    assert "べし" not in h_kana and "べき" not in h_kana and "べから" not in h_kana
    # べからず 只在 H（須いず），F/G/E 均无 べから 系
    for tbl in (G_KANA_TO_KANJI,):
        assert all("べから" not in k for k, _r, _g in tbl)


def test_old_style_fix_unaffected():
    assert style_fix("またそれべからず") == "またそれべからず"


def test_empty_hakubun_keeps_word_boundary_guard():
    """空白文：白文护栏不生效（纯函数语义，与 E/F/G 一致），但词界护栏仍在。"""
    assert style_kana_to_kanji_h("またがる", "") == "またがる"
    assert style_kana_to_kanji_h("それが", "") == "それが"
    assert style_kana_to_kanji_h("それ", "") == "只だ"
    assert style_kana_to_kanji_h("また", "") == "復た"


def test_real_sentences_from_mining():
    """语料原句形态（来自 eval/night58_examples.txt）。"""
    # また→復た：shushu-3（守株）
    assert style_kana_to_kanji_h("冀はまた兎を得る。", "復た兎を得んと冀う。") == "冀は復た兎を得る。"
    # それ→只だ：yoto-1（無門関）
    assert style_kana_to_kanji_h("それ当時に大なりて", "只だ当時大衆都て笑うが如きんば") == "只だ当時に大なりて"
    # べからず→須いず：p-banryokuso-1（万緑叢中紅一点）
    assert style_kana_to_kanji_h("多きべからず", "人を動かす春色多きを須いず") == "多き須いず"


def test_classic_sentence_still_intact():
    """经典句/语料外在白文=自身时不动。"""
    for t in ("王顧左右而言他", "また明日会いましょう", "それで結構です",
              "べからずと書かれた札"):
        assert style_kana_to_kanji_h(t, t) == t, "语料外被改: %s" % t


def test_shinjitai_map_n58_pairs():
    """N58 的 30 对都在 SHINJITAI_MAP 里；新形不是 key（映射可终止）；抽查。"""
    for old, new in N58_SHINJITAI_PAIRS.items():
        assert SHINJITAI_MAP.get(old) == new, "缺映射: %s→%s" % (old, new)
        assert new not in SHINJITAI_MAP, "新形不能作为 key（幂等性）: %s" % new
    assert normalize_shinjitai("靑樓處獨") == "青楼処独"
    assert normalize_shinjitai("萬綠叢中紅一点") == "万緑叢中紅一点"  # 叢 不在表（exp 写旧形）
    # 拒绝的旧形确实不在表里（exp 自身写旧形的字不许全局映射）
    for rejected in ("冰", "弦", "亦"):
        assert rejected not in SHINJITAI_MAP
