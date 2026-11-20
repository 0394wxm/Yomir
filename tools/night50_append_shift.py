# -*- coding: utf-8 -*-
"""night50_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT50）。

SHIFT_LOG.md 早期字节含非法 UTF-8 序列，只能用 'ab' 二进制追加，
并以「追加后 old 前缀逐字节不变」作为断言（与 night48/49 同一套做法）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N50 验收体系两处补强：pytest 收集隔离 + 顺序测量门（只测量不判死刑）"

BLOCK = u"""

## {mark}

**任务 A：pytest 收集隐患（已提交 `d99dd8f`）**

`tools/test_ocr.py` / `tools/test_ocr_samples.py` 是**脚本不是测试**：导入即加载
OCR 引擎并写文件，其中 `test_ocr_samples.py` 会重写 2 个**已跟踪**的
`eval/ocr_samples/*_clean__*.txt`。Night49 已踩过一次（无路径 `pytest` 收集并执行它们）。

修法两层：根目录新建 `conftest.py`（`collect_ignore` + `collect_ignore_glob` 列全 4 个
脚本文件，后者兜 `pytest tools/` 显式路径）+ 新建 `pytest.ini`（`testpaths = tests`，
让无路径 `pytest` 根本不进 `tools/`）。两层冗余：任一层失效另一层独立拦住。

**三点验证**：① 无路径 `python -m pytest -q` → **141 passed**，`--collect-only` 显示
**tools collected: 0**、收集耗时 **3.30s**（修前同类收集 306s——那 300 秒就是在跑 OCR）；
`eval/` **328 个已跟踪文件 sha256 逐个不变**（快照比对 `verdict: IDENTICAL`）；
② `pytest tests` 仍 **141 passed**；③ 两个脚本直接运行仍正常（16 行 / 8 条输出）。
脚本按设计会重写样本 txt，跑完 `git checkout --` 恢复并复验哈希 IDENTICAL。
验证前后各做 `git status --porcelain --untracked-files=no`，均为 `(none)`。

**任务 B：顺序测量门（`tools/accept_night.py` 第 7 项 `check_order_rate`）**

Night49 的证据：改了 34/47 页行序，**GT 92 行 CER 逐位不变**（0.3568/0.3053）——
**CER 对阅读顺序是盲的**，现有 6 项门一个都不会因此响。所以补一个独立指标。

口径实现单独成文件 `tools/night50_order_rate.py`，**直接 import
`tools/night49_final.py` 的 `find_pairs` / `order_of`**（连版面过滤、`_main_group`、
wmed 取法都同源）——口径分叉就没有可比性。两条线：`off` = filter_off 归档 + 离线
套版面过滤（生产口径）、`on` = filter_on 归档（交叉核对）；严格层 A_strict 判据与
`night49_pair_quality.py` 逐字一致。

门的行为按任务书钉死：**进程内导入 `measure()`，不二次运行脚本、不写文件、
不覆盖已存档 json**；输出右先率 / 严格层率 / 退化页数；**只有 pass 与 skip 两条返回
路径，函数体内一次都没调用 `c.fail()`**——数值再低也不改 verdict。

**实测（`accept_night.py 50`）**：
```
[PASS] order_rate   割注右先率（只测量，不判死刑）
   off 右先率 481/488 = 98.57%（基线 98.57%，差 +0.00pp）；严格层 296/296 = 100.00%；退化页 0
   on  右先率 503/510 = 98.63%（基线 98.63%，差 +0.00pp）；严格层 293/293 = 100.00%；退化页 0
```
与 Night49 报告逐位一致，**0 退化**。

**实现踩的两个坑（记录备查）**：`night49_final.py` 在**模块级**调
`sys.stdout.reconfigure()`，被 `redirect_stdout(StringIO())` 包住导入就
`AttributeError`（StringIO 没有 reconfigure）→ 改成 `_load_n49()` 缓存 + 在真实
stdout 下预导入；它还在模块级把 `sys.argv` 截成 `[argv[0]]`，会把验收门的
`night` / `--no-pytest` 参数抹掉 → 载入前后存/取 `sys.argv` 快照。

**GT 门**：本夜未改任何 `backend/` 代码，CER 必然不变；仍实跑 8 页 GT 作证据：
**raw micro 0.3568 / macro 0.2566，norm micro 0.3053 / macro 0.2242 —— 与 N44/46/49
逐位相同**，8 页 `unmatched_no` 全 0。
**一处副作用（已处理）**：`night49_gt_run.py` 把结果写回**已跟踪**的
`eval/night49_gt_lines.json`，跑完该文件被覆盖；逐行 diff 确认**只有 8 页的
`recognize_sec` 变了**，`lines`/`layout_filtered`/`junk_filtered`/`unmatched_line_no`
逐项相同（反证文本结果确定）。本次结果另存 `eval/night50_gt_lines.json`，
Night49 归档 `git checkout --` 恢复。

**待拍板**：① order_rate 要不要转成判死刑门、阈值取多少（建议生产口径下限 95% /
严格层必须 100% / 退化页 >0 即 FAIL 三选一，但建议先观察几夜波动）；
② `night49_gt_run.py` 应加 `--out` 或按夜命名，否则每次跑 GT 门都覆盖上一夜归档；
③ `eval/night50_*` 11 个临时证据文件要不要入库（当前保留磁盘不入库，与 Night4x 一致）；
④ Night49 §16 的 ②已修（A）、①已补测量版，③④仍未定。
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
