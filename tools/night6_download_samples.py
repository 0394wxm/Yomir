# -*- coding: utf-8 -*-
"""night6_download_samples.py — 从 NDL IIIF 建 20 张样张库（NIGHT6）。

优先不同书（候选 pid 列表），不足时用已知 4 本的不同页补足，每张记来源 URL。
输出: ocr_runtime/samples/batch20/*.jpg + manifest.json
"""
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ocr_runtime", "samples", "batch20")
os.makedirs(OUT, exist_ok=True)

# 候选：不同书的 pid（来源：WebSearch 公开页面引用 + ndlkotenocr-lite repo 资源名）
CANDIDATE_PIDS = [
    1287221,   # 竹取物語（既验证）
    10301438,  # 人間萬事翁馬（既验证）
    11892692,  # 既验证
    9973821,   # 伊藤博文関係文書（既验证）
    1033232,   # 墨場必携（漢文）
    12150869,  # 時秋物語
    781192,    # 信長公記 巻之上
    781193,    # 信長公記 巻之下
    1288060,   # 元和卯月本写本（うたひ鏡 調査で利用）
    1021188,   # 古文書翻刻参照
]
PAGES = ["R0000003", "R0000002", "R0000004", "R0000005"]  # 避开封面/扉页
KNOWN_PIDS = [1287221, 10301438, 11892692, 9973821]
TARGET = 20


def fetch(url, out_path, timeout=90):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 50_000:  # IIIF 错误页很小
            return None
        with open(out_path, "wb") as f:
            f.write(data)
        return len(data)
    except Exception as e:
        print("[SKIP] %s: %r" % (url.rsplit('/', 2)[-2] if url.count('/') >= 2 else url, e), flush=True)
        return None


def main():
    manifest = []
    n = 0
    # 1) 候选 pid 各取一个有效页（每书 1 张）
    for pid in CANDIDATE_PIDS:
        if n >= TARGET:
            break
        for page in PAGES:
            url = "https://dl.ndl.go.jp/api/iiif/%d/%s/full/1400,/0/default.jpg" % (pid, page)
            out = os.path.join(OUT, "ndl_%d_%s.jpg" % (pid, page))
            size = fetch(url, out)
            if size:
                manifest.append({"file": os.path.basename(out), "pid": pid, "page": page,
                                 "source_url": url, "bytes": size, "known_good": pid in KNOWN_PIDS})
                n += 1
                print("[%02d] ok %s (%d KB)" % (n, os.path.basename(out), size // 1024), flush=True)
                break
            elif os.path.exists(out):
                os.remove(out)
    # 2) 不足则用已知 4 本的额外页补足（同书不同页，manifest 里如实标注）
    for pid in KNOWN_PIDS:
        if n >= TARGET:
            break
        for page in PAGES[1:] + ["R0000006", "R0000007"]:
            if n >= TARGET:
                break
            url = "https://dl.ndl.go.jp/api/iiif/%d/%s/full/1400,/0/default.jpg" % (pid, page)
            out = os.path.join(OUT, "ndl_%d_%s.jpg" % (pid, page))
            if os.path.exists(out):
                continue
            size = fetch(url, out)
            if size:
                manifest.append({"file": os.path.basename(out), "pid": pid, "page": page,
                                 "source_url": url, "bytes": size, "known_good": True,
                                 "note": "same book as earlier sample, different page"})
                n += 1
                print("[%02d] ok %s (%d KB)" % (n, os.path.basename(out), size // 1024), flush=True)
            elif os.path.exists(out):
                os.remove(out)
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("total:", n, "manifest written", flush=True)


if __name__ == "__main__":
    main()
