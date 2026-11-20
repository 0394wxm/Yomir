# -*- coding: utf-8 -*-
"""night57_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT57）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N57 评测扩到 3000：新栏目 /syubu/ 詩経+漢詩 969 对 + 平行剩余 31；规则全跑 16.321，guwenbert 五五开"

BLOCK = u"""

## {mark}

**来源盘点**：kanbun_parallel.json（1705 对，100% /koji/ 故事页）在 golden_2000
里**已用尽（剩余 0）**；day16_pool 只剩 31 条 → 新增只能抓 kanbun.info 新栏目。
sitemap 实测新栏目 = **/syubu/（集部：詩経 shikyo_*、唐詩選、歴代 reki_*、詩人別
shijin_{{a..ra}}）**；keibu 只有論語/大学/孝経（已用尽）、shibu01-02 是 404 死链。

**抓取**（night57_scrape_syubu.py，D16 同款解析=剥 ruby/去空白，expected 一字不改，
限速 0.4s）：203 页 **1101 对**（詩経 102 + 漢詩 999），819s。推销页（honbun02
结构）0 对自然跳过。

**golden_3000**：前 2000 条与 golden_2000 **逐条相等且顺序一致**（构建断言 +
tests/test_golden_3000.py 3 条双保险）；新增 1000 = 平行剩余 31 + 詩経 102 +
漢詩 867（去重 skipped 93）；total 3000 / id 全唯一 / 白文唯一 2975（base 25 条
内部重复原样保留）。

**规则引擎全跑**（98s，D/E/F/G 全链）：**avgDist 16.321、精确 15/2999**、
error 1（toushisen135-12 應知黃綺心——**MeCab 词典缺「應」助動詞 token**，
guwenbert 同条同败，引擎层缺口如实入档）。
**两个强证据**：① 前 2000 条重跑 vs day17 归档**输出文本差异行数 = 136，
恰为 Rule G 改写行数**；② 前 2000 avgDist **20.916 与 N55 离线预测逐位一致**
（127 改善/0 变差）——API 全链与离线真函数第三次逐位等价。
分档单调 8.39/21.84/37.30/64.08；詩経 5.206/漢詩 7.247 都 100% ≤20 字短句
（N56 构成警告适用，不能读成「引擎擅长漢詩」）。

**guwenbert 新增段**（离线 1127s）：999 OK / avgDist **7.075** vs 规则 **7.122**
（Δ<0.05），逐条 **规则 306 / guwenbert 325 / 持平 368 五五开**——与 D16 同型，
「接不接 guwenbert」仍是 D16 产品拍板。

pytest **172→175**；accept57 PASS。待拍板新增 ⑨ golden_3000 登记进验收门
（需先统一 list 形状）+ 默认评测口径切换 ⑩ 「應」舊字体进引擎前要不要归一
（会改评测输出需拍板）。
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
