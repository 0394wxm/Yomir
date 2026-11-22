# -*- coding: utf-8 -*-
"""night71_verify_book.py — Night 71 整本导入批处理逐页核对（N63/N70 同口径，PID 参数化）。

用法: python tools/night71_verify_book.py <PID>
对 eval/import_pid_<PID>/book.md 做结构性逐页核对：
  1. 页集合 vs 下载页图（pages/*.jpg）vs IIIF manifest 页数（验证时实取 dl.ndl.go.jp）——
     三者不一致即 FAIL（防 canvas 缺图导致 p 号错位）；
  2. 每页白文/書き下し文行数；0 行页、OCR 失败页如实列出（跳过并记录，不判 fail）；
  3. 异常行盘点：纯 ASCII 符号行（刊本界框垃圾的已知形态）按页计数留痕。
输出: stdout 摘要 + eval/night71_verify_<PID>.json（含 book.md sha256[:16]）。
只读导入产物与 manifest，不改任何产品代码。页图不入库。
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PID = sys.argv[1] if len(sys.argv) > 1 else ""
BOOK_DIR = os.path.join(ROOT, "eval", "import_pid_%s" % PID)
BOOK_MD = os.path.join(BOOK_DIR, "book.md")
PAGES_DIR = os.path.join(BOOK_DIR, "pages")


def manifest_pages():
    req = urllib.request.Request(
        "https://dl.ndl.go.jp/api/iiif/%s/manifest.json" % PID,
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        m = json.load(r)
    return len(m.get("sequences", [{}])[0].get("canvases", [])), m.get("title", "")


def parse_book():
    """book.md → ({页号: {"status","hakubun":[...],"kudashi":[...]}}, 原文)。

    每页固定两段代码块：第 1 段=白文、第 2 段=書き下し文（import_pid.py 固定模板），
    fence 计数区分（N63/N70 同款解析）。
    """
    with open(BOOK_MD, encoding="utf-8") as f:
        text = f.read()
    pages, cur, block = {}, None, None
    for l in text.splitlines():
        m = re.match(r"^## p(\d+)$", l)
        if m:
            cur = {"status": "ok", "hakubun": [], "kudashi": [], "fences": 0}
            pages[m.group(1)] = cur
            block = None
            continue
        if cur is None:
            continue
        if l.strip() == "(0 行)":
            cur["status"] = "0行"
        elif l.startswith("(OCR 失败"):
            cur["status"] = "ocr_fail"
        elif l.strip() == "```":
            cur["fences"] += 1
            block = {1: "hakubun", 2: None, 3: "kudashi", 4: None}.get(cur["fences"])
            continue
        elif block == "hakubun":
            if l.strip():
                cur["hakubun"].append(l)
        elif block == "kudashi":
            if l.strip():
                cur["kudashi"].append(l)
    return pages, text


def is_ascii_noise(line):
    return all(ord(c) < 128 for c in line)


def main():
    n_manifest, title = manifest_pages()
    print("[manifest] %s: %d pages" % (title, n_manifest), flush=True)
    pages, raw = parse_book()
    jpg_nums = sorted(int(f[1:-4]) for f in os.listdir(PAGES_DIR) if f.endswith(".jpg"))

    fails = []
    md_nums = sorted(int(k) for k in pages)
    if not pages:
        fails.append("book.md 无任何页段（解析失败）")
    if jpg_nums and md_nums != jpg_nums:
        fails.append("book.md 页号 %s… != 下载页图 %s…（canvas 缺图会错位）"
                     % (md_nums[:5], jpg_nums[:5]))
    if jpg_nums and len(jpg_nums) != n_manifest:
        fails.append("下载页图 %d 张 != manifest %d 张" % (len(jpg_nums), n_manifest))

    rows, garbage = [], []
    n_ok = n_zero = n_fail = 0
    for k in sorted(pages.keys(), key=int):
        n = int(k)
        p = pages[k]
        haku, kud = p["hakubun"], p["kudashi"]
        g = [l for l in haku if is_ascii_noise(l)]
        if g:
            garbage.append({"page": n, "lines": g})
        if p["status"] == "0行":
            n_zero += 1
        elif p["status"] == "ocr_fail":
            n_fail += 1
        else:
            n_ok += 1
            if not haku:
                fails.append("p%03d 标记 ok 但白文 0 行" % n)
        rows.append({"page": n, "status": p["status"], "hakubun_lines": len(haku),
                     "kudashi_lines": len(kud), "ascii_noise_lines": len(g),
                     "hakubun_chars": sum(len(l) for l in haku)})

    summary = {
        "book": "%s (NDL %s)" % (title, PID),
        "pid": PID,
        "expected_pages_manifest": n_manifest,
        "jpg_pages": len(jpg_nums),
        "book_md_pages": len(pages),
        "ok": n_ok, "zero_line": n_zero, "ocr_fail": n_fail,
        "zero_line_pages": [r["page"] for r in rows if r["status"] == "0行"],
        "ocr_fail_pages": [r["page"] for r in rows if r["status"] == "ocr_fail"],
        "ascii_noise_total_lines": sum(len(g["lines"]) for g in garbage),
        "ascii_noise_pages": len(garbage),
        "book_md_sha256_16": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],
        "fails": fails,
        "rows": rows,
        "garbage_detail": garbage,
    }
    out = os.path.join(ROOT, "eval", "night71_verify_%s.json" % PID)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("[pages] manifest=%d jpg=%d book_md=%d" % (n_manifest, len(jpg_nums), len(pages)))
    for r in rows:
        print("  p%03d %-8s haku=%3d kun=%3d noise=%d chars=%d"
              % (r["page"], r["status"], r["hakubun_lines"], r["kudashi_lines"],
                 r["ascii_noise_lines"], r["hakubun_chars"]))
    print("[summary] ok=%d 0行=%d ocr_fail=%d; ascii-noise lines=%d on %d pages"
          % (n_ok, n_zero, n_fail, summary["ascii_noise_total_lines"],
             summary["ascii_noise_pages"]))
    print("[0行] %s" % (summary["zero_line_pages"] or "无"))
    print("[ocr_fail] %s" % (summary["ocr_fail_pages"] or "无"))
    print("[sha16] %s" % summary["book_md_sha256_16"])
    if fails:
        print("[FAIL] %s" % "; ".join(fails))
        print("verdict: FAIL")
        return 1
    print("verdict: PASS -> %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
