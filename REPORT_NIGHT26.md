# REPORT_NIGHT26.md — Night 26：评测集 500→1000 条落地与基线（2026-11-19 凌晨）

ROADMAP 准确率深水区明列方向「更大评测集（500–1000 条）」的落地夜。
**结论先给数字：1000 条新基线 avgDist 25.62、精确匹配 2/1000、engine OK 1000/0 error；
与 night22 归档交集 499 条逐位一致（引擎确定性复核）。原 golden.json 一个字节未动。**

起点：`git log -1` = `746868c`；数据源 kanbun.info 故事名言全站（与 Night 21 同一抓取器）。
工具：`tools/build_golden_1000.py`（安全封装）、`tools/run_eval_1000.py`、`tools/night26_exact.py`。

---

## 1. 安全封装（关键约束：不动 eval/golden.json）

golden.json 是 D2 验收门 expected 比对基准，不能重跑覆盖。`build_golden_1000.py` 的流程：

1. 备份 golden.json 原始字节；
2. `GOLDEN_TOTAL=1000` 调 build_golden.main()（复用原抓取器，不改它一行）；
3. 产物落 **eval/golden_1000.json**；原始字节写回 golden.json；
4. 对账：新旧前 500 的 id 差异 + 交集 expected 是否被改。

实测对账：**交集 499 条 expected 被改 0 条**；前 500 有 1 条 id 轮换
（inochi-1 → irojinwo-1）——与 DAY9 §9 记录过的「重跑换条目」现象一致（抓取顺序非确定），
这正是不能直接覆盖 golden.json 的原因的实证。

## 2. 1000 条新基线（当前生产线，Rule C' 后）

| 指标 | 值 |
| --- | --- |
| engine OK | 1000/1000（0 error） |
| 精确匹配 | **2/1000** |
| avgDist | **25.62**（500 条官方归档 26.21） |
| ≤20 字 | n=377，avgDist 10.43，精确 2 |
| 20-40 字 | n=341，avgDist 23.21，精确 0 |
| >40 字 | n=282，avgDist 48.83，精确 0 |

分档结构与 500 条版一致（短句好长句差、>40 字拉高均值），均值下降 0.59 主要来自
新 500 条里短句占比更高（37.7% vs 41.6%→37.7%……如实说：是新样本构成差异，不是引擎变好）。

**精确命中 2 条**：
- kantanayu-3「直匍匐而歸耳。」→「直に匍匐して帰るのみ。」（Night 22 已知）；
- **kunshikina-1「子曰、君子不器。」→「子曰く、君子は器ならず。」**（新，名句短句，
  ふ→う/は曰く/Rule C' 全链路恰好覆盖它）。

**确定性复核**：与 night22_results_full.json 交集 499 条，avgDist 26.18 vs 26.18 逐位一致
——同一引擎同一输入必然同一输出，归档可信。

## 3. 评测口径差异（如实）

- 进程内 TestClient 走完整 HTTP 栈（不起 uvicorn）；monkeypatch `db.save_kundoku` 不写库
  （Day4 §3 验证过的等价路径，只影响耗时不影响输出）。
- 尺子与 Night 4/21/22 完全相同（剥空白 + levenshtein + expected 逐字来自页面）。
- 文体：1000 条全部是故事名言（koji）；論語 117 条在 golden_rongo.json（Night 23），
  未混入本集。

## 4. 用途与后续

1. **规则验证的更大语料**：Night 22 式的规则实验以后可在 1000 条上做离线模拟
   （1571 处 して系出现 vs 之前 617 处），统计功效翻倍。
2. **Night 25 链条错位的复核候选**：にして 在 1000 条 expected 里的出现量待数
   （本轮未跑对齐，工具 night25_* 可直接复用于新归档）。
3. 精确匹配在 1000 条上仍只有 2——「精确匹配 ≈0」的现状判断进一步坐实。

## 5. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\build_golden_1000.py    :: 约 25 分钟网络抓取；golden.json 自动恢复
python -I tools\run_eval_1000.py        :: 约 7 分钟；写 eval/night26_results_full.json
python -I tools\night26_exact.py        :: 列精确命中
```

## 6. 禁止事项自查

golden.json 恢复后 `git status` 干净（字节级恢复，实测无 M 标记）；golden_1000.json 的
expected 全部来自页面剥 ruby 的事实文本，未改写；抓取器（build_golden.py）一行未改；
评测归档由脚本生成无手工编辑；自报 total/exact_match_count 与实际一致（验收门核对）；
无 key/token；只本地提交。
