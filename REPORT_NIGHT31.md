# REPORT_NIGHT31.md — Night 31：新正字化表下两套官方线重基线（2026-11-19 凌晨）

Night 30 的 40 对新字体映射只重评了 1705 语料；本夜把**官方两套线**也重基线，
把改动对既有口径的影响全部落账。

**结论：故事名言 500 条 26.21 → 25.88（-0.33，116 改善 / 0 变差）；論語 117 条
35.55 → 34.88（-0.67，43 改善 / 0 变差）——論語收益最大，与「學/樂/德 主要是
儒家语旧字体」的来源分析一致。两线 0 变差。**

起点：`git log -1` = `62719c0`。产物：`eval/night31_results_full.json`（500 条 HTTP 线）、
`eval/night31_results_rongo.json`（117 条）、`tools/night31_compare.py`。

---

## 1. 重基线数字（night31_compare.py 逐条对比）

| 线 | n | avgDist | delta | 改善/变差 | 精确 |
| --- | --- | --- | --- | --- | --- |
| 故事名言（night22 → night31） | 500 | 26.21 → **25.88** | -0.33 | 116/0 | 1 → 1 |
| 論語（night23 → night31） | 117 | 35.55 → **34.88** | -0.67 | 43/0 | 0 → 0 |
| 平行语料（night29 → night30） | 1705 | 24.77 → **24.38** | -0.39 | 433/0 | 4 → 4 |

（第三行是 Night 30 已落账的，列在这里凑齐三条线的全景。）

三套语料零回归；改善幅度与旧字体密度成正比（論語 > 平行 > 故事名言——平行语料
包含論語页之外的儒家引文所以居中）。

## 2. 論語分档变化

| 档 | night23 | night31 | delta |
| --- | --- | --- | --- |
| ≤20 字 | 13.74 | 13.58 | -0.16 |
| 20-40 字 | 20.33 | 19.76 | -0.57 |
| >40 字 | 56.98 | 56.04 | -0.94 |

>40 字收益最大（长句里旧字体出现次数多），Night 23 的「長句要等依存模型」结论里
现在有一部分（旧字体部分）已经由显示层吃掉了。

最差条目 rongo1601-1（季氏將伐顓臾）250 → 246，仍是最差——它的问题是结构性的
（长对话叙事），不是字体。

## 3. 口径备注（如实）

- 500 条线走的是 HTTP 路径（与 night22 同一 run_eval.py），論語线走 TestClient 进程内
  （与 night23 同一 run_eval_rongo.py，本次加输出文件名参数，night23 归档原样未动）；
- night22/night23 归档**保留原样**作为 Rule C' 上线时点的历史快照，night31 是新基线；
  后续夜的对比一律用 night31 系列；
- 1705 语料的 night29（旧表）/night30（新表）同理保留。

## 4. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
:: 起后端后：
python -X utf8 -I tools\run_eval.py night31_results_full.json
python -I tools\run_eval_rongo.py night31_results_rongo.json
python -I tools\night31_compare.py
```

## 5. 禁止事项自查

expected 未改（compare 只读归档）；旧归档 night22/night23/night29 未被覆盖（各自
新文件落盘）；参数化改动只是给输出加文件名参数、默认行为不变；无 key/token；
只本地提交。
