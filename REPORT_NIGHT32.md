# REPORT_NIGHT32.md — Night 32：論語全量 498 章（采样偏差修正 + 一次文件覆盖事故的恢复）（2026-11-19 凌晨）

Night 23 的論語语料只取了每篇前 6 章（117 条），报告里声明过采样偏差。本夜全量抓取，
**结论：論語真实难度被 Night 23 高估——全量 498 条 avgDist 28.12（抽样曾给 34.88，
高估约 7 点），且論語出现精确命中 2/498（此前 0），其中「德不孤、必有鄰」正是
Night 30 新增的 德→徳、鄰→隣 两条映射带来的直接闭环。**

起点：`git log -1` = `e5e3c8e`。产物：`eval/golden_rongo_full.json`（498 条）、
`eval/night32_results_rongo.json`、`tools/build_golden_rongo.py`（输出名参数化）、
`run_eval_rongo.py`（输入/输出名参数化 + 事故修复）、`night32_recover_golden.py`。

---

## 1. 全量論語基线（当前生产线：Rule C' + 新正字化表）

| 指标 | 抽样 117（night31） | **全量 498（night32）** |
| --- | --- | --- |
| avgDist | 34.88 | **28.12** |
| 精确匹配 | 0 | **2** |
| ≤20 字 | 13.58（n=19） | 10.72（n=142） |
| 20-40 字 | 19.76（n=46） | 21.09（n=196） |
| >40 字 | 56.04（n=52） | 52.17（n=160） |

- 抽样偏差的形态：前 6 章/篇系统性偏长偏难（>40 字占比 44% vs 全量 32%），把均值
  抬高了 ~7 点。**全量后論語(28.12)与故事名言(25.88)的文体差距收窄到 2.2**——
  Night 23 报告的「論語整体比故事名言难 9.3」要以本夜数字为准修正。
- 精确命中 2 条：rongo0212-1「君子不器」（与 koji 的 kunshikina-1 同文异页，两处都精确）
  和 **rongo0425-1「子曰、德不孤、必有鄰。」→「子曰く、徳は孤ならず、必ず隣有り。」**
  ——後者的 德→徳、鄰→隣 都是 Night 30 刚加的映射，新规则直接产出精确命中的闭环案例。
- 最差条目不变：rongo1601-1（246）/rongo2002-1（171）/rongo2001-1（135）——长对话
  叙事的结构性坏点，与 Night 23 判断一致。
- 512 章抓到 498：14 条被括号过滤/无对文本跳过（抓取器既定过滤，逐条有 [SKIP] 记录）。

## 2. 事故与恢复（如实记录，第 2 节是本夜最重要的一节）

**事故**：全量抓取完成后跑评测，`run_eval_rongo.py` 的**写出段残留了第一版参数解析**
（`out_name = args[0]`），把评测结果归档覆盖写到了 `args[0]` = golden_rongo_full.json 上
——刚抓好的 498 条语料被结果归档覆盖，且 exit code 0、无任何报错。

**发现**：归档文件不存在 + 日志里两处 written 都指向语料文件 → 读磁盘代码定位残留行。

**恢复（零重抓）**：results[] 每条都含 id/pian/source_url/hakubun/expected_kakikudashi
（评测归档本来就是语料字段的超集），`night32_recover_golden.py` 逐条抽取重建语料，
自检 id 唯一/无空字段 → **498 条 100% 恢复**。重跑评测 **28.12 / 2/498 与首次逐位一致**
（引擎确定性 + 恢复完整性双重验证）。

**修复**：写出段改用 main() 开头统一解析的 out_name，注释记明事故。golden_rongo.json
（117 条抽样版）全程未被触碰（git status 实证）。

## 3. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
set RONGO_PER_PIAN=999&& python -I -u tools\build_golden_rongo.py golden_rongo_full.json
python -I tools\run_eval_rongo.py golden_rongo_full.json night32_results_rongo.json
python -I tools\night26_exact.py night32_results_rongo.json
python -I tools\night32_recover_golden.py   :: 仅事故恢复用（幂等保护：非结果归档会拒绝执行）
```

## 4. 禁止事项自查

expected 未改一字（恢复脚本从评测结果的 expected 字段原样取回，无改写）；事故在报告
正文如实记录且恢复自检在案；golden_rongo.json 抽样版未动；两处归档（语料/结果）此后
文件名分离并有注释防再犯；无 key/token；只本地提交。
