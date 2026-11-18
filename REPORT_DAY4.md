# REPORT_DAY4.md — D4：cached 2.4s 离群值定位

日期：2026-11-18 / 班次：白天 D4 / 产物：`REPORT_DAY4.md`、`eval/day4_outlier_data.json`、
`tools/day4_*.py` 六个探针、`backend/main.py` 分段计时（env 门控，默认关闭）

**结论先说：离群值 100% 来自写库 `db.save_kundoku`，引擎侧全程 0–30ms。根因是 D: 盘的 fsync 延迟
（85–180ms/次），而一次请求要付 3–4 次 fsync。本次只定位，未重构。**

---

## 1. 症状与复现

原症状：/api/kundoku 在 cached 路径上偶发 2.4s 级响应。

今天的 20 连调（10 unique + 10 cached，5 个句子因假名占比高走 kana 早退、不计入）：

| 阶段 | n | median | max | 其中 db 段 median | db 段 max |
| --- | --- | --- | --- | --- | --- |
| unique | 8 | 790.5ms | 987.7ms | 781.0ms | 982.2ms |
| cached | 8 | 763.9ms | **1095.4ms** | 759.6ms | **1094.9ms** |
| cached（跳过写库） | 10 | **0.7ms** | 0.8ms | 0.0ms | 0.0ms |

读完三行的关系就结束了：cached 与 unique 几乎一样慢（缓存没起任何作用），而把写库摘掉之后
整个请求变成 **0.7ms**。也就是说「cached 2.4s」这个命名本身就是误导——慢与缓存命中与否无关。

关于 2.4s：今天这轮的最大值是 1.10s，没有复现出 2.4s 那么高。D: 盘的 fsync 抖动很大
（下面第 5 节同一段代码两次测出 85.1ms 与 180.3ms），2.4s 属于同一分布的长尾，
不是什么新的机制。这一点如实记录，不硬凑。

## 2. 分段计时：慢在哪一段

`backend/main.py` 加了 `KANBUN_TIMING=1` 门控的分段累加（engine / merge / kaeriten /
translate / style / glossary / db），默认不开启，生产路径行为与性能不变。

20 次调用中，每次的形态都一样：

```
cached #02 total 686.7 | engine 0.0 | merge 0.0 | kaeriten 0.0 | translate 0.0 | style 0.0 | glossary 0.6 | db 686.0
cached #03 total 1049.5 | engine 0.0 | merge 0.0 | kaeriten 0.0 | translate 0.0 | style 0.0 | glossary 0.5 | db 1048.8
unique #03 total  564.6 | engine 30.2 | merge 0.0 | kaeriten 0.1 | translate 0.7 | style 0.0 | glossary 0.6 | db 532.9
```

- 引擎侧峰值 **30.2ms**（MeCab 首句），其余 0–7ms。
- `db` 段在 532–1095ms，占 `total` 的 **97–100%**。
- `glossary` 0.5–4.3ms，`style` 恒为 0（merge 关闭时短路）。

## 3. 消融：把 db 摘掉

同一句 `宋人有耕田者。田中有株、兎走りて株に触る。`，各 10 次，用 monkeypatch 替换
`backend.db.save_kundoku`：

| 组 | n | min | median | max | db median |
| --- | --- | --- | --- | --- | --- |
| A. 正常路径（写库） | 10 | 350.5 | 613.7 | 1297.7 | 613.1 |
| B. 跳过写库（monkeypatch） | 10 | 0.6 | **0.6** | 4.5 | 0.0 |
| C. cache=false（整段路径+写库） | 10 | 494.1 | 709.3 | 1544.7 | 681.7 |
| D. 正常路径复测 | 10 | 440.7 | 593.3 | 952.0 | 592.7 |

A − B = 613ms ≈ A 的 db 段。C 与 A 差 96ms（关缓存要多算整段引擎，但仍然淹没在 db 里）。
D 复测确认 A 不是一次性波动。

## 4. db 内部：三处 fsync

`save_kundoku` 每次调用做 6 个动作，逐段计时 20 次（新连接路径 = 生产路径）：

| 动作 | 均值 | 说明 |
| --- | --- | --- |
| `sqlite3.connect` | 2.3–18.1ms | 打开库文件 |
| `PRAGMA journal_mode=WAL` | **52.5–70.8ms** | 每次连接都重设一遍，含 header 写 |
| INSERT requests | 0.25–0.9ms | 纯内存 |
| INSERT results | 0.05ms | 纯内存 |
| `commit` | **372.0–409.5ms** | WAL 落盘 fsync |
| `close` | **241.4–266.6ms** | 关闭时 checkpoint + 截断 WAL，再一次 fsync |
| 合计 | **724–729ms** | min 326.7 / median 690–728.8 / max 1420.4 |

对照：**复用同一连接**后 commit 降到 89.3ms、总 median 77.1ms。也就是说
`PRAGMA` 与 `close` 两段（合计 294–337ms）纯属「每次新建连接」带来的开销，与数据量无关。

INSERT 本身 0.3ms——库大小（737–770KB，1821 行）不是问题，写放大不在数据侧。

## 5. 换盘对照：同一段代码，两个盘

同一份 SQLite workload（connect → PRAGMA WAL → INSERT → commit → close），10 次：

| 位置 | median | pragma | commit | close |
| --- | --- | --- | --- | --- |
| `D:\kanbun-kakikudashi\kanbun.db`（项目盘） | **729.6ms** | 47.3 | 324.1 | 297.5 |
| `C:\Users\...\Temp\d4_probe.db` | **15.4ms** | 2.3 | 7.7 | 3.1 |

**47 倍**。代码一模一样，只有路径不同，所以不是 SQLite 配置问题、不是写法问题。

再往下剥一层，绕开 SQLite 直接测裸文件 fsync（4KB 写）：

| 位置 | write | flush | **fsync** |
| --- | --- | --- | --- |
| D: 项目目录 | 7.9ms | 0.1ms | **85.1ms** |
| C: %TEMP% | 0.5ms | 0.1ms | **6.1ms** |

（同一脚本第二次跑，D: 的 fsync 是 180.3ms，C: 是 1.1ms——波动本身就说明这是盘/驱动层的
排队延迟，不是固定开销。）

补测 D: 根目录时 `write` 报 `[Errno 13] Permission denied`，所以只拿到项目目录的数据；
不影响结论，因为项目目录与根目录同属 D: 卷。

## 6. 因果链

```
每次 /api/kundoku
  → db.save_kundoku 新建连接
  → PRAGMA journal_mode=WAL      （fsync #1，52–71ms）
  → INSERT × 2                    （0.3ms）
  → commit                        （fsync #2，372–410ms）
  → close（checkpoint + truncate）（fsync #3，241–267ms）
  ×  D: 卷 fsync 单次 85–180ms
  =  350ms–1.4s，长尾到 2.4s
```

四条独立证据指向同一处：**monkeypatch 摘除（613→0.6ms）、连接复用（724→77ms）、
换盘（729.6→15.4ms）、裸 fsync（85.1 vs 6.1ms）**。没有第五条解释的空间。

顺带一个结论：**行级缓存对总耗时几乎无收益**——命中只省 8ms 引擎时间，剩下 98% 是写库。
在写库修好之前，优化缓存是白做工。

## 7. 没有做什么

按任务书「只定位，不重构」，本次**没有改动 `backend/db.py`**、没有改写入策略、
没有动数据库位置。以下候选方案仅列出，等拍板：

| 候选 | 预期收益 | 风险 |
| --- | --- | --- |
| 复用长连接（模块级 connection） | 724 → ~90ms | 需处理线程安全（FastAPI 默认线程池） |
| `PRAGMA synchronous=NORMAL` | 省掉 commit 的 fsync | 断电可能丢最后一批写入 |
| 写库移到后台队列，接口先返回 | 用户侧 0ms | 请求 id 无法即时返回，语义变了 |
| 库移到 C: 或排除杀软扫描目录 | 47 倍 | 数据位置变更，需用户同意 |
| 只在 `PRAGMA` 首次执行（记标志位） | 省 52–71ms | 收益小，单独做不值得 |

推荐顺序：**先复用连接**（收益最大且不改变持久化语义），再评估是否换盘。
但这是 D4 之后的事，不在本次范围内。

## 8. 复现方式

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python tools\day4_collect.py       :: 一次跑完：20 连调 + 消融 + db 分段 + 换盘 + 裸 fsync
python tools\day4_ablate_db.py     :: 单独看 A/B/C/D 四组消融
python tools\day4_db_why.py        :: 新连接 vs 复用连接，逐语句计时
python tools\day4_disk_check.py    :: 同 workload 在 D: 与 %TEMP%
python tools\day4_raw_io.py        :: 裸 write/flush/fsync
python tools\day4_locate_outlier.py:: 原始 20 连调（带 TIMING 日志解析）
```

原始数据：`eval/day4_outlier_data.json`（含每次调用的 8 段耗时、db 分段、两个盘的
sqlite 与 fsync 分布）。

验收：`pytest tests/test_api.py -q` → **14 passed**（计时改动未破坏既有断言，
且 `KANBUN_TIMING` 未设置时所有计时分支都不执行）。
