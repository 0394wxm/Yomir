# -*- coding: utf-8 -*-
"""
kanbun-kakikudashi 后端（Night 2）。

- GET  /health        健康检查
- POST /api/kundoku   白文 -> 返り点付き原文 / 書き下し文（UD-Kundoku 本地引擎）+ SQLite 落库
- POST /api/ocr       图片 -> 白文（NDL 古典籍 OCR-Lite，Night 2 接通）

Night 2 变更:
- /api/ocr 从占位改为真实 OCR（backend/ocr_engine.py，NDL ndlkotenocr-lite CC BY 4.0）。
- kundoku 结果落 SQLite（backend/db.py，requests/results 两表）。
- 現代語訳/語釈走 backend/llm.py 适配层：无 KANBUN_LLM_API_KEY 时 mock 返回占位。
  key 由用户以后经环境变量提供，代码里不写死、不从 ZCode 抓 token。
"""
import logging
import os
import re

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend import db, llm
from backend.kundoku_rules import merge_proper_nouns, normalize_shinjitai
from backend.ocr_engine import get_engine, is_available

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
    # raw 版保留 udkanbun 的合字（㆒㆓㆑…），前端做ルビ用（合字无歧义，
    # 不会把白文里的“一/上/中”等汉字误当返り点）
    kaeriten_text_raw: str = ""
    kakikudashi: str
    modern: str
    glossary: list
    disclaimer: str = DISCLAIMER
    engine: str = "udkundoku"
    # NIGHT3: 文本类型分流。kana（假名文学文本）不进 UD-Kundoku，
    # 只回显原文 + 提示，避免输出乱插助词的“書き下し文”。
    text_type: str = "kanbun"   # "kanbun" | "kana"
    note: str = ""
    error: str = ""


def detect_text_type(text: str) -> str:
    """按假名比例分流：假名（平假名+片假名）占非标点字符 >30% 判为假名文学文本。

    阈值可经 KANBUN_KANA_RATIO 环境变量调整。漢文白文（kanbun.info 等）
    基本全汉字+句读点，比例接近 0；竹取物語等假名文远超 30%。
    """
    try:
        threshold = float(os.environ.get("KANBUN_KANA_RATIO", "0.3"))
    except ValueError:
        threshold = 0.3
    chars = [c for c in text if not c.isspace() and c not in "、。，．・「」『』（）！？―ー"]
    if not chars:
        return "kanbun"
    kana = sum(1 for c in chars if ("\u3041" <= c <= "\u309f") or ("\u30a0" <= c <= "\u30ff"))
    return "kana" if (kana / len(chars)) > threshold else "kanbun"


app = FastAPI(title="kanbun-kakikudashi", version="0.2.0-night2")

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
    db.init_db()
    try:
        _load_engine()
        logger.info("udkundoku engine loaded")
    except Exception as e:  # 引擎失败也允许服务启动，/health 仍 ok，/api/kundoku 报错
        ENGINE_ERROR = repr(e)
        logger.exception("engine load failed: %r", e)
    logger.info("ocr available: %s", is_available())


@app.get("/")
def root():
    return {
        "service": "kanbun-kakikudashi",
        "version": "0.2.0-night2",
        "endpoints": ["/health", "/api/kundoku", "/api/ocr"],
    }


@app.get("/health")
def health():
    return {"ok": True, "engine_loaded": ENGINE is not None, "ocr_available": is_available()}


def _extract_kakikudashi(conllu: str) -> str:
    lines = []
    for line in conllu.split("\n"):
        if line.startswith("# text = "):
            lines.append(line[9:])
    return "\n".join(lines)


@app.post("/api/kundoku", response_model=KundokuResponse)
def kundoku(
    req: KundokuRequest,
    merge: bool = Query(default=True, description="是否启用专名合并等后处理规则"),
    ortho: bool = Query(default=True, description="是否对書き下し文做旧字体→新字体显示转换"),
):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 为空，请先输入白文")

    # NIGHT3: 假名白文分流——假名文学文本（竹取物語等）与假名占多数的
    # 训读体/明治文书（侯文）都不适用漢文訓読，不做二次插助词。
    if detect_text_type(text) == "kana":
        return KundokuResponse(
            hakubun=text,
            kaeriten_text="",
            kaeriten_text_raw="",
            kakikudashi="",
            modern="",
            glossary=[],
            text_type="kana",
            note="假名为主的文本（假名文学・训读体・侯文等）不适用漢文訓読，"
                 "本接口不做訓読转换；请直接使用上方的白文转写。" + DISCLAIMER,
        )

    if ENGINE is None:
        raise HTTPException(
            status_code=503,
            detail="udkundoku 引擎未加载成功: %s；请先运行 python -I tools/make_qkana_shim.py 并重启" % (ENGINE_ERROR or "unknown"),
        )

    try:
        entry = ENGINE(text)
        if merge:
            entry = merge_proper_nouns(entry)  # Night 2: 专名切分错误的后处理（见 kundoku_rules.py）
        kaeriten_raw = entry.kaeriten()
        kaeriten_text = _normalize_kaeriten(kaeriten_raw)
        kakikudashi = _extract_kakikudashi(__import__("udkundoku").translate(entry, raw=True))
    except Exception as e:
        logger.exception("kundoku failed on %r", text[:50])
        raise HTTPException(status_code=500, detail="訓読処理失敗: %r" % (e,))

    # 現代語訳 / 語釈：适配层在 backend/llm.py。
    # 无 KANBUN_LLM_API_KEY 时 mock 返回占位，不联网、不写死 key。
    modern = llm.modern_translate(text, kakikudashi)
    glossary = llm.glossary(text)

    try:
        db.save_kundoku(text, kaeriten_text, kakikudashi)
    except Exception:
        logger.exception("db save failed (API 照常返回)")

    return KundokuResponse(
        hakubun=text,
        kaeriten_text=kaeriten_text,
        kaeriten_text_raw=kaeriten_raw,
        kakikudashi=normalize_shinjitai(kakikudashi) if ortho else kakikudashi,
        modern=modern,
        glossary=glossary,
    )


@app.post("/api/ocr")
async def ocr(file: UploadFile):
    """图片 -> 白文。Night 2 接通 NDL 古典籍 OCR-Lite（进程内，首调用加载模型约 10~30 秒）。"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="上传内容为空")
    if not is_available():
        return {
            "hakubun": "",
            "status": "not_implemented_yet",
            "note": "OCR 运行目录缺失：请按 backend/ocr_engine.py 头部注释解压 app.zip 到 ocr_runtime/。",
        }
    try:
        engine = await run_in_threadpool(get_engine)
        result = await run_in_threadpool(engine.recognize_bytes, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("ocr failed")
        return {"hakubun": "", "status": "ocr_error", "note": "OCR 处理失败: %r" % (e,)}
    return {
        "hakubun": result["text"],
        "status": "ok",
        "line_count": result["line_count"],
        "elapsed_sec": result["elapsed_sec"],
        "note": "NDL 古典籍 OCR-Lite（ndl-lab/ndlkotenocr-lite, CC BY 4.0）。白文可修改，请以原文为准。",
        "disclaimer": DISCLAIMER,
    }
