# -*- coding: utf-8 -*-
"""night53_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT53）。

SHIFT_LOG.md 早期字节含非法 UTF-8 序列，只能用 'ab' 二进制追加，
并以「追加后 old 前缀逐字节不变」作为断言（与 night48-52 同一套做法）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N53 白文 EPUB：POST /api/export/epub（未训读文本直接导出，导出方向闭环）"

BLOCK = u"""

## {mark}

**定位（已提交见 REPORT_NIGHT53.md）**

N52 的 GET 版只覆盖**已落库训读结果**；产品核心工作流「批量 OCR → 行级纠错 → 训读」
里，纠错后的白文在训读**之前**也该可带走（「批量导入一本古籍」前半段交付物）。
本夜补 **POST /api/export/epub**：客户端文本直接导出，不要求落库。与 N52 共用同一个
`build_epub`——`kakikudashi` 为空 = 纯白文章节（不渲染空训读段）。校验：非空、
≤500 章、每章白文/書き下し至少一项非空；title 缺省回退；确定性语义同 N52
（无落库时间 → dcterms:modified 走 1980 下限，同输入同字节）。前端导出区
第五个按钮「白文 EPUB」（白文框非空才可用），`saveBlob` 助手去重。

**验证**：导出测试 11→**16 条全过**（POST roundtrip 转义/空章 400/超限 400/
title 回退/POST 确定性），全套 **141→152→157 passed**（18.44s）；
`npx tsc --noEmit` 零错误、`npm run build` 通过；GET 路径行为不变（原 11 条断言未动全过）。

**已知限制（如实）**：真机阅读器人工验证仍缺（同 N52——结构级已尽）；
500 章上限是本夜拍的保守值；批量结果当前整本单章，「页=章」分章留待拍板（待拍板④⑤）。
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
