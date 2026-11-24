# -*- coding: utf-8 -*-
"""test_night92_rule_q.py — N92: Rule Q（かな→漢字第 12 批・1 字块锚定长键手測）锁定测试。

方法论同 N86/N73 test：每条正例（実語料行型）＋無護栏反例（一字不動）＋
空白文で guard 規則も発火（E〜K 世代同语义）／拒案不复活（ことなき→こと莫き・
は→将に／は→未だ／たる→為る／以て→以為えらく scramble・るべ→可・べきか→可きか・
べからず→可からず blanket・べからざる・なかれ→莫かれ・長尾 scan scramble patch 3 件
——いずれも night92_probe/sim 拒案の再発防止）／構造ロック（2 条・長詞表空壳・
repl 终字形）／链序 O→Q（pipeline 順）／幂等／無 kana 现代句一字不动／
N84 echo 行型一字不动。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    Q_KANA_TO_KANJI, Q_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_q, style_fix_with_hakubun,
)


# ---------- 各条正例（実語料行型） ----------
def test_rule_q_kotonaku_mokaku():
    # rikutou08-3 行型（白文尾段に 莫 有り＝rerun 行型・guard 上下文は尾段）
    assert style_kana_to_kanji_q("進むことなく而して争す、退くことなく而して遜る。",
                                 "進莫退莫") == \
        "進むこと莫く而して争す、退くこと莫く而して遜る。"
    # roushi32-2 行型（白文 民莫令而自均——engine 行型・guard 莫）
    assert style_kana_to_kanji_q("民は之をしてしむることなく而して自ら均す。",
                                 "民莫之令而自均") == \
        "民は之をしてしむること莫く而して自ら均す。"
    # kokyo09-15 行型（続して大なることなく焉×莫 型）
    assert style_kana_to_kanji_q("続して大なることなく焉。", "莫大焉") == \
        "続して大なること莫く焉。"


def test_rule_q_subekarazu_kanarazu():
    # sonshi12-25 行型（白文 亡国不可復存——すべからず のみ該当・するべからず は非該当）
    assert style_kana_to_kanji_q("亡国は以て復た存するべからず、死者は以て復た生すべからず。",
                                 "亡国不可復存") == \
        "亡国は以て復た存するべからず、死者は以て復た生可からず。"
    # toushisen308-3 行型（道が神仙が接すべからずと聞く）
    assert style_kana_to_kanji_q("道が神仙が接すべからずと聞く。", "可接神仙") == \
        "道が神仙が接可からずと聞く。"


# ---------- 無護栏反例（guard 外＝一字不動） ----------
def test_rule_q_guard_negative():
    # guard 莫 外：ことなく は不動
    assert style_kana_to_kanji_q("進むことなく而して争す。", "進退爭遜") == \
        "進むことなく而して争す。"
    # guard 可 外：すべからず は不動
    assert style_kana_to_kanji_q("死者は以て復た生すべからず。", "死者復生也") == \
        "死者は以て復た生すべからず。"


def test_rule_q_empty_hakubun_semantics():
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_q("進むことなく而して争す", "") == "進むこと莫く而して争す"
    assert style_kana_to_kanji_q("生すべからず", "") == "生可からず"


# ---------- 拒案不复活（night92_probe/sim 拒案の再発防止） ----------
def test_rule_q_rejection_kotonaki_and_nakare():
    # ことなき→こと莫き：probe T4 2 変差（roushi46-2/rikutou26-5＝got 已含莫かれ・
    # exp 字形混在 莫く/莫し）で拒——Q は ことなく のみ
    assert style_kana_to_kanji_q("咎して大なりて得んと欲することなきに。",
                                 "莫大於欲得") == \
        "咎して大なりて得んと欲することなきに。"
    # なかれ→莫かれ post-N umbrella：kokyo09-5 1 変差＝拍板事項のまま（O も Q も不収）
    assert style_kana_to_kanji_q("父を厳して大なりて天を配すことなかれ。",
                                 "嚴父莫大於配天") == \
        "父を厳して大なりて天を配すことなかれ。"


def test_rule_q_rejection_scramble_blankets():
    # は→将に／は→未だ／たる→為る／以て→以為えらく：probe T1/T2/T5/T8
    # blanket 発火 ≫ pair 行数＝語彙対応でない scramble（N88 T3 判別実例の适用）
    assert style_kana_to_kanji_q("吾は仕へんとするか。", "吾將仕之") == "吾は仕へんとするか。"
    assert style_kana_to_kanji_q("我は仁を好む者を未だ見ず。", "未見好仁者") == \
        "我は仁を好む者を未だ見ず。"
    assert style_kana_to_kanji_q("人君たる者は盂のごときなり。", "為君者猶盂") == \
        "人君たる者は盂のごときなり。"
    assert style_kana_to_kanji_q("以て天地万物の事を備したりて。", "以為備") == \
        "以て天地万物の事を備したりて。"


def test_rule_q_rejection_bekarazu_family_umbrella():
    # べからず→可からず blanket：N72 拒案 5 変差のまま（Q は すべからず prefix のみ）
    assert style_kana_to_kanji_q("久なりて豺虎が乱するに留めるべからず",
                                 "不可久留豺虎之乱") == \
        "久なりて豺虎が乱するに留めるべからず"
    # るべからず prefix：N86 T4 3 変差で拒（るべからず は すべからず 非該当）
    assert style_kana_to_kanji_q("勉せざるべからず。", "不可不自勉") == "勉せざるべからず。"
    # べからざる→可からざる：shiseinishite-1 1 変差で拒
    assert style_kana_to_kanji_q("民は得て治めるべからざるなり。", "不可得而治也") == \
        "民は得て治めるべからざるなり。"
    # るべ→可（91/7）・べきか→可きか（25/2）：N86 T1/T5 拒案維持
    assert style_kana_to_kanji_q("逝くべきなり", "可逝也") == "逝くべきなり"
    assert style_kana_to_kanji_q("則ち居るは知るべきか。", "則知居") == "則ち居るは知るべきか。"


def test_rule_q_rejection_longtail_scramble_patches():
    # 長尾 scan の 2 行 scramble patch 3 件（N86/N88 拒案逐字同名＝枯竭复核・過拟合拒）
    assert style_kana_to_kanji_q("其は民をしてなる義せしむ。", "其の民を使うや義") == \
        "其は民をしてなる義せしむ。"
    assert style_kana_to_kanji_q("必ず以て新なるをしむるの尹に告す。", "以て新令尹に告ぐ") == \
        "必ず以て新なるをしむるの尹に告す。"
    assert style_kana_to_kanji_q("吾はなる賤むを少なり。", "吾少くして賤し") == \
        "吾はなる賤むを少なり。"


# ---------- 構造ロック ----------
def test_rule_q_structure_and_chain_order():
    # 2 条構造・長詞表空壳（K 同款系列同构）
    assert len(Q_KANA_TO_KANJI) == 2
    assert [e[0] for e in Q_KANA_TO_KANJI] == ["ことなく", "すべからず"]
    assert [e[1] for e in Q_KANA_TO_KANJI] == ["こと莫く", "可からず"]
    assert all(len(e) == 3 for e in Q_KANA_TO_KANJI)
    assert set(Q_LONGER_WORDS) == {"ことなく", "すべからず"}
    assert all(v == () for v in Q_LONGER_WORDS.values())
    # repl は终字形（normalize_shinjitai 不変）
    for _kana, repl, _guard in Q_KANA_TO_KANJI:
        assert normalize_shinjitai(repl) == repl
    # 链序 O→Q：pipeline で Q が O の後（O が ことなきか→こと莫し した行に Q は非該当＝冪等）
    assert style_fix_with_hakubun("進むことなく而して争す。", "進莫退莫") == \
        "進むこと莫く而して争す。"
    assert style_fix_with_hakubun("我が守を攻しての計を測ることなきか。", "莫能測我攻守之計") == \
        "我が守を攻しての計を測ること莫し。"


def test_rule_q_idempotent_and_modern():
    for text, hb in (("進むことなく而して争す。", "進莫退莫"),
                     ("生すべからず。", "不可復生"),
                     ("測ることなきか。", "莫能測")):
        once = style_kana_to_kanji_q(text, hb)
        assert style_kana_to_kanji_q(once, hb) == once
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_q("本日の会議は十時から開始されます。", "") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝白文直出対象・kana なしで Q も非発火）
    assert style_kana_to_kanji_q("器械を習い用う", "莫不習用器械") == "器械を習い用う"
