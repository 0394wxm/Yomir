# -*- coding: utf-8 -*-
"""test_night99_rule_t.py — N99 拍板夜：Rule T（かな→漢字第 15 批・撤 0 変差硬门の
3 条収録）锁定测试。

方法论同 N96 test：正例（実語料行型・改善行 3 行）＋変差 6 行の行動ロック（N98 実測
ID の got→new 断言・sim JSON の ID 集合一致）＋無護栏反例（guard 可 外一字不動・空白文
で発火＝E〜K 世代同语义）／禁区不复活（なかれ・ことなく・は系・がため・何のごとく・
嗟や——本夜一字不動の再発防止）／構造ロック（3 条・長詞表空壳・repl 终字形）／
链序 Q→R→S→T（pipeline 順）／幂等／無 kana 现代句一字不动／N84 echo 行型一字不动。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    T_KANA_TO_KANJI, T_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_t, style_fix_with_hakubun,
)

EV = os.path.join(ROOT, "eval")


# ---------- 正例（実語料行型・night99_sim 改善行 3 行） ----------
def test_rule_t_positive_improvement_rows():
    # tankako_soso-20 行型（白文 不可斷絕 → got「断絶するべからず」→「断絶する可からず」・2→1 改善）
    assert style_kana_to_kanji_t("断絶するべからず", "不可斷絕") == "断絶する可からず"
    # yamai-x12 行型（白文 不可爲也 → 「為すべからざるなり。」→「為す可からざるなり。」・4→3 改善）
    assert style_kana_to_kanji_t("為すべからざるなり。", "不可爲也。") == "為す可からざるなり。"
    # gashin-x18 行型（白文 檟可材也 → 「檟は材べきなり。」→「檟は材可きなり。」・3→2 改善）
    assert style_kana_to_kanji_t("檟は材べきなり。", "檟可材也。") == "檟は材可きなり。"


# ---------- 変差 6 行の行動ロック（N98 実測 ID・got→new 一致＝拍板許容行） ----------
def test_rule_t_variation_rows_n98_fragments():
    # T1 べからず 変差 5 行中 4 行（saio-x13 は combo で持平＝変差外・交互作用）
    assert style_kana_to_kanji_t(
        "兎は復た得るべからず、而して身は宋の国たるに笑う。",
        "兎不可復得、而身爲宋國笑。") == \
        "兎は復た得る可からず、而して身は宋の国たるに笑う。"          # shushu-4 11→12
    assert style_kana_to_kanji_t(
        "然りて則ち小なるは固く以て敵を大なるべからずして。",
        "小固不可以敵大") == \
        "然りて則ち小なるは固く以て敵を大なる可からずして。"          # shukateki-1 36→39 の一分節
    assert style_kana_to_kanji_t(
        "夫の人は自らを勉せざるべからず。",
        "夫人不可不自勉") == \
        "夫の人は自らを勉せざる可からず。"                            # ryojo-3 26→27 の一分節
    assert style_kana_to_kanji_t(
        "久なりて豺虎が乱するに留めるべからず",
        "不可久留豺虎亂") == \
        "久なりて豺虎が乱するに留める可からず"                        # toushisen216-7 7→8（4000 外）
    # T2 べからざる 変差 1 行
    assert style_kana_to_kanji_t(
        "民は得て治めるべからざるなり。",
        "民不可得而治也") == \
        "民は得て治める可からざるなり。"                              # shiseinishite-1 73→74 の一分節
    # T3 べきなり 変差 1 行（白文 可＝可狎義と guard 可 非分離＝N88 §7 移交①）
    assert style_kana_to_kanji_t(
        "夫れ竜の虫たるなり、柔なりて狎して騎するべきなり。",
        "夫龍之爲蟲也、柔可狎而騎也") == \
        "夫れ竜の虫たるなり、柔なりて狎して騎する可きなり。"          # p-gekirin-1 8→9


def test_rule_t_variation_id_lock_n98():
    # N98 実測変差 6 行の ID ロック（eval/night99_sim.json 読み・上限 6 行・超出不可）
    sim = json.load(open(os.path.join(EV, "night99_sim.json"), encoding="utf-8"))
    assert sim["verdict"] == "PASS"
    c123 = sim["gates"]["combo123"]
    assert sorted(c123["worse_ids"]) == sorted([
        "shushu-4", "shukateki-1", "ryojo-3", "shiseinishite-1",
        "toushisen216-7", "p-gekirin-1"])
    assert c123["worse"] == 6 and c123["idempotent_bad"] == 0
    assert c123["pred_exact4000"] == 24 and c123["pred_exact8165"] == 30
    c12 = sim["gates"]["combo12"]
    assert sorted(c12["worse_ids"]) == sorted([
        "shushu-4", "shukateki-1", "ryojo-3", "shiseinishite-1", "toushisen216-7"])
    assert c12["changed"] == 157 and c12["better"] == 146 and c12["worse"] == 5


# ---------- 無護栏反例（guard 可 外＝一字不動・空白文で発火） ----------
def test_rule_t_guard_negative_and_empty_hb():
    # guard 可 外＝一字不動（N86 拒案「exp 自写仮名死因」の対象外行を守る机制自体は維持）
    assert style_kana_to_kanji_t("兎は復た得るべからず。", "兔不可復得莫") == \
        "兎は復た得る可からず。"   # 可 有り＝発火（対照）
    assert style_kana_to_kanji_t("兎は復た得るべからず。", "莫勿毋") == \
        "兎は復た得るべからず。"   # 可 無し＝不動
    assert style_kana_to_kanji_t("民は得て治めるべからざるなり。", "將未") == \
        "民は得て治めるべからざるなり。"
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_t("断絶するべからず", "") == "断絶する可からず"
    assert style_kana_to_kanji_t("為すべからざるなり", "") == "為す可からざるなり"
    assert style_kana_to_kanji_t("檟は材べきなり", "") == "檟は材可きなり"


# ---------- 禁区不复活（本夜一字不動の再発防止） ----------
def test_rule_t_forbidden_zones_untouched():
    # なかれ（別拍板・kokyo09-5 1 変差のまま）・ことなく（Q の領域）・は系・がため・
    # 何のごとく・嗟や——いずれも T の 3 键外＝一字不動
    assert style_kana_to_kanji_t("己に如かざる者を友すること毋かれ。", "友莫") == \
        "己に如かざる者を友すること毋かれ。"
    assert style_kana_to_kanji_t("之を事うることなく。", "事莫") == "之を事うることなく。"
    assert style_kana_to_kanji_t("夫れ人は自らを勉せざるべからず。", "將未") == \
        "夫れ人は自らを勉せざるべからず。"   # 可 無し→T 非発火・は系も T は触らない
    assert style_kana_to_kanji_t("武王がために備えしむ。", "爲") == \
        "武王がために備えしむ。"
    assert style_kana_to_kanji_t("今乃首率七國のごとくや。", "奈") == \
        "今乃首率七國のごとくや。"
    assert style_kana_to_kanji_t("嗟や、人を害すこと勿かれ。", "乎勿") == \
        "嗟や、人を害すこと勿かれ。"


# ---------- 構造ロック ----------
def test_rule_t_structure_and_chain_order():
    assert len(T_KANA_TO_KANJI) == 3
    assert [e[0] for e in T_KANA_TO_KANJI] == ["べからず", "べからざる", "べきなり"]
    assert [e[1] for e in T_KANA_TO_KANJI] == ["可からず", "可からざる", "可きなり"]
    assert [list(e[2]) for e in T_KANA_TO_KANJI] == [["可"], ["可"], ["可"]]
    assert all(len(e) == 3 for e in T_KANA_TO_KANJI)
    assert set(T_LONGER_WORDS) == {"べからず", "べからざる", "べきなり"}
    assert all(v == () for v in T_LONGER_WORDS.values())
    for _kana, repl, _guard in T_KANA_TO_KANJI:
        assert normalize_shinjitai(repl) == repl
    # 三键互不重叠（べからず は べからざる の部分文字列でない＝順序非依存）
    assert "べからず" not in "べからざる"
    # 链序 Q→R→S→T：同一 chain で併用可
    assert style_fix_with_hakubun(
        "進むことなく夷狄にゆく。欺すことなきなり。断絶するべからず。檟は材べきなり。",
        "進莫夷狄之勿不可斷絕檟可材也") == \
        "進むこと莫く夷狄に之く。欺すこと勿かれ。断絶する可からず。檟は材可きなり。"
    # Q すべからず（先に消費）と T べからず（残量）の共存
    assert style_fix_with_hakubun("すべからず得るべからず。", "不可復得") == \
        "可からず得る可からず。"
    # T 適用後の got に べからず/べからざる/べきなり が残らない（guard 内）
    out = style_fix_with_hakubun("断絶するべからず。為すべからざるなり。檟は材べきなり。",
                                 "不可斷絕不可爲也檟可材也")
    assert "べからず" not in out and "べからざる" not in out and "べきなり" not in out


def test_rule_t_idempotent_and_modern():
    for text, hb in (("断絶するべからず。", "不可斷絕"),
                     ("為すべからざるなり。", "不可爲也。"),
                     ("檟は材べきなり。", "檟可材也。")):
        once = style_kana_to_kanji_t(text, hb)
        assert style_kana_to_kanji_t(once, hb) == once
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_t("本日の会議は十時から開始されます。", "") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝白文直出対象・kana なしで T も非発火）
    assert style_kana_to_kanji_t("器械を習い用う", "勿不習用器械") == "器械を習い用う"
