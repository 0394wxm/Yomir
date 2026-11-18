# -*- coding: utf-8 -*-
"""day4_ablate_db.py — 对照实验：db 段是不是离群值的唯一来源。

三组（各 10 次，同一句子，缓存已预热）：
  A. 正常路径（db 写）
  B. monkeypatch 掉 db.save_kundoku（不写库）
  C. 正常路径但 cache=false（整段路径，验证引擎侧影响）

结论若为「A-B ≈ db 耗时」，则 db 段即根因。
"""
import logging
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
os.environ["KANBUN_TIMING"] = "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SENT = "宋人有耕田者。田中有株、兎走りて株に触る。"


class Capture(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.rows = []

    def emit(self, record):
        m = record.getMessage()
        if m.startswith("TIMING "):
            self.rows.append(m)


RX = re.compile(r"total=([\d.]+)ms \| engine ([\d.]+) \| merge ([\d.]+) \| kaeriten ([\d.]+) \| "
                r"translate ([\d.]+) \| style ([\d.]+) \| glossary ([\d.]+) \| db ([\d.]+)")


def run(client, cap, label, n=10, **params):
    vals = []
    dbs = []
    for _ in range(n):
        before = len(cap.rows)
        r = client.post("/api/kundoku", json={"text": SENT}, params=params)
        assert r.status_code == 200, r.text
        if len(cap.rows) == before:
            continue
        m = RX.search(cap.rows[-1])
        if not m:
            continue
        vals.append(float(m.group(1)))
        dbs.append(float(m.group(8)))
    med = sorted(vals)[len(vals) // 2] if vals else -1
    print("%-34s n=%2d total: min %7.1f median %7.1f max %7.1f | db: median %7.1f"
          % (label, len(vals), min(vals) if vals else -1, med,
             max(vals) if vals else -1, sorted(dbs)[len(dbs) // 2] if dbs else -1))
    return vals


def main():
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    cap = Capture()
    logging.getLogger("kanbun").addHandler(cap)
    logging.getLogger("kanbun").setLevel(logging.INFO)

    with TestClient(app) as client:
        client.post("/api/kundoku", json={"text": SENT})  # 预热
        cap.rows = []
        run(client, cap, "A. 正常路径（写库）")

        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            run(client, cap, "B. 跳过写库（monkeypatch）")
        finally:
            dbmod.save_kundoku = real

        run(client, cap, "C. cache=false（整段路径+写库）", cache="false")
        run(client, cap, "D. 正常路径复测", n=10)


if __name__ == "__main__":
    main()
