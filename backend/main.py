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
import collections
import logging
import os
import re
import time

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend import db, llm
from backend.kundoku_rules import merge_proper_nouns, normalize_shinjitai, style_fix
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

# NIGHT-D4: 分段计时开关。默认关闭（不改变生产路径的性能与行为）；
# 设 KANBUN_TIMING=1 后，每次 /api/kundoku 往 logger 打一行
# `TIMING <request> <总ms> = engine X | merge X | kaeriten X | translate X | style X | glossary X | db X`
_TIMING = os.environ.get("KANBUN_TIMING", "").strip() in ("1", "true", "yes", "on")


def _now_ms():
    return time.perf_counter() * 1000.0


def _normalize_kaeriten(text: str) -> str:
    for k, v in KAERITEN_MAP.items():
        text = text.replace(k, v)
    return text


class KundokuRequest(BaseModel):
    text: str
    # NIGHT7: 纠错工作流——OCR 原始白文（纠错基线）与上一条请求 id（翻回链）
    ocr_hakubun: str = ""
    prev_request_id: int = None


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
    request_id: int = None      # NIGHT7: 落库后的请求 id（前端翻回链用）
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


# NIGHT7: 行级缓存——"改一行只重跑一行"。键 = (行文本, merge)；
# 值 = (kaeriten_raw, kakikudashi_raw)。风格/正字化在取用时按开关叠加。
_SENT_CACHE = collections.OrderedDict()
_SENT_CACHE_MAX = 500


def _kundoku_line_cached(line: str, merge: bool):
    """行级缓存查询（Night 7）。计时版本 _kundoku_line_timed 复用本函数。"""
    return _kundoku_line_timed(line, merge, {})


def _kundoku_line_timed(line: str, merge: bool, seg: dict):
    """与 _kundoku_line_cached 同逻辑，但把各段耗时累加进 seg（NIGHT-D4 定位用）。

    seg 的键：engine / merge / kaeriten / translate / cache_hit
    """
    key = (line, merge)
    if key in _SENT_CACHE:
        _SENT_CACHE.move_to_end(key)
        seg["cache_hit"] += 1
        return _SENT_CACHE[key]
    t = _now_ms()
    entry = ENGINE(line)
    seg["engine"] += _now_ms() - t
    if merge:
        t = _now_ms()
        entry = merge_proper_nouns(entry)
        seg["merge"] += _now_ms() - t
    t = _now_ms()
    k_raw = entry.kaeriten()
    seg["kaeriten"] += _now_ms() - t
    t = _now_ms()
    kk_raw = _extract_kakikudashi(__import__("udkundoku").translate(entry, raw=True))
    seg["translate"] += _now_ms() - t
    _SENT_CACHE[key] = (k_raw, kk_raw)
    if len(_SENT_CACHE) > _SENT_CACHE_MAX:
        _SENT_CACHE.popitem(last=False)
    return _SENT_CACHE[key]


def _kundoku_result_for(text: str, merge: bool, ortho: bool, use_cache: bool, seg=None):
    """返回 (kaeriten_text, kaeriten_text_raw, kakikudashi)。

    use_cache=True 时按行拆分、逐行查缓存（改过的行才重算）；
    False 时走整段路径（Night1-3 原始行为，供测试对照）。
    seg 不为 None 时累加分段耗时（NIGHT-D4）。
    """
    if seg is None:
        seg = {}
    if use_cache:
        k_parts, kk_parts, kraw_parts = [], [], []
        for ln in text.split("\n"):
            s = ln.strip()
            if not s:
                continue
            k_raw, kk_raw = _kundoku_line_timed(s, merge, seg)
            kraw_parts.append(k_raw)
            k_parts.append(_normalize_kaeriten(k_raw))
            kk_parts.append(kk_raw)
        kaeriten_raw = "\n".join(kraw_parts)
        kaeriten_text = "\n".join(k_parts)
        kakikudashi = "\n".join(kk_parts)
    else:
        t = _now_ms()
        entry = ENGINE(text)
        seg["engine"] += _now_ms() - t
        if merge:
            t = _now_ms()
            entry = merge_proper_nouns(entry)
            seg["merge"] += _now_ms() - t
        t = _now_ms()
        kaeriten_raw = entry.kaeriten()
        seg["kaeriten"] += _now_ms() - t
        t = _now_ms()
        kaeriten_text = _normalize_kaeriten(kaeriten_raw)
        kakikudashi = _extract_kakikudashi(__import__("udkundoku").translate(entry, raw=True))
        seg["translate"] += _now_ms() - t
    # NIGHT4 Rule A：显示风格修正（ふ→う、は曰く→曰く），merge 开关下生效
    if merge:
        t = _now_ms()
        kakikudashi = style_fix(kakikudashi)
        seg["style"] += _now_ms() - t
    return kaeriten_text, kaeriten_raw, kakikudashi


@app.post("/api/kundoku", response_model=KundokuResponse)
def kundoku(
    req: KundokuRequest,
    merge: bool = Query(default=True, description="是否启用专名合并等后处理规则"),
    ortho: bool = Query(default=True, description="是否对書き下し文做旧字体→新字体显示转换"),
    cache: bool = Query(default=True, description="NIGHT7: 行级缓存（改过的行才重算）；false 走整段路径"),
):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 为空，请先输入白文")

    t_req = _now_ms()
    seg = collections.defaultdict(float)

    # NIGHT3: 假名白文分流——假名文学文本（竹取物語等）与假名占多数的
    # 训读体/明治文书（侯文）都不适用漢文訓読，不做二次插助词。
    if detect_text_type(text) == "kana":
        if _TIMING:
            logger.info("TIMING %d chars cache=%s hit=0 total=%.1fms | kana-branch (no kundoku)",
                        len(text), cache, _now_ms() - t_req)
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
        kaeriten_text, kaeriten_raw, kakikudashi = _kundoku_result_for(
            text, merge, ortho, use_cache=cache, seg=seg)
    except Exception as e:
        logger.exception("kundoku failed on %r", text[:50])
        raise HTTPException(status_code=500, detail="訓読処理失敗: %r" % (e,))

    # 現代語訳 / 語釈：适配层在 backend/llm.py。
    # 无 KANBUN_LLM_API_KEY 时：語釈先查 500 条文语词库（NIGHT8/D3）、modern 留占位。
    t = _now_ms()
    modern = llm.modern_translate(text, kakikudashi)
    glossary = llm.glossary(text, kakikudashi)
    seg["glossary"] = _now_ms() - t

    request_id = None
    t = _now_ms()
    try:
        request_id = db.save_kundoku(
            text, kaeriten_text, kakikudashi,
            ocr_hakubun=(req.ocr_hakubun or None),
            prev_request_id=req.prev_request_id,
        )
    except Exception:
        logger.exception("db save failed (API 照常返回)")
    seg["db"] = _now_ms() - t

    if _TIMING:
        logger.info(
            "TIMING %d chars cache=%s hit=%d total=%.1fms | engine %.1f | merge %.1f | "
            "kaeriten %.1f | translate %.1f | style %.1f | glossary %.1f | db %.1f",
            len(text), cache, int(seg.get("cache_hit", 0)), _now_ms() - t_req,
            seg["engine"], seg["merge"], seg["kaeriten"], seg["translate"],
            seg["style"], seg["glossary"], seg["db"],
        )

    return KundokuResponse(
        hakubun=text,
        kaeriten_text=kaeriten_text,
        kaeriten_text_raw=kaeriten_raw,
        kakikudashi=normalize_shinjitai(kakikudashi) if ortho else kakikudashi,
        modern=modern,
        glossary=glossary,
        request_id=request_id,
    )


@app.get("/api/history")
def history(limit: int = Query(default=20, description="返回最近 N 条（1~100）")):
    """NIGHT7: 历史记录——翻回上一条訓読请求。"""
    limit = max(1, min(limit, 100))
    return {"items": db.get_history(limit)}


@app.post("/api/ocr/batch")
async def ocr_batch(files: list[UploadFile]):
    """NIGHT11: OCR 批量端点——多张图按顺序串行识别（不并行压 Celeron）。"""
    if not files:
        raise HTTPException(status_code=400, detail="files 为空")
    results = []
    t0 = time.time()
    for f in files:
        data = await f.read()
        if not data:
            results.append({"file": f.filename or "", "status": "empty"})
            continue
        if not is_available():
            results.append({"file": f.filename or "", "hakubun": "", "status": "not_implemented_yet",
                            "note": "OCR 运行目录缺失"})
            continue
        try:
            engine = await run_in_threadpool(get_engine)
            r = await run_in_threadpool(engine.recognize_bytes, data)
            results.append({
                "file": f.filename or "",
                "hakubun": r["text"],
                "status": "ok",
                "line_count": r["line_count"],
                "elapsed_sec": r["elapsed_sec"],
            })
        except Exception as e:
            results.append({"file": f.filename or "", "hakubun": "", "status": "ocr_error",
                            "note": "%r" % (e,)})
    return {
        "n": len(results),
        "total_elapsed_sec": round(time.time() - t0, 1),
        "results": results,
        "disclaimer": DISCLAIMER,
    }


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
