# kanbun-kakikudashi

漢文 → 書き下し文 Web MVP（第 1 夜：骨架验证）。

两个入口汇到同一条訓読管线：

- 入口 A：粘贴活字漢文文本
- 入口 B：上传图片（くずし字 OCR，今晚为占位）

输出四样：

1. 返り点付き原文
2. 書き下し文（含送り仮名）
3. 現代語訳（今晚占位，待接 LLM）
4. 語釈（今晚占位，待接 LLM）

## 结构

```
backend/    FastAPI + Uvicorn（端口 8000），核心引擎 udkundoku
frontend/   Vite + React + TypeScript 单页（端口 5173，/api 代理到 8000）
eval/       golden.json 评测集（10 条 白文+書き下し文 成对样本）
tools/      环境修复与实测脚本（qkana shim、UD-Kundoku 三句实测）
```

## 启动

```bat
:: 后端（D:\Python312）
set PATH=D:\Python312;D:\Python312\Scripts;%PATH%
python -m uvicorn backend.main:app --port 8000

:: 前端
set PATH=D:\nodejs;%PATH%
cd frontend && npm install && npm run dev
```

## 环境备注（本机 NEC / Win10 IoT）

- Python 3.12.10 在 `D:\Python312`，Node v26.13.1 在 `D:\nodejs`，不在系统 PATH 里，需手动加。
- `clrd.ninjal.ac.jp`（UniDic 下载源）TLS 被重置，`import udkundoku` 会卡死。
  解法：`python -I tools/make_qkana_shim.py` 用本地 unidic_lite 词典生成
  `unidic2ud/download/qkana` shim（详见 `tools/make_qkana_shim.py` 头部注释）。
  详细经过见 `REPORT_NIGHT1.md`。

## 约束

- 只本地 git 提交，不建远程仓库、不推远程。
- 現代語訳 / 語釈 的 LLM 推理 key 由用户以后单独提供，代码里不写任何 key。
- 每句输出标注：「AI 初稿，仅供参考，请以原文和专业判断为准。」
