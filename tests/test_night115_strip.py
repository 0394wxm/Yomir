# -*- coding: utf-8 -*-
"""test_night115_strip.py — 剥夹注管線（N115 设计 Stage 0/1・N116 实施）的回归测试。

背景（N115 §2(B)）：engine 分支行若含 ruby 夹注，引擎会把注记括号卷进插助词/
送り仮名加工，got 残留（いわを曰いて）等加工残渣（8165 实测恰 2 行：
rikutou59-2・soji07-6）。N116 在 kundoku() engine 分支进规则链前剥掉含假名的
全角（…）span（剥下物丢弃＝N115 拍板①；hakubun 返原文＝拍板③・N84 先例）。

锁定（名取自 N115 §5）：
  ① has_ruby_annotation／strip_annotation 单元（不加载引擎）：
     真/假样本、rongo「N）」编号 6 行须假、dangling ）与空 （）保留、
     幂等、非注记行恒等；
  ② TestClient 端到端：两残渣行 got 无注记 span 且 d 224→155／36→23、
     hakubun 返原文、note 带 N116；
  ③ 防退化：非注记 engine 行 got 与 night111 归档逐位一致（scope 外 0 变差）、
     kana 分支（echo 行＝N84 尾段路径）一字不动、真·假名文本仍空串。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import (  # noqa: E402
    RUBY_SPAN_RE,
    detect_text_type,
    has_ruby_annotation,
    strip_annotation,
)

EV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")

# 单元样本（corpus 实测形态代表・N115 §3 三形态＋0 行形态）
RUBY_SAMPLE = "太公（たいこう）曰（いわ）く、騎（き）に十（じっ）勝（しょう）あり。"
NO_ANNOTATION_SAMPLE = "楚人有鬻楯與矛者。"
DANGLING_CLOSE = "1）子路曾晳冉有公西華侍坐。"          # rongo「N）」编号（無 （）
EMPTY_PARENS = "楚人（）有鬻楯與矛者。"                  # 空 （）＝剥ない
NO_KANA_PARENS = "武経本には「車」の字なし。（車）"       # 無仮名 （…）＝剥ない
KANA_TEXT = "いまはむかし、竹取の翁といふものありけり。"

RONGO_NUMBER_IDS = ["rongo1125-1", "rongo1125b-1", "rongo1125c-1",
                    "rongo1125d-1", "rongo1125e-1", "rongo1125f-1"]
RESIDUE_IDS = {"rikutou59-2": (224, 155), "soji07-6": (36, 23)}


def _load_rows(name):
    with open(os.path.join(EV, name), encoding="utf-8") as f:
        return {r["id"]: r for r in json.load(f)["results"]}


def _norm(s):
    return re.sub(r"\s+", "", s or "")


def _lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ---------------------------------------------------------------------------
# ① 单元（不加载引擎）


def test_has_ruby_annotation_true_false():
    assert has_ruby_annotation(RUBY_SAMPLE) is True
    assert has_ruby_annotation(NO_ANNOTATION_SAMPLE) is False
    assert has_ruby_annotation(DANGLING_CLOSE) is False      # 无开括号＝不触发
    assert has_ruby_annotation(EMPTY_PARENS) is False        # 空括号无假名
    assert has_ruby_annotation(NO_KANA_PARENS) is False      # 括号内无假名
    assert has_ruby_annotation(KANA_TEXT) is False           # 无括号假名文
    # rongo「N）」编号 6 行（N115 形態 2・归档实测）须全假
    rows = _load_rows("night111_results_8165.json")
    for rid in RONGO_NUMBER_IDS:
        assert has_ruby_annotation(rows[rid]["hakubun"]) is False, rid


def test_strip_idempotent_and_shape():
    st = strip_annotation(RUBY_SAMPLE)
    assert st == "太公曰く、騎に十勝あり。"                   # 剥下物丢弃・直接連結
    assert strip_annotation(st) == st                        # 幂等
    assert strip_annotation(NO_ANNOTATION_SAMPLE) == NO_ANNOTATION_SAMPLE
    # 归档两残渣行：剥前含 span・剥后无 span・幂等
    rows = _load_rows("night111_results_8165.json")
    for rid in RESIDUE_IDS:
        hb = rows[rid]["hakubun"]
        assert has_ruby_annotation(hb) is True, rid
        st = strip_annotation(hb)
        assert not RUBY_SPAN_RE.search(st), rid
        assert strip_annotation(st) == st, rid


def test_strip_identity_non_annotation_rows():
    rows = _load_rows("night111_results_8165.json")
    # rongo 编号 6 行・真·假名行：恒等
    for rid in RONGO_NUMBER_IDS:
        assert strip_annotation(rows[rid]["hakubun"]) == rows[rid]["hakubun"], rid
    assert strip_annotation(KANA_TEXT) == KANA_TEXT
    # sonshi09-38（括号外混在＝管線外）：白文本身含 ruby span（剥非恒等），
    # 但剥后仍 kana 分流＝N84 路径維持（N115 I4 実測）
    st = strip_annotation(rows["sonshi09-38"]["hakubun"])
    assert st != rows["sonshi09-38"]["hakubun"]
    assert detect_text_type(st) == "kana"


def test_dangling_and_empty_parens_preserved():
    assert strip_annotation(DANGLING_CLOSE) == DANGLING_CLOSE
    assert strip_annotation(EMPTY_PARENS) == EMPTY_PARENS
    assert strip_annotation(NO_KANA_PARENS) == NO_KANA_PARENS
    # 归档 dangling ） 6 行（有 ）無 （）＝I1 identity）
    rows = _load_rows("night111_results_8165.json")
    dang = [i for i, r in rows.items() if "）" in r["hakubun"] and "（" not in r["hakubun"]]
    assert len(dang) == 6
    for rid in dang:
        assert strip_annotation(rows[rid]["hakubun"]) == rows[rid]["hakubun"], rid


def test_detect_text_type_untouched():
    """detect_text_type 本体不改：N116 只加 helper 信号，分类值与阈值零变化。"""
    assert detect_text_type(RUBY_SAMPLE) == "kana"           # N84 误判機構そのまま
    assert detect_text_type(NO_ANNOTATION_SAMPLE) == "kanbun"
    assert detect_text_type(KANA_TEXT) == "kana"


# ---------------------------------------------------------------------------
# ②③ TestClient 端到端


@pytest.fixture(scope="module")
def client():
    from backend.main import app

    with TestClient(app) as c:  # with 语句触发 startup（加载 udkundoku 引擎）
        yield c


def test_residue_rows_annotation_stripped_end_to_end(client):
    """两残渣行：got 無注记 span・d 224→155／36→23・hakubun 返原文・note 带 N116。"""
    rows = _load_rows("night111_results_8165.json")
    for rid, (d0, d1) in RESIDUE_IDS.items():
        r = client.post("/api/kundoku", json={"text": rows[rid]["hakubun"]})
        assert r.status_code == 200, rid
        body = r.json()
        assert body["text_type"] == "kanbun", rid
        assert body["hakubun"] == rows[rid]["hakubun"], rid   # 拍板③ 返原文
        assert not RUBY_SPAN_RE.search(body["kakikudashi"]), rid   # I6
        assert "N116" in body["note"], rid
        # 归档侧 d0（剥前・night111 実測）が前提、剥後 d1 は設計予測値
        assert _lev(_norm(rows[rid]["udkundoku_kakikudashi"]),
                    _norm(rows[rid]["expected_kakikudashi"])) == d0, rid
        assert _lev(_norm(body["kakikudashi"]),
                    _norm(rows[rid]["expected_kakikudashi"])) == d1, rid


def test_engine_rows_without_annotation_byte_identical(client):
    """scope 外 engine 行（非注记）got 与 night111 归档逐位一致＝新增变差 0。"""
    # rikutou26-5 は 4000 归档外（N111 記録）＝8165 归档から取る
    rows = _load_rows("night111_results_8165.json")
    picked = [r for r in ["rongo1442-1", "rikutou26-5"] if r in rows]
    assert len(picked) == 2
    for rid in picked:
        r = client.post("/api/kundoku", json={"text": rows[rid]["hakubun"]})
        assert r.status_code == 200, rid
        body = r.json()
        assert body["kakikudashi"] == rows[rid]["udkundoku_kakikudashi"], rid
        assert body["hakubun"] == rows[rid]["hakubun"], rid
        assert "N116" not in body["note"], rid


def test_kana_branch_untouched_end_to_end(client):
    """kana 分支一字不动：echo 行（N84 尾段直出）got 与归档逐位一致、真·假名仍空串。"""
    rows = _load_rows("night111_results_8165.json")
    r = client.post("/api/kundoku", json={"text": rows["toushisen006-10"]["hakubun"]})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kana"
    assert body["kakikudashi"] == rows["toushisen006-10"]["udkundoku_kakikudashi"]
    assert "N116" not in body["note"]
    r = client.post("/api/kundoku", json={"text": KANA_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kana"
    assert body["kakikudashi"] == ""
