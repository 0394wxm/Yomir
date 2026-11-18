# -*- coding: utf-8 -*-
"""day4_locate_outlier.py — D4：复现 cached 2.4s 离群值并定位到段。

做法：
  * 直接走 TestClient（不依赖已启动的服务），避免网络/端口干扰；
  * 先用 UNIQUE 10 句各请求一次（预热 + 填缓存）；
  * 再对同样 10 句各请求一次（缓存命中路径），共 20 次调用；
  * 通过 KANBUN_TIMING 打开分段日志，抓 logger 的 TIMING 行；
  * 打印每次的总耗时与分段，标出 >500ms 的离群点。

用法：python tools/day4_locate_outlier.py [--repeat 2]
"""
import collections
import io
import logging
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("KANBUN_TIMING", "1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

UNIQUE = [
    "王顧左右而言他",
    "不入虎穴不得虎子",
    "欲治其國者先齊其家",
    "楚人有鬻楯與矛者。",
    "譽之曰、吾楯之堅、莫能陷也。",
    "宋人有耕田者。",
    "田中有株、兎走りて株に触る。",
    "項王軍壁垓下。",
    "夜、漢軍の四面に皆楚歌するを聞く。",
    "孟子曰く、勢い行われざればなり。",
]


class Capture(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.rows = []

    def emit(self, record):
        msg = record.getMessage()
        if msg.startswith("TIMING "):
            self.rows.append(msg)


TIMING_RX = re.compile(
    r"TIMING (\d+) chars cache=(\S+) hit=(\d+) total=([\d.]+)ms \| engine ([\d.]+) \| "
    r"merge ([\d.]+) \| kaeriten ([\d.]+) \| translate ([\d.]+) \| style ([\d.]+) \| "
    r"glossary ([\d.]+) \| db ([\d.]+)")


def main():
    from fastapi.testclient import TestClient
    from backend.main import app

    cap = Capture()
    logging.getLogger("kanbun").addHandler(cap)
    logging.getLogger("kanbun").setLevel(logging.INFO)

    with TestClient(app) as client:  # with 语句触发 startup（加载 udkundoku 引擎）
        # 预热引擎
        r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
        assert r.status_code == 200, r.text

        times = []
        print("=== 阶段 1：10 句首次请求（缓存未命中） ===")
        for i, s in enumerate(UNIQUE):
            cap.rows = []
            r = client.post("/api/kundoku", json={"text": s})
            assert r.status_code == 200
            m = TIMING_RX.search(cap.rows[-1]) if cap.rows else None
            tot = float(m.group(4)) if m else -1
            times.append(("unique", i + 1, tot, m))
            print("unique#%02d %8.1f ms  %s" % (i + 1, tot, _fmt(m)))

        print()
        print("=== 阶段 2：同样 10 句再请求一次（缓存命中） ===")
        for i, s in enumerate(UNIQUE):
            cap.rows = []
            r = client.post("/api/kundoku", json={"text": s})
            assert r.status_code == 200
            m = TIMING_RX.search(cap.rows[-1]) if cap.rows else None
            tot = float(m.group(4)) if m else -1
            times.append(("cached", i + 1, tot, m))
            print("cached#%02d %8.1f ms  %s" % (i + 1, tot, _fmt(m)))

    print()
    print("=== 离群点（>500ms） ===")
    out = [t for t in times if t[2] > 500]
    if not out:
        print("  本轮没有 >500ms 的调用")
    for kind, idx, tot, m in out:
        print("  %s#%02d %.1f ms -> %s" % (kind, idx, tot, _fmt(m)))

    for kind in ("unique", "cached"):
        vals = [t[2] for t in times if t[0] == kind]
        print()
        print("%s: n=%d min=%.1f median=%.1f max=%.1f avg=%.1f"
              % (kind, len(vals), min(vals), _median(vals), max(vals), sum(vals) / len(vals)))


def _median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _fmt(m):
    if not m:
        return "(无 TIMING 行)"
    return ("engine %6.1f | merge %5.1f | kaeriten %6.1f | translate %7.1f | "
            "style %4.1f | glossary %5.1f | db %5.1f | hit=%s"
            % (float(m.group(5)), float(m.group(6)), float(m.group(7)), float(m.group(8)),
               float(m.group(9)), float(m.group(10)), float(m.group(11)), m.group(3)))


if __name__ == "__main__":
    main()
