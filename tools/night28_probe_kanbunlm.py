# -*- coding: utf-8 -*-
"""night28_probe_kanbunlm.py — 探 hf-mirror 上的 Kanbun-LM 相关数据集（只读元数据）。"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}
BASE = "https://hf-mirror.com/api"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


for q in ("kanbun", "kanbunlm", "kundoku"):
    try:
        ds = get(BASE + "/datasets?search=" + q + "&limit=20")
        print("=== search %r: %d hits ===" % (q, len(ds)))
        for d in ds:
            print("  %-42s downloads=%s likes=%s" % (d.get("id"), d.get("downloads"), d.get("likes")))
    except Exception as e:
        print("search %r failed: %r" % (q, e))
