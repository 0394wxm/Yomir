# -*- coding: utf-8 -*-
"""test_night107_item4_impl.py — N107 項 4 実施夜：guard 変体字拡張 C1+C4 锁定测试。

N106 REPORT §2.1/§3 設計実施の行動ロック：正例 2 行（rikutou37-2 がため→為 44→43＝
tail 新字体 為・shiki050-4 何のごとく→奈何ぞ 25→20＝tail 異体字 柰・実 tail 语境で
Rule 単体＋全链双方）＋guard 反例（無/罔＝一字不動＝C2/C6 不採ロック・守り字全無＝
一字不動・旧字 爲/奈 のみ＝現行発火挙動不変の対照・空白文＝E〜K 世代同语义発火）＋
全域只改 2 行断言（night107_sim.json gates・night107_changed_rows.json ID・d0→d1・
変差 0・Δ8165 −0.001・Δ4000 0.000・幂等 bad 0・C3/C5 現行对照 0 発火・guard miss
残量恰 1 行）＋構造ロック（guard tuple 2 处のみ変更・repl/長词表/規則数不変・
Rule M (即,卽) と Rule O (爲,為) 先例不変）＋幂等＋無 kana 现代句一字不动＋
night104 基线锚（両行 d0＝44/25・両行 4000 外）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    L_KANA_TO_KANJI, M_KANA_TO_KANJI, O_KANA_TO_KANJI,
    L_LONGER_WORDS, M_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_l, style_kana_to_kanji_m, style_fix_with_hakubun,
)

EV = os.path.join(ROOT, "eval")


def _sim():
    return json.load(open(os.path.join(EV, "night107_sim.json"), encoding="utf-8"))


def _changed():
    return {c["id"]: c for c in
            json.load(open(os.path.join(EV, "night107_changed_rows.json"), encoding="utf-8"))}


# ---------- 正例（実語料行型・実 tail 语境・night107_sim new_text 逐位） ----------
def test_c1_c4_positive_rows_real_context():
    chg = _changed()
    assert sorted(chg) == ["rikutou37-2", "shiki050-4"]
    c1 = chg["rikutou37-2"]
    c4 = chg["shiki050-4"]
    # d0→d1 実測（night104 基线＝N106 §2.1 実測どおり）
    assert (c1["old_dist"], c1["new_dist"]) == (44, 43)
    assert (c4["old_dist"], c4["new_dist"]) == (25, 20)
    # Rule L 単体（guard 変体字 為＝rikutou37-2 tail の新字体・旧字 爲 は tail に無し）
    assert style_kana_to_kanji_l(c1["old_text"], c1["hb"]) == c1["new_text"]
    # Rule M 単体（guard 変体字 柰＝shiki050-4 tail の異体字・奈 は全文に無し）
    assert style_kana_to_kanji_m(c4["old_text"], c4["hb"]) == c4["new_text"]
    # 全链（style_fix_with_hakubun・rerun tail 语境＝N106「rerun 同一述語」実測どおり）
    assert style_fix_with_hakubun(c1["old_text"], c1["hb"]) == c1["new_text"]
    assert style_fix_with_hakubun(c4["old_text"], c4["hb"]) == c4["new_text"]
    # 実 tail 语境には変体字が在り旧字が無い（guard 変体字拡張の死因実証）
    assert "爲" not in c1["hb"] and "為" in c1["hb"]
    assert "奈" not in c4["hb"] and "柰" in c4["hb"]


# ---------- guard 反例（無/罔＝一字不動＝C2/C6 不採ロック・守り字全無・旧字対照） ----------
def test_guard_variant_negative_rows():
    # C2/C6 不採ロック：無/罔 を含む白文でも 爲/為・奈/柰 が無ければ一字不動
    # （N106 §2.1：C2 は tail 無 の偶然一致で不採・C6 は実測 0 発火＝無効）
    assert style_kana_to_kanji_l("之がため奈何。", "車騎又無以越其前後戦則不勝") == "之がため奈何。"
    assert style_kana_to_kanji_m("何のごとく其の後を続す。", "紛亂天下罔不有初") == "何のごとく其の後を続す。"
    # 守り字全無＝一字不動
    assert style_kana_to_kanji_l("之がため奈何。", "敵之地勢不可以伏其両旁") == "之がため奈何。"
    assert style_kana_to_kanji_m("何のごとく其の後を続す。", "今乃首率七國紛亂天下") == "何のごとく其の後を続す。"
    # 新字のみ＝C1/C4 核心（rikutou37-2 tail 型・shiki050-4 tail 型）
    assert style_kana_to_kanji_l("之がため奈何。", "戦則不勝為之奈何") == "之為奈何。"
    assert style_kana_to_kanji_m("何のごとく其の後を続す。", "柰何續其後") == "奈何ぞ其の後を続す。"
    # 旧字のみ＝現行発火挙動不変の対照（拡張で既存発火が消えない）
    assert style_kana_to_kanji_l("之がため奈何。", "爲之奈何") == "之為奈何。"
    assert style_kana_to_kanji_m("何のごとく其の後を続す。", "奈何續其後") == "奈何ぞ其の後を続す。"
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_l("之がため奈何。", "") == "之為奈何。"
    assert style_kana_to_kanji_m("何のごとく其の後を続す。", "") == "奈何ぞ其の後を続す。"


# ---------- 全域只改 2 行断言（night107_sim gates ロック） ----------
def test_full_domain_only_two_rows_lock():
    sim = _sim()
    assert sim["verdict"] == "PASS"
    combo = sim["gates"]["combo"]
    assert combo["changed"] == 2 and combo["better"] == 2 and combo["worse"] == 0
    assert combo["worse_ids"] == []
    assert combo["changed4000"] == 0 and combo["worse_ids4000"] == []
    assert abs(combo["delta8165"] - (-0.001)) <= 0.0005
    assert abs(combo["delta4000"]) <= 0.0005
    assert combo["idempotent_bad"] == 0
    assert combo["pred_exact4000"] == 24 and combo["pred_exact8165"] == 30
    c1 = sim["gates"]["c1"]
    c4 = sim["gates"]["c4"]
    assert c1["changed"] == 1 and c1["changed4000"] == 0 and c1["worse_ids"] == []
    assert c4["changed"] == 1 and c4["changed4000"] == 0 and c4["worse_ids"] == []
    # 現行 guard 对照（C3/C5）＝0 発火（残量確認＝N106 §2.1 実測どおり）
    assert sim["gates"]["c3_contrast"]["changed"] == 0
    assert sim["gates"]["c5_contrast"]["changed"] == 0
    # guard miss 残量＝恰 1 行（N106「唯一の guard miss 行」再確認）
    assert sim["guard_miss_c1"] == ["rikutou37-2"]
    assert sim["guard_miss_c4"] == ["shiki050-4"]
    # 行分类・词库・基线（N104 链尾）不動
    assert sim["class"] == {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}
    assert sim["lexicon"]["ordered_all"] == 1531
    assert abs(sim["baseline"]["avg4000"] - 13.460) <= 0.0005
    assert abs(sim["baseline"]["avg8165"] - 13.467) <= 0.0005


# ---------- 構造ロック（guard tuple 2 处のみ・先例不変・規則数不変） ----------
def test_structure_lock():
    l_entry = [e for e in L_KANA_TO_KANJI if e[0] == "がため"]
    assert l_entry == [("がため", "為", ("爲", "為"))]
    m_entry = [e for e in M_KANA_TO_KANJI if e[0] == "何のごとく"]
    assert m_entry == [("何のごとく", "奈何ぞ", ("奈", "柰"))]
    # 規則数不変（L 9 語・M 8 語＝README 実数・N107 で追加/削除なし）
    assert len(L_KANA_TO_KANJI) == 9
    assert len(M_KANA_TO_KANJI) == 8
    # repl 不変（guard 変体字拡張のみ＝repl/链序/長词表不変）
    assert l_entry[0][1] == "為" and m_entry[0][1] == "奈何ぞ"
    assert L_LONGER_WORDS["がため"] == ()
    assert M_LONGER_WORDS["何のごとく"] == ()
    # 先例不変：Rule M そく→即ち (即,卽)＝新旧並查成文慣例・Rule O たりせ→為ら (爲,為)
    suo = [e for e in M_KANA_TO_KANJI if e[0] == "そく"]
    assert suo == [("そく", "即ち", ("即", "卽"))]
    tarise = [e for e in O_KANA_TO_KANJI if e[0] == "たりせ"]
    assert tarise == [("たりせ", "為ら", ("爲", "為"))]
    # 現行 guard の他条も不変（M なかれ (勿,)・何のごとし (奈,)）
    nakare = [e for e in M_KANA_TO_KANJI if e[0] == "なかれ"]
    assert nakare == [("なかれ", "勿かれ", ("勿",))]
    gotoshi = [e for e in M_KANA_TO_KANJI if e[0] == "何のごとし"]
    assert gotoshi == [("何のごとし", "奈何", ("奈",))]
    # repl 终字形＋構造冪等（repl に kana 非含有＝再発火なし）
    assert normalize_shinjitai("為") == "為" and normalize_shinjitai("奈何ぞ") == "奈何ぞ"
    assert "がため" not in "為" and "何のごとく" not in "奈何ぞ"


# ---------- 幂等・無 kana 现代句・N84 echo 行型 ----------
def test_idempotent_and_modern():
    for fn, text, hb in ((style_kana_to_kanji_l, "之がため奈何。", "戦則不勝為之奈何"),
                         (style_kana_to_kanji_m, "何のごとく其の後を続す。", "柰何續其後")):
        once = fn(text, hb)
        assert fn(once, hb) == once
    # 同一行内 C1+C4 併用（全链・変体字両方の白文）
    out = style_fix_with_hakubun("之がため奈何。何のごとく其の後を続す。", "為柰")
    assert out == "之為奈何。奈何ぞ其の後を続す。"
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_l("本日の会議は十時から開始されます。", "為柰") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝kana なしで L/M も非発火）
    assert style_kana_to_kanji_m("器械を習い用う", "柰何") == "器械を習い用う"
    assert style_kana_to_kanji_l("器械を習い用う", "為之") == "器械を習い用う"


# ---------- 链序不変（T/U 領域との併用・N99 変差 6 行集合に触れない） ----------
def test_chain_order_and_neighbors_untouched():
    # Rule T（べからず族）＋Rule U（なかれ）＋C1 併用＝链序不変
    out = style_fix_with_hakubun("断絶するべからず。掃くことなかれ。之がため奈何。", "不可斷絕掃花莫為")
    assert out == "断絶する可からず。掃くこと莫かれ。之為奈何。"
    # kokyo09-5 行型（N104 変差 1 行＝拍板許容・U 挙動不変＝N99 変差集合不拡大）
    assert style_fix_with_hakubun("父を厳して大なりて天を配すことなかれ。", "嚴父莫大於配天。") == \
        "父を厳して大なりて天を配すこと莫かれ。"
    # U の禁区（本夜も一字不動）：がため の U 側非発火（U は なかれ 1 键のみ）
    assert style_kana_to_kanji_u_like("武王がために備えしむ。", "莫") == "武王がために備えしむ。"


def style_kana_to_kanji_u_like(text, hb):
    # U は本夜未触（链尾 T→U 不変の実働確認・U_KANA_TO_KANJI 直接 import を避ける迂回）
    from backend.kundoku_rules import style_kana_to_kanji_u
    return style_kana_to_kanji_u(text, hb)


# ---------- night104 基线锚（両行 d0＝44/25・両行 4000 外） ----------
def test_night104_baseline_anchor():
    doc8 = json.load(open(os.path.join(EV, "night104_results_8165.json"), encoding="utf-8"))
    sm8 = doc8["summary"]
    assert abs(sm8["avg_edit_distance"] - 13.467) <= 0.0005
    assert sm8["exact"] == 30 and sm8["errors"] == 0
    ids8 = {r["id"]: r for r in doc8["results"]}
    assert ids8["rikutou37-2"]["edit_distance"] == 44
    assert ids8["shiki050-4"]["edit_distance"] == 25
    # 両行とも 4000 外（golden_4000 逐位一致の根拠＝N106「両行 4000 外」実測）
    doc4 = json.load(open(os.path.join(EV, "night104_results_4000.json"), encoding="utf-8"))
    ids4 = {r["id"] for r in doc4["results"]}
    assert "rikutou37-2" not in ids4 and "shiki050-4" not in ids4
    assert abs(doc4["summary"]["avg_edit_distance"] - 13.460) <= 0.0005
