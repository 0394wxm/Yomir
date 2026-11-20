# -*- coding: utf-8 -*-
"""night60_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT60）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N60 评测扩 4000：/syubu/ 剩余栏目补抓 1203 对（N57 歴代/唐詩選从未访问）；golden_4000 前缀断言过；规则 13.889 精确19，前3000 vs night58 diff=0；新增段又出1条應error（⑬论据+1）；guwenbert 6.639 vs 规则 6.896"

BLOCK = u"""

## {mark}

**来源盘点**：N57 抓取器凑满 1100 对即停（196 页=shikyo102+shijin999），
**歴代/唐詩選内容页一个都没访问**。补抓（night60_scrape_left.py，N57 同款解析
expected 一字不改，限速 0.4s）：184 页 **1203 对** / 471s（shijin 剩页为主，
shijin 索引本身链到 toushisen 内容页）；对 golden_3000 去重后 **0 重复**。

**golden_4000**：前 3000 条与 golden_3000 **逐条相等且顺序一致**（构建断言 +
tests/test_golden_4000.py 3 条双保险）；新增 1000 = /syubu/ 补抓 1000；
total 4000 / id 全唯一 / 白文唯一 3975；**新增分档 ≤20字 1000（又全是诗短句，
构成注意第三次适用）**；文体全景 漢詩 1867。

**规则引擎全跑**（132s，D/E/F/G/H + SHINJITAI 30 对）：**avgDist 13.889、
精确 19/3998、error 2**。**确定性对照：前 3000 条 vs night58 归档 diff=0**
（跨夜跨进程第四次）。整体 13.889 < 16.219 是构成效应（新增段 100% ≤20字），
不能读成引擎变好；分档 ≤20字 7.840 / 21-40 21.742 / 41-60 37.162 / >60 63.845。

**error 2 条**：toushisen135-12（已知）+ **toushisen043-16「應照離人粧鏡臺」
同类應(必要) KeyError——N59 ⑬「非孤例」论据被扩语料直接证实**；
guwenbert 路径同行同败（kundoku 翻译层共享）。

**guwenbert 新增段**（离线 864s）：999 OK / avgDist **6.639** vs 规则 **6.896**，
逐条 **规则 291 / guwenbert 373 / 持平 335**（略优但差距 0.257=3.7%，仍同量级；
「接不接 guwenbert」维持 D16 产品拍板）。

pytest **190→193**（+3 test_golden_4000）；accept60 PASS（提交前 repo_clean
如实 FAIL，提交后终跑）。GT 门零 backend 改动 → N58 当夜实测覆盖。
待拍板新增 **⑭** golden_4000 登记/默认口径切换（同 ⑨ 结构）、
**⑮** /syubu/ 还剩 ~270 页 + 评测集偏科警告（漢詩 1867 全短句）。
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
