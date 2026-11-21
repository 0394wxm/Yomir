# -*- coding: utf-8 -*-
"""night62_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT62）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N62 评测扩 7908：全站剩页 1279 页抓尽（ok 3579 + paren 257 未启用）；kanbun.info 干净对枯竭实证（koji 剩 501 页仅 1 新、keibu 剩 165 页 0 新）；10000 不可达→用户拍板方案 A；规则 13.241 精确 25、前 4000 vs night60 diff=0；guwenbert 新增段 12.466 vs 规则 12.577 五五开"

BLOCK = u"""

## {mark}

**盘点与拍板**：sitemap.xml 全站 2696 URL（上一会话中断前的独立盘点产物
night62_sitemap_* 与本夜 night62_inventory 交叉印证，保留入档）。真正有新对的
剩页只有 syubu 317 / shibu02 216 / syubu02 42 / shibu01 10；koji 剩 501 页、
keibu 剩 165 页的对**全部**与 golden_4000 重复。加上 N57/N60 池剩 330（day16_pool、
golden_rongo_full、kanbun_parallel 与 golden_4000 白文完全重叠，并入 0 增益），
约束内上限 ≈3900 << 6000。**用户拍板方案 A：扩到约束内上限、按实数命名、
缺口与第二语源挂拍板**。

**抓取**（night62_scrape_10k.py，N57 同款解析 expected 一字不改，限速 0.35s，
断点续跑）：1279 页全量 / 6237s → **ok 3579 + paren 257**（白文含（），
N57 起约定不启用，只标记留档）；syubu 2189 / shibu02 1142 / syubu02 225 /
shibu01 22 / **koji 1** / **keibu 0** / history+misc 0；拒绝 dup_golden 668 /
dup_batch 5 / empty 1。**⑮（/syubu/ 剩 ~270 页）本夜清零。**

**golden_7908**：前 4000 条与 golden_4000 **逐条相等且顺序一致**（构建断言 +
tests/test_golden_7908.py 3 条双保险）；新增 3908 = 池剩 330 + 剩页 3579 − 跨源
重复 1；新增分档 ≤20字 3286 / 21-40字 361 / 41-60字 136 / >60字 125（**长文
构成显著改善**，非 N60 的清一色短句）；新增文体 漢詩 2518 / その他（子部
老子・孙子・墨子・荘子等）1389 / 故事 1。

**规则引擎全跑**（142s，D/E/F/G/H + SHINJITAI）：**avgDist 13.241、精确 25/7905、
error 3**。**确定性对照：前 4000 条 vs night60 归档 diff=0**（跨夜跨进程第五次）。
新增段 12.577 / 精确 6；子部（その他）首次基线 avgDist 22.315、shibu02 栏目
24.691。**error 3 条全是 應,v,助動詞,必要 KeyError**：toushisen135-12、
toushisen043-16（已知）+ **新增 zasshi-2「應知故鄉事」——N59 ⑬「非孤例」论据
再 +1**；guwenbert 路径同败（kundoku 翻译层共享）。

**guwenbert 新增段**（离线 2752s）：3907 OK / avgDist **12.466** / 精确 3 vs
规则 **12.577** / 精确 6；逐条 **规则更好 1366 / guwenbert 更好 1390 / 持平
1151**（差距 0.111=0.9%，仍同量级；「接不接 guwenbert」维持 D16 产品拍板）。
h2h 首版有 gmap 误用 rdoc 的复制粘贴 bug，已修复重跑（归档为修复后结果）。

pytest **193→196**（+3 test_golden_7908）；accept62：提交前 --no-pytest 预跑
repo_clean 如实 FAIL（验收门设计行为），提交后终跑 PASS。
待拍板新增 **⑯ 第二语源**（kanbun.info 枯竭后扩到 10000 的唯一路径）、
**⑰ paren 对 257 条是否启用**（N57 质量约定变更，重抓已见页可再收 ~600-700）。
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
