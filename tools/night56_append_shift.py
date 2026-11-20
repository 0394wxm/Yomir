# -*- coding: utf-8 -*-
"""night56_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT56）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N56 大学/孝経归因：两个都是短句构成主导（大学 100% 构成效应；孝経构成-11.1+文体-1.2）；論語同档反而比故事好"

BLOCK = u"""

## {mark}

**方法（D16 §3.3 遗留 / D17 §14 #4，零代码改动）**

基线 day17 真机归档（分文体复算与 REPORT_DAY17 §7.2 逐位一致，链路可信）。
分档口径 = 白文归一化长度（day16_split_stats.py 同款），文体按 source_url。
**反事实分解**：把每行按所在档套用故事的同档均值——
文体效应 = 实际 − 假设；构成效应 = 假设 − 故事整体。

| 文体 | 实际 | 若按故事同档 | 文体效应 | 构成效应 |
| --- | --- | --- | --- | --- |
| 大学 | 14.868 | 14.846 | **+0.022≈0** | **-6.854** |
| 孝経 | 9.374 | 10.577 | **-1.203** | **-11.123** |
| 論語 | 27.044 | 28.400 | -1.356 | +6.700 |

档位构成：大学 71% ≤20字（故事 52%）、孝経 94% ≤20字。

**结论**：①大学 = 100% 构成效应——同档反而比故事略难（≤20字 10.216 vs 9.746），
「経文更规整」不成立；②孝経 = 构成为主 + 小幅真实文体效应（同档略易 -9%，
但 21-40 档只有 9 条）；③**附带修正：「論語最难」要改口径——論語同档比故事好
（21-40 字 19.46 vs 23.31、41-60 字 34.04 vs 38.68），整体 27.0 高纯粹因为长句
占比是故事 2 倍（>60 字 17% vs 8%）。引擎困难度主要由句长驱动
（9.7→23.3→38.7→63.0 单调），文体同档差异 ≤1.5。**

本夜零代码改动（pytest 172、accept56 PASS、GT 证据沿用 N55 当夜实测）。
「分文体记分要做就做 分档×文体 交叉表」留拍板。
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
