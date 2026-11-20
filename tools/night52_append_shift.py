# -*- coding: utf-8 -*-
"""night52_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT52）。

SHIFT_LOG.md 早期字节含非法 UTF-8 序列，只能用 'ab' 二进制追加，
并以「追加后 old 前缀逐字节不变」作为断言（与 night48/49/50/51 同一套做法）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N52 EPUB 导出：产品深水区第一夜（导出 EPUB / PDF 的 EPUB 半边落地，PDF 留待拍板）"

BLOCK = u"""

## {mark}

**定位（队列推演，已提交 `818d7df`）**

N15（联网+拍板）/ N16-20（门禁，红线）跳过；N21-50 全 DONE。产品深水区（N51-70）里
唯一无门禁、可离线验证的是「导出 EPUB / PDF」→ 按 ROADMAP「阶段开头由当晚 agent
写细」执行 EPUB 半边。**PDF 明确不做**：CJK 縦書き PDF 需要嵌字体的组版引擎，
离线装不了/做不像样——要不要做、装什么引擎，写进 REPORT_NIGHT52.md §6 待拍板。

**实现（纯标准库，零新依赖，全离线）**

`backend/epub_export.py`：zipfile + xml.sax.saxutils，全内存 BytesIO。EPUB3 最小
合法结构（mimetype 首条目 ZIP_STORED → container.xml → content.opf → nav.xhtml →
chapter-NN.xhtml + style.css）；縦書き走 EPUB3 标准 CSS `writing-mode: vertical-rl`
（阅读器不支持自动回退横排）。**逐字节确定性**：uuid5(内容哈希) 派生 identifier、
zip 时间戳与 dcterms:modified 从 created_at 派生（坏/缺时间戳回退 1980-01-01）——
同输入同字节串，产物可 diff。正文全 escape（OCR 噪音 `< > &` 不破 XHTML）；
zip 条目名全常量，无路径穿越面。

`GET /api/export/epub`：`ids=1,2,3` 指定导出（缺 id → 404，非整数 → 400）；缺省
取最近 limit(1-100, 默认20) 条按 id 升序；无结果的 request 跳过，全跳完 404；
返回 application/epub+zip + ASCII attachment 文件名。`db.get_requests_by_ids`
与 get_history 同投影。前端导出区加第四个按钮「EPUB 出力」（result 没落库禁用）。

**验证（11 条新测试 → 全套 152 passed）**

结构级 EPUB3 规范要点逐条断言（mimetype 位置/压缩/内容、全 XML well-formed、
opf 元数据/spine 引用链、nav 链接一致、转义、确定性、空 rows、坏时间戳回退）+
端点 5 条（roundtrip / 缺省 limit / 404 / 400 / 孤儿 request 跳过）。中途 1 挂：
**测试自身**把 `<nav>` 当 epub 命名空间找（它是 XHTML 元素，epub 只在 epub:type
属性上）——生产代码零改动，修测试后 11/11。
`npx tsc --noEmit` 零错误、`npm run build` 通过、dist 不被跟踪不弄脏工作区。

**已知限制（如实）**：本机沙盒没有真实阅读器人工开过 EPUB（IAB 不能传文件）——
结构级验证已尽，縦書き渲染效果待用户点一次按钮人眼确认；現代語訳/語釈未进 EPUB
（modern 是无 key 占位，等 Night 9 门禁落地再随内容进）。

**待拍板**：① PDF 导出引擎（要吗/weasyprint 还是 pagedjs/允许联网吗）；
② EPUB 要不要带 現代語訳/語釈 段；③ N50 ①③、N49 §16 ③④ 原样保留。
""".format(mark=MARK)


def main():
    before = os.path.getsize(PATH)
    with io.open(PATH, "rb") as f:
        old = f.read()
    assert len(old) == before
    with io.open(PATH, "ab") as f:
        f.write(BLOCK.encode("utf-8"))
    after = os.path.getsize(PATH)
    with io.open(PATH, "rb") as f:
        new = f.read()
    assert new[:before] == old, "old bytes changed!"
    print("SHIFT_LOG.md: %d -> %d bytes (+%d)" % (before, after, after - before))
    print("old-byte prefix identical: YES")


if __name__ == "__main__":
    main()
