# -*- coding: utf-8 -*-
"""test_night82_lexicon_expand3.py — N82 词库再扩充第三波（1085 → 1301）的回归测试。

- 本体 GLOSSARY_LEXICON 仍 500 条（N75/N77 不变式维持——extra2 不 extend 本体）；
- extra2 = N79 324 + N80 261 + N82 216 = 801 条（总 1301）：格式断言、与本体零重复、
  组内零重复；
- N82 追加条目每条都有 weblio 辞書＋语料两条证据（直接断言
  eval/night82_decisions_*.json 底稿，全量校验而非抽查）；
- 排除清单全部条目不在 extra2 词形集合中（250 条全量）＋代表条目不在源文件中
  （引用形检查）；
- N82 追加代表条目在库且读法正确（各 batch 抽代表，含双读法）；
- find_in_lexicon2 对真实语料行命中 N82 新词；
- llm.glossary 离线路径命中 N82 新词；
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
N_N82 = 216
N_N89 = 230
N_EXTRA = N_N79 + N_N80 + N_N82 + N_N89  # 1031
N_TOTAL = N_BASE + N_EXTRA  # 1531

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXTRA2_PATH = os.path.join(ROOT, "backend", "glossary_lexicon_extra2.py")


def _by_word_extra(word):
    return [e for e in LEXICON_EXTRA2 if e.get("word") == word]


def test_base_lexicon_unchanged_500():
    assert len(GLOSSARY_LEXICON) == N_BASE


def test_extra2_size_and_total():
    assert len(LEXICON_EXTRA2) == N_EXTRA == 1031
    assert N_TOTAL == 1531


def test_source_string_mentions_all_waves():
    assert "N79" in LEXICON_EXTRA2_SOURCE
    assert "N80" in LEXICON_EXTRA2_SOURCE
    assert "N82" in LEXICON_EXTRA2_SOURCE


def test_n82_representative_entries_with_readings():
    pairs = ((("寒暑", "かんしょ"), ("将帥", "しょうすい"), ("尋常", "じんじょう"),
             ("尚書", "しょうしょ"), ("布衣", "ふい・ぬのきぬ"),
             ("山上", "さんじょう・やまのうえ"), ("平旦", "へいたん"),
             ("廟算", "びょうさん"), ("廷尉", "ていい"), ("張良", "ちょうりょう"),
             ("従来", "じゅうらい"), ("徳行", "とっこう・とくぎょう"),
             ("愚者", "ぐしゃ"), ("愛子", "あいし・まなご"), ("扶桑", "ふそう"),
             ("敵国", "てきこく・てっこく"), ("既往", "きおう"), ("日中", "にっちゅう"),
             ("日長", "ひなが・にっちょう"), ("星辰", "せいしん"), ("李白", "りはく"),
             ("梁園", "りょうえん"), ("楼蘭", "ろうらん"), ("歳寒", "さいかん"),
             ("比干", "ひかん"), ("毫末", "ごうまつ"),
             ("海上", "かいじょう・うなかみ"), ("涼州", "りょうしゅう"),
             ("滄浪", "そうろう"), ("穆穆", "ぼくぼく"), ("窮寇", "きゅうこう"),
             ("紅顔", "こうがん"), ("絶世", "ぜっせい"), ("軍容", "ぐんよう"),
             ("進止", "しんし"), ("郷原", "きょうげん"), ("闌干", "らんかん"),
             ("陽関", "ようかん"), ("離宮", "りきゅう"), ("雲梯", "うんてい"),
             ("顚沛", "てんぱい"), ("飄風", "ひょうふう"),
             ("藺相如", "りんしょうじょ"), ("諸葛亮", "しょかつりょう"),
             ("閔子騫", "びんしけん"), ("鬱金香", "うこんこう・うっこんこう"),
             ("善哉", "ぜんざい"), ("好學", "こうがく"), ("屈原", "くつげん"),
             ("約束", "やくそく"), ("三千里", "さんぜんり")))
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


def test_n82_dual_evidence_gate_full():
    """全量（非抽查）：N82 追加条目在 N82 判定底稿里 verdict=include 且双证据非空，
    且 N82 底稿的 include 条目全部在库。"""
    decs = {}
    n82_included = set()
    for path in sorted(glob.glob(os.path.join(ROOT, "eval", "night82_decisions_*.json"))):
        for d in json.load(open(path, encoding="utf-8"))["decisions"]:
            decs[d["word"]] = d
            if d.get("verdict") == "include":
                n82_included.add(d["word"])
    missing = []
    n82_hits = 0
    for e in LEXICON_EXTRA2:
        d = decs.get(e["word"])
        if d is None:
            continue  # N79/N80 条目（各自底稿由 test_night79/80 全量断言覆盖）
        n82_hits += 1
        if d.get("verdict") != "include":
            missing.append((e["word"], "verdict=%r" % d.get("verdict")))
        elif not str(d.get("dict_evidence", "")).strip() or not str(d.get("corpus_evidence", "")).strip():
            missing.append((e["word"], "evidence missing"))
    assert n82_hits == N_N82, "N82 追加条目 %d 条应全部出现在 N82 判定底稿" % N_N82
    assert not missing, "N82 双证据门未通过 %d 条: %s" % (len(missing), missing[:8])
    in_lex = {e["word"] for e in LEXICON_EXTRA2}
    not_in = sorted(n82_included - in_lex)
    assert not not_in, "N82 底稿 include 条目未入库: %s" % not_in[:8]


def test_n82_excluded_not_in_lexicon_and_file():
    """排除清单 250 条全量不在 extra2 词形集合；代表条目引用形不在源文件。"""
    exc = json.load(open(os.path.join(ROOT, "eval", "night82_excluded.json"),
                         encoding="utf-8"))["excluded"]
    in_lex = {e["word"] for e in LEXICON_EXTRA2}
    bad = [x["word"] for x in exc if x["word"] in in_lex]
    assert not bad, "排除条目在库: %s" % bad[:8]
    assert len(exc) == 250, "排除清单应 250 条（得 %d）" % len(exc)
    src = open(_EXTRA2_PATH, encoding="utf-8").read()
    for w in ("尾生", "帝郷", "征人", "平台", "建徳", "水光", "飄飄", "曹公",
              "斉王", "趙王", "終南", "李将軍", "夏后氏", "公子糾", "良弓蔵",
              "散地", "扶胥", "武城", "新豊", "彭沢"):
        assert '"%s"' % w not in src, "排除条目 %r 不应出现在 extra2 源文件" % w


def test_n82_find_in_lexicon2_hits_real_corpus_lines():
    hits = find_in_lexicon2("子曰く、歳寒くして、然る後に松柏の彫むに後るるを知るなり", max_hits=5)
    assert "歳寒" in [h["word"] for h in hits], "rongo 语料行应命中 歳寒"
    hits = find_in_lexicon2("子曰く、有司を先にし、小過を赦し、賢才を挙げよ", max_hits=5)
    assert "小過" in [h["word"] for h in hits], "rongo 语料行应命中 小過"
    hits = find_in_lexicon2("平明客を送れば楚山孤なり", max_hits=5)
    assert "平明" in [h["word"] for h in hits], "toushisen 语料行应命中 平明"
    hits = find_in_lexicon2("胡馬は北風に依り、越鳥は南枝に巣くう", max_hits=5)
    assert "胡馬" in [h["word"] for h in hits], "gushi 语料行应命中 胡馬"
    hits = find_in_lexicon2("王荊公の石榴の詩に、万緑叢中紅一点、人を動かす春色多きを須いず", max_hits=6)
    assert "石榴" in [h["word"] for h in hits], "setten 语料行应命中 石榴"
    hits = find_in_lexicon2("微子は之を去り、箕子は之が奴と為り、比干は諫めて死す", max_hits=6)
    assert "比干" in [h["word"] for h in hits], "rongo 语料行应命中 比干"


def test_n82_llm_glossary_offline_uses_extra2():
    from backend.llm import glossary
    hits = glossary("靖曰く、諸葛亮、七たび孟獲を擒にせり", "靖曰く、諸葛亮、七たび孟獲を擒にせり")
    assert "諸葛亮" in [h["word"] for h in hits], "llm.glossary 离线路径应命中 N82 新词 諸葛亮"


def test_n82_kundoku_endpoint_unchanged():
    """词库不进规则引擎——经典句 kakikudashi 与 test_api 断言逐字一致。"""
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
        assert r.status_code == 200
        assert r.json()["kakikudashi"].strip() == "王は左右を顧みて而して他を言う"
