# -*- coding: utf-8 -*-
"""day14_append_shift.py — 把 D13/D14 追加进 SHIFT_LOG.md。

同 day12_append_shift.py：SHIFT_LOG.md 早期条目编码损坏（含非法 UTF-8 字节），
任何「读全文 → 重写」都会失败或毁历史，所以只用二进制追加（'ab'）。

用法：python tools\\day14_append_shift.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "D13 拍板落地"

SECTION = u"""

# —— 2026-11-19 18:30 ～（白天班后段：D13 拍板落地 + D14 Rule E）——

注：本段由 `tools/day14_append_shift.py` 以二进制追加写入，未触碰上方任何历史字节。

- 2026-11-19 18:30 | D13 拍板落地（三条全做） | ①验收门 pytest 口径 `tests/test_api.py`（15 例）→ **全量 `tests`（50 例）**，基线 `MIN_PASSED` 14 → 50（防「删测试换绿灯」）；Night 22 回测 **PASS 6/6**、Night 35 **PASS 5/6+1 skip**，门耗时 24s→26s ②删两个未跟踪旧拷贝 `frontend/src-tauri/sidecar/_internal/`（732 文件/479.3MB）与 `target/release/sidecar/_internal/`（839 文件/496.7MB），共 **1,571 文件 / 976.0MB**；删前取证两者 `main.py` 仍带 `on_event`、无 `lifespan`、dist JS 仍带死全局，证据存 `eval/day13_old_copies.json`，脚本 `tools/day13_purge_old_copies.py`（默认 dry-run）③`VITE_API_BASE` 尾斜杠归一化**保留不回退**（唯一生效路径是空串默认，对空串是恒等） | 报告 REPORT_DAY13.md，提交 573709a + 2a5091b

- 2026-11-19 19:10 | D14 Rule E DONE（本段最大产出） | 在 **Rule D 之后的基线**（25.201）上重新解剖 1000 条，换角度查 `expected - got` 的汉字频次差：**皆 36/0、既 25/0、唯 17/0、豈 10/0、猶 33/1**（expected 次数/引擎输出次数）——引擎系统性地把这些汉字写成假名。5 条合表上线：`みな→皆 / すでに→既に / なお→猶お / あに→豈に / ただ→唯だ`，**avgDist 25.201 → 25.046（-0.155），改善 92 / 变差 0**，真机与离线**逐位一致**，pytest 50 → **65 passed**（门基线同步 50→65） | 关键发现：**词形不是裸汉字**。第一版做 `すでに→既` 时测试抓出 expected 是 `既に`（20/25）、`猶お`（29/33）、`豈に`（10/10）、`唯だ`（16/17），只有 `皆` 是裸字。裸汉字合计 -0.099（55 改善），按词形 **-0.155（92 改善）**——改善条目翻倍。**两次失败如实入档**：①第一版词界护栏用「后接假名就挡」，导致相邻候选词互相干扰（`皆すでになおあにただ` 里 すでに 的后面是 なお 的「な」），二次应用还不幂等 → 改成**显式更长词清单** `E_LONGER_WORDS` ②测试探针 `みなすでに` 本身有歧义（す 同属 みなす/すでに），换成两个独立探针。被拒绝（变差>0）：なかれ→勿（1/8）、いずくんぞ→焉（5/19）、また→亦（9/2）、ごとし→如（护栏下 0 改写） | 报告 REPORT_DAY14.md，提交 c147d71 + 6739edd

## D13/D14 数字汇总

| 指标 | D13 起点 791e451 | 现在 6739edd | Δ |
| --- | --- | --- | --- |
| pytest | 50 passed | **65 passed** | +15 |
| 门 pytest 口径 | test_api.py（15 例） | **tests 全量（65 例）** | — |
| 规则引擎 avgDist（1000 条） | 25.201（Rule D） | **25.046（Rule E）** | **-0.155** |
| 改善/变差（vs D11 基线） | — | **92 / 0** | — |
| 旧 sidecar 拷贝 | 1,571 文件 / 976MB | 0 | 已删 |
| 验收门 22 / 35 | — | **6/6 PASS / 5/6+1 skip** | — |

## 待拍板（D13/D14 之后）

1. 门的 `MIN_PASSED` 现在硬编码 65——以后每加测试要手动上调（安全方向：落后不会误放，只是不再是「一条都不许少」）
2. `VITE_API_BASE` 尾斜杠归一化没有专门单测（本仓库没有 JS 测试框架）
3. 两个 `kanbun-sidecar.exe` 仍留着（删了会让 Tauri resources 引用悬空，下次打包重建更安全）
4. Rule E 的 `E_LONGER_WORDS` 是人工清单，语料外遇到新长词（如 みなもと 以外的 みな〜）需要补
5. 「また→亦」0 变差方向但有 2 条变差（亦/又 同音），需要词级消歧才能做
"""


def main():
    with open(PATH, "rb") as f:
        head = f.read()
    if MARK.encode("utf-8") in head:
        print("已存在 D13/D14 段落，跳过（避免重复追加）")
        return
    before = len(head)
    with open(PATH, "ab") as f:
        f.write(SECTION.encode("utf-8"))
    after = os.path.getsize(PATH)
    print("appended: %d -> %d bytes (+%d)" % (before, after, after - before))
    print("旧字节前缀一致: %s" % (open(PATH, "rb").read(before) == head))


if __name__ == "__main__":
    main()
