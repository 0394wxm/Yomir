# -*- coding: utf-8 -*-
"""night49_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT49）。

SHIFT_LOG.md 在字节 807 处有非法 UTF-8 序列（见 night48_append_shift.py），
只能用 'ab' 二进制追加。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N49 割注阅读顺序实测：右先率 88.5% → 98.6%（真割注 100%）"

BLOCK = u"""

## {mark}

**问题**：Night48 发现 94% 的窄框是双行割注。理论上 `_cluster_order` 会把割注
并进主栏列再按 y 排序，自然得到「上方正文 → 割注(右→左) → 下方正文」。
**这从没被验证过。**

**先纠正上一会话的指标错误**：Q1「两半是否同一列单元」是错指标——两半 x 不相交，
`overlap_x=inter/min(w)` 必然 <0.4，本来就该在不同单元。281/488「不合格」
是指标定义错，不是代码错。正确指标只有一个：**最终扁平顺序里右半是否在左半之前**。

**复刻可信**：`tools/night49_replica_check.py` 把归档（已排序）框喂回复刻，
43/47 页恒等，只有 p021 错位 2 个（Night45 修过的那页）。最终数字改用归档下标
直接比较，不依赖复刻。

**实测（改前）**：filter_off+过滤 432/488 = **88.52%**；filter_on 归档
453/510 = **88.82%**。两线独立、几乎相同。例外全是**紧邻倒置**
（dist −1:38、−2:14、−3:3、−4:1），不是聚列错位。

**机制（关键发现）**：56 对颠倒里 **54 对在同一列单元内**，且
`dy(L−R) = -1..-4` —— **左半顶端只高 1-4px，`sorted(key=y)` 就把左半排到前面**。
严格割注层 25 个颠倒，`dy` **全部为负、无一例外**。这是**排序缺陷，不是聚列缺陷**：
縦書き同一行高应右→左读，1px 是检测噪声，不是排版信息。

**配对质量分层**（Night48 判据太松，混入「短碎片配整列」）：
A 严格割注（紧贴+顶端对齐+等高）296 对 / B 并排不等高 60 / C 松散 132。
A 层改前 271/296 = 91.6%。

**修法**：`backend/ocr_layout.reorder_warichu_slots(items, tol=8)` —— 列单元内把
连续且 `|Δy|≤8` 的框视为同一 y 槽，槽内按右缘 x 降序。插在 y 排序之后、
`reorder_main_slots` 之前；`KANBUN_OCR_WARICHU=0` 可回退。
**安全依据**：同槽内 Δy≤8px，几何上不可能是上下堆叠（真正相接的框 Δy≥半个行高）。
容差选型非拟合：TOL 4–30 是**平坦平台**（99.3%、退化恒 0），8 在平台中央；
|Δy| 直方图 7–12px 是空档。护栏变体（槽内 x 重叠上限 0/0.5/1.0）的
**「垂直堆叠对变序」全部为 0**。

**改后**（单变量隔离，同框集只差一个函数）：537/610 = 88.0% →
**603/610 = 98.9%**，退化 **0 页**，位置变化 266 行。生产口径（过滤后）
434/488 → **481/488 = 98.57%**；filter_on 453/510 → **503/510 = 98.63%**。
**严格割注层 296/296 = 100%**。

**残余 7 对全是伪配对**：dy_top 在 −65 ~ −103，Δh/h 0.36–0.77，
7/7 不满足「顶端对齐+等高」（`十歳集九草` h=63 配整列 h=166 之类）。

**安全审计**：全本 370 个多框 y 槽里实际重排 86 个；槽内含 x 重叠>0.5 的
9 个，**全部是「同一行被检测两次」**（文字高度相似，如 `学父与学於文不同` vs
`学父与学校文不同`），重排只交换两个几乎相同的框；S2（槽内 h<10px）**= 0**。

**GT 门**：产品流跑 8 页 GT → raw 0.3568 / norm 0.3053，**与 Night44/46 逐位相同**。
但**顺序确实变了**（2 页）：GT 按 line_no 对齐，行文本随框绑定，所以顺序变化
CER 测不出来——**这是 CER 门的已知盲区**，本夜用逐页右先率补上了。
两处变化都确认是右→左纠正（`一`x=247/`市川`x=274 → 市川在前）。

**全本影响面**：34/47 页输出序列变化，**全部页的行多重集不变**（无增删、只换序），
位移方向逐条核对全是右→左。

**一个失误（如实记录）**：我误用了无路径的 `python -m pytest -q`，pytest 收集了
`tools/test_ocr.py` 与 `tools/test_ocr_samples.py`——**这两个是脚本不是测试，
导入即跑 OCR 并写文件**，重写了 2 个已跟踪的 `eval/ocr_samples/*_clean__*.txt`。
已 `git checkout --` 恢复，工作区干净。验收口径是 `pytest tests`，以后不跑无路径 pytest。

**数字**：`backend/ocr_layout.py` +46 行（1 个函数 + 常量），`backend/ocr_engine.py`
+10 行（导入 + 3 行调用 + 开关）；新增 14 个可复跑工具 + 12 份证据 JSON +
11 条测试（`tests/test_ocr_night49.py`）；pytest 130→**141**；accept_night 49 **PASS**。

**待拍板**：① CER 门测不了阅读顺序，要不要补独立顺序门（本夜脚本可当基线）；
② `tools/test_ocr*.py` 应排除出 pytest 收集（本夜只记录未改）；
③ 割注配对口径要不要收紧到 A_strict（倾向测量双口径、产品不引入配对检测）；
④ `KANBUN_OCR_WARICHU` 开关保留（与既有三开关一致，建议保留）；
⑤ Night47 §8 / Night48 §11 条目状态不变。
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
