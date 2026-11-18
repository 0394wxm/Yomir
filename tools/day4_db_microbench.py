# -*- coding: utf-8 -*-
"""day4_db_microbench.py — 把 save_kundoku 拆成段做微基准，定位 db 段为何 700–1700ms。

分段：connect / PRAGMA journal_mode / INSERT requests / INSERT results / commit / close
以及文件体积（db / -wal / -shm）。
"""
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import sqlite3  # noqa: E402
from datetime import datetime  # noqa: E402

from backend import db  # noqa: E402


def ms():
    return time.perf_counter() * 1000.0


def bench(label):
    t = {}
    t0 = ms()
    conn = sqlite3.connect(db.DB_PATH)
    t["connect"] = ms() - t0
    t0 = ms()
    conn.execute("PRAGMA journal_mode=WAL")
    t["pragma"] = ms() - t0
    now = datetime.now().isoformat(timespec="seconds")
    t0 = ms()
    cur = conn.execute(
        "INSERT INTO requests (hakubun, ocr_hakubun, prev_request_id, created_at) VALUES (?, ?, ?, ?)",
        ("bench-" + label, None, None, now))
    t["insert_req"] = ms() - t0
    rid = cur.lastrowid
    t0 = ms()
    conn.execute(
        "INSERT INTO results (request_id, kaeriten_text, kakikudashi, created_at) VALUES (?, ?, ?, ?)",
        (rid, "k", "kk", now))
    t["insert_res"] = ms() - t0
    t0 = ms()
    conn.commit()
    t["commit"] = ms() - t0
    t0 = ms()
    conn.close()
    t["close"] = ms() - t0
    print("%-12s " % label + " | ".join("%s %7.1f" % (k, v) for k, v in t.items())
          + "  total %.1f" % sum(t.values()))
    return t


def main():
    print("DB_PATH =", db.DB_PATH)
    for suffix in ("", "-wal", "-shm"):
        p = db.DB_PATH + suffix
        if os.path.exists(p):
            print("  %-28s %10d bytes" % (os.path.basename(p), os.path.getsize(p)))
        else:
            print("  %-28s (absent)" % os.path.basename(p))

    # 表规模
    conn = sqlite3.connect(db.DB_PATH)
    for tb in ("requests", "results"):
        n = conn.execute("SELECT COUNT(*) FROM %s" % tb).fetchone()[0]
        print("  表 %-9s %8d 行" % (tb, n))
    conn.close()

    print()
    print("=== 逐段耗时（各 5 次） ===")
    sums = {}
    for i in range(5):
        t = bench("#%d" % (i + 1))
        for k, v in t.items():
            sums[k] = sums.get(k, 0.0) + v
    print()
    print("5 次平均： " + " | ".join("%s %7.1f" % (k, v / 5.0) for k, v in sums.items()))

    print()
    print("=== 直接调用 db.save_kundoku（含 _LOCK）10 次 ===")
    vals = []
    for i in range(10):
        t0 = ms()
        db.save_kundoku("bench-save-%d" % i, "k", "kk")
        vals.append(ms() - t0)
    print("  " + " ".join("%.1f" % v for v in vals))
    print("  min %.1f median %.1f max %.1f" % (min(vals), sorted(vals)[len(vals) // 2], max(vals)))


if __name__ == "__main__":
    main()
