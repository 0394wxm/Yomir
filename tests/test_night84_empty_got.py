# -*- coding: utf-8 -*-
"""test_night84_empty_got.py — ruby 夹注白文 kana 分流 fallback 的回归测试（Night 84）。

背景（N78 §8 交班点名的空 got 249 行）：
  kanbun.info 系白文行是「漢文＋（ruby 読み）」交织形，detect_text_type 把
  夹注内假名计入分子、括号排除出分母 → 假名占比 >30% 被误判为假名文学文本、
  kakikudashi 返回空串（引擎从未被调用）。N84 在 kana 分支加 ruby 尾段
  fallback：尾段 ≤8 字白文直出、>8 字分段重跑（绝不编造训读），无尾段的
  真·假名文本保持原空串行为。

三件套：
  ① _ruby_tail_kanbun 单元测试（不加载引擎）；
  ② TestClient 最小复现（夹注行不再返空串、真·假名文本行为不变）；
  ③ 防退化（echo/重跑两分支、幂等、无夹注文本不受影响）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import _RUBY_TAIL_ECHO_MAX, _ruby_tail_kanbun  # noqa: E402
from backend.main import detect_text_type, normalize_shinjitai  # noqa: E402

# golden_8165 实测空串行的最小复现样本（N83 归档 toushisen007-2）
RUBY_SHORT = "不知何王殿知（し）らず何王（なにおう）の殿（でん）ぞ遺構絶壁下"
RUBY_SHORT_TAIL = "遺構絶壁下"
# rikutou59-2 的尾段（>8 字 → 分段重跑分支）
RUBY_LONG = ("太公曰、騎有十勝九敗。太公（たいこう）曰（いわ）く、騎（き）に十（じっ）勝（しょう）九（きゅう）敗（はい）有（あ）り。"
             "武王曰、十勝奈何。武（ぶ）王（おう）曰（いわ）く、十（じっ）勝（しょう）とは奈何（いかん）。"
             "太公曰、敵人始至、行陳未定、前後不屬、陷其前騎、撃其左右、敵人必走。")
RUBY_LONG_TAIL = "太公曰、敵人始至、行陳未定、前後不屬、陷其前騎、撃其左右、敵人必走。"
KANA_TEXT = "いまはむかし、竹取の翁といふものありけり。"


def test_ruby_tail_kanbun_extraction():
    """① 尾段截取单元：夹注剥离、送り仮名残段剥离、无夹注/尾段含假名返空。"""
    assert _ruby_tail_kanbun(RUBY_SHORT) == RUBY_SHORT_TAIL
    assert _ruby_tail_kanbun(
        "壯士慘不驕壮（そう）士（し）惨（さん）として驕（おご）らず借問大將誰") == "借問大將誰"
    assert _ruby_tail_kanbun(RUBY_LONG) == RUBY_LONG_TAIL
    # 真·假名文本：无括号或尾段含假名 → 不触发 fallback
    assert _ruby_tail_kanbun(KANA_TEXT) == ""
    assert _ruby_tail_kanbun("いまは昔（むかし）竹取の翁（おきな）といふものありけり") == ""
    assert _ruby_tail_kanbun("楚人有鬻楯與矛者。") == ""
    # rongo 系「1）」编号只有闭括号、无 ruby 证据 → 不触发
    assert _ruby_tail_kanbun("1）子路曾晳冉有公西華侍坐。") == ""


def test_kana_classification_unchanged():
    """① 阈值不动（本夜只修 fallback，不改 detect_text_type 判定本身）。"""
    assert detect_text_type(RUBY_SHORT) == "kana"
    assert detect_text_type(KANA_TEXT) == "kana"
    assert detect_text_type("楚人有鬻楯與矛者。") == "kanbun"
    assert _RUBY_TAIL_ECHO_MAX == 8


@pytest.fixture(scope="module")
def client():
    from backend.main import app

    with TestClient(app) as c:  # with 语句触发 startup（加载 udkundoku 引擎）
        yield c


def test_ruby_short_tail_echo(client):
    """②③ 最小复现：夹注行不再返空串；≤8 字尾段走白文直出（无返り点）。"""
    r = client.post("/api/kundoku", json={"text": RUBY_SHORT})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kana"
    assert body["kakikudashi"] != ""
    assert body["kakikudashi"] == normalize_shinjitai(RUBY_SHORT_TAIL)
    assert body["kaeriten_text"] == ""  # 白文直出分支不做插助词训読
    assert "N84" in body["note"]


def test_ruby_long_tail_engine_rerun(client):
    """②③ >8 字尾段走分段重跑：真实训読输出（有返り点、含送り仮名假名）。"""
    r = client.post("/api/kundoku", json={"text": RUBY_LONG})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kana"
    assert body["kakikudashi"] != ""
    assert body["kaeriten_text"] != ""  # 分段重跑分支有返り点
    assert any("\u3041" <= c <= "\u309f" for c in body["kakikudashi"])
    assert "N84" in body["note"]
    assert body["hakubun"] == RUBY_LONG  # 白文原样保留（含夹注）


def test_true_kana_text_unchanged(client):
    """③ 真·假名文本保持原行为：kakikudashi 空串、note 无 N84。"""
    r = client.post("/api/kundoku", json={"text": KANA_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kana"
    assert body["kakikudashi"] == ""
    assert "N84" not in body["note"]


def test_plain_kanbun_untouched(client):
    """③ 无夹注普通汉文不走 fallback：kana 分流不命中、输出非空且有返り点。"""
    r = client.post("/api/kundoku", json={"text": "楚人有鬻楯與矛者。"})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kanbun"
    assert body["kakikudashi"] != ""
    assert "N84" not in body["note"]


def test_ruby_fallback_idempotent(client):
    """③ 幂等：同一输入两次请求输出逐位一致（行级缓存命中不改变结果）。"""
    b1 = client.post("/api/kundoku", json={"text": RUBY_SHORT}).json()
    b2 = client.post("/api/kundoku", json={"text": RUBY_SHORT}).json()
    assert b1["kakikudashi"] == b2["kakikudashi"]
    assert b1["kaeriten_text"] == b2["kaeriten_text"]
    l1 = client.post("/api/kundoku", json={"text": RUBY_LONG}).json()
    l2 = client.post("/api/kundoku", json={"text": RUBY_LONG}).json()
    assert l1["kakikudashi"] == l2["kakikudashi"]
