# -*- coding: utf-8 -*-
"""test_night64_rule_i.py — N64: Rule I（假名→汉字 第五批）与 SHINJITAI 99 对的锁定测试。

方法论同 N55 test（rule G）/N58：护栏转换 / 无护栏跳过 / 长词跳过 / 分工链序 /
幂等 / 正字化抽查与冲突性质 / 语料外现代和文探针。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    I_KANA_TO_KANJI, I_LONGER_WORDS, SHINJITAI_MAP,
    style_kana_to_kanji_i, style_fix_with_hakubun, normalize_shinjitai,
    style_kana_to_kanji_h, style_kana_to_kanji,
)


# ---------- Rule I 各条：护栏命中转换 ----------
def test_rule_i_kedashi_gai():
    assert style_kana_to_kanji_i("けだし人を知ること難し", "蓋し人を知ること難し") == \
        "蓋し人を知ること難し"


def test_rule_i_izukunzo_enkunzo():
    assert style_kana_to_kanji_i("いずくんぞ佞を用す", "焉佞を用す") == "焉くんぞ佞を用す"


def test_rule_i_moshi_gotoshi():
    assert style_kana_to_kanji_i("もし情を得る", "如し情を得る") == "如し情を得る"


def test_rule_i_sore_ware():
    # Rule I 只动 それ→夫れ（ひ→い 是活用改写，不在本规则范围）
    assert style_kana_to_kanji_i("それ石を負ひて", "夫れ石を負いて") == "夫れ石を負ひて"


def test_rule_i_tada_yui():
    assert style_kana_to_kanji_i("ただ疾者は之を甘しとす", "惟だ疾者のみ之を甘しとす") == \
        "惟だ疾者は之を甘しとす"


def test_rule_i_nakare_moka():
    assert style_kana_to_kanji_i("友とするなかれ", "友とする毋かれ") == "友とする毋かれ"


# ---------- 护栏：白文无对应汉字 → 一字不动 ----------
def test_rule_i_skips_without_guard():
    pairs = {k: r for k, r, g in I_KANA_TO_KANJI}
    hb_no_guard = "白文に守り字無し"   # 蓋/焉/如/夫/惟/毋 どれも含まない
    for kana, repl, _guard in I_KANA_TO_KANJI:
        text = "prefix" + kana + "suffix"
        assert style_kana_to_kanji_i(text, hb_no_guard) == text, kana
        assert repl not in style_kana_to_kanji_i(text, hb_no_guard)


# ---------- 词界护栏：更长词命中不替换 ----------
def test_rule_i_longer_words_protected():
    # もしも/もしか/もしや
    assert style_kana_to_kanji_i("もしも雨なら", "如しも雨なら") == "もしも雨なら"
    assert style_kana_to_kanji_i("もしかすると", "如しかすると") == "もしかすると"
    # それぞ/それで（H/E と共有の長語リスト）
    assert style_kana_to_kanji_i("それぞ人と謂う", "夫れぞ人と謂う") == "それぞ人と謂う"
    assert style_kana_to_kanji_i("それでよい", "夫れでよい") == "それでよい"
    # ただす/ただし/ただいま（E と共有）
    assert style_kana_to_kanji_i("真をただす", "唯だす") == "真をただす"
    assert style_kana_to_kanji_i("ただし書き", "唯だし書き") == "ただし書き"
    # なかれ は長語条目なし：ことなかれ は「なかれ」の后缀重叠で tail.startswith が
    # 届かない（死条目になる）→ 実測挙動=一律変換。模擬 10 行全部改善・0 变差。
    assert style_kana_to_kanji_i("封することなかれ", "封すること毋かれ") == "封すること毋かれ"


# ---------- 分工链序：E/H と I の白文分工 ----------
def test_rule_i_chain_division_tada_tada():
    # 白文含 唯 → E が 唯だ；白文含 惟（唯を含まない）→ I が 惟だ
    assert style_kana_to_kanji("ただ民は止す所", "唯れ民の止まる所") == "唯だ民は止す所"
    assert style_fix_with_hakubun("ただ民は止す所", "惟れ民の止まる所") == "惟だ民は止す所"


def test_rule_i_chain_division_sore():
    # 白文含 只 → H が 只だ；白文含 夫（只を含まない）→ I が 夫れ
    assert style_kana_to_kanji_h("それ古の道", "只だ古の道") == "只だ古の道"
    assert style_fix_with_hakubun("それ古の道", "夫れ古の道") == "夫れ古の道"


# ---------- 幂等 ----------
def test_rule_i_chain_idempotent():
    hb = "蓋焉如夫惟毋"
    text = "けだしいずくんぞもし、それだっただなかれ。"
    once = style_fix_with_hakubun(text, hb)
    twice = style_fix_with_hakubun(once, hb)
    assert once == twice


def test_rule_i_empty_hakubun_unguarded():
    # hakubun 空 = 护栏不适用（离线脚本沿用 E 以来の「無白文=纯函数」语义）
    assert style_kana_to_kanji_i("けだし", "") == "蓋し"


# ---------- SHINJITAI 99 对 ----------
def test_shinjitai_n64_spot_checks():
    assert normalize_shinjitai("聽觀沒卽髮") == "聴観没即髪"
    assert normalize_shinjitai("辯辨辦") == "弁弁弁"
    assert normalize_shinjitai("舍愼爭搖擧藏拂繼羣祿寢") == "舎慎争揺挙蔵払継群禄寝"
    assert normalize_shinjitai("囘卷靜勸溪鷄盜獵戲儉雜壯") == "回巻静勧渓鶏盗猟戯倹雑壮"
    assert normalize_shinjitai("總徑峯悅壽竝巖驅淚晝收豫爐") == "総径峰悦寿並巌駆涙昼収予炉"
    assert normalize_shinjitai("彈緣墮淺兔賴效淸假攝鎭薰") == "弾縁堕浅兎頼効清仮摂鎮薫"
    assert normalize_shinjitai("險壤絕劒攜增彥黑潛寫壓艷拔尙") == "険壌絶剣携増彦黒潜写圧艶抜尚"
    assert normalize_shinjitai("齡據碎嶽搜僞卻聰壞禪戶巢") == "齢拠砕岳捜偽却聡壊禅戸巣"
    assert normalize_shinjitai("齋覽貳驗螢絲鬪麥窻單每奧") == "斎覧弐験蛍糸闘麦窓単毎奥"
    assert normalize_shinjitai("戀歷曆荆濕") == "恋歴暦荊湿"


def test_shinjitai_n64_idempotent():
    s = "".join(SHINJITAI_MAP)
    once = normalize_shinjitai(s)
    assert normalize_shinjitai(once) == once, "新字体映射必须幂等"


def test_shinjitai_n64_no_key_target_conflict():
    targets = set(SHINJITAI_MAP.values())
    conflicts = [k for k in SHINJITAI_MAP if k in targets]
    assert not conflicts, "某映射目标同时是另一映射的旧形键：%s" % conflicts


# ---------- 语料外探针（现代和文・規範外の文は触らない）----------
def test_rule_i_probe_modern_japanese():
    probes = [
        ("それいいじゃん", "君の言う通り"),
        ("ただいま戻りました", "今帰宅"),
        ("もしもし", "電話"),
        ("ことなかれ主義", "莫れ主義とは言わない"),
        ("けだもの", "畜生"),
    ]
    for text, hb in probes:
        out = style_fix_with_hakubun(text, hb)
        assert out == text, "%s -> %s" % (text, out)


# ---------- 经典句不回归（Night7/22 约定，Rule I 不应有影响）----------
def test_rule_i_classic_sentence_intact():
    t = style_fix_with_hakubun("顧みて而して他を言う", "王顧左右而言他")
    assert "而して" in t, "经典句 而して 必须保留"


def test_rule_i_table_wellformed():
    assert len(I_KANA_TO_KANJI) == 6
    for kana, repl, guard in I_KANA_TO_KANJI:
        assert all(isinstance(g, str) and g for g in guard)
        assert repl not in kana
    # なかれ は意図的に長語条目を持たない（后缀重叠は前缀护栏が届かない=死条目）
    assert "なかれ" not in I_LONGER_WORDS
    for kana in ("けだし", "いずくんぞ", "もし", "それ", "ただ"):
        assert kana in I_LONGER_WORDS
