# -*- coding: utf-8 -*-
"""night51_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT51）。

SHIFT_LOG.md 早期字节含非法 UTF-8 序列，只能用 'ab' 二进制追加，
并以「追加后 old 前缀逐字节不变」作为断言（与 night48/49/50 同一套做法）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N51 GT 门 --out 参数：夜班跑门不再覆盖 Night49 归档（N50 待拍板② 落地）"

BLOCK = u"""

## {mark}

**任务：`tools/night49_gt_run.py` 加 `--out`（已提交 `5560080`）**

Night50 待拍板② 的落地。两个选项里选了 **--out（默认行为不变）**，不选按夜命名：
① 按夜命名需要知道「当前第几夜」，脚本无从得知——终究要传参，直接传输出路径最诚实；
② 改默认输出路径会断掉既有调用方（`night49_gt_diff.py` / `night49_gt_boxes.py`）与
`accept_night.py` 的历史可回测口径；③ `--out` 是纯增量：缺省赋值行一字未动，
不传参 = 与 Night49 逐位一致。相对路径以**仓库根**为基准（与脚本内其它路径同口径）。

**三点验证**：
① 实跑 `--out eval/night51_gt_lines.json`（GT 8 页，`unmatched_no` 全 0），
`eval/night49_gt_lines.json` sha256 跑前跑后**同为**
`ff21e4fa7d749c61f1fbe60ff753713941289a4a6d370feaabdedb7e60bd9cde`——**逐字节不变**，
「跑门必覆盖归档」副作用就此消除，也不再需要 `git checkout --` 恢复；
② GT CER **raw micro 0.3568 / macro 0.2566，norm micro 0.3053 / macro 0.2242**
——与 N44/46/49/50 四夜**逐位相同**（92 行，无 unmatched 警告）；
③ night51 与 night49 归档**逐字段比对 = ONLY_RECOGNIZE_SEC_DIFFERS**
（除 8 页 recognize_sec 外差异数 0，含 92 行 lines 的 line_no/x/y/w/h/text 全比），
反证 OCR 输出确定性。比对脚本在仓库外 Temp（不入库），结论存
`eval/night51_lines_diff.txt`。

`python -m pytest tests -q` = **141 passed**（改动后复跑 15.20s）。
`--help` 参数面证据见 REPORT_NIGHT51.md §4.4。未改任何 `backend/` 代码。

**待拍板更新**：N50 ②已解决；③（night50_* 证据是否入库）、①（order_rate 阈值）、
Night49 §16 ③④ 原样保留。本夜新增 `eval/night51_*` 5 个证据文件已随夜提交。
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
