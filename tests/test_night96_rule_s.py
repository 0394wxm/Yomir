# -*- coding: utf-8 -*-
"""test_night96_rule_s.py — N96: Rule S（かな→漢字第 14 批・micro 区带 rows<=2 ＋
B2 (べ,可) prefix 分離 副切面）锁定测试。

方法论同 N94 test：正例（実語料行型 4 行・含 rerun 行型）＋無護栏反例（一字不動）＋
空白文で guard 規則も発火（E〜K 世代同语义）／拒案不复活（か→哉・なるか→なる哉・
ず→毋く・なきなり→毋かれ・な→勿・るか→可し・べきか→可し・長尾 scan scramble
patch 3 件・禁区 4 件——いずれも night96_probe/sim 拒案の再発防止）／構造ロック
（1 条・長詞表空壳・repl 终字形）／链序 Q→R→S（pipeline 順）／幂等／無 kana
现代句一字不动／N84 echo 行型一字不动。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    S_KANA_TO_KANJI, S_LONGER_WORDS,
    normalize_shinjitai,
    style_kana_to_kanji_s, style_fix_with_hakubun,
)


# ---------- 正例（実語料行型） ----------
def test_rule_s_nakinari_motsukare():
    # azamukuko-1 行型（論語憲問 欺くこと勿かれ・guard 勿）
    assert style_kana_to_kanji_s("子曰く、欺すことなきなり。而して之を犯す。",
                                 "勿欺也而犯之") == \
        "子曰く、欺すこと勿かれ。而して之を犯す。"
    # sonshi09-19 行型（孫子 近づくこと勿かれ）
    assert style_kana_to_kanji_s("必ず亟なりて之に去く、近きことなきなり。",
                                 "必亟去之近勿") == \
        "必ず亟なりて之に去く、近きこと勿かれ。"
    # sonshi10-12 行型（孫子 従うこと勿かれ）
    assert style_kana_to_kanji_s("引きて之に去くは従うことなきなり。",
                                 "引去之従勿") == \
        "引きて之に去くは従うこと勿かれ。"
    # rikutou21-2 行型（rerun 行・guard 上下文＝尾段。尾段に 勿かれ 在りて発火）
    assert style_kana_to_kanji_s("弁して説くを以て必ず然るを為すことなきなり。",
                                 "勿坐") == \
        "弁して説くを以て必ず然るを為すこと勿かれ。"


# ---------- 無護栏反例（guard 外＝一字不動） ----------
def test_rule_s_guard_negative():
    # guard 勿 外：なきなり は不動（なきなり→毋かれ T5 変差 2 行＝exp 毋きなり 字形混在の再発防止）
    assert style_kana_to_kanji_s("所謂其が意するを誠なる者、自らを欺すことなきなり。",
                                 "自欺毋") == \
        "所謂其が意するを誠なる者、自らを欺すことなきなり。"
    # 白文に勿な なからん 型（rongo0604-1 行型）も不動
    assert style_kana_to_kanji_s("用することなからんと欲すと雖も。", "用欲") == \
        "用することなからんと欲すと雖も。"


def test_rule_s_empty_hakubun_semantics():
    # 空白文＝guard 規則も発火（E〜K 世代同语义）
    assert style_kana_to_kanji_s("欺すことなきなり", "") == "欺すこと勿かれ"
    assert style_kana_to_kanji_s("近きことなきなり", "") == "近きこと勿かれ"


# ---------- 拒案不复活（night96_probe/sim 拒案の再発防止） ----------
def test_rule_s_rejection_micro_blankets():
    # か→哉：104 発火 45 変差＝(か,哉) micro 2 pair は詩経反復の語汇対応だが guard では守れない
    assert style_kana_to_kanji_s("悠なるか悠なるか反側を輾転す。", "悠哉輾轉反側") == \
        "悠なるか悠なるか反側を輾転す。"
    # なるか→なる哉：集約パス (a) 不成立（28 発火 15 変差）
    assert style_kana_to_kanji_s("茫茫なるか天の常は在り。", "茫茫哉天常") == \
        "茫茫なるか天の常は在り。"
    # ず→毋く：7 発火 2 改善/3 変差（必ず→必毋く 2 行は改善だが shindoku-1 の exp 必ず で変差）
    assert style_kana_to_kanji_s("故に君子は必ず其が独なるを慎するなり。", "必固我毋") == \
        "故に君子は必ず其が独なるを慎するなり。"
    # な→勿：blanket scramble（31 発火 11 変差）
    assert style_kana_to_kanji_s("山川其れ諸を舎す。", "山川其舍諸勿") == \
        "山川其れ諸を舎す。"
    # るか→可し：blanket scramble（34 発火 11 変差）
    assert style_kana_to_kanji_s("行うべきか。是の籍は遂に剣を抜きて斬る。", "行可斬") == \
        "行うべきか。是の籍は遂に剣を抜きて斬る。"


def test_rule_s_rejection_bek_block_and_longtail():
    # べきか→可し：(べ,可) 族新 repl 実測 31 発火 26/3＝0 変差门で拒（B2 rows>=4 数字は
    # N86/N88/N92/N94 と完全一致の复核済み）
    assert style_kana_to_kanji_s("以て師たるべきか。", "温故知新師可") == \
        "以て師たるべきか。"
    # 禁区（拍板事項・本夜も一字未动）：べきなり／べからず族／なかれ／ことなき
    assert style_kana_to_kanji_s("其れ可きなり。", "其可") == "其れ可きなり。"
    assert style_kana_to_kanji_s("貧と雖もべからざるなり。", "貧可") == \
        "貧と雖もべからざるなり。"
    assert style_kana_to_kanji_s("己に如かざる者を友すること毋かれ。", "友莫") == \
        "己に如かざる者を友すること毋かれ。"
    assert style_kana_to_kanji_s("之を事うることなきなり。", "事莫") == \
        "之を事うることなきなり。"
    # 長尾 scan の 2 行 scramble patch 3 件（N86/N88/N92/N94 拒案逐字同名・5 夜連続＝
    # Δ線達成でも N86 惯例 過拟合拒）
    assert style_kana_to_kanji_s("其は民をしてなる義せしむ。", "其の民を使うや義") == \
        "其は民をしてなる義せしむ。"
    assert style_kana_to_kanji_s("必ず以て新なるをしむるの尹に告す。", "以て新令尹に告ぐ") == \
        "必ず以て新なるをしむるの尹に告す。"
    assert style_kana_to_kanji_s("吾はなる賤むを少なり。", "吾少くして賤し") == \
        "吾はなる賤むを少なり。"


# ---------- 構造ロック ----------
def test_rule_s_structure_and_chain_order():
    # 1 条構造・長詞表空壳（R/Q 同款系列同构）
    assert len(S_KANA_TO_KANJI) == 1
    assert [e[0] for e in S_KANA_TO_KANJI] == ["なきなり"]
    assert [e[1] for e in S_KANA_TO_KANJI] == ["勿かれ"]
    assert [list(e[2]) for e in S_KANA_TO_KANJI] == [["勿"]]
    assert all(len(e) == 3 for e in S_KANA_TO_KANJI)
    assert set(S_LONGER_WORDS) == {"なきなり"}
    assert all(v == () for v in S_LONGER_WORDS.values())
    # repl は终字形（normalize_shinjitai 不変・勿 は新旧変異なし）
    for _kana, repl, _guard in S_KANA_TO_KANJI:
        assert normalize_shinjitai(repl) == repl
    # 链序 Q→R→S：pipeline で Q ことなく/すべからず・R ゆく・S なきなり が同一 chain で併用可
    assert style_fix_with_hakubun("進むことなく夷狄にゆく。欺すことなきなり。",
                                  "進莫夷狄之勿") == \
        "進むこと莫く夷狄に之く。欺すこと勿かれ。"
    # S 適用後の got に なきなり が残らない（guard 内）
    assert "なきなり" not in style_fix_with_hakubun("欺すことなきなり。", "勿欺")
    # R も併用可（Rule R ゆく→之く との共存）
    assert style_fix_with_hakubun("走りて燕にゆく。欺すことなきなり。", "走燕之勿") == \
        "走りて燕に之く。欺すこと勿かれ。"


def test_rule_s_idempotent_and_modern():
    for text, hb in (("欺すことなきなり。", "勿欺也"),
                     ("必ず亟なりて之に去く、近きことなきなり。", "必亟去之近勿"),
                     ("引きて之に去くは従うことなきなり。", "引去之従勿")):
        once = style_kana_to_kanji_s(text, hb)
        assert style_kana_to_kanji_s(once, hb) == once
    # 無 kana 现代句一字不动
    assert style_kana_to_kanji_s("本日の会議は十時から開始されます。", "") == \
        "本日の会議は十時から開始されます。"
    # N84 echo 行型（純漢文尾段＝白文直出対象・kana なしで S も非発火）
    assert style_kana_to_kanji_s("器械を習い用う", "勿不習用器械") == "器械を習い用う"
