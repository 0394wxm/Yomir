# REPORT_NIGHT33.md — Night 33：OCR 深水区阶段开头写细 + GT 试点裁决（2026-11-19 凌晨）

准确率深水区（Night 21–35）的列名方向已全部处理完：更大评测集（Night 26/1000 条）、
分文体（Night 23/32 論語）、して系（Night 24/25/27 关闭）、Kanbun-LM 思路（Night 28 语料库）、
LLM 标注管线（Night 9 门禁未过，不可做）。按 ROADMAP「每到一个阶段开头，先由用户
（或当晚的 agent）把该阶段的第一夜写细」的授权，本夜给 **OCR 深水区（Night 36–50）
写细并做 GT 试点裁决**，为 Night 36（KuroNet 对照评测）扫清前置。

起点：`git log -1` = `5c0374a`。零生产改动。

---

## 1. 样张库现状盘点（实证）

- 20 张样张、OCR 输出与耗时元数据都在 `eval/ocr_samples/batch20_summary.json`
  （results[] 含 file/pid/page/img 尺寸/行数/URL/输出头）。
- **没有任何 ground truth 字段**（20 条 results 逐条核查 0 有 GT）。
- 4 个 `*_clean__cluster/native.txt` 是引擎输出存档，不是 GT。
- Night 6 报告所说的「manifest 全记 URL」实际就是 batch20_summary.json——
  独立 manifest 文件不存在。如实更正记录。

## 2. GT 试点（1 页，竹取物語 R0000002）

试点图像下载到 `eval/ocr_samples/gt_pilot/ndl_1287221_R0000002.jpg`
（NDL IIIF，1400×933，页面标签「竹取物語 3軸 本別12-3 / 01-002」，385KB）。

**目验结论（分两层，如实）：**

1. **内容层可验**：右起第一列为「いまはむかし、たけとりのおきなといふものありけり」
   ——与现有引擎输出（cluster.txt 首行）完全一致，同时是文学史固定的《竹取物語》
   开头。OCR 对这张木版本（活字清晰的印刷页）的读取是连贯可读的。
2. **逐字 GT 层 agent 不可靠**：草仓名的濁点/小書き/异体字/返り点的逐字转写，
   我目验无法保证逐字正确——由同一个 agent 既当转写者又当裁判是循环验证。
   **GT 的可信来源只剩两个，都是拍板项**：
   - a) 权威翻刻底本（日本古典文学大系等）——需要用户从可达渠道提供文本；
   - b) 人工转写/抽验（预算拍板；抽样 GT 也可：如 4 页 × 10 行）。

## 3. Night 36（KuroNet 对照评测）依赖清单（写细）

| 依赖 | 现状 | 拍板项 |
| --- | --- | --- |
| GT 20 样张 | 0/20（本夜实证） | 来源：权威翻刻 or 人工抽样 GT（§2 的 a/b） |
| KuroNet 模型 | hf-mirror 搜索 0 hit（kuronet/kuro-net/historicanybody 全试）；NII 配布在 GitHub release，本机 GitHub 慢且抖动（夜 1 实测） | 用户从 NII 配布页拿取或提供网络条件；拿不到就改做「dlkotenocr 自身改进」线 |
| 评测脚本 | 可复用 Night 6 的批量管线 + 行对齐 | 无 |

无 GT 时的替代质量指标（不需拍板也能做）：跨引擎一致率（需第二个引擎）、
行数/字符数结构指标、行内乱字率（符号行过滤器统计）——可作为 Night 36 的
GT 缺位降级方案，先写在计划里。

## 4. 产出与没做

- 产出：试点图像 + 目验记录（本报告）、依赖清单、Night 36 计划、
  `tools/night33_gt_pilot_dl.py`、`eval/ocr_samples/gt_pilot/`（1 图）。
- **没做**：GT 全量标注（agent 不可靠，等拍板）；KuroNet 下载（网络不可得）；
  任何 OCR 引擎改动。
- 之所以把"写细"提前到 Night 33：Night 34/35 没有列名任务（准确率阶段到 35 为止
  只剩这两夜的空位），与其空转，不如把下一阶段的第一夜写细——这是 ROADMAP 明文
  授权的动作。

## 5. 禁止事项自查

agent 转写的不可靠性如实声明（没有把我的目验包装成 GT）；依赖未得拍板的都标了
拍板项而没有自己定；KuroNet 可得性是实测（3 个搜索词全 0 hit）；Night 6 的
manifest 记录误差如实更正；无 key/token；只本地提交。
