# -*- coding: utf-8 -*-
"""test_night70_rule_k.py — N70: Rule K（仮名遣い族 + 苟くも + Xぞ族拆分）锁定测试。

方法论同 N68 test（rule J）：无条件规则（guard=()）发火 / 空白文发火 /
**空 guard 语义锁定**（不许退化成 E〜J 世代「空 guard=恒常 skip」的死规则）/
Xぞ族共享 kana「なんぞ」白文 guard 互斥（probe 実測多守り行＝無し）/ 拒案 4 条不复活 /
幂等 / 链序 J→K / 无 kana 现代句一字不动（はず 的已知局限如实锁定）。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    K_KANA_TO_KANJI, K_LONGER_WORDS,
    style_kana_to_kanji_k, style_fix_with_hakubun,
)


# ---------- 仮名遣い族（無条件）：各条発火 ----------
def test_rule_k_hite_ite():
    assert style_kana_to_kanji_k("相謂ひて曰く", "舎人相謂いて曰く") == "相謂いて曰く"
    assert style_kana_to_kanji_k("言ひて曰く", "") == "言いて曰く"      # 空白文でも発火


def test_rule_k_hete_ete():
    assert style_kana_to_kanji_k("敢へて我を食べる", "子敢えて我を食らう") == "敢えて我を食べる"
    assert style_kana_to_kanji_k("対へて曰く", "") == "対えて曰く"


def test_rule_k_hazu_wazu():
    assert style_kana_to_kanji_k("夫の人は言はず", "夫の人言わず") == "夫の人は言わず"
    assert style_kana_to_kanji_k("曰はず", "") == "曰わず"


def test_rule_k_hezu_ezu():
    assert style_kana_to_kanji_k("子路対へず", "子路対えず") == "子路対えず"


def test_rule_k_iyashikumo_kakukumo():
    # kana→漢字（exp 全写苟く系；got 15 行白文含苟 15/15）
    assert style_kana_to_kanji_k("いやしくも之を患す", "苟くも之を患う") == "苟くも之を患す"


# ---------- 空 guard 语义锁定：非空白文で死规则化しない ----------
def test_rule_k_empty_guard_is_not_dead_rule():
    # 白文に如何なる守り字候補（盍/奚/曷以外の何でも）も無くても無条件 5 条は発火する。
    # E〜J 世代の条件式（if hb and not any(...)）をそのまま持ち込むと
    # any(())=False → 恒常 skip（死规则）——この test がそれを捕まえる。
    hb = "何の守り字も無い白文"
    assert style_kana_to_kanji_k("言ひて曰く", hb) == "言いて曰く"
    assert style_kana_to_kanji_k("言はず曰く", hb) == "言わず曰く"
    assert style_kana_to_kanji_k("いやしくも疑う", hb) == "苟くも疑う"


# ---------- Xぞ族：共享 kana「なんぞ」、白文 guard 互斥 ----------
def test_rule_k_nanzo_kan():
    # 顏淵季路行（kanbun.info 白文把「盍」保留）
    assert style_kana_to_kanji_k("なんぞ各々志を言はざる", "盍各言爾志") == "盍ぞ各々志を言はざる"


def test_rule_k_nanzo_gei():
    # kikyorainoji-60 行（白文 樂夫天命復奚疑）
    assert style_kana_to_kanji_k("なんぞ疑わん", "樂夫天命復奚疑") == "奚ぞ疑わん"


def test_rule_k_nanzo_katsu():
    # montai02-6 行（白文含曷；exp 側曷んぞ/曷くに 混写行は sim 実測 same 非変差）
    assert style_kana_to_kanji_k("なんぞ奇なるを謂うか", "曷ぞ奇と謂うか") == "曷ぞ奇なるを謂うか"


def test_rule_k_nanzo_no_guard_untouched():
    # 白文に盍/奚/曷が無い行（何のみ・無守り）は一字不動——
    # N68 拒案 なんぞ→何ぞ（2 変差）を復活させない
    assert style_kana_to_kanji_k("なんぞは帰らず", "田園将に蕪れなんとす胡ぞ帰らざる") == \
        "なんぞは帰らず"
    assert style_kana_to_kanji_k("なんぞ至るか", "何ぞ至らざるや") == "なんぞ至るか"


def test_rule_k_nanzo_multi_guard_first_wins():
    # 多守り行は実測語料 0 行（night69_probe.py「多守り行：無し」）——
    # 表順の意味論を锁す：最初の命中規則（盍）が勝つ
    assert style_kana_to_kanji_k("なんぞ有り", "盍奚") == "盍ぞ有り"


# ---------- 表の整形性／拒案不复活 ----------
def test_rule_k_table_wellformed():
    assert len(K_KANA_TO_KANJI) == 8
    unconditional = [k for k, _r, g in K_KANA_TO_KANJI if g == ()]
    assert len(unconditional) == 5
    nanzo = [(r, g) for k, r, g in K_KANA_TO_KANJI if k == "なんぞ"]
    assert len(nanzo) == 3
    assert {g for _r, g in nanzo} == {("盍",), ("奚",), ("曷",)}
    for kana, repl, guard in K_KANA_TO_KANJI:
        # 恒真文字列で guard を偽装しない：guard は空タプルか非空文字列タプル
        assert guard == () or all(isinstance(g, str) and g for g in guard), kana
        assert repl not in kana, kana


def test_rule_k_rejected_not_registered():
    # 拒案 4 条（はざる/とも/がため/つひに）は不上线（0 変差门／目標混写／無益）
    kanas = {k for k, _r, _g in K_KANA_TO_KANJI}
    for banned in ("はざる", "とも", "がため", "つひに"):
        assert banned not in kanas, banned


def test_rule_k_longer_words_shape():
    # 本夜 8 条全部无更长词冲突（probe 実測）——表は系列同構の空壳
    assert set(K_LONGER_WORDS.keys()) == {"ひて", "へて", "はず", "へず",
                                          "いやしくも", "なんぞ"}
    assert all(v == () for v in K_LONGER_WORDS.values())


# ---------- 链序 J→K 与幂等 ----------
def test_rule_k_chain_order_after_j():
    # J の ごとし→若し（白文含若）が先、K の ひて→いて が後
    full = style_fix_with_hakubun("飄蓬のごとしに謂ひて曰く", "飄蓬若に謂いて曰く")
    assert full == "飄蓬の若しに謂いて曰く"


def test_rule_k_full_chain_combo_row():
    # 実在行型（dasoku-3×iyashikumo 混成）：ひて＋いやしくも 同行両発火
    full = style_fix_with_hakubun("相謂ひて曰く、いやしくも之を患す",
                                  "相謂いて曰く、苟くも之を患う")
    assert full == "相謂いて曰く、苟くも之を患す"


def test_rule_k_idempotent():
    hb = "相謂いて奚ぞ疑わん、苟くも之を患う"
    t1 = style_fix_with_hakubun("相謂ひてなんぞ疑わん、いやしくも之を患す", hb)
    t2 = style_fix_with_hakubun(t1, hb)
    assert t1 == t2


# ---------- 语料外探针（无 kana 目标的现代句一字不动） ----------
def test_rule_k_modern_probes():
    assert style_fix_with_hakubun("まさにその通りだ", "その通りだ") == "まさにその通りだ"
    assert style_fix_with_hakubun("それいいじゃん", "君の言う通り") == "それいいじゃん"
    assert style_fix_with_hakubun("王は左右を顧みて而して他を言う",
                                  "王は左右を顧みて而して他を言う") == \
        "王は左右を顧みて而して他を言う"


def test_rule_k_known_limitation_hazu_modern():
    # 已知局限（コード内注記通り、如实锁定）：無条件 はず→わず は現代和文の
    # 「来るはず（筈）」にも発火する。本管线的对象＝漢文訓読输出（筈义が出ない）、
    # 语料内 8165 条実測 0 変差（night69_sim）。
    assert style_kana_to_kanji_k("来るはずがない", "来るはずがない") == "来るわずがない"
