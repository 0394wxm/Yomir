# REPORT_NIGHT28.md — Night 28：全站平行语料库（Kanbun-LM 思路复现·本地版）（2026-11-19 凌晨）

ROADMAP 准确率深水区方向「Kanbun-LM 数据集思路复现」的落地夜。
**结论：hf-mirror 上没有可取的 Kanbun-LM 数据集（搜索 0 hit），「思路复现」落地为
本地平行语料库——kanbun.info 故事名言全站 1130 页抓全，1705 对 白文/書き下し文，
质检干净，golden.json 一个字节未动。**

起点：`git log -1` = `9e68df8`。工具：`tools/night28_probe_kanbunlm.py`、
`tools/build_parallel_corpus.py`、`tools/night28_corpus_qc.py`（`run_eval_parallel.py`
为 Night 29 备好）。

---

## 1. Kanbun-LM 方向的判定（不编造）

`hf-mirror.com/api/datasets?search=kanbun|kanbunlm|kundoku` 全部 **0 hit**（2026-11-19 实测）。
「思路复现」没有可下载的原始数据集，可复现的只有"思路"本身：**大规模 白文→書き下し文
平行语料**。唯一可达的来源是 kanbun.info（可直连），于是把评测抓取器用到全站。

## 2. 语料构建（复用 build_golden.py，一行不改）

- `build_parallel_corpus.py`：备份/恢复封装（同 Night 26 安全模式），
  `GOLDEN_TOTAL=5000`、`GOLDEN_PER_PAGE=10`，全站 1138 候选页抓完（~1.5 小时）。
- 产物 **eval/kanbun_parallel.json**：**1705 对，来自 1130 个页面**（页均 1.5 对——
  很多页只有 1 对可用文本，1138 页抓满后总数就是 1705，不是抓取失败）。
- 与既有集的关系：golden.json 500 条 ⊂ golden_1000 1000 条 ⊂ 本语料 1705 条（id 空间
  完全超集，見 QC 交集数字）；論語（rongo）0 交集（独立语料，不走 koji 页）。

## 3. 质检（`night28_corpus_qc.py`，全部实测）

| 检查 | 结果 |
| --- | --- |
| id 重复 | **0** |
| 空字段 | **0** |
| 白文注记括号泄漏 | **0**（抓取器过滤有效） |
| 完全重复对（跨页互抄） | **273 对**（保留，来源诚实；去重后 1432——训练用途时应去重） |
| 长度分布 | ≤20: 691 / 20-40: 561 / >40: 453 |
| 假名占比 >30%（引擎分流） | **0 条**（全量可进引擎） |

## 4. 用途定位（不夸大）

这是**数据基础设施**，不是新基线：1705 对里引擎没跑过的部分（golden_1000 之外的
~705 对）留待 Night 29 做语料基线；にして/して 系在更大语料上的计数复核也用它
（Night 26 §4 承诺的"统计功效翻倍"）。
**明确不做**：没有微调计划、没有把语料当训练集的授权——本夜只建库不训练。

## 5. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night28_probe_kanbunlm.py   :: HF 镜像搜索证明（0 hit）
python -I -u tools\build_parallel_corpus.py :: ~1.5 小时；golden.json 自动恢复
python -I tools\night28_corpus_qc.py        :: 质检
```

## 6. 禁止事项自查

抓取器一行未改；golden.json 字节级恢复（git status 实测干净）；expected 全部来自
页面事实文本未改写；273 对重复如实报告未静默去重；未做任何训练/微调（只有数据）；
无 key/token；只本地提交。
