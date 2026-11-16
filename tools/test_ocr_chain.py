# -*- coding: utf-8 -*-
"""test_ocr_chain.py — 4 张样张走完整 HTTP 链路：/api/ocr → 白文 → /api/kundoku（NIGHT3）。

记录每张的 status/行数/首行、text_type 分流结果。串行跑（Celeron 不并行）。
需后端已在 8000 端口运行。
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8000"

SAMPLES = [
    "ndl_1287221_R0000002_clean.jpg",   # 竹取物語（仮名）
    "ndl_10301438_R0000002_clean.jpg",  # 人間萬事翁馬（江戸絵本）
    "ndl_11892692_R0000003_clean.jpg",
    "ndl_9973821_R0000002_clean.jpg",   # 伊藤博文関係文書（明治文書）
]


def post_json(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode("utf-8"))


def post_file(url, path):
    boundary = "kanbun3f9a"
    name = os.path.basename(path)
    with open(path, "rb") as f:
        content = f.read()
    body = (
        ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
         "Content-Type: image/jpeg\r\n\r\n" % (boundary, name)).encode("utf-8")
        + content + ("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    summary = []
    for s in SAMPLES:
        path = os.path.join(ROOT, "ocr_runtime", "samples", s)
        if not os.path.isfile(path):
            print("[SKIP]", s)
            continue
        ocr = post_file(BASE + "/api/ocr", path)
        hakubun = ocr.get("hakubun", "")
        first = hakubun.split("\n")[0] if hakubun else "(empty)"
        print("[%s] ocr status=%s lines=%s junk=%s elapsed=%ss first=%r"
              % (s, ocr.get("status"), ocr.get("line_count"), ocr.get("junk_filtered"),
                 ocr.get("elapsed_sec"), first[:20]), flush=True)
        if not hakubun:
            summary.append({"sample": s, "ocr_status": ocr.get("status"), "kundoku": None})
            continue
        k = post_json(BASE + "/api/kundoku", {"text": hakubun})
        print("    kundoku: text_type=%s note=%r kaeriten_head=%r"
              % (k.get("text_type"), (k.get("note") or "")[:30], (k.get("kaeriten_text") or "")[:18]), flush=True)
        summary.append({
            "sample": s,
            "ocr_status": ocr.get("status"),
            "ocr_lines": ocr.get("line_count"),
            "junk_filtered": ocr.get("junk_filtered"),
            "ocr_elapsed_sec": ocr.get("elapsed_sec"),
            "ocr_first_line": first,
            "kundoku_text_type": k.get("text_type"),
            "kundoku_note": k.get("note"),
            "kundoku_kakikudashi_head": (k.get("kakikudashi") or "")[:40],
        })
    out = os.path.join(ROOT, "eval", "ocr_samples", "chain_summary.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
