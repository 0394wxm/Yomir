# -*- coding: utf-8 -*-
"""import_pid.py — 任意 NDL PID 整本导入：IIIF manifest → 逐页下载 → OCR → 训读 → 汇总（NIGHT42）。

用法: python tools/import_pid.py <pid> [--limit N] [--start K] [--out eval/import_pid_<pid>]
- 页清单来自 IIIF Presentation manifest（dl.ndl.go.jp 公开）；
- 页图下载 full/1400,/0/default.jpg 到 <out>/pages/（缓存，已存在则跳过下载）；
- OCR/kundoku 与 tools/import_book.py 同一产品流；单页失败跳过并记录。
产出: <out>/book.md + 控制台摘要。页图不入库。
"""
import json
import os
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_engine import get_engine  # noqa: E402
from backend.main import _kundoku_result_for, _load_engine  # noqa: E402

args = sys.argv[1:]
pid = args[0]


def argval(flag, default=None):
    return args[args.index(flag) + 1] if flag in args else default


limit = int(argval("--limit", "0"))          # 0 = 全本
start = int(argval("--start", "0"))
out_dir = os.path.join(ROOT, argval("--out", "eval/import_pid_%s" % pid))
pages_dir = os.path.join(out_dir, "pages")
os.makedirs(pages_dir, exist_ok=True)

req = urllib.request.Request(
    "https://dl.ndl.go.jp/api/iiif/%s/manifest.json" % pid,
    headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    manifest = json.load(r)
title = manifest.get("label", str(pid))
canvases = manifest.get("sequences", [{}])[0].get("canvases", [])
print("[manifest] %s: %d pages" % (title, len(canvases)), flush=True)

# 从 canvas 里抽 1400px 图 URL
img_urls = []
for c in canvases:
    u = None
    for im in c.get("images", []):
        res = im.get("resource", {})
        u = res.get("@id") or res.get("id")
    img_urls.append(u)

if start:
    img_urls = img_urls[start:]
if limit:
    img_urls = img_urls[:limit]
print("[plan] importing %d pages (start=%d, limit=%s)" % (len(img_urls), start, limit or "all"),
      flush=True)

# 下载（缓存）
paths = []
for i, u in enumerate(img_urls):
    if not u:
        continue
    dst = os.path.join(pages_dir, "p%03d.jpg" % (start + i + 1))
    if not os.path.exists(dst):
        t = time.time()
        # resource @id 已含 /full/full/0/default.jpg —— 只把尺寸段换成 1400px
        u1400 = u.replace("/full/full/", "/full/1400,/")
        req = urllib.request.Request(u1400, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f:
            f.write(r.read())
        if (i + 1) % 5 == 0:
            print("[dl] %d/%d %.1fs" % (i + 1, len(img_urls), time.time() - t), flush=True)
    paths.append(dst)
print("[dl] ready: %d files" % len(paths), flush=True)

print("[engine] loading...", flush=True)
t0 = time.time()
ocr = get_engine()
_load_engine()
print("[engine] load %.1fs" % (time.time() - t0), flush=True)

doc = ["# 批量导入：%s（NDL %s）" % (title, pid), ""]
total_ocr = total_kun = 0.0
n_ok = n_skip = 0
for i, path in enumerate(paths, start + 1):
    with open(path, "rb") as f:
        data = f.read()
    t1 = time.time()
    try:
        r = ocr.recognize_bytes(data)
    except Exception as e:
        n_skip += 1
        doc += ["## p%03d" % i, "", "(OCR 失败: %r)" % (e,), ""]
        print("[p%03d] OCR error %r" % (i, e), flush=True)
        continue
    ocr_sec = time.time() - t1
    total_ocr += ocr_sec
    hakubun = r["text"]
    if not hakubun.strip():
        n_skip += 1
        doc += ["## p%03d" % i, "", "(0 行)", ""]
        print("[p%03d] 0 行" % i, flush=True)
        continue
    t2 = time.time()
    kaeriten, _raw, kakikudashi = _kundoku_result_for(hakubun, merge=True, ortho=True,
                                                      use_cache=True)
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

doc += ["---", "", "耗时：OCR %.1fs / 训读 %.1fs；成功 %d 页，跳过/失败 %d 页（共 %d 页）"
        % (total_ocr, total_kun, n_ok, n_skip, len(paths)), ""]
out_md = os.path.join(out_dir, "book.md")
with open(out_md, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(doc))
print("[done] ok=%d skip=%d ocr=%.1fs kun=%.1fs -> %s" % (n_ok, n_skip, total_ocr, total_kun, out_md),
      flush=True)
