# REPORT_NIGHT54

## 0. 一句话结论

测试基建夜：**测试 KANBUN_DB 统一由根 conftest.py 分配**——消灭「各测试文件自设
DB 环境变量，全套连跑时只有字母序第一个真正生效，其余是死代码」的静默陷阱
（本夜 N52/N53 写测试时亲自踩到才看清）。新增 1 条隔离不变式测试，**全套
157→158 passed**；3 个被改文件独立跑全过；**真实 kanbun.db sha256 跑前跑后逐字节
不变**；无路径 `pytest -q` 158 passed（N50 的收集隔离未被破坏）。

## 1. 为什么做这个（队列推演 + 排除过程）

产品深水区（N51-70）其余项全部是门禁/拍板/人眼项：账号与订阅、历史云同步、
机构授权（门禁）、PDF（待拍板①）、手机版（需真机人眼，离线不可验）。OCR 深水区
N47/N48 已负结果收束。order_rate 阈值 = 待拍板①不动。

**候选里评估过两个，一个做了一个明确不做：**

- **批量 OCR 作业落库（重启不丢整本书扫描）**——有价值且桩引擎可测，但
  `backend/main.py:519-520` 有 Night 11 的**明文设计决定**：「作业只存在进程内存里
  （重启即丢）……所以不做持久化」。推翻一条记录在案的设计决定不该夜班擅自做，
  **降级为待拍板⑥写进报告**。
- **测试 DB 统一（本夜）**——本夜 N52 写 `test_export_epub.py` 时发现：自己文件头
  设置的 `KANBUN_DB` 在全套连跑时**根本不生效**（`backend/db.py` 首次 import 时读
  环境变量定 `DB_PATH`，之后改无效；字母序 test_api 先 import 就赢了）。这是真实的
  脚枪：①未来夜班以为自己有独立 DB，实际共享；②任何测试文件独立跑与全套跑的
  DB 语义不一致；③`test_web_mount.py` 独立跑时甚至会用**仓库根真实 kanbun.db**
  跑 `init_db`（幂等建表，无数据写入——但不该走到那一步）。零生产代码、完全可验。

## 2. 改动

| 文件 | 内容 |
| --- | --- |
| `conftest.py` | 顶部新增：`KANBUN_DB` 会话级临时库（`kanbun_pytest_db_` 前缀 mkdtemp）。机制写在 docstring：backend/db.py 首次 import 定 DB_PATH，conftest 先于一切测试模块导入 → 这里必然赢 |
| `tests/test_api.py` | 删自设 DB 的 2 行（`_TMPDIR` 保留——`test_ocr_missing_runtime_message_shape` 用它造假 OCR 源目录）；新增 `test_db_path_is_conftest_isolated` 锁不变式（DB_PATH ≠ 仓库根 kanbun.db 且带 conftest 前缀） |
| `tests/test_export_epub.py` | 删自设 DB 块（tempfile import 一并删） |
| `tests/test_ocr_batch_progress.py` | 删自设 DB 块（原为 setdefault，全套连跑同样是死代码） |

写库的测试文件共 3 个（全库扫描确认，见 §3.1）；`test_lifespan_migration.py`
全部 mock 了 `db.init_db`/`_load_engine` 不碰真库；`test_web_mount.py` 只触发
`init_db`（幂等建表、无数据写）。

## 3. 验证（全部离线）

### 3.1 全库扫描（依据）

`tests/*.py` 18 个文件里设置 `KANBUN_DB` 的恰为 3 个（test_api / test_export_epub /
test_ocr_batch_progress）；实际 import backend.db（经 backend.main）的 5 个；
其余 OCR/规则测试不触 DB。

### 3.2 四组运行 + 真实库哈希

```
python -m pytest tests -q                → 158 passed（17.28s）
python -m pytest -q（无路径）             → 158 passed（15.82s，N50 收集隔离完好）
pytest tests/test_api.py -q 独立          → 16 passed
pytest tests/test_export_epub.py -q 独立  → 16 passed
pytest tests/test_ocr_batch_progress.py -q 独立 → 6 passed
pytest tests/test_web_mount.py tests/test_lifespan_migration.py -q → 13 passed
```

真实 `kanbun.db` sha256 **跑前跑后同为**
`4e1ca3763e8454b55fe38715c1068f053cad05fbb7233f80d89486005eb93571`（全套 + 4 组独立跑共 5 次运行后复验）。

### 3.3 行为语义说明（如实）

统一后「会话内共享一个临时库」的**实际语义与改动前完全一致**（改前也是全套共享
test_api 的临时库）——本夜消灭的不是共享本身，而是**静默**：现在唯一入口在
conftest，注释写明机制，且有测试锁「绝不指向仓库根 kanbun.db」。
`test_db_persistence`（test_api）的 before+1 动态计数与字母序顺序不受影响。

## 4. 待拍板（编号 = 下一班的下单清单）

1-5：N52 §6 三条 + N53 两条，原样保留。
6. **新增：批量 OCR 作业要不要落库**（重启不丢整本书扫描、并为「页=章 EPUB」打底）
   ——Night 11 有「不做持久化」的明文决定（main.py:519），推翻需用户点头；
   建议方案：内存作业语义不变，GET 在内存 miss 时回退 DB（纯增量）。

## 5. 禁止事项自查

未发图 / 未改 eval 基线 / 未重跑全本 OCR / 未碰 N9、16-20 / 未动 order_rate 与
night50_* / 未改生产代码（backend/ 本次零改动）/ 心跳二进制追加前缀断言不变 /
本地提交不推远程 ✓
