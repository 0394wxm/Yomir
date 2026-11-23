# -*- coding: utf-8 -*-
"""test_night80_lexicon_expand2.py — N80 词库再扩充（824 → 1085）的回归测试。

- 本体 GLOSSARY_LEXICON 仍 500 条（N75/N77 不变式维持——extra2 不 extend 本体）；
- extra2 = N79 324 条 + N80 追加 261 条 = 585 条：格式断言（word/reading/meaning
  非空、kind 合法、≥2 字）、与本体零重复、组内零重复；
- N80 追加条目每条都有 weblio 辞書＋语料两条证据（直接断言
  eval/night80_decisions_*.json 底稿，全量校验而非抽查）；
- 排除清单代表条目不在 extra2 源文件中（引用形检查）；
- N80 追加代表条目在库且读法正确（batch5-9 各抽代表）；
- find_in_lexicon2 对真实语料行命中 N80 新词；
- llm.glossary 离线路径命中 N80 新词；
- /api/kundoku 规则引擎零变化（词库不进规则引擎，经典句输出逐字不变）。
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402
from backend.glossary_lexicon_extra2 import (  # noqa: E402
    LEXICON_EXTRA2, LEXICON_EXTRA2_SOURCE, find_in_lexicon2)

N_BASE = 500
N_N79 = 324
N_N80 = 261
N_EXTRA = N_N79 + N_N80  # 585
N_TOTAL = N_BASE + N_EXTRA  # 1085

_EXTRA2_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "backend", "glossary_lexicon_extra2.py")


def _by_word_extra(word):
    return [e for e in LEXICON_EXTRA2 if e.get("word") == word]


def test_base_lexicon_unchanged_500():
    assert len(GLOSSARY_LEXICON) == N_BASE


def test_extra2_size_and_total():
    assert len(LEXICON_EXTRA2) == N_EXTRA == 585
    assert N_TOTAL == 1085


def test_source_string_mentions_both_waves():
    assert "N79" in LEXICON_EXTRA2_SOURCE
    assert "N80" in LEXICON_EXTRA2_SOURCE


def test_n80_representative_entries_with_readings():
    pairs = (("孟嘗君", "もうしょうくん"), ("柳下恵", "りゅうかけい"),
             ("信賞必罰", "しんしょうひつばつ"), ("渾渾沌沌", "こんこんとんとん"),
             ("一夜", "いちや"), ("一行", "いちぎょう・いっこう"),
             ("万乗", "ばんじょう"), ("八陣", "はちじん"), ("冉冉", "ぜんぜん"),
             ("只今", "ただいま"), ("即今", "そっこん"), ("守成", "しゅせい"),
             ("太山", "たいざん"), ("孫呉", "そんご"), ("孔丘", "こうきゅう"),
             ("客心", "かくしん・きゃくしん"), ("吾子", "あこ"), ("夷狄", "いてき"))
    for w, r in pairs:
        e = _by_word_extra(w)
        assert len(e) == 1 and e[0]["reading"] == r, "%s 应在库且读法 %s（得 %r）" % (w, r, e)


def test_extra2_format():
    for e in LEXICON_EXTRA2:
        w, r, m = e.get("word"), e.get("reading"), e.get("meaning")
        assert isinstance(w, str) and len(w) >= 2, "word 必须 ≥2 字: %r" % e
        assert isinstance(r, str) and r.strip(), "reading 空: %r" % e
        assert isinstance(m, str) and m.strip(), "meaning 空: %r" % e
        assert e.get("kind") in ("content", "function"), "kind 不合法: %r" % e


def test_no_duplicates_and_no_overlap_with_base():
    base_words = [e["word"] for e in GLOSSARY_LEXICON]
    extra_words = [e["word"] for e in LEXICON_EXTRA2]
    assert len(extra_words) == len(set(extra_words)), "extra2 内部重复词形"
    overlap = set(base_words) & set(extra_words)
    assert not overlap, "extra2 与本体 500 重复: %s" % sorted(overlap)[:5]


def test_n80_dual_evidence_gate_full():
    """全量（非抽查）：N80 追加条目在 N80 判定底稿里 verdict=include 且双证据非空。"""
    decs = {}
    for path in sorted(glob.glob(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "eval", "night80_decisions_*.json"))):
        for d in json.load(open(path, encoding="utf-8"))["decisions"]:
            decs[d["word"]] = d
    missing = []
    n80_hits = 0
    for e in LEXICON_EXTRA2:
        d = decs.get(e["word"])
        if d is None:
            continue  # N79 条目（night79 底稿由 test_night79 全量断言覆盖）
        n80_hits += 1
        if d.get("verdict") != "include":
            missing.append((e["word"], "verdict=%r" % d.get("verdict")))
        elif not str(d.get("dict_evidence", "")).strip() or not str(d.get("corpus_evidence", "")).strip():
            missing.append((e["word"], "evidence missing"))
    assert n80_hits == N_N80, "N80 追加条目 %d 条应全部出现在 N80 判定底稿" % N_N80
    assert not missing, "N80 双证据门未通过 %d 条: %s" % (len(missing), missing[:8])


def test_n80_excluded_representatives_not_in_file():
    src = open(_EXTRA2_PATH, encoding="utf-8").read()
    for w in ("顔淵曰", "一匡", "三有", "万重", "天井", "子有", "右軍", "太廟",
              "宰我", "大象", "人知", "力足", "季康子", "四海困窮",
              "孟母曰", "管仲曰", "不教而殺", "冠者五六人", "令尹", "元王"):
        assert '"%s"' % w not in src, "排除条目 %r 不应出现在 extra2 源文件" % w


def test_n80_find_in_lexicon2_hits_real_corpus_lines():
    hits = find_in_lexicon2("万乗の主にして、身を以て天下より軽しとせんや", max_hits=5)
    assert "万乗" in [h["word"] for h in hits], "taisya-gyo 语料行应命中 万乗"
    hits = find_in_lexicon2("暴虎馮河し、死して悔ゆる無き者は、吾与にせざるなり", max_hits=5)
    assert "暴虎馮河" in [h["word"] for h in hits], "rongo 语料行应命中 暴虎馮河"
    hits = find_in_lexicon2("文質彬彬として、然る後に君子なり", max_hits=5)
    assert "文質彬彬" in [h["word"] for h in hits]
    hits = find_in_lexicon2("太宗、侍臣に謂いて曰く、帝王の業、草創と守成と", max_hits=6)
    words = [h["word"] for h in hits]
    assert "太宗" in words and "守成" in words, "teizong 语料行应命中 太宗・守成: %s" % words


def test_n80_llm_glossary_offline_uses_extra2():
    from backend.llm import glossary
    hits = glossary("万乗の主にして身を以て天下より軽しとせんや", "万乗の主にして身を以て天下より軽しとせんや")
    assert "万乗" in [h["word"] for h in hits], "llm.glossary 离线路径应命中 N80 新词 万乗"


def test_n80_kundoku_endpoint_unchanged():
    """词库不进规则引擎——经典句 kakikudashi 与 test_api 断言逐字一致。"""
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
        assert r.status_code == 200
        assert r.json()["kakikudashi"].strip() == "王は左右を顧みて而して他を言う"