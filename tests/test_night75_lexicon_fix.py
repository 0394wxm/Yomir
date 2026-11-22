# -*- coding: utf-8 -*-
"""test_night75_lexicon_fix.py — N75 词库 19 条错项修复的回归测试。

- 17 条照 N74 审计证据修了 reading/meaning/词头，逐条断言修后值；
- 舎／玷く 两条经核验**不改**（语料振り仮名/词典证据见 REPORT_NIGHT75.md §2），
  断言其保持原值；
- Top-20 第 20 位「而」是存疑项，N75 不修 → 断言未动；
- 另抽查 10 条未动 + find_in_lexicon 死条目（異端／収拾す）复活。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.glossary_lexicon import GLOSSARY_LEXICON, find_in_lexicon  # noqa: E402


def _by_word(word):
    return [e for e in GLOSSARY_LEXICON if e.get("word") == word]


def _one(word):
    hits = _by_word(word)
    assert len(hits) == 1, "词条 %r 应恰有 1 条，实得 %d" % (word, len(hits))
    return hits[0]


# ---- 17 条已修条目：断言修后值 ----

def test_kuonya_reading_fixed():
    assert _one("況んや")["reading"] == "いわんや"


def test_tari_conjugation_fixed():
    m = _one("たり")["meaning"]
    assert "たら・たり・たる・たれ" in m
    assert "たろ" not in m and "・て・" not in m


def test_yahoho_fixed():
    e = _one("犹ほ")
    assert e["reading"] == "なおほ"
    assert "異体表記" in e["meaning"]


def test_sakuchite_reading_fixed():
    assert _one("策うちて")["reading"] == "むちうちて"


def test_kaiuu_reading_fixed():
    assert _one("闚う")["reading"] == "うかがう"


def test_aiiite_reading_fixed():
    assert _one("相謂いて")["reading"] == "あいいいて"


def test_hofuru_meaning_fixed():
    assert "ほしいまま" not in _one("屠る")["meaning"]
    assert "切り裂く" in _one("屠る")["meaning"]


def test_ikki_reading_fixed():
    assert _one("一簣")["reading"] == "いっき"


def test_itann_headword_fixed():
    assert _one("異端")["reading"] == "いたん"  # 词头「異端」存在本身即修复


def test_shuushisu_headword_fixed():
    assert _one("収拾す")["reading"] == "しゅうしゅうす"


def test_shikarite_meaning_fixed():
    m = _one("然りて")["meaning"]
    assert "supar 出力でよく見る接続形" in m
    assert "输出" not in m and "常见的" not in m  # 中文残留清除


def test_izureka_reading_fixed():
    assert _one("孰か学を好む")["reading"] == "いずれかがくをこのむ"


def test_kakusu_reading_fixed():
    assert _one("画す")["reading"] == "かくす"


def test_tsukau_reading_fixed():
    assert _one("事う")["reading"] == "つかう"


def test_shusha_reading_fixed():
    assert _one("守株")["reading"] == "しゅしゅ"


def test_shikou_reading_fixed():
    assert _one("子貢")["reading"] == "しこう"


def test_idedo_reading_fixed():
    assert _one("雖")["reading"] == "いえど"


# ---- 2 条核验后不改：断言保持原值 ----

def test_sha_kept():
    """舎：语料 golden_8165 自身用「舎つれば／舎てんや／舎きて」（すつ系），
    与词库 reading「す」一致（rongo0710-1 / rongo0604-1 / rongo1601-1）。不动。"""
    assert _one("舎")["reading"] == "す"
    assert "すてる" in _one("舎")["meaning"]


def test_den_kept():
    """玷く：词典训仅「かける」（Wiktionary/KANJIDIC），「かく」无在册证据。不动。"""
    assert _one("玷く")["reading"] == "おかす"


# ---- Top-20 第 20 位「而」（存疑）未动 ----

def test_niku_touched_not():
    e = _one("而")
    assert e["reading"] == "て"
    assert e["meaning"] == "接続「…して」。"


# ---- 抽查 10 条未动 ----

def test_spot_check_untouched():
    expect = {
        "孔子": ("こうし", "儒家の祖"),
        "君子": ("くんし", "徳の高い人"),
        "金": ("きん", "黄金・金属"),
        "天": ("てん", "天空・天帝"),
        "者": ("もの", "…する者"),
        "然": ("しか", "然り"),
        "曾子": ("そうし", "曾参"),
        "楚": ("そ", "戦国の国名"),
        "幸": ("さいわ", "さいわい"),
        "誠": ("まこと", "まこと"),
    }
    for w, (r, mpart) in expect.items():
        e = _one(w)
        assert e["reading"] == r, "%s reading 不应变动" % w
        assert mpart in e["meaning"], "%s meaning 不应变动" % w


# ---- 死条目复活 + 查词行为抽查 ----

def test_dead_entries_revived():
    # 異端：真实语料 3 行（itanosamu-1 / kyorankito-1 / daigaku00a-27）書き下し文
    # 都含「異端」→ 词头简体「异」修正后真正复活。
    hits = find_in_lexicon("異端を攻むるは、斯れ害あるのみ", max_hits=5)
    assert any(h["word"] == "異端" for h in hits), "異端 应能命中（N74 前词头简体＝死条目）"
    # 収拾す：语料 akujisenri-2 書き下し文只有連用形「収拾し」（白文为「收拾」），
    # 终止形「収拾す」在语料中不存在 → 用含终止形的文本验证词形本身已可命中；
    # 该语料行的命中与否属 find_in_lexicon 精确子串匹配的既有局限（残課題），
    # 与本夜修复无关，见 REPORT_NIGHT75.md §2。
    hits2 = find_in_lexicon("焚毀の書を収拾す", max_hits=5)
    assert any(h["word"] == "収拾す" for h in hits2), "収拾す 词形应可命中（终止形文本）"


def test_lookup_behavior_spot_check():
    hits = find_in_lexicon("馬に策うちて", max_hits=5)
    assert any(h["word"] == "策うちて" and h["reading"] == "むちうちて" for h in hits)
    hits2 = find_in_lexicon("況んやは言うまでもない", max_hits=5)
    assert any(h["word"] == "況んや" and h["reading"] == "いわんや" for h in hits2)


def test_lexicon_size_unchanged():
    assert len(GLOSSARY_LEXICON) == 500
