# -*- coding: utf-8 -*-
"""night11_perf.py — 连续 20 次 /api/kundoku 的耗时记录（NIGHT11）。

前 10 次为不重复句（缓存未命中路径），后 10 次为重复句（缓存命中路径）。
"""
import json
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000/api/kundoku"
UNIQUE = [
    "王顧左右而言他", "不入虎穴不得虎子", "欲治其國者先齊其家",
    "楚人有鬻楯與矛者。", "譽之曰、吾楯之堅、莫能陷也。",
    "宋人有耕田者。", "田中有株、兎走りて株に触る。",
    "項王軍壁垓下。", "夜、漢軍の四面に皆楚歌するを聞く。",
    "孟子曰く、勢い行われざればなり。",
]


def post(text):
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"}, method="POST")
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        json.loads(r.read().decode("utf-8"))
    return round((time.time() - t) * 1000)


def main():
    times_unique, times_cached = [], []
    for i in range(10):
        ms = post(UNIQUE[i])
        times_unique.append(ms)
        print("unique#%02d %d ms" % (i + 1, ms), flush=True)
    for i in range(10):
        ms = post(UNIQUE[i])  # 重复 → 行级缓存命中
        times_cached.append(ms)
        print("cached#%02d %d ms" % (i + 1, ms), flush=True)
    print("unique: avg %d ms (min %d max %d)" % (sum(times_unique) / 10, min(times_unique), max(times_unique)))
    print("cached: avg %d ms (min %d max %d)" % (sum(times_cached) / 10, min(times_cached), max(times_cached)))


if __name__ == "__main__":
    main()
