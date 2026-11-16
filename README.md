# kanbun-kakikudashi

漢文 → 書き下し文 Web MVP（第 3 夜完成：双入口 + 訓読 + OCR + 评测/测试基建）。

两个入口汇到同一条訓読管线：

- 入口 A：粘贴活字漢文文本
- 入口 B：上传图片（くずし字，NDL 古典籍 OCR-Lite，已接通）

输出四样：

1. 返り点付き原文（縦書き + 返り点ルビ）
2. 書き下し文（含送り仮名，縦書き，旧字体→新字体显示转换）
3. 現代語訳（占位：等用户给 LLM key）
4. 語釈（占位：同上）

假名文学文本（竹取物語等）会自动分流：不进漢文訓読引擎，只回显白文 + 提示。

## 启动

```bat
:: 后端（Python 3.12 在 D:\Python312）
set PATH=D:\Python312;D:\Python312\Scripts;%PATH%
python -X utf8 -m uvicorn backend.main:app --port 8000

:: 前端（Node 在 D:\nodejs）
set PATH=D:\nodejs;%PATH%
cd frontend && npm install && npm run dev
:: 浏览器打开 http://localhost:5173/ 或 http://127.0.0.1:5173/（vite 双栈监听）
```

OCR 首次调用前解压引擎目录（模型 ~80MB 不入库）：

```bat
python -I -m zipfile -e "D:\dlkotenocr-lite\data\flutter_assets\app\app.zip" ocr_runtime
```

OCR 依赖直接复用官方 GUI 自带的 `D:\dlkotenocr-lite\site-packages`（onnxruntime/numpy/PIL，零新装）。
首次调用 /api/ocr 要加载两个 ONNX 模型（本机 Celeron 约 40~60s），单张图推理约 35~80s。

## 用法

- 贴文本：输入区粘漢文 → 「→ 送入白文」→ 白文区可改 → 「重新訓読」
- 传图片：选一张くずし字扫描图 → OCR 自动填入白文区 → 修改后「重新訓読」
- 输出①②是縦書き；返り点做成了ルビ；③④显示占位直到配置 LLM key

环境变量（全部可选）：

| 变量 | 作用 | 默认 |
| --- | --- | --- |
| `KANBUN_LLM_API_KEY` | 現代語訳/語釈 的 LLM key（没配就走 mock 占位） | 无 |
| `KANBUN_LLM_BASE_URL` / `KANBUN_LLM_MODEL` | OpenAI 兼容端点/模型名 | openai / gpt-4o-mini |
| `KANBUN_KANA_RATIO` | 假名分流阈值（假名字符占比） | 0.3 |
| `KANBUN_OCR_ORDER` | OCR 行序：native（官方 xy_cut）/ cluster（列聚类） | native |
| `KANBUN_OCR_JUNK_FILTER` | 色卡/标尺过滤开关 | 1（开） |
| `KANBUN_OCR_SITE` / `KANBUN_OCR_SRC` | OCR 依赖包 / 引擎源码路径 | dlkotenocr-lite 侧 / ocr_runtime |
| `KANBUN_DB` | SQLite 路径 | 项目根 kanbun.db |

## 测试与评测

```bat
:: API/规则测试（11 条，进程内 TestClient，不依赖 uvicorn 在跑）
python -X utf8 -m pytest tests\test_api.py -v

:: 评测（eval/golden.json 50 条，需后端在 8000 跑着）
python -I tools\run_eval.py --no-merge --no-ortho night3_results_baseline.json   :: 引擎原始基线
python -I tools\run_eval.py night3_results_full.json                             :: merge+正字化
python -I tools\eval_summary.py night3_results_baseline.json night3_results_full.json
```

## 已知上限（如实记录，不要当它全能）

- **訓読准确率**：eval/golden.json 50 条（kanbun.info 白文+書き下し文成对样本）
  精确匹配 **0/50**；merge+正字化后平均编辑距离 13.2→12.3、28/50 条改善、0 条变差。
  简单句（王顧左右而言他 等）正确；长难句的助词选择、名词化（祠る者）、
  动词条目（壁す）是解析层问题，字符串后处理修不动。
- **再読文字**：udkundoku 只对应「未」；應・當・須・蓋・宜・將等未对应；駢文和诗难。
- **OCR**：无 ground truth，不给准确率数字；色卡/标尺过滤是启发式（饱和像素占比+
  超宽条+贴边条），边界情况可能误滤/漏滤；多列密排页面的行序可选 cluster 模式改善。
- **假名文本**：不适用漢文訓読，接口会自动分流（text_type=kana）并给提示。
- **現代語訳/語釈**：占位。key 由用户单独提供（`KANBUN_LLM_API_KEY`），
  不要写死在代码里，也不要从 ZCode 抓 token。

## qkana shim（重要）

`import udkundoku` 需要 UniDic qkana 词典，官方源 `clrd.ninjal.ac.jp` 在本机被墙
（TLS 重置）。当前用 unidic_lite 冒充的 shim：
`D:\Python312\Lib\site-packages\unidic2ud\download\qkana\`（unidic_lite + 自定义
dicrc 输出标准 UniDic 29 列）。可复现：`python -I tools/make_qkana_shim.py`。

在能直连 NINJAL 的网络环境运行 `python -X utf8 tools/fetch_official_qkana.py`
即可下载官方词典并自动备份/替换 shim（280MB，脚本支持断点续传）。
guwenbert BERT 模式同理：`tools/try_guwenbert.py`（还需 `pip install supar`，
依赖 torch）。

## 结构

```
backend/       FastAPI + Uvicorn（8000）
  main.py      /health /api/kundoku（merge/ortho 参数、假名分流）/api/ocr
  ocr_engine.py  NDL 古典籍 OCR-Lite 进程内包装（CC BY 4.0）+ 垃圾框过滤 + 列序聚类
  kundoku_rules.py  专名合并 + 旧→新字体映射（仅显示层）
  db.py        SQLite（requests/results 两表）
  llm.py       LLM 适配层（无 key 时 mock）
frontend/      Vite + React + TS 单页（5173）
eval/          golden.json 50 条 + night3_results_*.json + ocr_samples/ 实测文本
tests/         pytest 套件（11 条）
tools/         shim/评测/OCR/CLI 等脚本
ocr_runtime/   不入库：app.zip 解压 + NDL 样张
```

## 约束

- 只本地 git 提交，不建远程仓库、不推远程。
- 每句输出标注：「AI 初稿，仅供参考，请以原文和专业判断为准。」
