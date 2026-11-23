# -*- coding: utf-8 -*-
"""test_night73_rule_m.py — N73: Rule M（かな→漢字第 9 批＋禁止族 guard 分割）锁定测试。

方法论同 N72 test（rule L）：每条正例（実語料行型）＋無護栏反例（一字不動）＋
長語マスク（もしも/もしや/もしか＝I 同款）／空白文で guard 規則も発火
（E〜L 世代同语义）／拒案不复活（莫かれ・莫/勿し 裸形・若し・べき・陳→陣・
短 key はある・も其れ）／鏈不変式ロック（もし+如 は I が先勝、はそれ+夫 は
I が先勝——M は早期 guard 未命中行のみに発火）／链序 L→M／幂等／
無 kana 现代句一字不动／経典句回帰。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    M_KANA_TO_KANJI, M_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_m, style_fix_with_hakubun,
)


# ---------- 各条正例（実語料行型） ----------
def test_rule_m_nakare_butsukare():
    # moshisono-1（白文 勿喜；exp こと勿かれ）——I 毋かれ 同構の guard 分割
    assert style_kana_to_kanji_m("則ち哀矜して喜ぶことなかれ",
                                 "則哀矜而勿喜") == "則ち哀矜して喜ぶこと勿かれ"
    # onorenoho-1 行型（勿施於人）
    assert style_kana_to_kanji_m("己は欲さざる所、人に施すことなかれ",
                                 "己所不欲、勿施於人") == "己は欲さざる所、人に施すこと勿かれ"


def test_rule_m_soku_imachi():
    # katsumoku-4（白文 即；exp 即ち 12/12 均一）
    assert style_kana_to_kanji_m("士は三日を別つ、そく当して目を刮ぎて相待つ",
                                 "士別三日、即當刮目相待") == \
        "士は三日を別つ、即ち当して目を刮ぎて相待つ"


def test_rule_m_soku_old_font_guard():
    # keimei-4（白文は旧字体 卽——新字体 即 だけで探すと N69 爲/爲 教训同款の取り逃し）
    assert style_kana_to_kanji_m("孟は嘗て君は得て出づ、そく馳して去く",
                                 "卽馳去") == "孟は嘗て君は得て出づ、即ち馳して去く"
    # 新字体 白文でも発火（guard は 即/卽 の OR）
    assert style_kana_to_kanji_m("そく馳して去く", "即馳去") == "即ち馳して去く"


def test_rule_m_aruiwa():
    # rongo0223-1（白文 或；got「はあるいは」＝余計な は 付き）
    assert style_kana_to_kanji_m("其はあるいは周を継する者",
                                 "其或繼周者") == "其或いは周を継する者"


def test_rule_m_yuki_kore():
    # daigaku08-2（之其所賤惡而辟焉——系列 5 行のみ）
    assert style_kana_to_kanji_m("其が賤悪する所にゆきて辟す",
                                 "之其所賤惡而辟焉") == "其が賤悪する所に之て辟す"


def test_rule_m_hasore_sore():
    # rongo0604-1（白文 其舍諸；exp 山川其れ諸を舎てんや）
    assert style_kana_to_kanji_m("山川はそれ諸を舎す",
                                 "山川其舍諸") == "山川其れ諸を舎す"
    # onoreosame-1 行型（exp に も 有り——其れ repl で距離同数〜改善、0 変差の内側）
    assert style_kana_to_kanji_m("堯舜はそれ猶お諸を病む",
                                 "堯舜其猶病諸") == "堯舜其れ猶お諸を病む"


def test_rule_m_nanigotoshi_daga():
    # goshi02-1（白文 奈何；exp 此を憂うること奈何）
    assert style_kana_to_kanji_m("此を憂ひるは何のごとし",
                                 "憂此奈何") == "此を憂ひるは奈何"


def test_rule_m_nanigotoku_dagazo():
    # kiyu-7（白文 奈何憂崩墜乎；exp 奈何ぞ崩墜を憂えんや）
    assert style_kana_to_kanji_m("何のごとく憂いて崩して墜すや",
                                 "奈何憂崩墜乎") == "奈何ぞ憂いて崩して墜すや"


def test_rule_m_moshi_waka():
    # enou-1（白文 若能使冢合；exp 若し能く——裸形 repl で 1 字改善）
    assert style_kana_to_kanji_m("もし能く冢の合すをしてしむ",
                                 "若能使冢合") == "若能く冢の合すをしてしむ"
    # enjaku-2 行型（exp が裸形 若、を自書——repl 若 の根拠）
    assert style_kana_to_kanji_m("もし庸の耕すを為す",
                                 "若爲庸耕") == "若庸の耕すを為す"


# ---------- 反例：守り字無しは一字不動（guard 規則） ----------
def test_rule_m_guard_miss_untouched():
    assert style_kana_to_kanji_m("喜ぶことなかれ", "則ち哀矜而喜ず") == "喜ぶことなかれ"
    assert style_kana_to_kanji_m("そく已む", "且つ壯士は死せずして已む") == "そく已む"
    assert style_kana_to_kanji_m("其はあるいは周を継す", "其れ周を繼ぐ者") == "其はあるいは周を継す"
    assert style_kana_to_kanji_m("ゆきて辟す", "其の賤悪する所に辟す") == "ゆきて辟す"
    assert style_kana_to_kanji_m("山川はそれ諸を舎す", "山川は諸を舎つ") == "山川はそれ諸を舎す"
    assert style_kana_to_kanji_m("此を憂ひるは何のごとし", "此を憂う") == "此を憂ひるは何のごとし"
    assert style_kana_to_kanji_m("もし能く冢を合す", "能く冢を合せしむれば") == "もし能く冢を合す"


# ---------- 莫 白文行は不触（なかれ→莫かれ は kokyo09-5 1 変差で拒案） ----------
def test_rule_m_moku_rejected_not_fired():
    # kokyo09-5（白文 莫大於配天——莫 guard は M 表に無い）
    assert style_kana_to_kanji_m("父を厳して大なりて天を配すことなかれ",
                                 "嚴父莫大於配天") == \
        "父を厳して大なりて天を配すことなかれ"
    # 莫∧勿 多守り行（rinkiohen-2）——勿かれ のみ発火（莫 rule 不在）
    assert style_kana_to_kanji_m("多く言うことなかれ",
                                 "號令莫行。勿多言") == "多く言うこと勿かれ"


# ---------- 長語マスク（I もし 同款） ----------
def test_rule_m_longer_words_mask():
    assert style_kana_to_kanji_m("もしも阻まざるなり", "若くんば阻まざるなり") == "もしも阻まざるなり"
    assert style_kana_to_kanji_m("もしや違うまい", "若くは違うまい") == "もしや違うまい"
    assert style_kana_to_kanji_m("もしかすると違う", "若くば違うかも") == "もしかすると違う"


# ---------- 空白文：guard 規則も発火（E〜L 世代同语义） ----------
def test_rule_m_empty_hakubun_guard_rules_fire():
    assert style_kana_to_kanji_m("そく已む", "") == "即ち已む"
    assert style_kana_to_kanji_m("喜ぶことなかれ", "") == "喜ぶこと勿かれ"


# ---------- 表の整形性 ----------
def test_rule_m_table_wellformed():
    assert len(M_KANA_TO_KANJI) == 8
    for kana, repl, guard in M_KANA_TO_KANJI:
        assert guard == () or all(isinstance(g, str) and g for g in guard), kana
        assert repl not in kana, kana
        # repl は終字形（响应端 normalize_shinjitai が再変換しない）
        assert normalize_shinjitai(repl) == repl, kana
    kanas = {k for k, _r, _g in M_KANA_TO_KANJI}
    assert kanas == {"なかれ", "そく", "はあるいは", "ゆき", "はそれ",
                     "何のごとし", "何のごとく", "もし"}
    # guard=() 無条件規則は本系列なし（陳→陣 拒案の反映）
    assert all(g != () for _k, _r, g in M_KANA_TO_KANJI)
    # そく の守りは新旧両形（即 9＋卽 3）
    soku = [(r, g) for k, r, g in M_KANA_TO_KANJI if k == "そく"]
    assert soku == [("即ち", ("即", "卽"))]


def test_rule_m_longer_words_shape():
    assert set(M_LONGER_WORDS.keys()) == {"なかれ", "そく", "はあるいは", "ゆき",
                                          "はそれ", "何のごとし", "何のごとく", "もし"}
    assert M_LONGER_WORDS["もし"] == ("もしも", "もしや", "もしか")  # I 同款
    for k in ("なかれ", "そく", "はあるいは", "ゆき", "はそれ",
              "何のごとし", "何のごとく"):
        assert M_LONGER_WORDS[k] == (), k


# ---------- 拒案不复活 ----------
def test_rule_m_rejected_not_registered():
    kanas = {k for k, _r, _g in M_KANA_TO_KANJI}
    for banned in ("べき", "るべ", "ことな", "はある", "陳"):
        assert banned not in kanas, banned
    # なかれ の repl は 勿かれ のみ（莫かれ/莫/莫し/勿/勿し は落选）
    nakare_repls = [r for k, r, _g in M_KANA_TO_KANJI if k == "なかれ"]
    assert nakare_repls == ["勿かれ"]
    # もし の repl は裸形 若 のみ（若し は kyugyu-2 1 変差で拒）
    moshi_repls = [r for k, r, _g in M_KANA_TO_KANJI if k == "もし"]
    assert moshi_repls == ["若"]
    # はそれ の repl は 其れ（も其れ は落选——delta 劣る）
    hasore_repls = [r for k, r, _g in M_KANA_TO_KANJI if k == "はそれ"]
    assert hasore_repls == ["其れ"]


def test_rule_m_rejected_rows_untouched():
    # べき→可き（6 変差：omoi-1 等 exp 自写 べし）——M は べき を触らない
    assert style_kana_to_kanji_m("居るは知るべきか", "則居可知矣") == "居るは知るべきか"
    # はある→或（短 key 不採用——は それ自体が対象）
    assert style_kana_to_kanji_m("限りはあるまい", "限りは有るまい") == "限りはあるまい"
    # 陳→陣（無条件文字置換 30 変差——kana 規則の外・拒案）
    assert style_kana_to_kanji_m("堂々の陳を撃することなかれ", "勿撃堂堂之陳") == \
        "堂々の陳を撃すること勿かれ"


# ---------- 链不変式：早期 guard 命中行は I が先勝し M は発火しない ----------
def test_rule_m_chain_invariant_moshi_ru():
    # 如∧若 両守り行——I の もし→如し が先勝（链順 I < M）、M は触らない
    full = style_fix_with_hakubun("もし能く之を為す",
                                  "如く能く之を為す。若し能く之を為す")
    assert full == "如し能く之を為す"


def test_rule_m_chain_invariant_hasore_fu():
    # 夫∧其 両守り行——I の それ→夫れ が先勝、M の はそれ は発火しない
    full = style_fix_with_hakubun("山川はそれ諸を舎す",
                                  "山川其舍諸。夫禮本於天")
    assert full == "山川は夫れ諸を舎す"


# ---------- 链序 L→M ----------
def test_rule_m_chain_order_after_l():
    # L の つひに→終に と M の そく→即ち 同時発火
    full = style_fix_with_hakubun("つひに已みてそく大名を挙す",
                                  "終に已み、即ち大名を挙げん")
    assert full == "終に已みて即ち大名を挙す"


def test_rule_m_chain_combo_with_l():
    # L の がため→為（guard 爲）＋M の 何のごとし→奈何（guard 奈）
    # （憂ふる は E〜K 既存の現代仮名遣い変換で 憂うる になる——链前段の挙動）
    full = style_fix_with_hakubun("之がため憂ふるは何のごとし",
                                  "之が爲に憂ふるは奈何")
    assert full == "之為憂うるは奈何"


def test_rule_m_idempotent():
    hb = "士別三日、即當刮目相待。勿多言。憂此奈何"
    t1 = style_fix_with_hakubun("士は三日を別つ、そく当して相待つ。多く言うことなかれ。"
                                "此を憂ひるは何のごとし", hb)
    t2 = style_fix_with_hakubun(t1, hb)
    assert t1 == t2


# ---------- 语料外探针（無 kana 目標の现代句一字不動） ----------
def test_rule_m_modern_probes():
    assert style_fix_with_hakubun("もしよろしければ、お先にどうぞ", "その通りです") == \
        "もしよろしければ、お先にどうぞ"
    assert style_fix_with_hakubun("北へゆき着く", "北へ行き着く") == "北へゆき着く"


def test_rule_m_classic_sentence_regression():
    # 经典句（accept_night CLASSIC_CASES 同款）不回帰
    full = style_fix_with_hakubun("王は左右を顧みて而して他を言う", "王顧左右而言他")
    assert full == "王は左右を顧みて而して他を言う"
