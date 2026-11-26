# -*- coding: utf-8 -*-
"""test_night104_rule_u.py — N104 拍板夜：Rule U（かな→漢字第 16 批・なかれ→莫かれ
guard 莫・撤 0 変差硬门の一条収録）锁定测试。

方法论同 N99 test：正例（実語料行型・night104_sim 改善行 3 行）＋変差 1 行 kokyo09-5
の行動ロック（N98 実測 ID・got→new 断言・sim JSON の ID 集合一致）＋無護栏反例
（guard 莫 外一字不動・空白文で発火＝E〜K 世代同语义）／I→M→U 守り字三分割
（毋/勿/莫 の guard 分消費・post-N 残量は白文 莫 行のみ）＋禁区不復活（T 键・Q こと
なく・ことなき・嗟や・がため——本夜一字不動の再発防止）／構造ロック（1 条・長詞
マスク なかれ主義＝事勿れ主義 守り・repl 终字形）／链序 T→U（pipeline 順・べからず
族との併用）／幂等／無 kana 现代句一字不动／N84 echo 行型一字不动。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    U_KANA_TO_KANJI, U_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_u, style_fix_with_hakubun,
)

EV = os.path.join(ROOT, "eval")


# ---------- 正例（実語料行型・night104_sim 改善行 3 行） ----------
def test_rule_u_positive_improvement_rows():
    # toushisen034-4 行型（白文 可惜落花君莫掃 → got「落花の君を惜む可く掃くことなかれ」
    # →「…こと莫かれ」・11→10 改善）
    assert style_kana_to_kanji_u("落花の君を惜む可く掃くことなかれ", "可惜落花君莫掃") == \
        "落花の君を惜む可く掃くこと莫かれ"
    # toushisen409-3 行型（白文 行人莫上長堤望 → 12→11 改善）
    assert style_kana_to_kanji_u("人を行いて堤望を長きを上すことなかれ", "行人莫上長堤望") == \
        "人を行いて堤望を長きを上すこと莫かれ"
    # soko-3 行型（白文 群臣莫及 → 17→16 改善）
    assert style_kana_to_kanji_u(
        "主は曰いて、宋の公は威すは徳の器を容して、群臣及ぶことなかれ。",
        "主曰、宋公威容德器、群臣莫及。") == \
        "主は曰いて、宋の公は威すは徳の器を容して、群臣及ぶこと莫かれ。"


# ---------- 変差 1 行の行動ロック（N98 実測 ID・got→new 一致＝拍板許容行） ----------
def test_rule_u_variation_row_kokyo09_5_lock():
    # kokyo09-5（孝経・白文 嚴父莫大於配天＝すことなかれ 行・莫大 co-occurrence 死因）
    # N78 umbrella ことなかれ→こと莫かれ の死行そのもの＝N prefix keys（することなかれ は
    # 「すること＋なかれ」で「す＋ことなかれ」非匹配）の機構境界を本行が維持する
    assert style_kana_to_kanji_u("父を厳して大なりて天を配すことなかれ。", "嚴父莫大於配天。") == \
        "父を厳して大なりて天を配すこと莫かれ。"          # kokyo09-5 15→16（拍板許容・唯一変差）


def test_rule_u_variation_id_lock_n98():
    # N98 実測変差 1 行の ID ロック（eval/night104_sim.json 読み・17/13/1・超出不可）
    sim = json.load(open(os.path.join(EV, "night104_sim.json"), encoding="utf-8"))
    assert sim["verdict"] == "PASS"
    g = sim["gates"]["nakare"]
    assert g["worse_ids"] == ["kokyo09-5"]
    assert g["changed"] == 17 and g["better"] == 13 and g["worse"] == 1
    assert g["idempotent_bad"] == 0
    assert abs(g["delta8165"] - (-0.002)) <= 0.0005
    assert g["pred_exact4000"] == 24 and g["pred_exact8165"] == 30
    assert g["changed4000"] == 12


# ---------- 無護栏反例（guard 莫 外＝一字不動・空白文で発火） ----------
def test_rule_u_guard_negative_and_empty_hb():
    # guard 莫 外＝一字不動（I 毋/M 勿 の領域も U は触らない）
    assert style_kana_to_kanji_u("落花の君を惜む可く掃くことなかれ", "可惜落花君惜掃") == \
        "落花の君を惜む可く掃くことなかれ"   # 莫 無し＝不動
    assert style_kana_to_kanji_u("掃くことなかれ", "掃莫花勿") == "掃くこと莫かれ"   # 莫 有り＝発火（対照）
    assert style_kana_to_kanji_u("群臣及ぶことなかれ", "將未勿毋") == "群臣及ぶことなかれ"
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_u("掃くことなかれ", "") == "掃くこと莫かれ"
    assert style_kana_to_kanji_u("及ぶべきことなかれ。", "") == "及ぶべきこと莫かれ。"


# ---------- I→M→U 守り字三分割（毋/勿/莫 の guard 分消費・链不变式） ----------
def test_rule_u_guard_partition_with_i_and_m():
    # 白文 毋 → Rule I が消費（U は発火しない）
    assert style_fix_with_hakubun("悌するに善くなかれ。", "毋") == "悌するに善く毋かれ。"
    # 白文 勿 → Rule M が消費（U は発火しない）
    assert style_fix_with_hakubun("悌するに善くなかれ。", "勿") == "悌するに善く勿かれ。"
    # 白文 莫 → Rule U が消費（本夜新設の第三片）
    assert style_fix_with_hakubun("悌するに善くなかれ。", "莫") == "悌するに善く莫かれ。"


# ---------- 禁区不復活（本夜一字不動の再発防止） ----------
def test_rule_u_forbidden_zones_untouched():
    # T 键（べからず族＝T の領域）・ことなく（Q の領域）・ことなき・嗟や・がため／
    # 何のごとく・毋/勿かれ済み行——いずれも U の 1 键外＝一字不動
    assert style_kana_to_kanji_u("断絶するべからず。", "莫") == "断絶するべからず。"
    assert style_kana_to_kanji_u("之を事うることなく。", "事莫") == "之を事うることなく。"
    assert style_kana_to_kanji_u("欺すことなきなり。", "莫") == "欺すことなきなり。"
    assert style_kana_to_kanji_u("嗟や、人を害すこと勿かれ。", "乎勿") == \
        "嗟や、人を害すこと勿かれ。"   # 勿かれ 済み（M 消費後）行に U は触らない
    assert style_kana_to_kanji_u("己に如かざる者を友すること毋かれ。", "友莫") == \
        "己に如かざる者を友すること毋かれ。"   # 毋かれ 済み（I 消費後）行に U は触らない
    assert style_kana_to_kanji_u("武王がために備えしむ。", "莫") == "武王がために備えしむ。"


# ---------- 構造ロック ----------
def test_rule_u_structure_and_chain_order():
    assert len(U_KANA_TO_KANJI) == 1
    assert [e[0] for e in U_KANA_TO_KANJI] == ["なかれ"]
    assert [e[1] for e in U_KANA_TO_KANJI] == ["莫かれ"]
    assert [list(e[2]) for e in U_KANA_TO_KANJI] == [["莫"]]
    assert all(len(e) == 3 for e in U_KANA_TO_KANJI)
    assert set(U_LONGER_WORDS) == {"なかれ"}
    assert [v for v in U_LONGER_WORDS.values()] == [("なかれ主義",)]
    # 長詞マスク：ことなかれ主義（事勿れ主義・現代語複合語）は一字不動（N64 probe 同款）
    assert style_kana_to_kanji_u("ことなかれ主義", "莫れ主義とは言わない") == "ことなかれ主義"
    assert style_fix_with_hakubun("ことなかれ主義", "莫れ主義とは言わない") == "ことなかれ主義"
    for _kana, repl, _guard in U_KANA_TO_KANJI:
        assert normalize_shinjitai(repl) == repl
    # 構造冪等：repl 莫かれ に なかれ 非含有（再発火なし）
    assert "なかれ" not in "莫かれ"
    # 链序 T→U：べからず族（T）と なかれ（U）の同一 chain 併用
    out = style_fix_with_hakubun("断絶するべからず。掃くことなかれ。", "不可斷絕掃花莫")
    assert out == "断絶する可からず。掃くこと莫かれ。"
    # U 適用後の got に なかれ が残らない（guard 莫 内）
    out2 = style_fix_with_hakubun("掃くことなかれ。及ぶべきことなかれ。", "掃莫花莫")
    assert out2 == "掃くこと莫かれ。及ぶべきこと莫かれ。"
    assert "なかれ" not in out2


def test_rule_u_idempotent_and_modern():
    for text, hb in (("掃くことなかれ。", "可惜落花君莫掃"),
                     ("父を厳して大なりて天を配すことなかれ。", "嚴父莫大於配天。")):
        once = style_kana_to_kanji_u(text, hb)
        assert style_kana_to_kanji_u(once, hb) == once
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_u("本日の会議は十時から開始されます。", "") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝白文直出対象・kana なしで U も非発火）
    assert style_kana_to_kanji_u("器械を習い用う", "莫不習用器械") == "器械を習い用う"
