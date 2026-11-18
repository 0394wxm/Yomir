# -*- coding: utf-8 -*-
"""bench_v4_latency.py — guwenbert vs udpipe 单句耗时（接后端可行性依据）。"""
import json
import os
import statistics
import sys
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import run_eval_guwenbert as R  # noqa: E402
import udkanbun  # noqa: E402


def bench(eng, lines, label):
    ts = []
    for ln in lines:
        t = time.time()
        R.kundoku_line(eng, ln)
        ts.append(time.time() - t)
    ts_ms = [t * 1000 for t in ts]
    print("%-12s n=%d  median %.0fms  mean %.0fms  p90 %.0fms  max %.0fms"
          % (label, len(ts), statistics.median(ts_ms), statistics.mean(ts_ms),
             statistics.quantiles(ts_ms, n=10)[-1] if len(ts_ms) > 2 else max(ts_ms), max(ts_ms)))


def main():
    with open(os.path.join(ROOT, "eval", "night21_results_full.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    short = [r["hakubun"] for r in items if len(r["hakubun"]) <= 20][:10]
    long_ = [r["hakubun"] for r in items if len(r["hakubun"]) > 60][:10]

    print("[1] 规则引擎（udkanbun 默认 udpipe）")
    eng_rule = udkanbun.UDKanbun(True, False, None)
    eng_rule("王顧左右而言他")
    bench(eng_rule, short, "short<=20")
    bench(eng_rule, long_, "long>60")

    print("\n[2] guwenbert 依存（本报告 v4 路线）")
    t = time.time()
    eng_gw = R.build_engine(None)
    print("load %.1fs" % (time.time() - t))
    eng_gw("王顧左右而言他")
    bench(eng_gw, short, "short<=20")
    bench(eng_gw, long_, "long>60")


if __name__ == "__main__":
    main()
