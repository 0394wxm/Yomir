# -*- coding: utf-8 -*-
"""night46_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT46）。

SHIFT_LOG.md 在字节 807 处有非法 UTF-8 序列，任何 read-then-rewrite 都会
触发 UnicodeDecodeError 或静默损坏。本脚本**只用二进制追加**（'ab'），
并校验旧字节前缀逐字节不变。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N46 上部手写批注长条过滤"

BLOCK = u"""

## {mark}

**目标**：Night43 挂起的「上部头注带过滤」。先审挂起理由，再审方案。

**关键发现（推翻 Night43 的挂起理由）**：Night43 说「p012/p017 上主栏若有
顶格长列（miban.y=35），头注带落入版心内部 → 判据越界误杀头注正文」。
但 `miban.y = min(主栏 y)`，而 p012/p017 的**手写长条自己被误判为主栏**
（w=33-41 刚过 `0.65×P90(w)=33.1`），所以 miban.y 才等于 38/36 —— 用被污染
的量论证不能修污染，是**循环论证**。其余 41 页 miban.y 都在 204-252。

**两个中间方案均被证伪**：
1. y 聚类护栏：p009 有真正文列「子曰。弟子入則孝。出則弟謹」（x=1036 y=417
   w=50 h=379），起点低是因为上方被批注占用 → y 聚类把它当离群剔掉，误杀。
2. 宽度分布最大间隙法：p012 的间隙落在 28.5/30.5（rel=0.21），阈值 29.5
   比固定 33.15 **更低** → 多收 2 条窄条，miban.y 只降到 35，更糟。
→ 结论：不该改 `_main_group`，另开独立判据。

**最终判据** `judge_headnote_strip`：縦框 ∧ `y + 100 <= body_top` ∧
`h >= 0.5*hmax`，其中 `body_top = median(主栏 y)`（47 页实测 209-256，
离群拉不动）。灵敏度：offset 60-150 × h_frac 0.4-0.6 命中数完全不变（平台区）。

**验证**：
- 47 页命中 62 框/18 页，文本全为手写公文批注（夹「候」「御」「様」）；
  与页脚带判据**零重叠**；命中框 y 在 16/18 页完全早于主栏 y 最小值。
- 生产实现与离线调查**逐框一致**（页脚 223 / 上部 62 / 保留 1770）。
- 真实 OCR 6 页：内容守恒 6/6、保留行顺序反转 ≤0.1%、账目闭合
  （99 删行 = 39 上部 + 74 页脚 − 14 已被 junk 前置剔除）。
- GT 92 行 CER raw 0.3568 / norm 0.3053 / raw macro 0.2566 / norm macro
  0.2242 **逐位不变**；GT 8 页 layout_filtered 计数与 Night44 逐页相同，
  新增滤框 **0**。

**生产接入**：复用 `KANBUN_OCR_LAYOUT_FILTER`（不新增开关），
`layout_filtered.reason` 新增 `headnote_strip`；日志分母修正为进入过滤前的框数。

**顺带查清**：① `miban.y` 污染对产品流零影响（引擎丢弃 miban，页脚判据用
y_max，实测 798-823）→ Night45 §7 第 1 条的 w 门槛收紧建议关掉；② 横排行
单元在 47 页里零命中（1832 框全部 h>=w），是死代码；③ 81 个「割注候选」里
55 个是上部手写长条的伪阳性，真割注（p019 x=1015 y=229 w=22 h=271）Night43
已按 h 上限保护，不是本夜问题域。

**数字**：pytest 116→124（新增 8 条）；accept_night 46 PASS（fail=0 skip=1）；
提交 b2567f4。被证伪的 2 个方案与 13 个临时调查脚本已删除，未进生产。
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
    # 旧字节前缀必须逐字节不变
    assert new[:before] == old, "old bytes changed!"
    print("SHIFT_LOG.md: %d -> %d bytes (+%d)" % (before, after, after - before))
    print("old-byte prefix identical: YES")
    print("appended block starts with: %r" % new[before:before + 40])


if __name__ == "__main__":
    main()
