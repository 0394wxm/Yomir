# -*- coding: utf-8 -*-
"""test_night78_rule_n.py — N78: Rule N（かな→漢字第 10 批＋ことな族活用形分割＋現代語副詞族）锁定测试。

方法论同 N73 test（rule M）：每条正例（実語料行型）＋無護栏反例（一字不動）＋
空白文で guard 規則も発火（E〜M 世代同语义）／死行不触（kokyo09-5＝すことなかれ 行は
prefix keys で非該当——umbrella ことなかれ は拒案未登録）／拒案不复活（umbrella・
き/ぶ/く/つことなかれ 無益 4 条・落选字形 屢/弥/偶〻）／新旧字体 guard（彌）／
鏈不変式ロック（盍∧胡 は K が先勝、莫∧勿 は M・莫∧毋 は I が先勝——N は早期
guard 未命中行のみに発火）／链序 M→N／幂等／無 kana 现代句一字不动／経典句回帰。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    N_KANA_TO_KANJI, N_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_n, style_fix_with_hakubun,
)


# ---------- 各条正例（実語料行型） ----------
def test_rule_n_koto_suru():
    # isshoko-3（白文 憑君莫話封侯事；exp こと莫かれ＝こと 保持形）
    assert style_kana_to_kanji_n("君を憑きて話侯の事を封することなかれ",
                                 "憑君莫話封侯事") == "君を憑きて話侯の事を封すること莫かれ"
    # iboku-1 行型（莫敢徙）
    assert style_kana_to_kanji_n("敢えて徙することなかれ",
                                 "莫敢徙") == "敢えて徙すること莫かれ"


def test_rule_n_koto_ru():
    # kenro-1（白文 憖憖然莫相知；exp こと落とし 莫し——repl こと莫かれ でも改善）
    assert style_kana_to_kanji_n("憖憖は然りて相知ることなかれ",
                                 "憖憖然莫相知") == "憖憖は然りて相知ること莫かれ"
    # gabei-2 行型（選舉莫取有名；exp 取ること莫かれ exact 型）
    assert style_kana_to_kanji_n("選びて挙して名有るを取ることなかれ",
                                 "選舉莫取有名") == "選びて挙して名有るを取ること莫かれ"


def test_rule_n_koto_uzaru():
    # kamireikei-1（白文 則民莫敢不敬）
    assert style_kana_to_kanji_n("則ち民は敢えて敬さざることなかれ",
                                 "則民莫敢不敬") == "則ち民は敢えて敬さざること莫かれ"
    # daigaku00a-22 行型（蓋莫不聞其説）
    assert style_kana_to_kanji_n("三千の徒、蓋し其の説くと聞かざることなかれ",
                                 "三千之徒、蓋莫不聞其説") == \
        "三千の徒、蓋し其の説くと聞かざること莫かれ"


def test_rule_n_koto_naru_moku_dai_syntax():
    # kokyo09-3（白文 人之行、莫大於孝——「莫大」構文行も 0 変差の内側で改善）
    assert style_kana_to_kanji_n("人の行、孝より大なることなかれ",
                                 "人之行、莫大於孝") == "人の行、孝より大なること莫かれ"
    # kowokaete-4（白文 離則不祥莫大焉——莫大焉 構文も同様）
    assert style_kana_to_kanji_n("祥ならざるは焉に大なることなかれ",
                                 "離則不祥莫大焉") == "祥ならざるは焉に大なること莫かれ"


def test_rule_n_koto_u():
    # kanae-2（白文 螭魅罔兩、莫能逢之）
    assert style_kana_to_kanji_n("能く之に逢うことなかれ",
                                 "莫能逢之") == "能く之に逢うこと莫かれ"
    # kanyojotoro-7 行型（行人莫問當年事）
    assert style_kana_to_kanji_n("人を行いて当年の事を問うことなかれ",
                                 "行人莫問當年事") == "人を行いて当年の事を問うこと莫かれ"


def test_rule_n_koto_ru_substring_coverage():
    # ることなかれ 1 本で さしむる/てする 等 〜る 系を substring 覆盖
    # （さしむることなかれ には することなかれ は含まれず、ることなかれ のみ一致）
    assert style_kana_to_kanji_n("敢えて言はさしむることなかれ",
                                 "莫敢令言") == "敢えて言はさしむること莫かれ"


def test_rule_n_shibashiba():
    # rongo1118-1（白文 屢空・億則屢中——1 行 2 発火）
    assert style_kana_to_kanji_n("回なるは其は庶なりや。しばしば空く。億して則ちしばしば中。",
                                 "回也其庶乎。屢空。億則屢中。") == \
        "回なるは其は庶なりや。屢〻空く。億して則ち屢〻中。"
    # izukunei-1 行型（禦人以口給、屢憎於人）
    assert style_kana_to_kanji_n("人を口が給べるを以て禦ぐ、しばしば人に憎す",
                                 "禦人以口給、屢憎於人") == "人を口が給べるを以て禦ぐ、屢〻人に憎す"


def test_rule_n_hondo():
    # karewoshiri-3（白文 毎戰必殆）
    assert style_kana_to_kanji_n("戦う毎に必ずほとんど",
                                 "毎戰必殆") == "戦う毎に必ず殆"
    # rongo1510-1 行型（佞人殆）
    assert style_kana_to_kanji_n("佞なるの人はほとんど",
                                 "佞人殆") == "佞なるの人は殆"


def test_rule_n_haiyoiyoi_old_font_guard():
    # rongo0910-1（白文は旧字体 彌——単形 guard 弥 では N72 移交①同款の取り逃し）
    assert style_kana_to_kanji_n("之を仰ぐはいよいよ高し、之を鑽るはいよいよ堅なり",
                                 "仰之彌高、鑽之彌堅") == "之を仰ぐ弥〻高し、之を鑽る弥〻堅なり"
    # 新字体 白文でも発火（guard は 弥/彌 の OR）——は は exp 同款に落とす
    assert style_kana_to_kanji_n("之を仰ぐはいよいよ高し",
                                 "仰之弥高") == "之を仰ぐ弥〻高し"


def test_rule_n_yoiyoi_standalone():
    # は 無し行は 長 key はいよいよ 非該当・いよいよ が発火
    assert style_kana_to_kanji_n("いよいよ堅なり",
                                 "鑽之彌堅") == "弥〻堅なり"


def test_rule_n_hayayaya():
    # toushisen138-11（白文 晚來風稍緊；exp 稍く——は を含むキーごと置換）
    assert style_kana_to_kanji_n("晩なりて来風はやや緊す",
                                 "晚來風稍緊") == "晩なりて来風稍く緊す"


def test_rule_n_yaya():
    # kenro-1（白文 稍出近之）
    assert style_kana_to_kanji_n("やや出でて之を近し",
                                 "稍出近之") == "稍出でて之を近し"


def test_rule_n_tama():
    # toushisen227-2（白文 偶坐爲林泉；exp 偶坐——裸形 偶 が exp 実書形）
    assert style_kana_to_kanji_n("たま坐して林泉たり",
                                 "偶坐爲林泉") == "偶坐して林泉たり"


def test_rule_n_nanzo_hu():
    # manwojisu-1（白文 胡急撃之——K の 守り 盍/奚/曷 外の残量）
    assert style_kana_to_kanji_n("なんぞ急ぎて之を撃す",
                                 "胡急撃之") == "胡急ぎて之を撃す"


# ---------- 反例：守り字無しは一字不動（guard 規則） ----------
def test_rule_n_guard_miss_untouched():
    assert style_kana_to_kanji_n("喜ぶことなかれ", "則ち哀矜而喜ず") == "喜ぶことなかれ"
    assert style_kana_to_kanji_n("いよいよ高し", "仰之高") == "いよいよ高し"
    assert style_kana_to_kanji_n("しばしば空く", "回也其庶乎") == "しばしば空く"
    assert style_kana_to_kanji_n("戦う毎に必ずほとんど", "毎戰必危") == "戦う毎に必ずほとんど"
    assert style_kana_to_kanji_n("やや出でて之を近し", "出て之に近づく") == "やや出でて之を近し"
    assert style_kana_to_kanji_n("たま坐して林泉たり", "坐爲林泉") == "たま坐して林泉たり"
    assert style_kana_to_kanji_n("なんぞ急ぎて之を撃す", "急に之を撃つ") == "なんぞ急ぎて之を撃す"


# ---------- 死行不触：kokyo09-5（すことなかれ）は N 全键が非該当 ----------
def test_rule_n_death_row_untouched():
    # umbrella ことなかれ は拒案（kokyo09-5 1 変差）・すことなかれ は登録なし
    assert style_kana_to_kanji_n("父を厳して大なりて天を配すことなかれ",
                                 "嚴父莫大於配天") == \
        "父を厳して大なりて天を配すことなかれ"


def test_rule_n_below_line_rows_untouched():
    # き/ぶ/く/つことなかれ 4 条は Δ−0.000 無益で拒案——N は触らない
    assert style_kana_to_kanji_n("一年の計、穀を樹するが如きことなかれ",
                                 "一年之計、莫如樹穀") == \
        "一年の計、穀を樹するが如きことなかれ"
    assert style_kana_to_kanji_n("小子は何ぞ夫の詩を学ぶことなかれ",
                                 "小子何莫學夫詩") == \
        "小子は何ぞ夫の詩を学ぶことなかれ"


# ---------- 空白文：guard 規則も発火（E〜M 世代同语义） ----------
def test_rule_n_empty_hakubun_guard_rules_fire():
    assert style_kana_to_kanji_n("しばしば空く", "") == "屢〻空く"
    assert style_kana_to_kanji_n("取ることなかれ", "") == "取ること莫かれ"


# ---------- 表の整形性 ----------
def test_rule_n_table_wellformed():
    assert len(N_KANA_TO_KANJI) == 13
    for kana, repl, guard in N_KANA_TO_KANJI:
        assert guard == () or all(isinstance(g, str) and g for g in guard), kana
        assert repl not in kana, kana
        # repl は終字形（响应端 normalize_shinjitai が再変換しない）
        assert normalize_shinjitai(repl) == repl, kana
    kanas = [k for k, _r, _g in N_KANA_TO_KANJI]
    assert kanas == ["することなかれ", "ざることなかれ", "なることなかれ", "うことなかれ",
                     "ることなかれ", "はいよいよ", "いよいよ", "しばしば", "ほとんど",
                     "はやや", "やや", "たま", "なんぞ"]
    # guard=() 無条件規則は本系列なし
    assert all(g != () for _k, _r, g in N_KANA_TO_KANJI)
    # いよいよ族の守りは新旧両形（白文は旧字体 彌）
    for k, _r, g in N_KANA_TO_KANJI:
        if k in ("はいよいよ", "いよいよ"):
            assert g == ("弥", "彌"), k
    # 長 key 先行：はやや < やや、はいよいよ < いよいよ
    assert kanas.index("はやや") < kanas.index("やや")
    assert kanas.index("はいよいよ") < kanas.index("いよいよ")


def test_rule_n_longer_words_shape():
    assert set(N_LONGER_WORDS.keys()) == {k for k, _r, _g in N_KANA_TO_KANJI}
    assert all(v == () for v in N_LONGER_WORDS.values())  # sim 実測で長詞衝突なし


# ---------- 拒案不复活 ----------
def test_rule_n_rejected_not_registered():
    kanas = {k for k, _r, _g in N_KANA_TO_KANJI}
    # umbrella ことなかれ（kokyo09-5 1 変差・N58/N68/N73 同死因の機構境界）
    assert "ことなかれ" not in kanas
    # 死行を避けるため意図的に外した すことなかれ
    assert "すことなかれ" not in kanas
    # Δ−0.000 無益 4 条（N69 収録線 −0.001 未満）
    for banned in ("きことなかれ", "ぶことなかれ", "くことなかれ", "つことなかれ"):
        assert banned not in kanas, banned
    # 落选字形：しばしば の repl は 屢〻 のみ（屢 は過門だが劣る）
    assert [r for k, r, _g in N_KANA_TO_KANJI if k == "しばしば"] == ["屢〻"]
    # はいよいよ/いよいよ の repl は 弥〻 のみ（弥 は過門だが劣る）
    assert [r for k, r, _g in N_KANA_TO_KANJI if k == "はいよいよ"] == ["弥〻"]
    assert [r for k, r, _g in N_KANA_TO_KANJI if k == "いよいよ"] == ["弥〻"]
    # たま の repl は 偶 のみ（偶〻 は無益 −0.000）
    assert [r for k, r, _g in N_KANA_TO_KANJI if k == "たま"] == ["偶"]


def test_rule_n_rejected_forms_untouched():
    # 落选字形の裸形でも発火しない（repl が違うだけで key は同じ——これは
    # 辞書の動作確認ではなく、落选 repl が表中に無いことの動作面の確認）
    assert style_kana_to_kanji_n("たま然りて指の爪に留む", "泥上偶然留指爪") == \
        "偶然りて指の爪に留む"


# ---------- 链不変式：早期 guard 命中行は K/M/I が先勝し N は発火しない ----------
def test_rule_n_chain_invariant_nanzo_kan_koku():
    # 盍∧胡 両守り行——K の なんぞ→盍ぞ が先勝（链順 K < N）、N は触らない
    full = style_fix_with_hakubun("なんぞ撃たざるや", "盍撃之。胡急撃之")
    assert full == "盍ぞ撃たざるや"


def test_rule_n_chain_invariant_kotona_butsu():
    # 莫∧勿 多守り行——M の なかれ→勿かれ が先勝、N の ことな族は こと勿かれ に不一致
    full = style_fix_with_hakubun("多く言うことなかれ", "號令莫行。勿多言")
    assert full == "多く言うこと勿かれ"


def test_rule_n_chain_invariant_kotona_bo():
    # 莫∧毋 多守り行——I の なかれ→毋かれ が先勝（K 世代から継続）
    full = style_fix_with_hakubun("喜ぶことなかれ", "莫喜。毋吾以也")
    assert full == "喜ぶこと毋かれ"


# ---------- 链序 M→N ----------
def test_rule_n_chain_order_after_m():
    # M の そく→即ち と N の しばしば→屢〻 同時発火
    full = style_fix_with_hakubun("そく当して相待つ、しばしば人に憎す",
                                  "即當刮目相待。屢憎於人")
    assert full == "即ち当して相待つ、屢〻人に憎す"


def test_rule_n_chain_combo_with_m():
    # M の そく→即ち ＋ N の たま→偶（guard 偶）
    full = style_fix_with_hakubun("そく已む、たま坐して林泉たり",
                                  "即已矣。偶坐爲林泉")
    assert full == "即ち已む、偶坐して林泉たり"


def test_rule_n_idempotent():
    hb = "仰之彌高、鑽之彌堅。屢憎於人。莫敢徙。稍出近之。偶坐爲林泉"
    t1 = style_fix_with_hakubun("之を仰ぐはいよいよ高し。しばしば人に憎す。"
                                "敢えて徙することなかれ。やや出でて之を近し。"
                                "たま坐して林泉たり", hb)
    t2 = style_fix_with_hakubun(t1, hb)
    assert t1 == t2


# ---------- 语料外探针（無 kana 目標の现代句一字不动） ----------
def test_rule_n_modern_probes():
    assert style_fix_with_hakubun("いよいよだね、やや難しいけどしばしばある",
                                  "その通りです") == \
        "いよいよだね、やや難しいけどしばしばある"
    assert style_fix_with_hakubun("北へゆき着く", "北へ行き着く") == "北へゆき着く"


def test_rule_n_classic_sentence_regression():
    # 经典句（accept_night CLASSIC_CASES 同款）不回帰
    full = style_fix_with_hakubun("王は左右を顧みて而して他を言う", "王顧左右而言他")
    assert full == "王は左右を顧みて而して他を言う"
