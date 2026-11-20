# -*- coding: utf-8 -*-
"""
test_export_epub.py — EPUB 导出的离线验证（NIGHT52）。

约定与 test_api.py 相同：临时 DB（import 前设环境变量）、进程内 TestClient。
不联网、不依赖 OCR 真模型（引擎经 startup 缓存后复用）。

EPUB 3 关键不变式：
  * mimetype 是第一个 zip 条目、ZIP_STORED、内容逐字节 == "application/epub+zip"；
  * container.xml / content.opf / nav.xhtml / chapter-*.xhtml 全部是 well-formed XML；
  * 同一输入逐字节确定（uuid5 + created_at 派生时间戳）；
  * 文本经 XML 转义（OCR 噪音含 < > & 不会破坏 xhtml）。
"""
import io
import os
import sys
import tempfile
import zipfile
from xml.etree import ElementTree

# 在 import backend.* 之前固定环境：临时 DB（与 test_api.py 同款）
_TMPDIR = tempfile.mkdtemp(prefix="kanbun_test_epub_")
os.environ["KANBUN_DB"] = os.path.join(_TMPDIR, "test.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend import db, epub_export  # noqa: E402

_NS_OPF = "http://www.idpf.org/2007/opf"
_NS_DC = "http://purl.org/dc/elements/1.1/"
_NS_XHTML = "http://www.w3.org/1999/xhtml"
_NS_EPUB = "http://www.idpf.org/2007/ops"
_NS_CNT = "urn:oasis:names:tc:opendocument:xmlns:container"

_ROWS = [
    {"id": 1, "hakubun": "王顧左右而言他", "kaeriten_text": "王は左右を顧みて而して他を言う",
     "kakikudashi": "王は左右を顧みて而して他を言う", "created_at": "2026-11-20T23:00:00"},
    {"id": 2, "hakubun": "學<而>時習之 & 不亦說乎", "kaeriten_text": "",
     "kakikudashi": "学びて時に習ふ", "created_at": "2026-11-20T23:30:00"},
]


def _parse_xml(data):
    return ElementTree.parse(io.BytesIO(data)).getroot()


@pytest.fixture(scope="module")
def client():
    from backend.main import app

    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------
# 纯模块级（不碰 DB / 不碰 API）
# --------------------------------------------------------------------------
def test_mimetype_first_entry_stored_exact():
    data = epub_export.build_epub(_ROWS)
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    assert names[0] == "mimetype"
    info = z.getinfo("mimetype")
    assert info.compress_type == zipfile.ZIP_STORED
    assert z.read("mimetype") == b"application/epub+zip"


def test_zip_layout_and_all_xml_wellformed():
    data = epub_export.build_epub(_ROWS)
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    assert names[1] == "META-INF/container.xml"
    assert "OEBPS/content.opf" in names and "OEBPS/nav.xhtml" in names
    assert "OEBPS/style.css" in names
    assert names.count("OEBPS/text/chapter-01.xhtml") == 1
    # 每个条目都是 well-formed XML（css 除外）
    for name in names:
        if name.endswith(".xhtml") or name.endswith(".xml") or name.endswith(".opf"):
            _parse_xml(z.read(name))


def test_opf_metadata_manifest_spine():
    data = epub_export.build_epub(_ROWS)
    z = zipfile.ZipFile(io.BytesIO(data))
    root = _parse_xml(z.read("OEBPS/content.opf"))
    assert root.tag == "{%s}package" % _NS_OPF
    assert root.get("unique-identifier") == "book-id"
    ident = root.find(".//{%s}identifier" % _NS_DC)
    assert ident is not None and ident.text.startswith("urn:uuid:")
    modified = root.find('.//{%s}meta[@property="dcterms:modified"]' % _NS_OPF)
    assert modified is not None and modified.text == "2026-11-20T23:30:00Z"
    nav = root.find('.//{%s}item[@id="nav"]' % _NS_OPF)
    assert nav is not None and nav.get("properties") == "nav"
    hrefs = {i.get("href") for i in root.findall(".//{%s}item" % _NS_OPF)}
    assert hrefs >= {"nav.xhtml", "style.css", "text/chapter-01.xhtml", "text/chapter-02.xhtml"}


def test_nav_and_chapter_content():
    data = epub_export.build_epub(_ROWS)
    z = zipfile.ZipFile(io.BytesIO(data))
    nav = _parse_xml(z.read("OEBPS/nav.xhtml"))
    # <nav> 是 XHTML 元素；epub 命名空间在 *属性* epub:type 上
    toc = nav.find(".//{%s}nav" % _NS_XHTML)
    assert toc is not None and toc.get("{%s}type" % _NS_EPUB) == "toc"
    links = [a.get("href") for a in toc.findall(".//{%s}a" % _NS_XHTML)]
    assert links == ["text/chapter-01.xhtml", "text/chapter-02.xhtml"]

    ch1 = z.read("OEBPS/text/chapter-01.xhtml").decode("utf-8")
    assert "王顧左右而言他" in ch1
    assert "王は左右を顧みて而して他を言う" in ch1
    ch2 = z.read("OEBPS/text/chapter-02.xhtml").decode("utf-8")
    # XML 转义：原文里的 < > & 必须以实体出现，raw 字符不能出现在文本位
    assert "學&lt;而&gt;時習之 &amp; 不亦說乎" in ch2
    assert "學<而>時習之" not in ch2


def test_determinism_byte_identical_and_uuid_sensitive():
    a = epub_export.build_epub(_ROWS)
    b = epub_export.build_epub(_ROWS)
    assert a == b
    changed = [dict(_ROWS[0], kakikudashi="王は左右を顧みて他を言う")]
    c = epub_export.build_epub(changed + _ROWS[1:])
    assert a != c
    za, zc = zipfile.ZipFile(io.BytesIO(a)), zipfile.ZipFile(io.BytesIO(c))
    ua = _parse_xml(za.read("OEBPS/content.opf")).find(".//{%s}identifier" % _NS_DC).text
    uc = _parse_xml(zc.read("OEBPS/content.opf")).find(".//{%s}identifier" % _NS_DC).text
    assert ua != uc


def test_empty_rows_still_builds():
    data = epub_export.build_epub([])
    z = zipfile.ZipFile(io.BytesIO(data))
    assert "mimetype" in z.namelist()
    root = _parse_xml(z.read("OEBPS/content.opf"))
    assert root.find(".//{%s}itemref" % _NS_OPF) is not None


def test_created_at_missing_falls_back():
    rows = [{"id": 9, "hakubun": "x", "kaeriten_text": "", "kakikudashi": "y",
             "created_at": "not-a-date"}]
    data = epub_export.build_epub(rows)
    z = zipfile.ZipFile(io.BytesIO(data))
    root = _parse_xml(z.read("OEBPS/content.opf"))
    modified = root.find('.//{%s}meta[@property="dcterms:modified"]' % _NS_OPF)
    assert modified.text == "1980-01-01T00:00:00Z"


# --------------------------------------------------------------------------
# 端点级（TestClient + 临时 DB）
# --------------------------------------------------------------------------
def test_export_endpoint_roundtrip(client):
    rid = db.save_kundoku("王顧左右而言他", "王は左右を顧みて而して他を言う",
                          "王は左右を顧みて而して他を言う")
    r = client.get("/api/export/epub?ids=%d" % rid)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/epub+zip"
    assert "attachment" in r.headers["content-disposition"]
    data = r.content
    z = zipfile.ZipFile(io.BytesIO(data))
    assert z.namelist()[0] == "mimetype"
    ch1 = z.read("OEBPS/text/chapter-01.xhtml").decode("utf-8")
    assert "王は左右を顧みて而して他を言う" in ch1


def test_export_endpoint_default_limit_and_order(client):
    rid2 = db.save_kundoku("梁惠王曰", "梁恵王曰く", "梁恵王曰く")
    r = client.get("/api/export/epub?limit=1")
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = [n for n in z.namelist() if n.startswith("OEBPS/text/")]
    assert len(names) == 1
    assert "梁恵王曰く" in z.read(names[0]).decode("utf-8")


def test_export_endpoint_missing_id_404_and_bad_ids_400(client):
    r = client.get("/api/export/epub?ids=999999999")
    assert r.status_code == 404
    r = client.get("/api/export/epub?ids=abc")
    assert r.status_code == 400


def test_export_endpoint_skips_resultless_requests(client):
    """无 results 的 request（理论上不该有，防御性）被跳过，不进 EPUB。"""
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO requests (hakubun, created_at) VALUES ('孤儿请求', '2026-11-20T23:59:00')")
        orphan_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    rid = db.save_kundoku("有結果", "ある", "ある")
    r = client.get("/api/export/epub?ids=%d,%d" % (orphan_id, rid))
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = [n for n in z.namelist() if n.startswith("OEBPS/text/")]
    assert len(names) == 1
    body = z.read(names[0]).decode("utf-8")
    assert "孤儿请求" not in body and "ある" in body


# --------------------------------------------------------------------------
# NIGHT53: POST /api/export/epub（客户端文本直接导出，不要求落库）
# --------------------------------------------------------------------------
def test_export_raw_post_roundtrip(client):
    r = client.post("/api/export/epub", json={
        "title": "漢文 白文",
        "chapters": [{"hakubun": "学<而>時習之"}, {"hakubun": "有朋自遠方来"}],
    })
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/epub+zip"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = [n for n in z.namelist() if n.startswith("OEBPS/text/")]
    assert len(names) == 2
    ch1 = z.read("OEBPS/text/chapter-01.xhtml").decode("utf-8")
    assert "学&lt;而&gt;時習之" in ch1
    # kakikudashi 为空 = 纯白文章节，不渲染空训读段
    assert "書き下し文" not in ch1


def test_export_raw_post_empty_chapters_400(client):
    r = client.post("/api/export/epub", json={"chapters": []})
    assert r.status_code == 400
    r = client.post("/api/export/epub", json={"chapters": [{"hakubun": "  ", "kakikudashi": ""}]})
    assert r.status_code == 400


def test_export_raw_post_too_many_400(client):
    r = client.post("/api/export/epub", json={"chapters": [{"hakubun": "x"}] * 501})
    assert r.status_code == 400


def test_export_raw_post_title_fallback(client):
    r = client.post("/api/export/epub", json={"title": "  ", "chapters": [{"hakubun": "天命"}]})
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    opf = z.read("OEBPS/content.opf").decode("utf-8")
    assert "漢文 書き下し文" in opf


def test_export_raw_post_deterministic(client):
    body = {"title": "t", "chapters": [{"hakubun": "王顧左右而言他", "kakikudashi": "王は左右を顧みて"}]}
    a = client.post("/api/export/epub", json=body).content
    b = client.post("/api/export/epub", json=body).content
    assert a == b
