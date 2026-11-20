# -*- coding: utf-8 -*-
"""night55_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT55）。

SHIFT_LOG.md 早期字节含非法 UTF-8 序列，只能用 'ab' 二进制追加，
并以「追加后 old 前缀逐字节不变」作为断言（与 night48-54 同一套做法）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N55 Rule G 上线：4 条假名→汉字（また→又/ゆゑん→所以/いはゆる→所謂/たがいに→相），2000 条 -0.200 0 变差"

BLOCK = u"""

## {mark}

**方法论与基线（按 N22/D17 四步：解剖→模拟→真函数→门+pytest）**

基线换成 **day17 真机归档**（Rule F 已上线，avgDist 21.116）——不再用 pre-F 快照。
挖掘 `night55_mine.py`：字符 delta + difflib 对齐收集引擎假名碎片。
D17 §14 五项遗留逐项处置（见 REPORT_NIGHT55.md §10 处置表）。

**上线 4 条（全部 0 变差，expected 假名残留全 0）**：
また→又（白文含又，44 条 -0.040，36/0）、ゆゑん→所以（30 条 -0.033，29/0）、
いはゆる→所謂（23 条 -0.044，23/0）、たがいに→相（43 条 -0.084，43/0）。
组合 **136 条改写，21.116→20.916（-0.200），127 改善/0 变差**；
真函数核对与模拟逐位一致，幂等 2000/2000，语料外 9 探针不动。
F 的 また 长词表提取为 _MATA_LONGER_WORDS 常量供 F/G 共享（三表独立+また共享有测试锁）。
链序 F→G：白文含亦时 F 先吃掉 また、G no-op；含又时 G 接手（分工测试锁定）。

**D17 遗留 #1（また→又 1 变差）解决机理**：那条变差（rongo2002-1）是对 pre-F
快照算的；post-F 真机基线上该行已无 また 可改（行级 dist 154→151 反而改善），
day16 上的双规则组合本来就是 0 变差 → F 已上线的现实里また→又干净。

**D17 遗留 #3（べき/べから 各 4 变差）逐条核因，维持拒绝**：8 条全部是
**expected 自身写假名 べき/べからず**（omoi-1/p-gekirin-1/kenro-1/mobosansen-1/
shushu-4/shukateki-1/ryojo-3/shiseinishite-1），改善行与变差行的白文都含「可」
——运行时信号完全相同，无法用护栏拯救（Night 27「逐页编辑习惯」定性一致）。
「為/不/与」结构性不可做：為 的 kana 是ため/す/なり类超高频假名（ために→為に
模拟 0 命中证伪）；不 是 不可/不仁 等汉字复合词 vs kana 谓语的翻译形态差异；
与 无稳定词形映射。

**验证**：pytest **158→172 passed**（+14 test_rule_g_kana_kanji.py，E/F/D/链/API
零破坏）；GT 门 `--out eval/night55_gt_lines.json` 实跑 8 页（unmatched 全 0），
GT CER **0.3568/0.3053 逐位不变**，N49 归档 sha256 跑前跑后同为 ff21e4fa…；
accept55 PASS。またも→亦たも（D17 遗留#2）未动——0 变差但属风格拍板。
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
