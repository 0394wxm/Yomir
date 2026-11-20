# -*- coding: utf-8 -*-
"""conftest.py — pytest 根配置（NIGHT50 建 / NIGHT54 扩）。

**为什么存在**：`tools/` 下有 4 个「名字像测试、其实是脚本」的文件——
它们**在模块导入时就执行 OCR / 加载引擎 / 写文件**，不是 pytest 测试：

  tools/test_ocr.py           导入即加载引擎 + 识别 1 页（写 stdout）
  tools/test_ocr_samples.py   导入即识别 4 页 × 2 模式，**重写
                              eval/ocr_samples/*_clean__*.txt（已跟踪文件）**
  tools/test_ocr_chain.py     需要 8000 端口后端在跑
  tools/test_udkundoku.py     导入即加载 udkundoku 引擎（44s+）

2026-11-20（Night 49）踩过：无路径跑 `pytest` 会把它们当测试收集并执行，
改写了两个已跟踪的样本 txt。本文件把它们排除出**任何** pytest 收集，
包括显式 `pytest tools/`。脚本本身仍可直接
`python -X utf8 tools/test_ocr_samples.py` 运行，行为不变。

配套的 `pytest.ini` 里还有 `testpaths = tests`（无路径时只跑 tests），
两者是双保险。

**NIGHT54 追加：测试 KANBUN_DB 统一在这里分配**。机制：`backend/db.py` 在
**首次 import** 时读 `KANBUN_DB` 定 `DB_PATH`（之后改环境变量无效）；
conftest 先于一切测试模块被 pytest 导入，所以这里定的值必然赢。
在此之前各测试文件自设环境变量，全套连跑时只有字母序第一个 import
backend 的文件（test_api.py）真正生效，其余文件的环境变量行是死代码——
让人误以为「每文件独立 DB」。现在：会话内全部测试共享一个临时库，
与仓库根 kanbun.db（真实运行数据）物理隔离；逐文件独立跑走同一入口。
"""
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="kanbun_pytest_db_")
os.environ["KANBUN_DB"] = os.path.join(_TMP, "test.db")

collect_ignore = [
    "tools/test_ocr.py",
    "tools/test_ocr_samples.py",
    "tools/test_ocr_chain.py",
    "tools/test_udkundoku.py",
]

# 显式指定 tools/ 目录时也不收集上述文件（collect_ignore 只对同目录
# 生效，这里再按 glob 兜一层，防有人 `pytest tools/`）
collect_ignore_glob = [
    "tools/test_ocr.py",
    "tools/test_ocr_samples.py",
    "tools/test_ocr_chain.py",
    "tools/test_udkundoku.py",
]
