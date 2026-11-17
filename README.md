# kanbun-kakikudashi — 漢文→書き下し文 Web MVP v0.1

漢文（白文）→ 書き下し文 Web MVP。两个入口汇到同一条訓読管线：

- 入口 A：粘贴活字漢文文本
- 入口 B：上传图片（くずし字，NDL 古典籍 OCR-Lite，已接通）

输出四样：①返り点付き原文（縦書き+ルビ）②書き下し文（含送り仮名）③現代語訳（占位）④語釈（词库/占位）。
逐行纠错、历史翻回、行级缓存、导出（复制/txt/打印）齐备。

---

## 一键启动（v0.1）

双击 `start_backend.bat` → 后端 http://127.0.0.1:8000
双击 `start_frontend.bat` → 前端 http://localhost:5173/ （或 127.0.0.1:5173）

评测一键跑通（需后端已启动）：双击 `tools\eval_all.bat`（200 条基线+全规则+对比+分类）。

OCR 首次调用前解压引擎目录（模型 ~80MB 不入库）：

```bat
python -I -m zipfile -e "D:\dlkotenocr-lite\data\flutter_assets\app\app.zip" ocr_runtime
```

## 环境变量（全部可选）

| 变量 | 作用 | 默认 |
| --- | --- | --- |
| `KANBUN_LLM_API_KEY` | 現代語訳/語釈 的 LLM key（没配走 mock+词库） | 无 |
| `KANBUN_LLM_BASE_URL` / `KANBUN_LLM_MODEL` | OpenAI 兼容端点/模型名 | openai / gpt-4o-mini |
| `KANBUN_KANA_RATIO` | 假名分流阈值 | 0.3 |
| `KANBUN_OCR_ORDER` | OCR 行序 native/cluster | cluster |
| `KANBUN_OCR_JUNK_FILTER` | 垃圾框过滤开关 | 1 |
| `KANBUN_DB` | SQLite 路径 | kanbun.db |

## 测试

```
python -X utf8 -m pytest tests\test_api.py -v     # 14 条全过
```

## 评测分数（如实，v0.1 口径）

- `eval/golden.json` 200 条（kanbun.info 白文+書き下し文成对）。
- 精确匹配：**0/200**（引擎原始 / +全部规则 都是 0）。
- 编辑距离（归一化口径）：基线 22.14 → 全规则 21.02；**改善 124 条 / 变差 6 条 / 持平 70 条**。
- 分类（多标签）：助词错 92%、切分错 90%、旧字体 12%、专名 0.5%。
- 夜5 规则 C（て而して→て）曾带来 26 条改善但破坏经典句而撤销（见 REPORT_NIGHT7 §4）。

## 已知问题（v0.1，按严重程度排）

1. **訓読精确匹配 0/200**——长难句的助词插入位置、名词化（祠る者）、动词条目（壁す）
   是 mecab-kanbun 词典/解析层问题；简单句（王顧左右而言他 等）正确。
2. **再読文字只有「未」**（udkundoku 已知上限）：應・當・須・蓋・宜・將 未对应；駢文・诗难。
3. **OCR 无 ground truth**：不给准确率；刊本界框会被识别为「}」等符号行（过滤未覆盖）；
   絵本散字页面输出碎片；密集页识别 ~2.2s/行（87 行≈137s）。
4. **假名文本分流**：>30% 假名的输入不训读只转写——侯文/明治文书会被分流（行为正确但
   note 措辞可能引起误解）。
5. **語釈词库 209 条未经人工校对**（agent 整理），且功能词可能排进前 5 条。
6. **cached 路径偶发 2.4s 离群值**（原因未定位）。
7. guwenbert（BERT 依存）模型已下载但 PyPI supar 与 checkpoint 不兼容，未接入（Night5 报告）。
8. 瀏覽器人工确认清单（Night10）未由用户打勾。

## qkana shim 说明

`import udkundoku` 需要 UniDic qkana 词典；官方源 `clrd.ninjal.ac.jp` 在本机被墙
（TLS 重置/半阻断）。当前用 unidic_lite 冒充的 shim：
`D:\Python312\Lib\site-packages\unidic2ud\download\qkana\`（unidic_lite + 自定义 dicrc）。
可复现：`python -I tools/make_qkana_shim.py`。
在可达 NINJAL 的网络运行 `python -X utf8 tools/fetch_official_qkana.py` 即下载官方词典
（280MB，断点续传）并自动备份/替换 shim。**不要删 shim。**

## 结构

```
backend/       FastAPI(8000)：main / ocr_engine / kundoku_rules / db / llm / glossary_lexicon
frontend/      Vite+React+TS(5173)：行別対照・履歴・导出・响应式
tests/         pytest 14 条
eval/          golden.json 200 条 + night4/5 结果 + ocr_samples/
tools/         shim/评测/分类/挖掘/OCR 基准/下载脚本
ocr_runtime/   不入库：OCR 引擎+样张库（batch20 等）
ROADMAP.md     任务队列（Night 4-12 已 DONE，13+ 待做）
REPORT_NIGHT*.md
```
