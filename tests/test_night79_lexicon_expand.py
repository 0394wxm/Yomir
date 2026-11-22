# -*- coding: utf-8 -*-
"""test_night79_lexicon_expand.py — N79 词库扩充（500 → 824）的回归测试。

- 本体 GLOSSARY_LEXICON 仍 500 条（N75/N77 不变式维持——extra2 不 extend 本体）；
- extra2 324 条：格式断言（word/reading/meaning 非空、kind 合法、≥2 字）、
  与本体零重复、组内零重复；
- 每条都有 weblio 辞書＋语料两条证据（直接断言 eval/night79_decisions_*.json 底稿，
  全量校验而非抽查）；
- 排除清单代表条目不在 extra2 源文件中（引用形 `"词"` 检查）；
- N76 §3.5 覆盖缺口 3 条（而る後／而ち／利す）在库且读法正确；
- find_in_lexicon2 对真实语料行命中新词；本体 find_in_lexicon 看不到 extra2 词
  （合并查找只在 llm 层）；
- llm.glossary 离线路径命中 extra2 新词；
- /api/kundoku 规则引擎零变化（词库不进规则引擎，经典句输出逐字不变）。
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.glossary_lexicon import GLOSSARY_LEXICON, find_in_lexicon  # noqa: E402
from backend.glossary_lexicon_extra2 import (  # noqa: E402
    LEXICON_EXTRA2, LEXICON_EXTRA2_SOURCE, find_in_lexicon2)

N_BASE = 500
N_EXTRA = 324

_EXTRA2_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "backend", "glossary_lexicon_extra2.py")


def _by_word_extra(word):
    return [e for e in LEXICON_EXTRA2 if e.get("word") == word]


def test_base_lexicon_unchanged_500():
    assert len(GLOSSARY_LEXICON) == N_BASE


def test_extra2_size_and_total():
    assert len(LEXICON_EXTRA2) == N_EXTRA
    assert N_BASE + N_EXTRA == 824


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


def test_source_string_present():
    assert "N79" in LEXICON_EXTRA2_SOURCE


def test_n76_gaps_present_with_readings():
    e = _by_word_extra("利す")
    assert len(e) == 1 and e[0]["reading"] == "りす", "N76 缺口 利す（りす）应在库"
    e = _by_word_extra("而る後")
    assert len(e) == 1 and e[0]["reading"] == "しかるのち", "N76 缺口 而る後（しかるのち）应在库"
    e = _by_word_extra("而ち")
    assert len(e) == 1 and e[0]["reading"] == "すなわち", "N76 缺口 而ち（すなわち）应在库"


def test_every_entry_has_dual_evidence():
    """全量（非抽查）：每条入库条目在判定底稿里都有 weblio 辞書＋语料两条非空证据。"""
    decs = {}
    for path in sorted(glob.glob(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "eval", "night79_decisions_*.json"))):
        for d in json.load(open(path, encoding="utf-8"))["decisions"]:
            decs[d["word"]] = d
    missing = []
    for e in LEXICON_EXTRA2:
        d = decs.get(e["word"])
        if d is None:
            missing.append((e["word"], "no decision record"))
        elif d.get("verdict") != "include":
            missing.append((e["word"], "verdict=%r" % d.get("verdict")))
        elif not str(d.get("dict_evidence", "")).strip() or not str(d.get("corpus_evidence", "")).strip():
            missing.append((e["word"], "evidence missing"))
    assert not missing, "双证据门未通过的条目 %d 条: %s" % (len(missing), missing[:8])


def test_excluded_representatives_not_in_file():
    src = open(_EXTRA2_PATH, encoding="utf-8").read()
    # 排除清单的代表条目（404 型／sense-mismatch 型／構文断片型 各取若干）
    for w in ("子曰", "所有", "昔者", "凡戰", "大学", "相当", "相見", "車騎",
              "子之", "東流", "越人", "諸有", "堯曰", "者有"):
        assert '"%s"' % w not in src, "排除条目 %r 不应出现在 extra2 源文件" % w


def test_find_in_lexicon2_hits_real_corpus_lines():
    hits = find_in_lexicon2("知者は仁を利す", max_hits=5)
    words = [h["word"] for h in hits]
    assert "利す" in words, "rongo0402-1 语料行应命中 利す: %s" % words
    assert hits[words.index("利す")]["reading"] == "りす"

    hits = find_in_lexicon2("先ず其の言を行い、而る後に之に従う", max_hits=5)
    assert "而る後" in [h["word"] for h in hits], "rongo0213-1 语料行应命中 而る後"

    hits = find_in_lexicon2("而ち曰く、然り。", max_hits=5)
    assert "而ち" in [h["word"] for h in hits], "kasei-5 语料行应命中 而ち"

    hits = find_in_lexicon2("以て天下を治める", max_hits=5)
    assert "天下" in [h["word"] for h in hits]


def test_base_matcher_does_not_see_extra2():
    # 本体 500 条查找器看不到 extra2 词——合并查找只在 llm 层（find_in_lexicon2）
    assert "利す" not in [h["word"] for h in find_in_lexicon("知者は仁を利す")]
    assert "而る後" not in [h["word"] for h in
                            find_in_lexicon("先ず其の言を行い、而る後に之に従う")]


def test_llm_glossary_offline_uses_extra2():
    from backend.llm import glossary
    hits = glossary("知者は仁を利す", "知者は仁を利す")
    words = [h["word"] for h in hits]
    assert "利す" in words, "llm.glossary 离线路径应命中 extra2 新词 利す: %s" % words


def test_kundoku_endpoint_unchanged():
    """词库不进规则引擎——经典句 kakikudashi 与 test_api 断言逐字一致。"""
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
        assert r.status_code == 200
        assert r.json()["kakikudashi"].strip() == "王は左右を顧みて而して他を言う"
