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
import sys
import threading
import time
import uuid

from typing import Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend import db, llm
from backend.kundoku_rules import merge_proper_nouns, normalize_shinjitai, style_fix_with_hakubun
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

# NIGHT-D6: 桌面壳模式下后端兼顾托管前端。这里是 StaticFiles 的挂载点与
# index.html 的绝对路径；为 None 表示「纯 API 模式」。
# 之所以用模块级变量而不是在 _mount_web() 里再定义 @app.get("/")：Starlette
# 的路由按注册顺序匹配，本文件前面的 root() 会先命中，后注册的同路径永远不可达。
_WEB_DIST = None
_WEB_INDEX = None


def _web_index():
    from fastapi.responses import FileResponse
    return FileResponse(_WEB_INDEX)


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
    # D7 修正: 原为 `int = None`，pydantic v2 下 None 不满足 int，前端首次訓読
    # 必带 prev_request_id=null -> 422 "Input should be a valid integer"。
    # 前端 runKundoku() 在 lastRequestId 为 null 时就是发 null，所以旧代码
    # 「第一次点重新訓読」必然失败。这里允许 None。
    prev_request_id: Optional[int] = None


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
    # D6: sidecar 模式下先把端口让出来、再后台加载引擎。
    # 目的：桌面壳能在 1~2 秒内连上 /health（此时 engine_loaded=false），
    # 前端显示「引擎加载中」，而不是让用户对着白窗口等 10~30 秒。
    # 普通模式仍同步加载——tests 依赖 startup 返回时引擎已就绪。
    lazy = os.environ.get("KANBUN_LAZY_ENGINE", "").strip() in ("1", "true", "yes", "on")
    if lazy:
        def _bg():
            try:
                _load_engine()
                logger.info("udkundoku engine loaded")
            except Exception as e:
                global ENGINE_ERROR
                ENGINE_ERROR = repr(e)
                logger.exception("engine load failed: %r", e)
        threading.Thread(target=_bg, name="engine-loader", daemon=True).start()
    else:
        try:
            _load_engine()
            logger.info("udkundoku engine loaded")
        except Exception as e:  # 引擎失败也允许服务启动，/health 仍 ok，/api/kundoku 报错
            ENGINE_ERROR = repr(e)
            logger.exception("engine load failed: %r", e)
    logger.info("ocr available: %s", is_available())


@app.get("/")
def root():
    # D6: 桌面壳里后端同时托管前端，这时 / 要给 index.html 而不是 JSON。
    # 不能靠 _mount_web() 里再注册一个 @app.get("/")——Starlette 按注册顺序
    # 匹配，本函数在文件靠前处注册，永远先命中。所以这里查一个模块级变量。
    if _WEB_DIST:
        return _web_index()
    return {
        "service": "kanbun-kakikudashi",
        "version": "0.2.0-night2",
        "endpoints": ["/health", "/api/kundoku", "/api/ocr",
                      "/api/ocr/batch", "/api/ocr/batch/async", "/api/ocr/batch/{job_id}"],
    }


@app.get("/health")
def health():
    return {"ok": True, "engine_loaded": ENGINE is not None, "ocr_available": is_available(),
            "engine_error": ENGINE_ERROR}


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
    # D11：Rule D（これ→之）需要白文做护栏，改用 style_fix_with_hakubun
    if merge:
        t = _now_ms()
        kakikudashi = style_fix_with_hakubun(kakikudashi, text)
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


# ---------------------------------------------------------------------------
# D7: OCR 批量作业（后台跑 + 轮询进度）
#
# 原 POST /api/ocr/batch 是同步的：2 张图要 126 秒，期间没有任何反馈。
# 这里加一对端点，不改原端点：
#   POST /api/ocr/batch/async  -> {"job_id": ...}，立即返回，识别在后台线程串行跑
#   GET  /api/ocr/batch/<id>   -> 进度快照（percent / done / total / 当前文件）
#
# 作业只存在进程内存里（重启即丢）。OCR 结果本来就是「草稿」，落库的只有
# 训读结果，所以不做持久化；这也是 Night 11 串行不并行的延续。
# ---------------------------------------------------------------------------
_JOBS = {}
_JOBS_LOCK = threading.Lock()
_JOB_KEEP = 20          # 最多保留最近 20 个作业快照
_JOB_TTL_SEC = 3600     # 一小时前的作业，下一次创建时清掉


def _job_percent(job):
    """总进度百分比。

    只按「整张图完成数」算的话，单张图内部 30~50 秒 percent 一动不动
    （2 张图时前 47 秒全是 0%，然后一步跳到 50%）——实测就是这么难看。
    这里把当前这张图内部的行级进度折算进去：detect 占该图的 0~15%，
    recognize 占 15~100%。done 增加时 frac 归零，但 (done+1) 的跳幅
    始终大于丢失的 frac，所以整体仍然单调不减。
    """
    total = job["total"]
    if not total:
        return 0.0
    frac = 0.0
    if job["status"] == "running" and job["phase"]:
        pt = job["phase_total"]
        r = (job["phase_done"] / pt) if pt else 0.0
        if job["phase"] == "detect":
            frac = 0.15 * r
        elif job["phase"] == "recognize":
            frac = 0.15 + 0.85 * r
    return round(100.0 * (job["done"] + frac) / total, 1)


def _job_snapshot(job):
    """给 API 返回的作业视图（副本，避免调用方看到半更新的 dict）。"""
    with _JOBS_LOCK:
        return {
            "job_id": job["job_id"],
            "status": job["status"],            # queued|loading|running|done|error|cancelled
            "total": job["total"],
            "done": job["done"],
            "percent": _job_percent(job),
            "current_file": job["current_file"],
            "phase": job["phase"],              # 当前图片内部阶段：detect|recognize|""
            "phase_done": job["phase_done"],
            "phase_total": job["phase_total"],
            "elapsed_sec": round(time.time() - job["t0"], 1),
            "results": list(job["results"]),
            "error": job["error"],
            "disclaimer": DISCLAIMER,
        }


def _run_batch_job(job_id, files):
    """后台线程体：串行识别，边跑边更新 job 快照。"""
    with _JOBS_LOCK:
        job = _JOBS[job_id]
        job["status"] = "loading"
    try:
        if not is_available():
            with _JOBS_LOCK:
                job["status"] = "error"
                job["error"] = "OCR 运行目录缺失（ocr_runtime/），无法识别"
            return
        engine = get_engine()          # 首次可能 10~50 秒
        with _JOBS_LOCK:
            if job["status"] == "cancelled":
                return
            job["status"] = "running"

        for idx, (name, data) in enumerate(files):
            with _JOBS_LOCK:
                if job["status"] == "cancelled":
                    return
                job["current_file"] = name
                job["phase"] = ""
                job["phase_done"] = 0
                job["phase_total"] = 0

            if not data:
                item = {"file": name, "status": "empty"}
            else:
                def _cb(phase, d, t, _jid=job_id):
                    with _JOBS_LOCK:
                        j = _JOBS.get(_jid)
                        if j is None:
                            return
                        j["phase"] = phase
                        j["phase_done"] = d
                        j["phase_total"] = t

                try:
                    r = engine.recognize_bytes(data, progress_cb=_cb)
                    item = {
                        "file": name,
                        "hakubun": r["text"],
                        "status": "ok",
                        "line_count": r["line_count"],
                        "elapsed_sec": r["elapsed_sec"],
                    }
                except Exception as e:
                    logger.exception("batch ocr failed on %r", name)
                    item = {"file": name, "hakubun": "", "status": "ocr_error",
                            "note": "%r" % (e,)}

            with _JOBS_LOCK:
                job["results"].append(item)
                job["done"] = idx + 1
                job["phase"] = ""
                job["current_file"] = ""

        with _JOBS_LOCK:
            if job["status"] != "cancelled":     # 取消优先，别被收尾覆盖
                job["status"] = "done"
            job["elapsed_sec"] = round(time.time() - job["t0"], 1)
    except Exception as e:
        logger.exception("batch job %s crashed", job_id)
        with _JOBS_LOCK:
            job["status"] = "error"
            job["error"] = "%r" % (e,)


@app.post("/api/ocr/batch/async")
async def ocr_batch_async(files: list[UploadFile]):
    """D7: 提交批量 OCR 作业，立即返回 job_id；进度查 GET /api/ocr/batch/<id>。"""
    if not files:
        raise HTTPException(status_code=400, detail="files 为空")
    payload = []
    for f in files:
        payload.append((f.filename or "", await f.read()))

    job_id = uuid.uuid4().hex[:12]
    job = {
        "job_id": job_id,
        "status": "queued",
        "total": len(payload),
        "done": 0,
        "current_file": "",
        "phase": "",
        "phase_done": 0,
        "phase_total": 0,
        "results": [],
        "error": "",
        "t0": time.time(),
    }
    with _JOBS_LOCK:
        # 顺手清理：超 TTL 的、或超出保留条数的旧作业
        now = time.time()
        for k in [k for k, v in _JOBS.items()
                  if v["status"] in ("done", "error", "cancelled")
                  and now - v["t0"] > _JOB_TTL_SEC]:
            _JOBS.pop(k, None)
        while len(_JOBS) >= _JOB_KEEP:
            oldest = min(_JOBS.values(), key=lambda v: v["t0"])
            _JOBS.pop(oldest["job_id"], None)
        _JOBS[job_id] = job

    threading.Thread(target=_run_batch_job, args=(job_id, payload),
                     name="ocr-batch-%s" % job_id, daemon=True).start()
    return {"job_id": job_id, "total": len(payload), "status": "queued"}


@app.get("/api/ocr/batch/{job_id}")
def ocr_batch_progress(job_id: str):
    """D7: 查询批量 OCR 进度。完成前 done 单调递增；done==total 且 status=done 即结束。"""
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job 不存在（进程重启会清空作业表）")
    return _job_snapshot(job)


@app.post("/api/ocr/batch/{job_id}/cancel")
def ocr_batch_cancel(job_id: str):
    """D7: 请求取消作业。当前这张图跑完后停止，已在跑的推理不打断。"""
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job 不存在")
        if job["status"] in ("done", "error"):
            return {"job_id": job_id, "status": job["status"], "note": "已结束，无需取消"}
        job["status"] = "cancelled"
    return {"job_id": job_id, "status": "cancelled"}


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


# ---------------------------------------------------------------------------
# D6: 桌面壳模式——后端顺便把构建好的前端一起发出去。
#
# 为什么不是让 Tauri 直接加载 dist/ 再跨域调 127.0.0.1:8000：
#   那样每个请求都要 CORS 预检，还要在 CSP 里开白名单；而且端口是动态的。
# 改成后端托管后，页面与 API 同源（都是 http://127.0.0.1:<port>），
# 前端一行 CORS 配置都不用改。
#
# 只在 KANBUN_SERVE_WEB=1 或 sidecar 模式（KANBUN_SIDECAR=1）下挂载，
# 检测到 frontend/dist 才挂；开发时用 vite 代理，行为完全不变。
# ---------------------------------------------------------------------------
def _mount_web():
    global _WEB_DIST, _WEB_INDEX
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dist = os.path.join(root, "frontend_dist")
    if not os.path.isdir(dist):
        dist = os.path.join(root, "frontend", "dist")
    if not os.path.isdir(dist):
        logger.info("web: dist 不存在，仅提供 API（%s）", root)
        return False

    index = os.path.join(dist, "index.html")
    if not os.path.isfile(index):
        logger.info("web: %s 下没有 index.html，跳过", dist)
        return False

    _WEB_DIST = dist
    _WEB_INDEX = index

    app.mount("/assets", StaticFiles(directory=os.path.join(dist, "assets")), name="assets")

    # / 由前面注册的 root() 按 _WEB_DIST 分流，这里不再重复注册。

    # 单页应用：未命中的非 API 路径一律回 index.html（现在只有一屏，但便宜）
    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("health", "docs", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = os.path.join(dist, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(index)

    logger.info("web: 已挂载 %s", dist)
    return True


if os.environ.get("KANBUN_SERVE_WEB", "").strip() in ("1", "true", "yes", "on") \
        or os.environ.get("KANBUN_SIDECAR", "") == "1":
    _mount_web()