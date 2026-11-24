# -*- coding: utf-8 -*-
"""test_night89_lexicon_freq2.py — N89 词库频次 2 区扩充（1301 → 1531）的回归测试。

- 本体 GLOSSARY_LEXICON 仍 500 条（N75/N77 不变式维持——extra2 不 extend 本体）；
- extra2 = N79 324 + N80 261 + N82 216 + N89 230 = 1031 条（总 1531）：格式断言、
  与本体零重复、组内零重复；
- N89 追加条目每条都有 weblio 辞書＋语料两条证据（直接断言
  eval/night89_decisions_*.json 底稿，全量校验而非抽查）；
- 排除清单 270 条全量不在 extra2 词形集合中＋代表条目不在源文件中（引用形检查）；
- N89 追加代表条目在库且读法正确（含双读法・五组全・proper/verb/modifier/function）；
- find_in_lexicon2 对真实语料行命中 N89 新词；
- llm.glossary 离线路径命中 N89 新词；
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

N_N79 = 324
N_N80 = 261
N_N82 = 216
N_N89 = 230
N_EXTRA = N_N79 + N_N80 + N_N82 + N_N89  # 1031
N_TOTAL = 500 + N_EXTRA  # 1531

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXTRA2_PATH = os.path.join(ROOT, "backend", "glossary_lexicon_extra2.py")


def _by_word_extra(word):
    return [e for e in LEXICON_EXTRA2 if e.get("word") == word]


def test_base_lexicon_unchanged_500():
    assert len(GLOSSARY_LEXICON) == 500


def test_extra2_size_and_total():
    assert len(LEXICON_EXTRA2) == N_EXTRA == 1031
    assert N_TOTAL == 1531


def test_source_string_mentions_all_waves():
    assert "N79" in LEXICON_EXTRA2_SOURCE
    assert "N80" in LEXICON_EXTRA2_SOURCE
    assert "N82" in LEXICON_EXTRA2_SOURCE
    assert "N89" in LEXICON_EXTRA2_SOURCE


def test_n89_representative_entries_with_readings():
    pairs = (("一体", "いったい"), ("丈人", "じょうじん"),
             ("上客", "じょうかく・じょうきゃく"), ("一月", "いちげつ・いちがつ"),
             ("万金", "ばんきん・まんきん"), ("上疏", "じょうそ"),
             ("不敏", "ふびん"), ("中州", "ちゅうしゅう"), ("仁賢", "じんけん"),
             ("他人", "たにん"), ("以下", "いか"), ("以来", "いらい"),
             ("会稽", "かいけい"), ("侍食", "じしょく"), ("壮麗", "そうれい"),
             ("天理", "てんり"), ("太平", "たいへい"), ("太守", "たいしゅ"),
             ("夫人", "ふじん"), ("孤月", "こげつ"), ("学校", "がっこう"),
             ("孫子", "そんし"), ("宰予", "さいよ"), ("寒山", "かんざん"),
             ("寒食", "かんしょく"), ("小学", "しょうがく"),
             ("少者", "しょうしゃ"), ("屋下", "おくか"),
             ("単于", "ぜんう"), ("匈奴", "きょうど"), ("刎頸", "ふんけい"),
             ("娟娟", "けんけん"), ("啾啾", "しゅうしゅう"), ("堂堂", "どうどう"))
    for w, r in pairs:
        e = _by_word_extra(w)
        assert len(e) == 1 and e[0]["reading"] == r, "%s 应在库且读法 %s（得 %r）" % (w, r, e)


def test_n89_dual_evidence_gate_full():
    """全量（非抽查）：N89 追加条目在 N89 判定底稿里 verdict=include 且双证据非空，
    且 N89 底稿的 include 条目全部在库。"""
    decs = {}
    n89_included = set()
    for path in sorted(glob.glob(os.path.join(ROOT, "eval", "night89_decisions_*.json"))):
        for d in json.load(open(path, encoding="utf-8"))["decisions"]:
            decs[d["word"]] = d
            if d.get("verdict") == "include":
                n89_included.add(d["word"])
    missing = []
    n89_hits = 0
    for e in LEXICON_EXTRA2:
        d = decs.get(e["word"])
        if d is None:
            continue  # N79/N80/N82 条目（各自底稿由 test_night79/80/82 全量断言覆盖）
        n89_hits += 1
        if d.get("verdict") != "include":
            missing.append((e["word"], "verdict=%r" % d.get("verdict")))
        elif not str(d.get("dict_evidence", "")).strip() or not str(d.get("corpus_evidence", "")).strip():
            missing.append((e["word"], "evidence missing"))
    assert n89_hits == N_N89, "N89 追加条目 %d 条应全部出现在 N89 判定底稿" % N_N89
    assert not missing, "N89 双证据门未通过 %d 条: %s" % (len(missing), missing[:8])
    in_lex = {e["word"] for e in LEXICON_EXTRA2}
    not_in = sorted(n89_included - in_lex)
    assert not not_in, "N89 底稿 include 条目未入库: %s" % not_in[:8]


def test_n89_excluded_not_in_lexicon_and_file():
    """排除清单 270 条全量不在 extra2 词形集合；代表条目引用形不在源文件。"""
    exc = json.load(open(os.path.join(ROOT, "eval", "night89_excluded.json"),
                         encoding="utf-8"))["excluded"]
    in_lex = {e["word"] for e in LEXICON_EXTRA2}
    bad = [x["word"] for x in exc if x["word"] in in_lex]
    assert not bad, "排除条目在库: %s" % bad[:8]
    assert len(exc) == 270, "排除清单应 270 条（得 %d）" % len(exc)
    src = open(_EXTRA2_PATH, encoding="utf-8").read()
    for w in ("一乗", "三宮", "三山", "予譲", "人望", "人言", "十手", "十一",
              "万徹", "中略", "分限", "単車", "周文", "国富", "大黄", "大方",
              "大風", "太清", "宣王", "小白", "少陵", "居延", "天牢", "天陣",
              "娥娥", "媯汭", "孔氏", "兵教", "五車", "六寸"):
        assert '"%s"' % w not in src, "排除条目 %r 不应出现在 extra2 源文件" % w


def test_n89_find_in_lexicon2_hits_real_corpus_lines():
    hits = find_in_lexicon2("亭亭たる孤月行舟を照らし", max_hits=5)
    assert "孤月" in [h["word"] for h in hits], "詩语料行应命中 孤月"
    hits = find_in_lexicon2("孝悌の至りは、神明に通じ、四海に光ち", max_hits=5)
    assert "孝悌" in [h["word"] for h in hits], "論語语料行应命中 孝悌"
    hits = find_in_lexicon2("塵埃に見えず咸陽橋", max_hits=5)
    assert "塵埃" in [h["word"] for h in hits], "漢詩语料行应命中 塵埃"
    hits = find_in_lexicon2("宰予、昼寝ぬ。朽木は雕る可からず", max_hits=5)
    assert "宰予" in [h["word"] for h in hits], "論語语料行应命中 宰予"
    hits = find_in_lexicon2("今天下は太平なり。汝曹能く両石の弓を挽くも", max_hits=5)
    assert "太平" in [h["word"] for h in hits], "语料行应命中 太平"


def test_n89_llm_glossary_offline_uses_extra2():
    from backend.llm import glossary
    hits = glossary("宰予、昼寝ぬ。朽木は雕る可からず", "宰予、昼寝ぬ。朽木は雕る可からず")
    assert "宰予" in [h["word"] for h in hits], "llm.glossary 离线路径应命中 N89 新词 宰予"


def test_n89_kundoku_endpoint_unchanged():
    """词库不进规则引擎——经典句 kakikudashi 与 test_api 断言逐字一致。"""
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
        assert r.status_code == 200
        assert r.json()["kakikudashi"].strip() == "王は左右を顧みて而して他を言う"
