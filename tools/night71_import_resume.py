# -*- coding: utf-8 -*-
"""night71_import_resume.py — N71②：import_pid.py 的增量续跑版（墨場必携 1033232 专用，通用 PID 参数）。

背景：import_pid.py 的 book.md 只在结尾写出，进程被硬杀（N71 夜间宿主重试事故）后
449 页 OCR 结果不可恢复。本脚本同款产品流（get_engine().recognize_bytes →
_kundoku_result_for(merge=True, ortho=True, use_cache=True) → 同一 book.md 模板），
但**每页完成即整本落盘**——再被杀时重启可从已完成的页续跑（跳过已有页段）。
末尾 [done] 行与 import_pid.py 同格式（管线 night71_pipeline.py 的探测正则兼容）。
页图仍不入库。stdout 追加到原导入日志（管线轮询同一文件）。

用法: python tools/night71_import_resume.py <PID>
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_engine import get_engine  # noqa: E402
from backend.main import _kundoku_result_for, _load_engine  # noqa: E402

pid = sys.argv[1] if len(sys.argv) > 1 else "1033232"
out_dir = os.path.join(ROOT, "eval", "import_pid_%s" % pid)
pages_dir = os.path.join(out_dir, "pages")
out_md = os.path.join(out_dir, "book.md")

# ---- manifest ----
req = urllib.request.Request(
    "https://dl.ndl.go.jp/api/iiif/%s/manifest.json" % pid,
    headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    manifest = json.load(r)
title = manifest.get("label", str(pid))
canvases = manifest.get("sequences", [{}])[0].get("canvases", [])
n_manifest = len(canvases)
print("[manifest] %s: %d pages（resume 版）" % (title, n_manifest), flush=True)

paths = []
for i in range(1, n_manifest + 1):
    dst = os.path.join(pages_dir, "p%03d.jpg" % i)
    if not os.path.exists(dst):
        # 从 canvas 抽 URL 下载（缓存；一般全部已缓存）
        c = canvases[i - 1]
        u = None
        for im in c.get("images", []):
            res = im.get("resource", {})
            u = res.get("@id") or res.get("id")
        u1400 = (u or "").replace("/full/full/", "/full/1400,/")
        req = urllib.request.Request(u1400, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f:
            f.write(r.read())
    paths.append(dst)
print("[dl] ready: %d files" % len(paths), flush=True)

print("[engine] loading...", flush=True)
t0 = time.time()
ocr = get_engine()
_load_engine()
print("[engine] load %.1fs" % (time.time() - t0), flush=True)

# ---- 已完成页段恢复 ----
doc = ["# 批量导入：%s（NDL %s）" % (title, pid), ""]
done_pages = set()
if os.path.exists(out_md):
    raw = open(out_md, encoding="utf-8").read()
    done_pages = set(int(m) for m in re.findall(r"^## p(\d+)$", raw, re.M))
    if done_pages:
        doc = raw.split("\n")
        # 去掉旧 footer（重新生成）
        while doc and (doc[-1].startswith("耗时：") or doc[-1] == "---" or doc[-1] == ""):
            doc.pop()
        print("[resume] 已完成 %d 页（%s…%s）——跳过其 OCR"
              % (len(done_pages), min(done_pages), max(done_pages)), flush=True)


def flush_doc():
    with open(out_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(doc) + "\n")


total_ocr = total_kun = 0.0
n_ok = n_skip = 0
t_start = time.time()
for i, path in enumerate(paths, 1):
    if i in done_pages:
        continue
    with open(path, "rb") as f:
        data = f.read()
    t1 = time.time()
    try:
        r = ocr.recognize_bytes(data)
    except Exception as e:
        n_skip += 1
        doc += ["## p%03d" % i, "", "(OCR 失败: %r)" % (e,), ""]
        flush_doc()
        print("[p%03d] OCR error %r" % (i, e), flush=True)
        continue
    ocr_sec = time.time() - t1
    total_ocr += ocr_sec
    hakubun = r["text"]
    if not hakubun.strip():
        n_skip += 1
        doc += ["## p%03d" % i, "", "(0 行)", ""]
        flush_doc()
        print("[p%03d] 0 行" % i, flush=True)
        continue
    t2 = time.time()
    try:
        kaeriten, _raw, kakikudashi = _kundoku_result_for(hakubun, merge=True, ortho=True,
                                                          use_cache=True)
    except Exception as e:
        # udkanbun kaeriten 偶发 IndexError（N71 p450 附近密页）——页级容错：白文保留、訓読记失败，整本继续
        n_skip += 1
        doc += ["## p%03d" % i, "", "**白文**", "", "```", hakubun, "```", "",
                "(训读失败: %r)" % (e,), ""]
        flush_doc()
        print("[p%03d] kundoku error %r" % (i, e), flush=True)
        continue
    kun_sec = time.time() - t2
    total_kun += kun_sec
    n_ok += 1
    print("[p%03d] ocr %.1fs lines=%d kundoku %.1fs" % (i, ocr_sec, r["line_count"], kun_sec),
          flush=True)
    doc += [
        "## p%03d" % i,
        "",
        "**白文**",
        "", "```", hakubun, "```", "",
        "**書き下し文（merge+ortho）**",
        "", "```", kakikudashi, "```", "",
    ]
    flush_doc()

doc += ["---", "",
        "耗时：OCR %.1fs / 训读 %.1fs；成功 %d 页，跳过/失败 %d 页（共 %d 页；本次续跑 %d 页）"
        % (total_ocr, total_kun, len(done_pages) + n_ok, n_skip, len(paths), len(paths) - len(done_pages)),
        ""]
flush_doc()
print("[done] ok=%d skip=%d ocr=%.1fs kun=%.1fs -> %s（resume：先前已完成 %d 页）"
      % (len(done_pages) + n_ok, n_skip, total_ocr, total_kun, out_md, len(done_pages)), flush=True)
print("[wall] %.1f 分钟" % ((time.time() - t_start) / 60.0), flush=True)
