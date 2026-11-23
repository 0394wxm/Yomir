# -*- coding: utf-8 -*-
"""test_night86_rule_o.py — N86: Rule O（かな→漢字第 11 批＋はざる接続者補完＋爲-完了形族）锁定测试。

方法论同 N73/N78 test：每条正例（実語料行型）＋無護栏反例（一字不動）＋
空白文で guard 規則も発火（E〜K 世代同语义）／拒案不复活（べからず・べからざる・
はざる blanket・はざるか・使役族 4 条・べきか・とも・無益 ことな prefix 5 条・
長尾 scan scramble patch 3 件——いずれも night86_sim/probe 拒案の再発防止）／
新旧字体 guard（爲）／链序 N→O（pipeline 順）／幂等／無 kana 现代句一字不动／
N84 echo 行型（白文直出・純漢文尾段）一字不动。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    O_KANA_TO_KANJI, O_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_o, style_fix_with_hakubun,
)


# ---------- 各条正例（実語料行型） ----------
def test_rule_o_hazaru_mono():
    # roushi33-2（白文 不失其所者久。死而不亡者壽。）
    assert style_kana_to_kanji_o("其の所を失はざる者は久なり。死して亡ばざる者は寿なり。",
                                 "不失其所者久。死而不亡者壽。") == \
        "其の所を失わざる者は久なり。死して亡ばざる者は寿なり。"  # 亡ばざる者＝ば で非該当
    # utsuryo24-2（白文 不能死敵者斬——rerun 行型・替换点＝能はざる者）
    assert style_kana_to_kanji_o("敵に死すること能はざる者は斬る。",
                                 "不能死敵者斬") == "敵に死すること能わざる者は斬る。"
    # shiki001a-7 行型（白文 天下有不順者——者有り 型）
    assert style_kana_to_kanji_o("天下は順はざる者有り、黄帝は従いて之を征く。",
                                 "天下有不順者、黃帝從而征之") == \
        "天下は順わざる者有り、黄帝は従いて之を征く。"


def test_rule_o_tari_se():
    # moshisono-1（白文 孟氏使陽膚爲士師——guard 爲＝旧字体）
    assert style_kana_to_kanji_o("孟氏は陽膚をして士の師たりせしむ。",
                                 "孟氏使陽膚爲士師") == "孟氏は陽膚をして士の師為らしむ。"
    # rongo0911-1 行型（白文 使子路問臣於孔子——guard 新字体 為 も発火＝新旧両形並查）
    assert style_kana_to_kanji_o("門の人をして臣たりせしむ。",
                                 "使門人為臣") == "門の人をして臣為らしむ。"
    # kanohitono-1 行型（費の宰たりせしむ→費の宰為らしむ）
    assert style_kana_to_kanji_o("子路は子羔をして費の宰たりせしむ。",
                                 "使子羔爲費宰") == "子路は子羔をして費の宰為らしむ。"


def test_rule_o_nakika():
    # montai12-10（白文 莫能測我攻守之計——「ことなきか」×「こと莫し」）
    assert style_kana_to_kanji_o("我が守を攻しての計を測ることなきか。",
                                 "莫能測我攻守之計") == "我が守を攻しての計を測ること莫し。"
    # daigaku00a-2 行型（白文 莫不以此与仁義礼智之性）
    assert style_kana_to_kanji_o("仁義礼智の性を以て与へざることなきか。",
                                 "莫不以此与仁義礼智之性") == \
        "仁義礼智の性を以て与へざること莫し。"


# ---------- 無護栏反例（guard 外＝一字不動） ----------
def test_rule_o_guard_negative():
    # はざる者 は guard=() 無条件（K 世代同款）——反例は無いが、guard 付き 2 条は検証
    assert style_kana_to_kanji_o("費の宰たりせしむ。", "使子羔為費宰") == "費の宰為らしむ。"
    assert style_kana_to_kanji_o("費の宰たりせしむ。", "使子羔宰費") == "費の宰たりせしむ。"
    assert style_kana_to_kanji_o("測ることなきか。", "能測我攻守之計") == "測ることなきか。"


def test_rule_o_empty_hakubun_semantics():
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_o("費の宰たりせしむ", "") == "費の宰為らしむ"
    assert style_kana_to_kanji_o("測ることなきか", "") == "測ること莫し"


# ---------- 拒案不复活（night86_sim/probe 拒案の再発防止） ----------
def test_rule_o_rejection_bekarazu_family():
    # べからず→可からず：N72 拒案 5 変差のまま（O は収録しない）
    assert style_kana_to_kanji_o("久なりて豺虎が乱するに留めるべからず",
                                 "不可久留豺虎之乱") == "久なりて豺虎が乱するに留めるべからず"
    # べからざる→可からざる：shiseinishite-1 1 変差で拒
    assert style_kana_to_kanji_o("民は得て治めるべからざるなり。",
                                 "不可得而治也") == "民は得て治めるべからざるなり。"
    # ざるべからず prefix・るべからず prefix も不収（ryojo-3/3 変差）
    assert style_kana_to_kanji_o("勉せざるべからず。", "不可不自勉") == "勉せざるべからず。"


def test_rule_o_rejection_hazaru_blanket_and_ka():
    # はざる blanket：24shihin10-4（はざるとも）1 変差で拒——はざる者 key のみ
    assert style_kana_to_kanji_o("真なりて奪はざるとも、強いて貧なり易きを得る。",
                                 "眞與不奪、強得易貧") == \
        "真なりて奪はざるとも、強いて貧なり易きを得る。"
    # はざるか：3 改善/Δ-0.000＝無益拒
    assert style_kana_to_kanji_o("其の後を善なる能はざるか。", "不能善其後矣") == \
        "其の後を善なる能はざるか。"


def test_rule_o_rejection_shimi_causative():
    # 使役族：してしむ/してしむる/しむ→使う は構造差で不可達（T9/T10/T8 拒案）
    assert style_kana_to_kanji_o("三軍の衆、必ず敵を受て敗者無きをしてしむる可し。",
                                 "必使敗者無き可し") == \
        "三軍の衆、必ず敵を受て敗者無きをしてしむる可し。"
    assert style_kana_to_kanji_o("天の帝は我をして百獣を長くせしむ。",
                                 "使我長百獣") == "天の帝は我をして百獣を長くせしむ。"


def test_rule_o_rejection_scramble_patches():
    # 長尾 scan の 2 行 scramble patch 3 件（語彙対応でない＝過拟合拒）
    assert style_kana_to_kanji_o("其は民をしてなる義せしむ。", "其の民を使うや義") == \
        "其は民をしてなる義せしむ。"
    assert style_kana_to_kanji_o("必ず以て新なるをしむるの尹に告す。", "以て新令尹に告ぐ") == \
        "必ず以て新なるをしむるの尹に告す。"
    assert style_kana_to_kanji_o("吾はなる賤むを少なり。", "吾少くして賤し") == \
        "吾はなる賤むを少なり。"


def test_rule_o_rejection_bekika_tomo_nakare():
    # べきか→可きか：omoi-1/mobosansen-1 2 変差で拒
    assert style_kana_to_kanji_o("則ち居るは知るべきか。", "則ち居ながらにして知るべし") == \
        "則ち居るは知るべきか。"
    # とも→与に：N72 拒案 137 変差の再確認
    assert style_kana_to_kanji_o("之を與に共す。", "与之共") == "之を與に共す。"
    # なかれ→莫かれ post-N umbrella：kokyo09-5 1 変差＝排除 guard 拍板事項のまま
    assert style_kana_to_kanji_o("父を厳して大なりて天を配すことなかれ。",
                                 "嚴父莫大於配天") == \
        "父を厳して大なりて天を配すことなかれ。"
    # 無益 ことな prefix（Δ-0.000）
    assert style_kana_to_kanji_o("祥ならざるは焉に大なることなかれ", "離則不祥莫大焉") == \
        "祥ならざるは焉に大なることなかれ"


# ---------- 構造ロック ----------
def test_rule_o_structure_and_chain_order():
    # 3 条構造・長詞表空壳（K 同款系列同构）
    assert len(O_KANA_TO_KANJI) == 3
    assert [e[0] for e in O_KANA_TO_KANJI] == ["はざる者", "たりせ", "なきか"]
    assert all(len(e) == 3 for e in O_KANA_TO_KANJI)
    assert set(O_LONGER_WORDS) == {"はざる者", "たりせ", "なきか"}
    assert all(v == () for v in O_LONGER_WORDS.values())
    # repl は终字形（normalize_shinjitai 不変）
    for _kana, repl, _guard in O_KANA_TO_KANJI:
        assert normalize_shinjitai(repl) == repl
    # 链序 N→O：pipeline で O が N の後（はざる者 行は N 非該当・O 該当の組合せ）
    assert style_fix_with_hakubun("其の所を失はざる者は久なり。", "不失其所者久。死而不亡者壽。") == \
        "其の所を失わざる者は久なり。"


def test_rule_o_idempotent_and_modern():
    for text, hb in (("其の所を失はざる者は久なり。", "不失其所者久"),
                     ("費の宰たりせしむ。", "使子羔爲費宰"),
                     ("測ることなきか。", "莫能測")):
        once = style_kana_to_kanji_o(text, hb)
        assert style_kana_to_kanji_o(once, hb) == once
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_o("本日の会議は十時から開始されます。", "") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝白文直出対象・kana なしで O も非発火）
    assert style_kana_to_kanji_o("器械を習い用う", "莫不習用器械") == "器械を習い用う"
