# -*- coding: utf-8 -*-
"""night45_append_shift.py — Night 45 的 SHIFT_LOG 条目（二进制追加，不碰旧字节）。

SHIFT_LOG.md 早期条目含非法 UTF-8 字节（Night36 §7 已记录），任何「读全文→重写」
都会失败或毁历史，故沿用 day12/night44 的 'ab' 模式并校验旧字节前缀。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N45 行序模型调优"

SECTION = u"""

- 2026-11-20 白天 | N45 行序模型调优（ROADMAP OCR 深水区下一夜）| **原假设被自己的度量证伪，是本夜最重要的结果**。开工时的观察是「头注被 `_cluster_order` 的全局 x 排序切开」，据此写了 `tools/night45_headnote_check.py`，量出 1245 个非主栏框里 161 个（13%）「排在所属列正文之后」，套上「头注归列」原型（P1）后降到 0。**但这是错的**：①该定义把所有非主栏框都当成「必须排在正文之前的头注」，而本书页大量非主栏框是列中/列末割注与手写批注，本就在正文之后；②P1 的构造规则与「违规」定义同源，「重排后=0」是循环论证。改用**与 P1 无关**的列连续性指标（`night45_contiguity.py`：同一列是否连续出现，列定义用生产 `_cluster_order` 同一算法）：**A 生产顺序 659 列零打断（43/43 页每列连续），B=P1 反而 48 处打断、31 页变差、0 页变好 → P1 证伪并已从 `backend/` 完全删除**（含 `KANBUN_OCR_ORDER=headnote` 分支，未留死代码）。**真缺陷另由 I5 定位**（`night45_maincol_order.py`：主栏列对必须右列全先于左列）：544 对里 **2 对颠倒**——p021（右列 x=1135「…天下之無道也」被排到左列 x=1081「久矣天将以夫子爲木鐸」之后，原文应为「天下之無道也久矣、天将以夫子爲木鐸」→**真错**）与 p017（两条 w=39/41 手写批注被 w 判据纳入主栏，非正文）。**机制**：`_cluster_order` 用 x 重叠≥0.4 的**传递闭包**聚列，p021 一个跨列头注（x=1111 w=21）把左右两主栏桥接进同一列单元，单元内只按 y 排序，而两主栏 y 只差 **2px**（215 vs 217）→ 先后由检测噪声决定。**修复**（`backend/ocr_layout.reorder_main_slots` + `main_column_keys`，接进 `_cluster_order`，`KANBUN_OCR_MAINCOL=0` 回退）：**只在列单元内重排主栏框所占的槽位**（按右缘 x 右→左），非主栏框位置逐位不动；只在单元内存在「x 互不重叠的主栏框对」时才动手（上下堆叠的同列长框 x 必然重叠，不触发，普通正文列完全不受影响）。**四个版本都试过并记档**：P1（废弃）/v2 用 h≥0.6hmax 判长框（9 页变化、7 页是无谓改动）/v3 拆子列（修好 p021 但把 p018 改坏：注文碎框分到不同子列、正文排到注文后）/v4 只重排主栏槽位（**采用**）。**影响面**：`night45_prod_equiv.py` 证明生产路径与 v4 逐页完全等价；47 页里**只有 p021 一页顺序变化**，其余 42 页逐位相同，置换与内容多重集不变。**端到端**（`night45_e2e_check.py`，真实 OCR 跑开关 ON/OFF）：p020 56 行**逐行完全相同**（无副作用）、p021 41 行只交换 2 行且方向正确。**GT 门**：`night45_gt_cer_check.py` 把生产顺序套到 Night44 已存档 GT 产品流输出再喂 `eval_ocr_gt.py` → **raw micro 0.3568 / norm micro 0.3053 / macro 0.2566 / 0.2242 全部与基线逐位相同**；1/8 GT 页顺序变化（`ndl_781193_R0000003`）逐行核过是**同类缺陷的修正**（《信長公記》目録 (九)(十) 列 y=281 与 (十一)(十二) 列 y=263 判反，编号小的应在右）。pytest 104→**116**（`tests/test_ocr_night45.py` 12 条：置换/多重集/槽位保持/堆叠不触发/并排纠正/p021 正文验证/归档只变 1 页/I5 只剩 p017 等）。accept45 **PASS**。如实记录：p017 的 1 处 I5 颠倒未修（w 门槛 0.65→0.75 能排除，但会改 2 页主栏框集合且与 `judge_layout` 共用判据，需全本重跑，列为拍板项）；I2 的 3 个过合并单元（p018/p021/p045）仍在（修复只改单元内顺序不改边界，故 I2 修复前后数值相同）；I4=176 口径过宽（多为头注带内相邻批注间的「颠倒」，本无竖排列序）只作诊断不进门禁；未跑全本 47 页 OCR（离线度量已覆盖全部 47 页，端到端只跑应变化/应不变各 1 页）。提交 `4ac432f`，未推远程。
"""


def main():
    with open(PATH, "rb") as f:
        head = f.read()
    if MARK.encode("utf-8") in head:
        print("已存在 N45 段落，跳过")
        return
    before = len(head)
    with open(PATH, "ab") as f:
        f.write(SECTION.encode("utf-8"))
    after = os.path.getsize(PATH)
    print("appended: %d -> %d bytes (+%d)" % (before, after, after - before))
    print("旧字节前缀一致: %s" % (open(PATH, "rb").read(before) == head))


if __name__ == "__main__":
    main()
