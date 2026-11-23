# -*- coding: utf-8 -*-
"""test_night72_rule_l.py — N72: Rule L（かな→漢字第 8 批＋N69/N70 拒案翻案）锁定测试。

方法论同 N70 test（rule K）：每条正例（实语料行型）＋无护栏反例（一字不动）＋
guard=() 無条件規則（はざる接続拆分）の空白文発火 / 空白文で guard 規則も発火
（E〜K 世代同语义）/ いずくんぞ 2 条の多守り行先勝（安∧惡 1 行実測）／
拒案不复活（はざる裸・とも・がため落选字形・べからず・べず・はざるか/に）／
長語マスク（ただす・ゆえん）／链序 K→L／幂等／無 kana 现代句一字不动／
N69 変差行（24shihin10-4 の はざるとも）が L で不触であることの锁定。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    L_KANA_TO_KANJI, L_LONGER_WORDS, E_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_l, style_fix_with_hakubun,
)


# ---------- 各条正例（実語料行型） ----------
def test_rule_l_tsuhini_owari():
    # dasoku-x14（白文含終；exp 終に）
    assert style_kana_to_kanji_l("蛇の足にたる者、つひに其の酒を亡ぶ",
                                 "蛇の足を為す者、終に其の酒を亡えり") == \
        "蛇の足にたる者、終に其の酒を亡ぶ"


def test_rule_l_izukunzo_an():
    # montai01-11 行型（白文含安；exp 安んぞ）
    assert style_kana_to_kanji_l("いずくんぞ能く遠きを致す",
                                 "安んぞ能く遠きを致さん") == "安んぞ能く遠きを致す"


def test_rule_l_izukunzoaku():
    # hippu-1 行型（白文は旧字体「惡」——新字体「悪」で探すと 0 命中になる N69 教训）
    assert style_kana_to_kanji_l("彼はいずくんぞ敢えて我を当するか",
                                 "彼は惡んぞ敢えて我に当らんや") == "彼は悪んぞ敢えて我を当するか"
    # 新字体 白文でも発火（guard は 惡/悪 の OR）
    assert style_kana_to_kanji_l("いずくんぞ来たるか", "悪んぞ来たるや") == "悪んぞ来たるか"


def test_rule_l_tada_dada():
    # kokifuku-5（白文含但；exp 但だ 26/26）
    assert style_kana_to_kanji_l("家を持すはただ四壁を立つ有り",
                                 "家を持するも但だ四立の壁有るのみ") == "家を持すは但だ四壁を立つ有り"


def test_rule_l_yue_yuin():
    # rongo0911-1 行型（白文含由；exp 由の詐り）
    assert style_kana_to_kanji_l("久なるか、之ゆえ詐るを行うなり",
                                 "由の詐りを行うや") == "久なるか、之由詐るを行うなり"


def test_rule_l_hajime_hajime():
    # kanpo-3 行型（白文含始；exp 始め）
    assert style_kana_to_kanji_l("吾ははじめ時を困る",
                                 "吾始め困しみし時") == "吾は始め時を困る"


def test_rule_l_gatame_i():
    # ayamachifu-1 行型（白文含舊字 爲；exp と為す——repl 為 が 為すの為 に对位）
    assert style_kana_to_kanji_l("孰は学を好むをがため",
                                 "孰か学を好むと爲す") == "孰は学を好むを為"
    # atauruno-2 行型（exp が為に 行は repl 為 で same 距離——0 変差の内側、挙動を锁定）
    assert style_kana_to_kanji_l("民は之がため憂労す",
                                 "民は之が爲に憂労す") == "民は之為憂労す"


def test_rule_l_hazaru_nari():
    # mujun-5 行型（guard=() 無条件・接続拆分）
    assert style_kana_to_kanji_l("其の人は応へる能はざるなり",
                                 "其の人応うる能わざるなり") == "其の人は応へる能わざるなり"


def test_rule_l_hazaru_wo():
    # iukotoata-1 行型
    assert style_kana_to_kanji_l("者を言う能はざるを似る",
                                 "言うこと能わざる者に似たり") == "者を言う能わざるを似る"


# ---------- 反例：守り字無しは一字不動（guard 規則） ----------
def test_rule_l_guard_miss_untouched():
    assert style_kana_to_kanji_l("つひに至らず", "遂に至らず") == "つひに至らず"
    assert style_kana_to_kanji_l("いずくんぞ疑わん", "焉くんぞ疑わん") == "いずくんぞ疑わん"
    assert style_kana_to_kanji_l("ただ四壁", "唯だ四壁") == "ただ四壁"      # E の 唯 分工行
    assert style_kana_to_kanji_l("ただ四壁", "惟だ四壁") == "ただ四壁"      # I の 惟 分工行
    assert style_kana_to_kanji_l("之ゆえ詐る", "故の詐り") == "之ゆえ詐る"   # 由 無し（故 行は対象外）
    assert style_kana_to_kanji_l("はじめまして", "初めまして") == "はじめまして"


# ---------- guard=() 無条件規則：空白文でも発火（K 世代同语义） ----------
def test_rule_l_empty_guard_is_not_dead_rule():
    assert style_kana_to_kanji_l("能はざるなり", "何の守り字も無い白文") == "能わざるなり"
    assert style_kana_to_kanji_l("能はざるを恐す", "") == "能わざるを恐す"


def test_rule_l_empty_hakubun_guard_rules_fire():
    # E〜K 世代同款：空白文（hb=""）では guard 規則も適用（词界护栏のみ）
    assert style_kana_to_kanji_l("つひに大なりたらず", "") == "終に大なりたらず"
    assert style_kana_to_kanji_l("ただ四壁", "") == "但だ四壁"


# ---------- いずくんぞ 2 条：多守り行は先勝（安） ----------
def test_rule_l_izukunzo_multi_guard_first_wins():
    # 実測多守り行 sanryaku03-4（安∧惡）——表順どおり 安んぞ が勝つ
    assert style_kana_to_kanji_l("いずくんぞ帰らずんば",
                                 "安くんぞ帰らざれば惡んぞ帰らざるや") == "安んぞ帰らずんば"


# ---------- 長語マスク ----------
def test_rule_l_longer_words_mask():
    assert style_kana_to_kanji_l("其れをただす", "但だ其れを正す") == "其れをただす"
    assert style_kana_to_kanji_l("ただいま帰る", "但だ今帰る") == "ただいま帰る"
    assert style_kana_to_kanji_l("之ゆえんに非ず", "之が為に由るに非ず") == "之ゆえんに非ず"
    assert style_kana_to_kanji_l("由縁ゆえにあらず", "由縁に由らず") == "由縁ゆえにあらず"


# ---------- 表の整形性 ----------
def test_rule_l_table_wellformed():
    assert len(L_KANA_TO_KANJI) == 9
    for kana, repl, guard in L_KANA_TO_KANJI:
        assert guard == () or all(isinstance(g, str) and g for g in guard), kana
        assert repl not in kana, kana
        # repl は終字形（响应端 normalize_shinjitai が再変換しない）
        assert normalize_shinjitai(repl) == repl, kana
    kanas = {k for k, _r, _g in L_KANA_TO_KANJI}
    assert kanas == {"つひに", "いずくんぞ", "ただ", "ゆえ", "はじめ",
                     "がため", "はざるなり", "はざるを"}
    izu = [(r, g) for k, r, g in L_KANA_TO_KANJI if k == "いずくんぞ"]
    assert len(izu) == 2 and izu[0] == ("安んぞ", ("安",)) and izu[1] == ("悪んぞ", ("惡", "悪"))


def test_rule_l_longer_words_shape():
    assert set(L_LONGER_WORDS.keys()) == {"つひに", "いずくんぞ", "ただ", "ゆえ",
                                          "はじめ", "がため", "はざるなり", "はざるを"}
    assert set(L_LONGER_WORDS["ただ"]) == set(E_LONGER_WORDS["ただ"]) | {"たださ"}
    assert L_LONGER_WORDS["ゆえ"] == ("ゆえん", "ゆえに")
    for k in ("つひに", "いずくんぞ", "はじめ", "がため", "はざるなり", "はざるを"):
        assert L_LONGER_WORDS[k] == (), k


# ---------- 拒案不复活 ----------
def test_rule_l_rejected_not_registered():
    kanas = {k for k, _r, _g in L_KANA_TO_KANJI}
    for banned in ("はざる", "とも", "べからず", "べず", "はざるか", "はざるに"):
        assert banned not in kanas, banned
    gatame_repls = [r for k, r, _g in L_KANA_TO_KANJI if k == "がため"]
    assert gatame_repls == ["為"]  # が為に/が為/為に は落选（同一 kana 一条のみ）


def test_rule_l_rejected_rows_untouched():
    # N69 変差行 24shihin10-4（はざるとも）——L は触らない
    assert style_kana_to_kanji_l("真なりて奪はざるとも、強いて貧なり易きを得る",
                                 "真に與えらるるは奪われず、強いて得れば貧なり易し") == \
        "真なりて奪はざるとも、強いて貧なり易きを得る"
    # とも（1 変差 yoryoezu-1）・べからず（5 変差）・べず——全部不触
    assert style_kana_to_kanji_l("趙とも親するを従う", "趙と従親せしめんとす") == \
        "趙とも親するを従う"
    assert style_kana_to_kanji_l("得べからずして", "得べからずして") == "得べからずして"
    assert style_kana_to_kanji_l("覚るべず", "覚る可らず") == "覚るべず"
    # 残量 singleton（か/に/者 接続）は拒（無益/拆分外）——不触
    assert style_kana_to_kanji_l("能はざるか", "能わずか") == "能はざるか"
    assert style_kana_to_kanji_l("失はざる者なり", "失わざる者なり") == "失はざる者なり"


# ---------- 链序 K→L 与幂等 ----------
def test_rule_l_chain_order_after_k():
    # K の ひて→いて（無条件）と L の つひに→終に・いずくんぞ→安んぞ 同時発火
    full = style_fix_with_hakubun("相謂ひてつひに曰く、いずくんぞ能く疑わん",
                                  "相謂いて終に曰く、安んぞ能く疑わん")
    assert full == "相謂いて終に曰く、安んぞ能く疑わん"


def test_rule_l_chain_combo_with_k():
    # K の いやしくも→苟くも（無条件）＋L の ただ→但だ（guard 但）
    full = style_fix_with_hakubun("いやしくもただ之を患す",
                                  "苟くも但だ之を患う")
    assert full == "苟くも但だ之を患す"


def test_rule_l_idempotent():
    hb = "蛇の足を為す者、終に其の酒を亡えり、但だ始めに由るや"
    t1 = style_fix_with_hakubun("蛇の足にたる者、つひに其の酒を亡ぶ、ただはじめにゆえんあり", hb)
    t2 = style_fix_with_hakubun(t1, hb)
    assert t1 == t2


# ---------- 语料外探针（无 kana 目标的现代句一字不动） ----------
def test_rule_l_modern_probes():
    assert style_fix_with_hakubun("はじめまして、ただいま帰りました", "その通りだ") == \
        "はじめまして、ただいま帰りました"
    assert style_fix_with_hakubun("王は左右を顧みて而して他を言う",
                                  "王は左右を顧みて而して他を言う") == \
        "王は左右を顧みて而して他を言う"


def test_rule_l_classic_sentence_regression():
    # 经典句（accept_night CLASSIC_CASES 同款）不回归
    full = style_fix_with_hakubun("王は左右を顧みて而して他を言う", "王顧左右而言他")
    assert full == "王は左右を顧みて而して他を言う"
