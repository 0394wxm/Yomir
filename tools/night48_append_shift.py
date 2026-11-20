# -*- coding: utf-8 -*-
"""night48_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT48）。

SHIFT_LOG.md 在字节 807 处有非法 UTF-8 序列，只能用 'ab' 二进制追加。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N48 窄框（割注）判据的否证"

BLOCK = u"""

## {mark}

**起点**：Night44 §7 记着 p044 有两个页脚框没滤掉（`一元条同不出旨…` h=150、
`大金表主` dy −40），当时标「判据已知边界，未修」。本夜想给它一个交代。

**第一个发现就推翻了定性**：这两框的 `dy`（中心相对主栏底）是 **−70.0 / −40.5**
—— 中心在主栏底**之上**。页脚判据 `cy >= y_max − 12` 几何上不可能抓到它们。
全本 47 页 `dy > 0` 的保留框 = **0**，即**页脚判据没有漏滤**。
Night44 那两框不是「页脚边界」，是**版心内窄条**。

**第二个发现是根本原因**：全本窄框（`w < 0.6×主栏宽`）有 **1118 框 / 40 页**，
其中 **1047（94%）能配成对**——并排、y 高度重合、两框宽+间隙≈主栏宽。
**这是双行割注本**：经文全宽，注文半宽双行。「窄」是**注文的版式定义**，
不是噪音特征。逐页成对率多在 80–100%（p008 28/28、p024 35/35、p039 36/35…）。

**三条几何路线全部否决**：
- R1「窄框=噪音」：阈值 0.35 就删 584 框，其中 **291 带句读**（`'芸、即文芸、今之所謂'`
  `'是日是、是レ幾日也、来字、'`）—— 删的是注文。
- R2「未配对窄框=噪音」：71 个未配对里 **29 个是割注**（C4），C5 还混着
  `'者、猶報道、'`（带句读真正文）和 `'汝'`/`'女'`（割注单字）。
- R3「未配对+贴页边」：只命中 16/71，其中 **5 个全高割注 → 误伤 31%**。
  「贴栏」在矮框 51/60、全高 6/11 —— 两类都贴栏，没有区分力。

**与 Night47 互为印证**（不是重复）：N47 用假名比率切、N48 用宽度+配对切，
两条独立路径都撞到同一堵墙——**手写書き入れ与版心内的注文在几何与文本上全部重合**。
合起来可以定论：**版心内残留噪音没有纯离线判据能干净分离**。
Night43 的设计原则（纯几何只处理版心之外）第三次得到独立确认。

**顺带**：p044 那两个框（`一元条同不出旨` w=18/主栏54、`大金表主` w=13/主栏54）
确认**未配对**，是手写書き入れ，与 Night44 的人读结论一致，只是定性要改。

**数字**：生产代码**零改动**；新增 6 工具 + 5 证据 JSON + 6 测试；
pytest 124→**130**；提交 fd29c6c。

**待拍板**：① Night44 §7 的「页脚边界」定性要不要在 ROADMAP 订正
（本夜只在报告里订正，历史条目未动）；② 版心内残留噪音（本夜 71 框 + N47 的 48 框）
修不修——倾向「不修 + UI 让用户删」，纯算法修在无标注数据下只会重复失败；
③ 双行割注这个几何事实能不能产品化（「只显示经文/隐藏注文」是现成信号，独立设计）。
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
