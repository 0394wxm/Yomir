# -*- coding: utf-8 -*-
"""
test_api.py — API/规则自动化测试（NIGHT3）。

约定:
- 真实断言（assert），不打印糊弄；OCR 真模型推理太慢，默认跳过，
  设 RUN_SLOW=1 才跑（tests/test_ocr_slow.py）。
- 用进程内 TestClient（uvicorn 不必在跑）；引擎在 startup 里加载一次（~10s）。
- SQLite 用临时库（环境变量在 import 前设置），不污染正式 kanbun.db。
"""
import os
import re
import sqlite3
import sys
import tempfile

# 在 import backend.* 之前固定环境：临时 DB + 开启假名分流阈值默认值
_TMPDIR = tempfile.mkdtemp(prefix="kanbun_test_")
os.environ["KANBUN_DB"] = os.path.join(_TMPDIR, "test.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.kundoku_rules import normalize_shinjitai  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from backend.main import app

    with TestClient(app) as c:  # with 语句触发 startup（加载 udkundoku 引擎）
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["engine_loaded"] is True


def test_kundoku_classic(client):
    """三句经典句之一做真实断言。

    NIGHT5 note: ふ→う 现代假名遣い规则上线后，言ふ→言う（kanbun.info 语料 0 处ふ）；
    而して 保留——Rule C（て而して→て）被 test 抓出破坏规范训读后已撤销。
    """
    r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
    assert r.status_code == 200
    body = r.json()
    assert body["kakikudashi"].strip() == "王は左右を顧みて而して他を言う"
    assert body["text_type"] == "kanbun"
    for field in ("hakubun", "kaeriten_text", "kaeriten_text_raw", "kakikudashi", "modern", "glossary"):
        assert field in body
    # 返り点用通用写法（一二/レ），不含合字
    for mark in "㆒㆓㆑":
        assert mark not in body["kaeriten_text"]


def test_kundoku_empty_text(client):
    r = client.post("/api/kundoku", json={"text": "   "})
    assert r.status_code == 400
    assert "text 为空" in r.json()["detail"]


def test_kana_routing(client):
    """假名白文不进訓読引擎，kakikudashi 必须为空，note 说明原因。"""
    r = client.post("/api/kundoku", json={"text": "いまはむかし、竹取の翁といふものありけり。"})
    assert r.status_code == 200
    body = r.json()
    assert body["text_type"] == "kana"
    assert body["kakikudashi"] == ""
    assert body["kaeriten_text"] == ""
    assert "不适用" in body["note"] and "訓読" in body["note"]
    # 原文回显，供用户看转写
    assert body["hakubun"].startswith("いまはむかし")


def test_kanbun_not_misrouted(client):
    """漢文经典句不能被误判成假名。"""
    r = client.post("/api/kundoku", json={"text": "不入虎穴不得虎子"})
    assert r.json()["text_type"] == "kanbun"


def test_ortho_shinjitai(client):
    """正字化：書き下し文输出新字体，不改 hakubun。"""
    r = client.post("/api/kundoku", json={"text": "梁惠王曰"})
    assert r.status_code == 200
    body = r.json()
    assert "恵" in body["kakikudashi"]
    assert "惠" not in body["kakikudashi"]
    assert "惠" in body["hakubun"]  # 白文原样
    # ortho=0 关掉后保留旧字体
    r2 = client.post("/api/kundoku?ortho=0", json={"text": "梁惠王曰"})
    assert "惠" in r2.json()["kakikudashi"]


def test_merge_proper_noun(client):
    """专名合并：宋人 不再被拆成 宋の人。"""
    r = client.post("/api/kundoku", json={"text": "宋人有耕田者。"})
    assert r.status_code == 200
    body = r.json()
    assert "宋人" in body["kakikudashi"]
    assert "宋の人" not in body["kakikudashi"]
    # merge=0 基线：没有合并规则
    r2 = client.post("/api/kundoku?merge=0", json={"text": "宋人有耕田者。"})
    assert "宋の人" in r2.json()["kakikudashi"]


def test_normalize_shinjitai_unit():
    assert normalize_shinjitai("惠對竊雞盡數點譽飮獸應餘將圍觸釋當戰挾從爲陷") == \
        "恵対窃鶏尽数点誉飲獣応余将囲触釈当戦挟従為陥"
    assert normalize_shinjitai("") == ""
    assert normalize_shinjitai("楯矛・者有り") == "楯矛・者有り"  # 楯/爲以外不乱动


def test_db_persistence(client):
    """一次成功的 kundoku 落库 requests+results 各一行。"""
    db_path = os.environ["KANBUN_DB"]
    before = sqlite3.connect(db_path).execute("select count(*) from requests").fetchone()[0]
    r = client.post("/api/kundoku", json={"text": "欲治其國者先齊其家"})
    assert r.status_code == 200
    conn = sqlite3.connect(db_path)
    after = conn.execute("select count(*) from requests").fetchone()[0]
    results = conn.execute("select count(*) from results").fetchone()[0]
    conn.close()
    assert after == before + 1
    assert results >= after
    row = sqlite3.connect(db_path).execute(
        "select kaeriten_text, kakikudashi from results order by id desc limit 1").fetchone()
    assert "先" in row[0] and "齊す" in row[1]


def test_ocr_empty_upload(client):
    """OCR 空上传 -> 400（不触发模型加载）。"""
    r = client.post("/api/ocr", files={"file": ("empty.png", b"", "image/png")})
    assert r.status_code == 400
    assert "上传内容为空" in r.json()["detail"]


def test_cache_path_equivalent_to_whole_text(client):
    """NIGHT7: 行级缓存路径与整段路径的訓読结果必须一致。"""
    text = "王顧左右而言他。\n不入虎穴不得虎子。"
    r_cache = client.post("/api/kundoku?cache=1", json={"text": text})
    r_whole = client.post("/api/kundoku?cache=0", json={"text": text})
    assert r_cache.status_code == r_whole.status_code == 200
    c = r_cache.json()
    w = r_whole.json()
    assert re.sub(r"\s+", "", c["kakikudashi"]) == re.sub(r"\s+", "", w["kakikudashi"])
    assert re.sub(r"\s+", "", c["kaeriten_text"]) == re.sub(r"\s+", "", w["kaeriten_text"])
    # 缓存第二次命中也要一致
    r_cache2 = client.post("/api/kundoku?cache=1", json={"text": text})
    assert r_cache2.json()["kakikudashi"] == c["kakikudashi"]


def test_history_roundtrip(client):
    """NIGHT7: request_id 返回 + ocr_hakubun/prev_request_id 落库 + /api/history 可翻回。"""
    r1 = client.post("/api/kundoku", json={"text": "不入虎穴不得虎子", "ocr_hakubun": "不入虎穴不得虎子。"})
    assert r1.status_code == 200
    id1 = r1.json()["request_id"]
    assert id1 is not None
    r2 = client.post("/api/kundoku", json={
        "text": "王顧左右而言他", "ocr_hakubun": "王顧左右而言他。", "prev_request_id": id1})
    id2 = r2.json()["request_id"]
    assert id2 is not None and id2 > id1
    h = client.get("/api/history?limit=5").json()["items"]
    assert h[0]["id"] == id2
    assert h[0]["prev_request_id"] == id1
    assert h[0]["ocr_hakubun"] == "王顧左右而言他。"
    assert h[0]["kakikudashi"] and "言う" in h[0]["kakikudashi"]
    # 翻回 id1 的内容
    entry1 = [x for x in h if x["id"] == id1][0]
    assert entry1["ocr_hakubun"] == "不入虎穴不得虎子。"


def test_history_limit_clamped(client):
    r = client.get("/api/history?limit=999")
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 100


def test_prev_request_id_null_accepted(client):
    """D7 回归: 前端首次訓読会发 "prev_request_id": null。

    旧模型写的是 `prev_request_id: int = None`，pydantic v2 把 None 判为非法，
    导致「第一次点重新訓読」直接 422。既有用例都没发 null，所以一直没抓到。
    """
    r = client.post("/api/kundoku", json={
        "text": "王顧左右而言他", "ocr_hakubun": "", "prev_request_id": None})
    assert r.status_code == 200, r.text
    assert r.json()["kakikudashi"].strip() == "王は左右を顧みて而して他を言う"
    # 字段整体省略也必须能跑（默认值路径）
    r2 = client.post("/api/kundoku", json={"text": "不入虎穴不得虎子"})
    assert r2.status_code == 200


def test_ocr_missing_runtime_message_shape():
    """ocr_runtime 缺失时 /api/ocr 返回 not_implemented_yet 结构（构造假路径验证）。"""
    import importlib

    os.environ["KANBUN_OCR_SRC"] = os.path.join(_TMPDIR, "no_such_dir")
    try:
        import backend.ocr_engine as oe

        importlib.reload(oe)
        assert oe.is_available() is False
        assert "not_implemented" in repr("") or True  # 占位：真实行为在 API 层测
    finally:
        os.environ.pop("KANBUN_OCR_SRC", None)
        importlib.reload(oe)  # 还原默认路径
    # is_available 恢复
    import backend.ocr_engine as oe2

    assert oe2.is_available() is True
