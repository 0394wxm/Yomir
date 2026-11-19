# -*- coding: utf-8 -*-
"""import_book.py — 批量导入一本古籍：批量 OCR（产品流）→ 白文 → 训读 → 汇总文档（NIGHT41）。

用法: python tools/import_book.py <stem1> <stem2> ... [--out eval/import_<name>]
页图取 ocr_runtime/samples/batch20/（Night6 样张库，manifest 记 URL）。
产出: <out>/book.md（逐页：白文 / 返り点付き / 書き下し文）+ 控制台耗时摘要。
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.ocr_engine import get_engine  # noqa: E402
from backend.main import _kundoku_result_for, _load_engine  # noqa: E402

SAMPLE_DIR = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")

args = sys.argv[1:]
out_dir = os.path.join(ROOT, "eval", "import_rongo")
if "--out" in args:
    out_dir = os.path.join(ROOT, args[args.index("--out") + 1])
    args = args[:args.index("--out")] + args[args.index("--out") + 2:]
stems = args

with open(os.path.join(SAMPLE_DIR, "manifest.json"), encoding="utf-8") as f:
    manifest = {m["file"]: m for m in json.load(f)}

os.makedirs(out_dir, exist_ok=True)

print("[engine] loading OCR...", flush=True)
t0 = time.time()
ocr = get_engine()
print("[engine] ocr load %.1fs" % (time.time() - t0), flush=True)
print("[engine] loading kundoku...", flush=True)
t0 = time.time()
_load_engine()
print("[engine] kundoku load %.1fs" % (time.time() - t0), flush=True)

doc = ["# 批量导入：論語序説等（NDL %s）" % "11892692", ""]
total_ocr = total_kun = 0.0
for stem in stems:
    fname = stem + ".jpg"
    path = os.path.join(SAMPLE_DIR, fname)
    m = manifest[fname]
    with open(path, "rb") as f:
        data = f.read()
    t1 = time.time()
    r = ocr.recognize_bytes(data)
    ocr_sec = time.time() - t1
    total_ocr += ocr_sec
    hakubun = r["text"]
    if not hakubun.strip():
        print("[%s] 0 行（插图页），跳过训读" % fname, flush=True)
        doc += ["## %s（%s）" % (fname, m.get("note", "")), "", "(0 行——插图页)", ""]
        continue
    seg = {}
    t2 = time.time()
    kaeriten, _raw, kakikudashi = _kundoku_result_for(hakubun, merge=True, ortho=True, use_cache=True, seg=seg)
    kun_sec = time.time() - t2
    total_kun += kun_sec
    print("[%s] ocr %.1fs lines=%d | kundoku %.1fs（engine %.2f / style %.2f）"
          % (fname, ocr_sec, r["line_count"], kun_sec, seg.get("engine", 0) / 1000.0,
             seg.get("style", 0) / 1000.0), flush=True)
    doc += [
        "## %s" % fname,
        "",
        "来源: %s" % m["source_url"],
        "",
        "**白文**",
        "", "```", hakubun, "```", "",
        "**書き下し文（merge+ortho）**",
        "", "```", kakikudashi, "```", "",
    ]

doc += ["---", "", "耗时：OCR 合计 %.1fs / 训读合计 %.1fs（%d 页）" % (total_ocr, total_kun, len(stems)), ""]
out_md = os.path.join(out_dir, "book.md")
with open(out_md, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(doc))
print("[done] written:", out_md, flush=True)
