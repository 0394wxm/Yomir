# -*- coding: utf-8 -*-
"""night54_append_shift.py — SHIFT_LOG.md 二进制追加（NIGHT54）。

SHIFT_LOG.md 早期字节含非法 UTF-8 序列，只能用 'ab' 二进制追加，
并以「追加后 old 前缀逐字节不变」作为断言（与 night48-53 同一套做法）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "N54 测试 DB 统一：KANBUN_DB 唯一入口移到根 conftest.py（消灭「死代码环境变量」陷阱）"

BLOCK = u"""

## {mark}

**起因（已提交见 REPORT_NIGHT54.md）**

N52 写 test_export_epub.py 时发现：文件头自设的 KANBUN_DB 在**全套连跑时不生效**
——backend/db.py 首次 import 时读环境变量定 DB_PATH，之后改无效；字母序 test_api
先 import 就赢，其余文件的环境变量行全是死代码。脚枪三面：未来夜班误以为每文件
独立 DB；独立跑与全套跑语义不一致；test_web_mount 独立跑会用**仓库根真实
kanbun.db** 走 init_db（幂等建表无数据写，但不该走到）。

**改法（零生产代码）**：conftest.py 顶部统一分配会话级临时库
（`kanbun_pytest_db_` 前缀）——conftest 先于一切测试模块导入，这里必然赢；
3 个真正写库的测试文件删掉各自的自设块；test_api 新增
`test_db_path_is_conftest_isolated` 锁「DB_PATH ≠ 仓库根 kanbun.db 且带 conftest
前缀」不变式。全库扫描确认设置 KANBUN_DB 的恰为 3 个文件、写库的也只有这 3 个
（lifespan_migration 全 mock、web_mount 只 init_db）。

**验证**：全套 **157→158 passed**（17.28s）；无路径 `pytest -q` **158 passed**
（N50 收集隔离完好）；被改 3 文件 + web_mount/lifespan 独立跑 **全过**
（16/16/6/13）；真实 `kanbun.db` sha256 跑前跑后**逐字节不变**
（`4e1ca376…3571`，5 次运行后复验）。行为语义与改前一致（改前也是全套共享
一个临时库）——消灭的是**静默**，不是共享本身。

**待拍板⑥（新增）**：批量 OCR 作业要不要落库（重启不丢整本书扫描、为「页=章
EPUB」打底）——Night 11 在 main.py:519 有「不做持久化」的明文决定，推翻需用户
点头；建议方案：内存作业语义不变，GET 内存 miss 时回退 DB（纯增量）。
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
