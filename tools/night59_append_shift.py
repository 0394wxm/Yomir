# -*- coding: utf-8 -*-
"""night59_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT59）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N59 「應」调查闭环（只诊断零代码）：缺的是 udkundoku AUX 活用表条目而非 MeCab token；應→応 预处理实证 no-op（⑩建议否决结案）；新增拍板⑬ AUX补1条"

BLOCK = u"""

## {mark}

**三层定位**（night59_repro）：MeCab 词典**有**應 token（v,助動詞,必要,應/应,AUX,
Mood=Nec——N57「词典缺token」定性不成立）；udkanbun 两形态解析等价（新字体応的
**lemma 也是應**）；失败在 **udkundoku/auxiliary.py 的 AUX 25 键**——`v,助動詞,必要`
组只有 儀/宜/須，**唯独缺 應**。API 对该输入返回「訓読処理失敗: KeyError」=用户可见失败。

**全库扫描**（night59_scan）：3000 条 hakubun 助動詞 token 13 组 lemma×xpos、
509 行——**12 组覆盖、唯一缺 應×1行**；含應 hakubun 18 行（17 行名詞/動詞用法全部
正常）；1756/3000 行含旧形字全部可解析——旧字体不是缺陷源。

**應→応 预处理模拟**（night59_sim，18 行走 main.py 同款全链）：**完全 no-op 且
不修复**（17 行逐字节不变、1 行同 KeyError、语料外 4 探针不变）——lemma 不变所致。
**N57 拍板⑩ 的预设方案实证无效，建议否决结案。**

**内存补丁对照**（night59_aux_patch_probe，零落盘）：AUX 补
`應,v,助動詞,必要,* = 須同值` 1 条 → toushisen135-12 从 error 变
「黄の綺心を知るべし」（dist 4，expected 応に前缀引擎不给，如实记录）；
**其余 2999 行逐字节不变、0 新 error、幂等**——纯增益。
**新增拍板⑬**：要不要上这个引擎层补丁（路径 a=backend runtime 2 行 /
b=site-packages 直接改），等用户拍板，未动。

pytest 190 维持；GT 门零改动（N58 当夜实测覆盖）；引擎三包零改动（红线自查）。
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
