# -*- coding: utf-8 -*-
"""test_night94_rule_r.py — N94: Rule R（かな→漢字第 13 批・1 字块 3〜5 行区长键手測）锁定测试。

方法论同 N92 test：正例（実語料行型）＋無護栏反例（一字不動）＋空白文で guard 規則も
発火（E〜K 世代同语义）／拒案不复活（N92 未试替 11 块・(は,*) scramble・嗟や→嗟乎
収録線未達・は→将に／は→未だ blanket・長尾 scan scramble patch 3 件——いずれも
night94_probe/sim 拒案の再発防止）／構造ロック（1 条・長詞表空壳・repl 终字形）／
链序 Q→R（pipeline 順）／幂等／無 kana 现代句一字不动／N84 echo 行型一字不动。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    R_KANA_TO_KANJI, R_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_r, style_fix_with_hakubun,
)


# ---------- 正例（実語料行型） ----------
def test_rule_r_yuku_shiku():
    # orutokoro-1 行型（白文 夷狄之 与……——engine 行型・guard 之）
    assert style_kana_to_kanji_r("夷狄にゆくと雖も、棄するべからざるなり。",
                                 "夷狄之與棄不可") == \
        "夷狄に之くと雖も、棄するべからざるなり。"
    # kotaku-1 行型（走りて燕にゆく→走りて燕に之く）
    assert style_kana_to_kanji_r("走りて燕にゆく。鴟の夷子は皮に負いて伝えて従う。",
                                 "走燕之鴟夷子皮負傳而従") == \
        "走りて燕に之く。鴟の夷子は皮に負いて伝えて従う。"
    # sonshi11-42 行型（ゆく所を知る→之く所を知る）
    assert style_kana_to_kanji_r("駆られて往き、駆られて来るも、ゆく所を知ら",
                                 "之所不知") == \
        "駆られて往き、駆られて来るも、之く所を知ら"


# ---------- 無護栏反例（guard 外＝一字不動） ----------
def test_rule_r_guard_negative():
    # guard 之 外：ゆく は不動（rongo1705-1 は guard 内改善行・この行は白文に之なし）
    assert style_kana_to_kanji_r("樊遅は仁を問う。夷狄にゆくと雖も。",
                                 "樊遅問仁夷狄") == \
        "樊遅は仁を問う。夷狄にゆくと雖も。"
    # 白文に之なゆゆく連用形は不動
    assert style_kana_to_kanji_r("水はゆく方無し。", "水流無方") == "水はゆく方無し。"


def test_rule_r_empty_hakubun_semantics():
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_r("夷狄にゆくと雖も", "") == "夷狄に之くと雖も"
    assert style_kana_to_kanji_r("走りて燕にゆく", "") == "走りて燕に之く"


# ---------- 拒案不复活（night94_probe/sim 拒案の再発防止） ----------
def test_rule_r_rejection_n92_untested_blocks():
    # (a) N92 未试替块（任务书清单）：実測 blanket scramble（probe T1〜T4・T12）
    # の→之に：1464 発火 1393 変差＝の blanket scramble
    assert style_kana_to_kanji_r("宗の瀟が美なるを灑するは年を少なり。", "宗之瀟灑美少") == \
        "宗の瀟が美なるを灑するは年を少なり。"
    # も→与に：248 発火 173 変差
    assert style_kana_to_kanji_r("嘗て人とも傭耕す。", "嘗與人傭耕") == "嘗て人とも傭耕す。"
    # とも→与に：B2 4 字长键でも 245 発火 137 変差＝とも blanket scramble
    assert style_kana_to_kanji_r("君孰とも足さず。", "君孰與不足") == "君孰とも足さず。"
    # は→有：614 発火 186 変差（烏は→烏有・冉は→冉有 专名 patch も非収）
    assert style_kana_to_kanji_r("冉は僕有り。", "冉有僕") == "冉は僕有り。"
    assert style_kana_to_kanji_r("烏は先生の者有り。", "烏有先生") == "烏は先生の者有り。"
    # な→莫：85 発火 24 変差＝ことなき/なかれ 禁区残量の blanket（R は不収）
    assert style_kana_to_kanji_r("何ぞ斯の道を由ることなきなり。", "何莫由斯道") == \
        "何ぞ斯の道を由ることなきなり。"


def test_rule_r_rejection_ha_onechar_blocks():
    # (は,*) 7 块（少/白/行/来/尽/樹/闕）：probe T5〜T11 いずれも blanket scramble
    assert style_kana_to_kanji_r("陳渉は時を少なり。", "陳渉少時") == "陳渉は時を少なり。"
    assert style_kana_to_kanji_r("頭の鬚は白にたり。", "頭鬚尽白") == "頭の鬚は白にたり。"
    assert style_kana_to_kanji_r("君は行かんと欲すも留まる。", "行留") == "君は行かんと欲すも留まる。"
    assert style_kana_to_kanji_r("客は来たりて門を叩く。", "客來叩門") == "客は来たりて門を叩く。"
    assert style_kana_to_kanji_r("言は尽くされり。", "言尽") == "言は尽くされり。"
    assert style_kana_to_kanji_r("庭は樹を植う。", "庭樹") == "庭は樹を植う。"
    assert style_kana_to_kanji_r("礼は闕くること無し。", "礼闕") == "礼は闕くること無し。"


def test_rule_r_rejection_b_band_uniform():
    # (b) 3〜5 行区 uniform 候补の全滅実測（probe T13〜T31）
    # 嗟や→嗟乎：3 発火 3 改善 0 変差 だが Δ−0.000367＝収録線未達の無益拒
    assert style_kana_to_kanji_r("嗟や、燕雀が安んぞ鴻鵠のを知りて志か。", "嗟乎燕雀安知鴻鵠志") == \
        "嗟や、燕雀が安んぞ鴻鵠のを知りて志か。"
    # や→乎 blanket：251 発火 82 変差
    assert style_kana_to_kanji_r("嗟や、士は己を知る者たりて死す。", "嗟乎") == \
        "嗟や、士は己を知る者たりて死す。"
    # 重排 artifact 型（は→請う 46/42・は→見ずや 196/183・は→無 535/152・は→不 1245/430・
    # は→為に 615/561・は→復た 91/72・は→自ずから 191/166・に→郷 48/30・を→者に 798/759）
    assert style_kana_to_kanji_r("臣は璧を完して帰るを請う。", "臣請完璧帰趙") == \
        "臣は璧を完して帰るを請う。"
    assert style_kana_to_kanji_r("君は管の鮑は貧時に交すを見ず", "君見ずや管鮑貧時交") == \
        "君は管の鮑は貧時に交すを見ず"
    assert style_kana_to_kanji_r("碣石瀟湘は限ること無き路", "碣石瀟湘無限路") == \
        "碣石瀟湘は限ること無き路"
    assert style_kana_to_kanji_r("回は敏ならずと雖も。", "回不敏") == "回は敏ならずと雖も。"
    assert style_kana_to_kanji_r("頭の鬚は白にたり。", "頭鬚為に白し") == "頭の鬚は白にたり。"
    assert style_kana_to_kanji_r("復た旧き池台を尋ぬ。", "復た旧池台") == "復た旧き池台を尋ぬ。"
    assert style_kana_to_kanji_r("万物は自らを賓んとす。", "万物将自賓") == "万物は自らを賓んとす。"
    assert style_kana_to_kanji_r("故に今の夜を郷して千里を思す", "故郷今夜千里思") == \
        "故に今の夜を郷して千里を思す"
    assert style_kana_to_kanji_r("人とも忠す。", "與人忠") == "人とも忠す。"
    # な→悠た（19 発火 16 変差）・ら→回か（16 発火 10 変差）・に→来（135 発火 63 変差）
    assert style_kana_to_kanji_r("悠たるかな。", "悠た哉") == "悠たるかな。"
    assert style_kana_to_kanji_r("幾らべからざるなり。", "回か幾") == "幾らべからざるなり。"
    assert style_kana_to_kanji_r("之に来たる者。", "之來") == "之に来たる者。"


def test_rule_r_rejection_scramble_blankets_and_longtail():
    # は→将に／は→未だ：N92 T1/T2 blanket scramble の再確認（guard 新旧両形＝將 含む）
    assert style_kana_to_kanji_r("吾は仕へんとするか。", "吾將仕之") == "吾は仕へんとするか。"
    assert style_kana_to_kanji_r("我は仁を好む者を未だ見ず。", "未見好仁者") == \
        "我は仁を好む者を未だ見ず。"
    # 長尾 scan の 2 行 scramble patch 3 件（N86/N88/N92 拒案逐字同名＝枯竭复核・過拟合拒）
    assert style_kana_to_kanji_r("其は民をしてなる義せしむ。", "其の民を使うや義") == \
        "其は民をしてなる義せしむ。"
    assert style_kana_to_kanji_r("必ず以て新なるをしむるの尹に告す。", "以て新令尹に告ぐ") == \
        "必ず以て新なるをしむるの尹に告す。"
    assert style_kana_to_kanji_r("吾はなる賤むを少なり。", "吾少くして賤し") == \
        "吾はなる賤むを少なり。"


# ---------- 構造ロック ----------
def test_rule_r_structure_and_chain_order():
    # 1 条構造・長詞表空壳（K/Q 同款系列同构）
    assert len(R_KANA_TO_KANJI) == 1
    assert [e[0] for e in R_KANA_TO_KANJI] == ["ゆく"]
    assert [e[1] for e in R_KANA_TO_KANJI] == ["之く"]
    assert [list(e[2]) for e in R_KANA_TO_KANJI] == [["之"]]
    assert all(len(e) == 3 for e in R_KANA_TO_KANJI)
    assert set(R_LONGER_WORDS) == {"ゆく"}
    assert all(v == () for v in R_LONGER_WORDS.values())
    # repl は终字形（normalize_shinjitai 不変・之 は新旧変異なし）
    for _kana, repl, _guard in R_KANA_TO_KANJI:
        assert normalize_shinjitai(repl) == repl
    # 链序 Q→R：pipeline で Q ことなく/すべからず と R ゆく が同一 chain で併用可
    assert style_fix_with_hakubun("進むことなく夷狄にゆくと雖も。", "進莫夷狄之") == \
        "進むこと莫く夷狄に之くと雖も。"
    # R 適用後の got に ゆく が残らない（guard 内）
    assert "ゆく" not in style_fix_with_hakubun("走りて燕にゆく。", "走燕之")


def test_rule_r_idempotent_and_modern():
    for text, hb in (("夷狄にゆくと雖も。", "夷狄之"),
                     ("走りて燕にゆく。", "走燕之"),
                     ("ゆく所を知ら", "之所不知")):
        once = style_kana_to_kanji_r(text, hb)
        assert style_kana_to_kanji_r(once, hb) == once
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_r("本日の会議は十時から開始されます。", "") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝白文直出対象・kana なしで R も非発火）
    assert style_kana_to_kanji_r("器械を習い用う", "莫不習用器械") == "器械を習い用う"
