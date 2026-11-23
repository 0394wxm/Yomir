# -*- coding: utf-8 -*-
"""test_night77_lexicon_fix16.py — N77 词库 16 条（N76 存疑定案）修复的回归测试。

- 16 条照 eval/night76_suspect43.md §3.2 / .json 底稿修 reading/meaning/词头，
  逐条断言修后值（读法 10 + 释义 6）；
- 词头改动 2 条（冀ふ→冀う、貳す→弐びす）另断言旧词头已不存在＋find_in_lexicon 行为；
- 抽查 10 条 N76 確認OK 条目未动；
- 词库总数仍 500（README 数字不动）。
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


# ---- 读法 10 条：断言修后值 ----

def test_mokisu_reading_fixed():
    e = _one("牧す")
    assert e["reading"] == "ぼくす"
    assert e["meaning"] == "飼う・牧す（牛馬を）。"  # meaning 不动（任务书只改读法）


def test_sonan_reading_fixed():
    assert _one("狙")["reading"] == "そ"


def test_kitau_headword_and_reading_fixed():
    assert _by_word("冀ふ") == []  # 旧词头已不存在
    e = _one("冀う")
    assert e["reading"] == "こいねが"
    assert e["meaning"] == "望む。期待する。"  # meaning 不动


def test_ikkenhoukei_reading_fixed():
    assert _one("一犬吠形")["reading"] == "いっけん・ほ・かたち"


def test_nibisu_headword_and_reading_fixed():
    assert _by_word("貳す") == []  # 旧词头（简体字形）已不存在
    e = _one("弐びす")
    assert e["reading"] == "ふたたびす"
    assert e["meaning"] == "ふたごする・重ねて過ちを犯す（「過ちを弐びせず」）。"  # meaning 不动


def test_izure_reading_and_meaning_fixed():
    e = _one("孰")
    assert e["reading"] == "いずれ・たれ"
    assert e["meaning"] == ("どれ・どちら（比較・選択の疑問）。「孰れか」＝どちらが。"
                            "また「孰か」＝誰が（反語）。")


def test_nanzo_added():
    assert _one("奚")["reading"] == "なに・いずれ・なんぞ"


def test_masareru_reading_fixed():
    assert _one("愈れる")["reading"] == "まされる"


def test_ushina_shitsu_reading_fixed():
    e = _one("失")
    assert e["reading"] == "うしな・しっ"
    assert e["meaning"] == "失ふ。うしなう。"  # 现状维持（底稿：meaning は現状のまま可）


def test_ya_todo_reading_fixed():
    e = _one("止")
    assert e["reading"] == "や・とど"
    assert e["meaning"] == "止む。とどまる。"  # 现状维持


# ---- 释义 6 条：断言修后值 ----

def test_sunawachi_meaning_fixed():
    e = _one("乃ち")
    assert e["reading"] == "すなわち"  # 不动
    assert e["meaning"] == "すなわち。あるいは「そこで」。"
    assert "そのまま" not in e["meaning"]


def test_katsu_meaning_fixed():
    e = _one("且つ")
    assert e["reading"] == "かつ"  # 不动
    assert e["meaning"] == "そのうえ。同時に。"
    assert "おもむろに" not in e["meaning"]


def test_ooini_meaning_fixed():
    e = _one("大いに")
    assert e["reading"] == "おおいに"  # 不动
    assert e["meaning"] == "はなはだ。"
    assert "大きく" not in e["meaning"]


def test_icchoisseki_meaning_fixed():
    e = _one("一朝一夕")
    assert e["reading"] == "いっちょういっせき"  # 不动
    assert e["meaning"] == "一夜両日ではない＝短期ではできない（易・坤文言）。"
    assert "两" not in e["meaning"]  # 简体清除


def test_suushokusu_meaning_fixed():
    e = _one("崇飾す")
    assert e["reading"] == "すうしょくす"  # 不动
    assert e["meaning"] == "崇め飾りたてる（「武帝仏寺を崇飾する」）。"
    assert "堂々と" not in e["meaning"]


def test_toshi_meaning_fixed():
    e = _one("利し")
    assert e["reading"] == "とし"  # 读法不动
    assert e["meaning"] == "鋭い（「矛の利」＝矛の鋭さ）。"
    assert "有利" not in e["meaning"]


# ---- 词头改动的 find_in_lexicon 行为 ----

def test_kitau_find_in_lexicon():
    # 语料 shushu-3「復た兎を得んと冀う」——词头改动后新词形可命中
    hits = find_in_lexicon("復た兎を得んと冀う", max_hits=5)
    assert any(h["word"] == "冀う" and h["reading"] == "こいねが" for h in hits), \
        "冀う（新词头）应能命中"


def test_nibisu_exact_match_limitation():
    # 语料实际形是「弐びせず」（ayamachifu-1/ikariutsu-1），终止形「弐びす」
    # 不在语料文本中出现——find_in_lexicon 精确子串匹配命中 0 属既有局限
    # （N75 収拾す 案同型），与本夜修复无关。0 命中也如实记：
    # eval/night77_headword_hits.json / REPORT_NIGHT77.md。
    hits = find_in_lexicon("怒りを遷さず、過ちを弐びせず", max_hits=5)
    assert not any(h["word"] == "貳す" for h in hits), "旧词头貳す 不应再命中"
    assert not any(h["word"] == "弐びす" for h in hits), \
        "终止形弐びす 与语料活用形弐びせず 不精确匹配（既有局限，如实记录）"


# ---- 抽查 10 条 N76 確認OK 条目未动 ----

def test_spot_check_untouched():
    expect = {
        "所謂達": "いわゆるたつ",
        "釈て": "すて",
        "夏虫": "かちゅう",
        "噫": "ああ",
        "凶なる": "きょうなる",
        "過": "す",
        "布": "し",
        "樹": "う",
        "直": "なお",
        "而": "て",
    }
    for w, r in expect.items():
        e = _one(w)
        assert e["reading"] == r, "%s reading 不应变动（N76 確認OK）" % w


# ---- 词库总数 ----

def test_lexicon_size_unchanged():
    assert len(GLOSSARY_LEXICON) == 500
