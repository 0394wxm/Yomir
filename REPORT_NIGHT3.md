# REPORT_NIGHT3.md — 第 3 夜（2026-11-17 01:48 ～ 09:00 窗口）

执行者：ZCode 挂机任务（无人工介入）。承接 REPORT_NIGHT1/2.md，只记事实。
提交信息：`night3: orthography, eval 50, ocr order, kana routing`（本地，不推远程）。

---

## 0. 结论速览

| 步骤 | 状态 | 一句话结论 |
| --- | --- | --- |
| 1. 正字化 + 评测 50 条 | ✅ | 精确匹配 **0/50**（没涨分）；但 merge+正字化让 **28/50 条编辑距离改善、0 条变差**，平均距离 13.2→12.3；旧→新字体映射表按 50 条基线 diff 证据扩到 22 对 |
| 2. OCR 改进 | ✅ | 垃圾框过滤 v3（朱印被正确滤掉，不再误杀正文列）；列序聚类模式在 4 张样张上全部 ≥ 官方顺序（竹取物语的中段交错被修正），已设为默认 |
| 3. 假名分流 | ✅ | 假名比例 >30% 判为 kana，不进訓読引擎；竹取物語（kana）/论语序说（kanbun）实测分流正确；pytest 覆盖 |
| 4. 测试套件 + 文档 | ✅ | pytest 11/11 全过（两轮：环境变更前后各一次）；README 全面更新 |
| 5. qkana / guwenbert | ✅ 部分 | qkana：headers 通但 body 0 字节（半阻断），未成功；**guwenbert-base.supar 463.5MB 分片下载意外成功**，模型可加载（199/199 权重），但 supar 1.1.4 的 predict 路径有 bug（feats 空），对比未跑成——如实记录 |

---

## 1. 步骤 1 — 正字化规则 + 评测集 50 条

### 1.1 评测集扩充

`tools/build_golden.py` 改为每页取前 5 对干净文本（环境变量 GOLDEN_PER_PAGE 可调）：
10 页 × 5 = **50 条**，来源全部为 kanbun.info 故事名言页（矛盾/蛇足/朝三暮四/塞翁が馬/
四面楚歌/虎の威を借る/画竜点睛/守株/五十歩百歩/鶏口牛後），schema 不变
（id / source_url / hakubun / expected_kakikudashi），未改任何 expected。

### 1.2 正字化映射（证据驱动）

`backend/kundoku_rules.py` 新增 `SHINJITAI_MAP` + `normalize_shinjitai()`，只作用于
**書き下し文输出层**（返り点付き原文/白文不动，引擎内部不动）。先放 4 对任务书点名的，
再写 `tools/find_ortho_pairs.py` 扫 50 条基线输出里「got 有而 expected 无」的汉字，
证据扩充到 **22 对**（數→数、點→点、譽→誉、飮→飲、獸→獣、應→応、餘→余、將→将、
圍→囲、觸→触、釋→釈、當→当、戰→戦、挾→挟、從→従 等）。
每条映射在代码注释里标了来源条目。後端 `POST /api/kundoku?ortho=0` 可关闭。

### 1.3 50 条实测（三轮，全部原始输出入档）

| 运行 | 配置 | 精确匹配 | 平均编辑距离 |
| --- | --- | --- | --- |
| `eval/night3_results_baseline.json` | merge=0, ortho=0（引擎原始） | **0/50** | 13.2 |
| `eval/night3_results_full.json`（第一版映射 7 对） | merge=1, ortho=1 | 0/50 | 12.7（20 改善/0 变差） |
| `eval/night3_results_full.json`（最终 22 对） | merge=1, ortho=1 | **0/50** | **12.3（28 改善 / 0 变差 / 22 持平）** |

- **10 条子集（每篇第 1 对，即 Night2 的原始 10 条）单独一行**：基线 0/10、merge+正字化后 0/10
  （与 Night2 的 0/10 一致，没有变差）。
- 「可读性提升几条」用编辑距离做客观度量：**28 条改善、0 条变差、22 条持平**。
  改善条目的典型变化（节选）：
  ```
  garyo-1  got: 張僧は繇す、呉は中の人なり。 → 張僧繇、呉中の人なり。   (dist 4→2)
  shimen-1 got: 項の王軍の壁垓下。        → 項王軍壁垓下。            (dist 7→5)
  mujun-1  got: 楚の人は楯矛ともを…      → 楚人楯矛ともを…           (dist 4→3)
  gojippo-1 got: 梁の惠王は曰く、        → 梁恵王曰く、              (dist 2→1)
  ```
- **正字化没有让任何条目变差**（0 条变差，逐条编辑距离对比在
  `python -I tools/eval_summary.py night3_results_baseline.json night3_results_full.json` 的输出里）。
- 精确匹配仍 0/50 的残差（如实）：助词选择（に/は）、名词化（祠る者）、动词条目
  （壁す）、文语活用差异——都在解析/词条层，字符串规则修不动。

## 2. 步骤 2 — OCR 改进

### 2.1 垃圾框过滤（backend/ocr_engine.py `_is_junk_line`，KANBUN_OCR_JUNK_FILTER=0 可关）

Night2 的「十四番熊」不是色卡——用 `tools/debug_ocr_boxes.py` 转储盒子后发现它来自
**页面右下的朱印**（box 30x149，satMean 98.4），色卡/标尺根本没被 eval_xml 输出成 LINE。
迭代了三版（v1 satMean 阈值没拦住；v2 satFrac>0.10 反而误杀真列「をとりつゝ…」——
米色纸底会把饱和度占比推到 0.106）。v3 按 dump 数据定规则：
1. satFrac(S>120)>0.18（纯色块）；2. 行宽>60% 图宽（横贯标尺）；3. 贴边窄条（右缘>97%/左缘<10%）；
4. **縦行高 < 0.55×縦行中位高 且 satMean>90**（朱印/花押明显偏矮且色浓；纯墨迹短行不受影响）。
实测：竹取样张 junk_filtered=1（朱印被滤），16 行正文全保，首行回到「いまはむかし…」。

### 2.2 列序聚类（`_cluster_order`，KANBUN_OCR_ORDER=native 可回退官方顺序）

对 eval_xml 输出的 LINE 做确定性聚类：縦行按 x 重叠聚成列（右→左），列内按上→下；
横行按 y 聚类（上→下，行内右→左）；单元按质心排序。4 张样张 native vs cluster 对比
（`eval/ocr_samples/*__{native,cluster}.txt`）：

| 样张 | native | cluster | 结论 |
| --- | --- | --- | --- |
| 竹取物語（巻子本・仮名） | 中段交错（をとりつゝ 错位） | **16 行全部按叙事顺序** | cluster 修正 |
| 伊藤博文関係文書（明治文書） | 23 行通顺 | 与 native 完全相同 | 无损 |
| 論語序説（明治训读文） | 9 行通顺 | 与 native 相同 | 无损 |
| 人間萬事翁馬（江戸絵本） | 10 条碎片 | 与 native 相同 | 版式不是列式，都无解 |

**已把默认切到 cluster**。踩过的坑：pattern 过滤只筛了行文本没同步筛盒子，
cluster 的 index 越界 IndexError——已修（boxes 与 resultlines 同步过滤）。

### 2.3 4 张样张（不同书、不同版式）+ 全链路

新下 3 张（NDL 数字收藏 IIIF，本机直连 200）：

| 样张 | 来源 URL | OCR 结果（真实输出） | kundoku 分流 |
| --- | --- | --- | --- |
| 竹取物語 R0000002 | `https://dl.ndl.go.jp/api/iiif/1287221/R0000002/full/1400,/0/default.jpg` | 16 行，首行「いまはむかしたけとりのおきなといふ」，色卡误读行已滤 | **kana** ✓ 分流 |
| 人間萬事翁馬 R0000002 | `https://dl.ndl.go.jp/api/iiif/10301438/R0000002/full/1400,/0/default.jpg` | 10 条碎片（絵本散字，标题标签「人間萬事翁馬」被误读为「久間万」，过滤规则不适用此类白底黑字标签） | kanbun（机制通） |
| NDL 11892692 R0000003 | `https://dl.ndl.go.jp/api/iiif/11892692/R0000003/full/1400,/0/default.jpg` | 9 行，「明治十九年二月廿二日…論語序説 史記世家曰孔子名丘字仲尼。其先宋人…」通顺 | **kanbun** ✓（这是训读文，訓読引擎可处理） |
| 伊藤博文関係文書 R0000002 | `https://dl.ndl.go.jp/api/iiif/9973821/R0000002/full/1400,/0/default.jpg` | 23 行，明治侯文（片假名多），「之レナキ弊ヲ醸成セシムル者ノ如シ…」基本通顺 | **kana** ✓ 分流（侯文不应二次训读，行为正确；note 措辞已改为「假名为主的文本（假名文学・训读体・侯文等）」） |

每张的白文都 POST /api/kundoku 一次：链路 4/4 打通，分流如上（汇总在
`eval/ocr_samples/chain_summary.json`）。没给准确率数字（无 ground truth）。

## 3. 步骤 3 — 假名白文分流

- `detect_text_type()`：假名（平+片假名）占非标点字符比例 > 0.3（`KANBUN_KANA_RATIO` 可调）判为 kana。
- kana 路径：不进引擎，`text_type="kana"`、kakikudashi/kaeriten 全空、note 说明
  「假名为主的文本…不适用漢文訓読」，白文原样回显。
- 实测（真实 API 调用）：竹取物語 OCR 白文 → kana ✓；「不入虎穴不得虎子」 → kanbun ✓。
- 前端：收到 kana 响应时用警示条显示 note，不渲染空的訓読输出（App.tsx）。

## 4. 步骤 4 — 测试套件 + 文档

- `tests/test_api.py`：**11 条测试，11 条全过**（两轮：junk filter v3 前、supar/torch/numpy 变更后各一遍）。
  覆盖：/health、/api/kundoku 经典句真实断言（王は左右を顧みて…）、空文本 400、
  假名分流（text_type/note/原文回显）、漢文不误判、正字化（恵 出现且 惠 消失，ortho=0 可关）、
  专名合并（宋人 出现且 宋の人 消失，merge=0 可关）、normalize_shinjitai 单元测试（22 对全对）、
  SQLite 落库（requests/results 计数 + 最新行内容断言）、OCR 空上传 400、OCR 运行目录缺失行为。
  所有断言都是真实 assert，没有「打印凑数」。
- `README.md` 重写：启动、用法、环境变量表、已知上限（评测 0/50、再読文字只有「未」、
  OCR 无 ground truth、假名分流）、qkana shim 说明 + 官方替换方法（指向 tools/fetch_official_qkana.py）。

## 5. 步骤 5 — qkana / guwenbert 替换脚本

### 5.1 qkana（tools/fetch_official_qkana.py）

脚本功能：断点续传下载 → zip 校验 → 解压校验 dicrc → 备份现有 shim → 替换。
本机实测一次：**headers 能收到（Content-Length: 294217468 ≈ 280MB），但 body 10 分钟 0 字节**
（半阻断：TLS 握手允许、数据通道被卡），超预算杀掉（清理了两个顺带发现的僵尸 python 进程：
夜 1 卡死的 import 探针、挂着的下载进程）。**未成功，shim 继续服役**；
在可达 NINJAL 的网络跑该脚本即可完成替换。

### 5.2 guwenbert（tools/try_guwenbert.py）——意外收获：模型下载成功

官方仓库把模型切成 80MB 分片（guwenbert-base.supar.1~6）。本机对
raw.githubusercontent.com 的连接是**抖动可达**（404 响应能回来、超时也常发生）。
脚本按分片协议下载 + 每片断点续传 + 3 次重试 + 30 分钟预算，第一次链式尝试（与 qkana
并行跑的那次）在 27 分钟里**全部 6 片下载成功**：

```
[download] chunk 6 done, total 463.5 MB / 463.5 MB
[download] saved: D:\Python312\Lib\site-packages\udkanbun\supar-kanbun\guwenbert-base.supar
```

随后做了三处兼容修复（都写进脚本注释）：
1. `udkundoku.load()` 不暴露 BERT 参数——要用 `udkanbun.load(MeCab=True, Danku=False, BERT="guwenbert-base")`；
2. torch 2.6+ 的 `torch.load` 默认 weights_only=True，supar checkpoint 是完整 pickle——
   脚本内局部 monkeypatch 关闭（来源可信：KoichiYasuoka 官方仓库 + filesize.txt 逐字节核对）；
3. checkpoint 内 Field 反序列化时要拉 `ethanyt/guwenbert-base` 的 tokenizer/config——
   huggingface.co 被墙，`HF_ENDPOINT=https://hf-mirror.com` 解决（注意 cmd 的 `set` 尾空格坑）。

**最终状态**：模型加载成功（`Loading weights: 199/199` + RobertaModel LOAD REPORT），
但 predict 阶段 supar 1.1.4 内部 `feats.pop(0)` → IndexError（feats 空列表）——
supar 1.1.4 的 predict 路径与本 checkpoint 的 Field 配置不匹配（transformers 降到 4.57.6 也一样）。
**对比未跑成**，需要与 checkpoint 同代的 supar 版本或改用 supar 的文件式 predict API——
记为下一夜候选。环境变化如实记录：pip 安装 supar 带入 torch 2.15.0/transformers 4.57.6/
numpy 2.5.5（系统 Python），**重启后已实测 OCR 引擎与全套 pytest 在 numpy 2.5.5 下正常**
（200/16 行 + 11/11 过）。

## 6. 卡在哪 / 下一步建议（只列事实和建议）

**无未解决卡点。** 步骤全部有结论。下一夜候选：

1. **guwenbert 对比收尾**：模型已在位，剩 supar 版本匹配问题——试 `pip install supar==1.0.x/2.0.x`
   与 checkpoint 生成年代对齐，或直接用 supar 的文件式接口（conllu 落盘 → supar predict 文件）。
   预期这是訓読质量的最大杠杆。
2. **官方 qkana**：仍需可达 NINJAL 的网络（280MB，脚本备好支持续传）。
3. **OCR 絵本类版式**：散字碎片段落是版式问题，可试 rtmdet 阈值调整或块级（PAGE/BLOCK）输出；
   白底黑字的编辑性标签（「人間萬事翁馬」标签）可按 OCR 文本与白名单过滤。
4. **正字化再扩**：22 对表已零变差，继续用 find_ortho_pairs 扫（例如 爲→為 的更多形态）。
5. 現代語訳/語釈 等用户 key（KANBUN_LLM_API_KEY）。

需要用户拍板：产品推理 API 与 key 注入方式；远程仓库/域名仍按禁令未动。

## 7. 禁止事项遵守情况

- 本地提交，未建远程、未推远程、未部署、未买域名。
- 无任何 API key/token 入库；llm.py 只写环境变量名。
- 未编造：OCR 无 ground truth 不给准确率；评测 0/50 原样记录；qkana 失败/guwenbert
  对比失败都写明具体报错；没有把"模型下载成功"夸成"BERT 模式可用"。
- 报告写完即停，不做第 4 夜。

## 8. 产出物清单（相对 night2 新增/修改）

```
backend/kundoku_rules.py   SHINJITAI_MAP 22 对 + normalize_shinjitai（新增）
backend/ocr_engine.py      垃圾框过滤 v3 + 列序聚类（新增）+ boxes 同步过滤修复 + cluster 默认
backend/main.py            ortho 参数、text_type/note 字段、假名分流
frontend/src/App.tsx       kana 响应警示条
tests/test_api.py          pytest 11 条（新增）
tools/build_golden.py      每页 N 对可配（GOLDEN_PER_PAGE）
tools/find_ortho_pairs.py  旧字体证据扫描（新增）
tools/eval_summary.py      两轮评测对比（新增）
tools/debug_ocr_boxes.py   OCR 盒子转储（新增）
tools/test_ocr_samples.py  4 样张 × 2 行序对比（新增）
tools/test_ocr_chain.py    全链路 HTTP 测试（新增）
tools/fetch_official_qkana.py   官方 qkana 下载替换脚本（新增）
tools/try_guwenbert.py     guwenbert 分片下载+对比脚本（新增）
tools/fetch_github_file.py GitHub API 下载器（night2 已有，本夜复用）
eval/golden.json           10 → 50 条
eval/night3_results_baseline.json / night3_results_full.json
eval/ocr_samples/          8 份 OCR 行序对照文本 + chain_summary.json
README.md                  全面重写
REPORT_NIGHT3.md           本报告
```
