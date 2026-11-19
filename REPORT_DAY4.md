# REPORT_DAY4.md — D4 复验：cached 2.4s 离群值定位（2026-11-19）

任务单：白天清单第 2 项（D4 离群值：加分段计时日志，20 连调定位 cached 2.4s 是哪一段慢，**只定位不重构**）。

起点：`4117d1c`，工作分支 `ds/dayshift-text-mining`。

**结论：上一班的定位结论完整复现，没有新机制。慢 100% 在 `db.save_kundoku` 的三次 fsync，
D: 卷单次 fsync 70–180ms。cached 与 unique 一样慢，缓存对总耗时无收益。本次未改任何生产代码。**

---

## 1. 复验方法

分段计时埋点上一班已加在 `backend/main.py`（`KANBUN_TIMING=1` 门控，默认关闭，生产路径零开销）。
本班直接复用，跑四个探针：

| 探针 | 作用 |
| --- | --- |
| `tools/day4_locate_outlier.py` | 20 连调（10 unique + 10 cached），带分段日志 |
| `tools/day4_ablate_db.py` | A/B/C/D 四组消融（正常 / monkeypatch 摘 db / cache=false / 复测） |
| `tools/day4_db_why.py` | db 内部逐语句计时，新连接 vs 复用连接 |
| `tools/day4_disk_check.py` + `day4_raw_io.py` | D: vs C: 换盘对照 + 裸 fsync |

## 2. 20 连调（分段计时）

| 阶段 | n | median | max | db 段 median | db 段 max |
| --- | --- | --- | --- | --- | --- |
| unique | 7 | 413.2ms | 615.2ms | 465.1ms | 606.9ms |
| cached | 7 | 400.8ms | **806.4ms** | 468.5ms | **805.8ms** |

**n=7 不是 10**：10 句里有 3 句假名占比高，走 `kana-branch` 早退（TIMING 行显示 `total=0.0ms | kana-branch`），
不进引擎也不写库。上一班记录同样现象（当时 5 句早退）。这一点如实说明，不凑数。

关键读数：

```
cached#03 806.4 ms | engine 0.0 | merge 0.0 | kaeriten 0.0 | translate 0.0 | style 0.0 | glossary 0.5 | db 805.8
unique#02 615.2 ms | engine 6.2 | merge 0.0 | kaeriten 0.1 | translate 1.3 | style 0.0 | glossary 0.5 | db 606.9
```

- cached 路径 `engine/merge/kaeriten/translate` **全为 0.0**（缓存确实命中了，`hit=1`），
  但 `db` 段仍要 806ms → 总耗时与 unique 无差别。
- `glossary` 0.4–16.7ms，`style` 恒 0。

**「cached 2.4s」这个命名本身就是误导**：慢与缓存命中无关，写库每次都发生。

关于 2.4s：本轮最大 806ms，没复现 2.4s。上一班也没复现（最大 1.10s）。
D: 卷 fsync 抖动极大（见 §4：同一脚本两次测 70.8ms / 180ms），2.4s 属同一分布长尾。
**如实记录：本班没观测到 2.4s 量级，不硬凑。**

## 3. 消融：摘掉写库

同一句 21 字，各 10 次：

| 组 | n | min | median | max | db median |
| --- | --- | --- | --- | --- | --- |
| A. 正常路径（写库） | 10 | 300.6 | 495.3 | 820.3 | 494.6 |
| B. 跳过写库（monkeypatch） | 10 | 0.5 | **0.6** | 1.0 | **0.0** |
| C. cache=false（整段引擎 + 写库） | 10 | 303.7 | 568.6 | 907.7 | 551.2 |
| D. 正常路径复测 | 10 | 353.1 | 469.8 | 563.6 | 469.2 |

A − B = 494.7ms，与 A 的 db 段 494.6ms 几乎完全相等（差 0.1ms）。
B 组 0.6ms 证明引擎+规则+glossary 全加起来不到 1ms（cached 路径）。
C 比 A 多 73ms = 引擎整段重算的代价，仍然淹没在 db 里。
D 复测确认 A 不是一次性波动。

## 4. db 内部：三处 fsync（20 次逐段）

| 动作 | 均值 | 上一班实测 | 一致性 |
| --- | --- | --- | --- |
| `sqlite3.connect` | 11.4ms | 2.3–18.1ms | ✓ |
| `PRAGMA journal_mode=WAL` | **25.3ms** | 52.5–70.8ms | 同量级（本班偏低） |
| INSERT requests | 0.95ms | 0.25–0.9ms | ✓ |
| INSERT results | 0.18ms | 0.05ms | ✓ |
| `commit` | **262.4ms** | 372.0–409.5ms | 同量级（本班偏低） |
| `close`（checkpoint+truncate） | **158.1ms** | 241.4–266.6ms | 同量级（本班偏低） |
| **合计** | **458.3ms** | 724–729ms | 同量级（本班偏低） |

本班各项普遍比上一班低 30–40%，但**结构完全一致**：commit 最大、close 次之、pragma 第三。
绝对值波动本身也是证据——这是盘/驱动层的排队延迟，不是固定开销。

对照：**复用同一连接** 20 次 → median 106.1ms（新连接 448.4ms）。差 342ms 全部来自
「每次新建连接」多付的 pragma + close 两次 fsync。

`db.save_kundoku` 原样 20 次：median 455.7ms / max 1049.4ms，与 A 组吻合。

## 5. 换盘对照

同一 SQLite workload（connect → PRAGMA WAL → INSERT ×2 → commit → close），10 次：

| 位置 | total median | pragma | commit | close |
| --- | --- | --- | --- | --- |
| `D:\kanbun-kakikudashi\kanbun.db` | **446.0ms** | 36.4 | 227.1 | 169.0 |
| `C:\Users\...\Temp\d4_probe.db` | **13.6ms** | 1.9 | 25.7 | 3.2 |

**32.8 倍**。代码逐字相同，只有路径不同。

裸文件 fsync（4KB 写）：

| 位置 | write | flush | **fsync** |
| --- | --- | --- | --- |
| D: 项目目录 | 6.0ms | 0.2ms | **70.8ms** |
| C: %TEMP% | 0.5ms | 0.1ms | **1.8ms** |

**39.3 倍**。D: 根目录仍 `[Errno 13] Permission denied`（与上一班相同，非本次引入）。

## 6. 因果链（四条独立证据）

```
每次 /api/kundoku（无论 cache 命中与否）
  → db.save_kundoku 新建连接
  → PRAGMA journal_mode=WAL        fsync #1
  → INSERT × 2                     (1.1ms，可忽略)
  → commit                         fsync #2  ← 最大项
  → close（checkpoint + truncate）  fsync #3
  ×  D: 卷 fsync 单次 70–180ms
  =  300ms–1.0s，长尾到 2.4s
```

| 证据 | 数据 |
| --- | --- |
| ① monkeypatch 摘除写库 | 495.3 → **0.6ms** |
| ② 连接复用 | 448.4 → **106.1ms** |
| ③ 换盘（同一段代码） | 446.0 → **13.6ms**（32.8×） |
| ④ 裸 fsync | 70.8 → **1.8ms**（39.3×） |

四条独立证据指向同一处，无第五条解释空间。

**附带结论（与上一班一致）**：行级缓存对总耗时几乎无收益。命中只省掉引擎的 3–15ms，
剩下 97–100% 是写库。**在写库修好之前优化缓存是白做工。**

## 7. 未做什么（严格按任务书「只定位，不重构」）

- 未改 `backend/db.py`（一字未动）
- 未改写入策略、未改 synchronous 设置
- 未移动数据库位置
- 未改 `backend/main.py` 的计时埋点（复用上一班的，默认关闭）

方案表原样保留，等拍板：

| 候选 | 预期收益 | 风险 |
| --- | --- | --- |
| 复用长连接（模块级 connection） | 448 → ~106ms | 需处理线程安全（FastAPI 线程池） |
| `PRAGMA synchronous=NORMAL` | 省掉 commit 的 fsync | 断电可能丢最后一批写入 |
| 写库移后台队列，接口先返回 | 用户侧 ~0ms | 请求 id 无法即时返回，语义变了 |
| 库移到 C: 或排除杀软目录 | 32.8× | 数据位置变更，需用户同意 |
| `PRAGMA` 只在首次连接执行 | 省 25–37ms | 收益小，单独做不值得 |

推荐顺序（不变）：**先复用连接**（收益最大且不改变持久化语义），再评估换盘。
**这是拍板项，不在本班范围内。**

## 8. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
set PYTHONIOENCODING=utf-8
python tools\day4_locate_outlier.py     :: 20 连调 + 分段日志（约 1 分钟）
python tools\day4_ablate_db.py          :: A/B/C/D 消融
python tools\day4_db_why.py             :: db 逐语句 + 连接复用对照
python tools\day4_disk_check.py         :: D: vs %TEMP%
python tools\day4_raw_io.py             :: 裸 write/flush/fsync
```

## 9. 与上一班的差异（如实记录）

| 项 | 上一班（2026-11-18） | 本班（2026-11-19） |
| --- | --- | --- |
| 20 连调有效 n | 8 unique / 8 cached（5 句早退） | 7 unique / 7 cached（3 句早退） |
| cached max | 1095.4ms | 806.4ms |
| 是否观测到 2.4s | 否（最大 1.10s） | 否（最大 0.81s） |
| 摘 db 后 | 0.6ms | 0.6ms |
| 换盘倍数 | 47× | 32.8× |
| 裸 fsync 倍数 | 14×（85.1 vs 6.1） | 39.3×（70.8 vs 1.8） |

**所有绝对数字都比上一班低，但每一条结论的形态完全相同**，倍数差异来自 D: 卷 fsync 抖动本身。
这不影响「慢在 db 写库」这个结论。

## 10. 禁止事项自查

- 未改 expected、未改评测数据、未改 golden。
- 未碰 `eval/ocr_gt_*`、`REPORT_NIGHT36/37/38.md`、`backend/ocr*.py`、`ocr_runtime/`、已有评测归档。
- 未编造：2.4s 没复现就写没复现；n 从 10 变 7 就写清楚为什么。
- 只本地提交到 `ds/dayshift-text-mining`，未推远程，未动 master。
- 全程未发图、未读图、未打开任何图片文件。
