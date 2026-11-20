# -*- coding: utf-8 -*-
"""
epub_export.py — 訓読結果の EPUB 3 書き出し（NIGHT52，ROADMAP 产品深水区「导出 EPUB / PDF」）。

设计要点：
  * **纯标准库**（zipfile + xml.sax.saxutils），不加依赖、全离线、全内存（BytesIO，
    不落临时文件）。
  * **逐字节确定性**：同一输入 → 同一字节串。UUID 用 uuid5（内容哈希派生），
    zip 条目时间戳 / dcterms:modified 都从条目 created_at 派生（无则取固定下限）。
    这让「导出产物可 diff」成为可能，测试可以做逐字节断言。
  * 縦書き：style.css 用 writing-mode: vertical-rl（EPUB3 标准做法，日文书阅读器
    都走这条）；不用图片、不用 JS。阅读器不支持时回退横排，内容仍可读。
  * 条目名全部是常量/编号派生，无用户输入进文件名，无路径穿越面。
  * PDF 不在本夜范围：CJK 縦書き PDF 需要嵌入字体的排版引擎，本机离线做不了
    逐字正确的组版（见 REPORT_NIGHT52.md）。

条目数据（rows，与 db.get_history 返回形状一致）：
    {"id", "hakubun", "kaeriten_text", "kakikudashi", "created_at", ...}
"""
import io
import uuid
import zipfile
from datetime import datetime
from xml.sax.saxutils import escape

# EPUB 3.3 要求的 mimetype（必须第一个条目、ZIP_STORED、无额外字节）
MIMETYPE = "application/epub+zip"

DEFAULT_TITLE = "漢文 書き下し文"

# zip 时间戳下限（DOS 纪元从 1980 起）
_ZIP_MIN = (1980, 1, 1, 0, 0, 0)
# dcterms:modified 下限（xsd dateTime，合法即可；确定性优先于真实性，见上）
_MODIFIED_MIN = "1980-01-01T00:00:00Z"

_CONTAINER = u"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

_CSS = u"""/* NIGHT52: 縦書き（EPUB3 writing-mode）。阅读器不支持时自动回退横排。 */
body { writing-mode: vertical-rl; line-height: 2; margin: 1em; }
h1, h2, h3 { margin: 0 0 0.5em 0; }
.hakubun { color: #333; margin-bottom: 1em; }
.kakikudashi { font-weight: normal; }
"""

_XHTML_HEAD = u"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>%s</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
"""


def _parse_ts(ts):
    """created_at（db.py 的 isoformat 秒级）-> datetime；解析失败返回 None。"""
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    except (TypeError, ValueError):
        return None


def _book_uuid(rows, title):
    """uuid5（SHA-1 派生）：同内容同 UUID，不同内容必不同。"""
    key = u"\n".join([title] + [
        u"%s|%s|%s|%s" % (r.get("id"), r.get("hakubun", ""),
                          r.get("kaeriten_text", ""), r.get("kakikudashi", ""))
        for r in rows])
    return str(uuid.uuid5(uuid.NAMESPACE_URL, u"kanbun-epub:" + key))


def _modified_and_dt(rows):
    """从条目 created_at 派生 dcterms:modified 与 zip 时间戳（确定性）。"""
    dts = [d for d in (_parse_ts(r.get("created_at")) for r in rows) if d]
    if not dts:
        return _MODIFIED_MIN, _ZIP_MIN
    newest = max(dts)
    return (newest.strftime("%Y-%m-%dT%H:%M:%SZ"),
            (max(newest.year, 1980), newest.month, newest.day,
             newest.hour, newest.minute, newest.second))


def _build_opf(rows, title, uuid_str, modified):
    opf_items = [u'    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                 u'    <item id="css" href="style.css" media-type="text/css"/>']
    opf_refs = []
    for i in range(1, len(rows) + 1):
        opf_items.append(u'    <item id="ch%d" href="text/chapter-%02d.xhtml" media-type="application/xhtml+xml"/>' % (i, i))
        opf_refs.append(u'    <itemref idref="ch%d"/>' % i)
    return u"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="ja">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:%s</dc:identifier>
    <dc:title>%s</dc:title>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">%s</meta>
  </metadata>
  <manifest>
%s
  </manifest>
  <spine>
    <itemref idref="nav"/>
%s
  </spine>
</package>
""" % (uuid_str, escape(title), modified, u"\n".join(opf_items), u"\n".join(opf_refs))


def _build_nav(rows, title):
    nav_lis = [u'    <li><a href="text/chapter-%02d.xhtml">%s</a></li>' % (i, escape(u"第%d条" % i))
               for i in range(1, len(rows) + 1)]
    return u"".join([
        _XHTML_HEAD % u"目次",
        u'<nav epub:type="toc">\n  <h1>%s</h1>\n  <ol>\n' % escape(title),
        u"\n".join(nav_lis) if nav_lis else u"    <li>（无条目）</li>",
        u"\n  </ol>\n</nav>\n</body>\n</html>\n",
    ])


def _chapter_xhtml(idx, row):
    title = u"第%d条" % idx
    parts = [_XHTML_HEAD % title, u'<section epub:type="chapter">\n']
    parts.append(u"  <h2>%s</h2>\n" % title)
    parts.append(u'  <h3>原文（白文）</h3>\n  <div class="hakubun">%s</div>\n'
                 % escape(row.get("hakubun", "") or ""))
    if row.get("kaeriten_text"):
        parts.append(u'  <h3>返り点付き</h3>\n  <div class="kaeriten">%s</div>\n'
                     % escape(row["kaeriten_text"]))
    parts.append(u'  <h3>書き下し文</h3>\n  <div class="kakikudashi">%s</div>\n'
                 % escape(row.get("kakikudashi", "") or ""))
    parts.append(u'</section>\n</body>\n</html>\n')
    return u"".join(parts)


def build_epub(rows, title=DEFAULT_TITLE):
    """构建 EPUB 3 字节串。rows 按 id 升序；空 rows 也可构建（只有目次）。"""
    rows = list(rows)
    uuid_str = _book_uuid(rows, title)
    modified, zdt = _modified_and_dt(rows)

    def zi(name):
        z = zipfile.ZipInfo(name, date_time=zdt)
        z.compress_type = zipfile.ZIP_DEFLATED
        z.external_attr = 0o600 << 16
        return z

    out = io.BytesIO()
    z = zipfile.ZipFile(out, "w")

    # mimetype 必须第一个条目且 ZIP_STORED
    m = zi("mimetype")
    m.compress_type = zipfile.ZIP_STORED
    z.writestr(m, MIMETYPE.encode("utf-8"))

    z.writestr(zi("META-INF/container.xml"), _CONTAINER.encode("utf-8"))
    z.writestr(zi("OEBPS/content.opf"), _build_opf(rows, title, uuid_str, modified).encode("utf-8"))
    z.writestr(zi("OEBPS/nav.xhtml"), _build_nav(rows, title).encode("utf-8"))
    z.writestr(zi("OEBPS/style.css"), _CSS.encode("utf-8"))
    for i, row in enumerate(rows, 1):
        z.writestr(zi("OEBPS/text/chapter-%02d.xhtml" % i),
                   _chapter_xhtml(i, row).encode("utf-8"))
    z.close()
    return out.getvalue()
