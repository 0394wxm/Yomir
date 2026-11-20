# -*- coding: utf-8 -*-
"""night58_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT58）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N58 Rule H 挖掘上线：また→復た/それ→只だ/べからず→須いず + SHINJITAI 30 对；3000 条 -0.102 0变差，真机 317/317 与模拟逐位一致"

BLOCK = u"""

## {mark}

**时钟异常（如实）**：开工机器时钟 2026-11-21 02:05，比上一班收尾（11-22 02:55）
早 ~24.8h——时钟被回拨，本班心跳与「跑到 09:00」按机器时钟执行。

**解剖**（golden_3000 新增段=詩経/漢詩，下标 2000+，≤20字 996 条 avgDist 7.078）：
两大类信号——① 舊字体残留（靑28/處51/獨37/樓18/遙7/舊15/曉11/醉10/縱10/晚4/橫9…，
kanbun.info 一律写新字体）；② 假名读法缺口第三/四形态（また→復た、それ→只だ、
べからず→須いず）。於（碎片散乱）、将（無稳定词形+已在表）不出候选，如实记录。

**离线模拟**（基线=night57 真机 16.321，逐条真算 Levenshtein）：
SHINJITAI 30 对 -0.084（226/0）；Rule H 三条 -0.011/-0.004/-0.002 全 0 变差；
组合 **317 条改写、-0.102、改善 264/变差 0**、幂等 PASS。
拒绝（N55 べき 同机制「运行时无信号可分」）：ことなかれ→莫かれ 11 变差（exp 写
莫し/莫き/莫けん）、なかれ→莫かれ 1 变差、べし→須らく 5 变差（同行混写
須らく…べし）；1:1 扫描拒 冰→氷/弦→絃/亦→又（exp 自身写旧形）。

**上线**：backend/kundoku_rules.py（Rule H 3 条+H_LONGER_WORDS+链接入；
SHINJITAI_MAP +30 对，含异体 寳 U+5BF3）。
**真机**：3000 条 101s，**vs night57 归档不同行数=317=模拟、新文本逐位一致 317/317、
变差 0**（第四次「API=离线真函数」）；**avgDist 16.321→16.219**；精确 **15→16**
（toushisen244-2 復聞啼鳥聲→復た啼鳥の声を聞く）；全档/全文体单调改善。

**验证**：pytest **175→190**（test_rule_h 15 条）；GT 门 8 页 **raw 0.3568/
norm 0.3053 逐位不变**、night49 sha256 `ff21e4fa…` 不变；accept58 提交前
repo_clean 如实 FAIL、其余全 PASS，提交后终跑。过程自查纠错 3 件（1:1 判据放宽、
解剖对过滤器误杀 9 对、误覆盖 night36_cer.json 已恢复）如实入报告 §7。

待拍板新增 **⑪** それ→只だ 护栏加严（高频词风险）、**⑫** SHINJITAI 表拆独立
数据文件（N60 扩语料后自动重核验用）。
"""


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
