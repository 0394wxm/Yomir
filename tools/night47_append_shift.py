# -*- coding: utf-8 -*-
"""night47_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT47）。

SHIFT_LOG.md 在字节 807 处有非法 UTF-8 序列，只能用 'ab' 二进制追加。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N47 版面过滤后的残留噪音盘点"

BLOCK = u"""

## {mark}

**目标**：Night43-46 的版面过滤全是纯几何（不看文本），但**滤完还剩多少噪音
从没量过**。本夜做盘点，并验证两条修补路线。

**先纠正一个基线错误**：第一版测量读 `eval/night44_full/filter_on` 归档，
报「p031 还有 5 个手写长条没滤掉」。但该归档是 **Night44 生成的**，不含
Night46 的 judge_headnote_strip。用当前代码在 p031 原始框上重跑，那 13 个
长条（含这 5 个）**全部被滤掉**，与 Night46 e2e 的 headnote_strip 命中 13
逐一对上。教训：归档 JSON 的「当前状态」只等于生成它的那次代码的状态。

**盘点结果**（当前判据，filter_off 47 页）：原始 2055 框 → 页脚滤 223 +
上部滤 62 → 保留 **1770**。按假名比率（假名/(假名+汉字)）分布：
- **89.9%** 的保留框假名比率 < 0.01 —— 该版白文基本是纯汉字
- **>0.15 的 48 框 / 30 页（2.7%）** 是几何漏掉的真噪音
  例：p032「一腰に仕上る」「こ同一丁目を」「アノ神経理」（y=0 页顶裁切）、
  p044「にやしかけ」（r=1.00）、p010「□やれし。」（r=1.00）

**路线 A（纯几何）失败**：对比 48 高假名 vs 1722 低假名框，
h_rel 中位 0.24 vs 0.28、w_rel 0.31 vs 0.39、n_main_ov 中位都 1.00
——**几乎完全重合**。若用「h_rel<0.3 = 短框 → 噪音」，删 1109 框，
其中高假名 45、**低假名 1064**（正文列末 2-3 字短行）→ 误删比 **24:1**。
原因：手写書き入れ本身就是短竖条，与「列末剩两三个字的正文短行」在框几何上
不可区分。这正是 Night43 当初放弃文本外判据的原因。

**路线 B（假名比率文本判据）也不干净**：阈值 0.10-0.30 在 GT 8 页**零误伤**，
但 GT 只有 124 行，不能代表 47 页。全本查出：
- F1 在主栏集合里且 r>0.15 的 1 个：p026「如丘者焉不レ如レ如クリ丘之好レ学也」
  ——**这是正文**，夹了返り点「レ」和送り仮名「クリ」，r=0.29
- F2 含返り点/送り仮名记号的 23 框（判据无法区分「数字 三」与「返り点 三」）
→ GT 零误伤是**采样侥幸**，**不上线**。

**顺带查清 stale 归档**：`filter_on` 是 Night44 产物。已评估对 Night45/46
结论无影响（Night46 只删不排，不改行序；相关工具都已用 filter_off 重算）。
建议给归档加 `generated_by_commit` 字段（拍板项，本夜未动）。

**数字**：生产代码**零改动**；新增 5 个可复跑工具 + 4 份证据 JSON；
pytest 124 不变；提交 12a52fd。

**待拍板**：① 48 个高假名噪音要不要修（倾向「不修」或「只标记不删」；
若加文本判据须加返り点护栏，但护栏是从单样本反推的，属拟合）；
② stale 归档标注；③ 假名比率是否作为「汉文/和文」分类信号接进产品（独立设计）。
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
