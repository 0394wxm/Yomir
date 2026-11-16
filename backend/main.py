# -*- coding: utf-8 -*-
"""
kanbun-kakikudashi 后端骨架（Night 1）。

- GET  /health        健康检查
- POST /api/kundoku   白文 -> 返り点付き原文 / 書き下し文（UD-Kundoku 本地引擎）
- POST /api/ocr       图片 OCR（今晚占位，NDL 古典籍 OCR-Lite 尚未接入）

注意:
- 現代語訳 (modern) 与 語釈 (glossary) 今晚不接任何 LLM API，留空 + TODO。
  产品推理用的 key 由用户以后单独提供，绝不能写进代码。
- 返回的每个输出都带免责说明，前端同样显示。
"""
import logging
import re

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger("kanbun")
logging.basicConfig(level=logging.INFO)

# udkanbun.kaeriten 用的 Unicode 合字 -> 通用写法
KAERITEN_MAP = {
    "\u3191": "レ",              # ㆑ レ点
    "\u3192": "一", "\u3193": "二", "\u3194": "三", "\u3195": "四",  # 一二点
    "\u3196": "上", "\u3197": "中", "\u3198": "下",                  # 上下点
    "\u3199": "甲", "\u319A": "乙", "\u319B": "丙", "\u319C": "丁",  # 甲乙点
    "\u319D": "天", "\u319E": "地", "\u319F": "人",                  # 天地点
}

DISCLAIMER = "AI 初稿，仅供参考，请以原文和专业判断为准。"


def _normalize_kaeriten(text: str) -> str:
    for k, v in KAERITEN_MAP.items():
        text = text.replace(k, v)
    return text


class KundokuRequest(BaseModel):
    text: str


class KundokuResponse(BaseModel):
    hakubun: str
    kaeriten_text: str
    kakikudashi: str
    modern: str
    glossary: list
    disclaimer: str = DISCLAIMER
    engine: str = "udkundoku"
    error: str = ""


app = FastAPI(title="kanbun-kakikudashi", version="0.1.0-night1")

ENGINE = None          # udkundoku pipeline, 启动时惰性加载一次
ENGINE_ERROR = ""


def _load_engine():
    """加载 udkundoku（本地引擎，含 MeCab + UDPipe 模型，全离线）。"""
    global ENGINE, ENGINE_ERROR
    if ENGINE is not None:
        return
    import udkundoku  # import 时会找 unidic2ud/download/qkana（见 tools/make_qkana_shim.py）

    ENGINE = udkundoku.load(MeCab=True, Danku=False)
    # 预热一次，避免首个请求慢
    ENGINE("王顧左右而言他")
    ENGINE_ERROR = ""


@app.on_event("startup")
def startup():
    try:
        _load_engine()
        logger.info("udkundoku engine loaded")
    except Exception as e:  # 引擎失败也允许服务启动，/health 仍 ok，/api/kundoku 报错
        ENGINE_ERROR = repr(e)
        logger.exception("engine load failed: %r", e)


@app.get("/")
def root():
    return {
        "service": "kanbun-kakikudashi",
        "version": "0.1.0-night1",
        "endpoints": ["/health", "/api/kundoku", "/api/ocr"],
    }


@app.get("/health")
def health():
    return {"ok": True, "engine_loaded": ENGINE is not None}


def _extract_kakikudashi(conllu: str) -> str:
    lines = []
    for line in conllu.split("\n"):
        if line.startswith("# text = "):
            lines.append(line[9:])
    return "\n".join(lines)


@app.post("/api/kundoku", response_model=KundokuResponse)
def kundoku(req: KundokuRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 为空，请先输入白文")

    if ENGINE is None:
        raise HTTPException(
            status_code=503,
            detail="udkundoku 引擎未加载成功: %s；请先运行 python -I tools/make_qkana_shim.py 并重启" % (ENGINE_ERROR or "unknown"),
        )

    try:
        entry = ENGINE(text)
        kaeriten_text = _normalize_kaeriten(entry.kaeriten())
        kakikudashi = _extract_kakikudashi(__import__("udkundoku").translate(entry, raw=True))
    except Exception as e:
        logger.exception("kundoku failed on %r", text[:50])
        raise HTTPException(status_code=500, detail="訓読処理失敗: %r" % (e,))

    # TODO(Night2+): modern（現代語訳）与 glossary（語釈）接入 LLM。
    # 约束: 推理 key 由用户单独提供，不在代码/环境里写死，也不从 ZCode 抓 token。
    return KundokuResponse(
        hakubun=text,
        kaeriten_text=kaeriten_text,
        kakikudashi=kakikudashi,
        modern="",       # 占位: 待接入 LLM
        glossary=[],     # 占位: 待接入 LLM
    )


@app.post("/api/ocr")
async def ocr(file: UploadFile):
    # Night 1 占位: NDL 古典籍 OCR-Lite 只做了“GUI 能否启动”的验证，
    # 命令行/管道方式接入留到下一夜。不要假装它能识别。
    await file.read()  # 读掉内容避免连接悬挂，不做识别、不落盘
    return {
        "hakubun": "",
        "status": "not_implemented_yet",
        "note": "OCR agent 尚未接入（NDL 古典籍 OCR-Lite）。今晚请先粘贴文本或手动输入白文。",
    }
