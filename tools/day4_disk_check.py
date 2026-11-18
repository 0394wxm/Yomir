# -*- coding: utf-8 -*-
"""day4_disk_check.py — 同样的 SQLite 写入，分别放 D:（项目盘）与 %TEMP%，区分代码问题与磁盘问题。"""
import os
import sqlite3
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime  # noqa: E402


def ms():
    return time.perf_counter() * 1000.0


def bench(path, n=10):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY AUTOINCREMENT, a TEXT, b TEXT)")
    conn.commit()
    conn.close()

    vals = []
    parts = {"pragma": 0.0, "commit": 0.0, "close": 0.0}
    for i in range(n):
        t0 = ms()
        c = sqlite3.connect(path)
        t1 = ms()
        c.execute("PRAGMA journal_mode=WAL")
        t2 = ms()
        c.execute("INSERT INTO t (a, b) VALUES (?, ?)", ("x" * 40, "y" * 400))
        c.commit()
        t3 = ms()
        c.close()
        t4 = ms()
        parts["pragma"] += t2 - t1
        parts["commit"] += t3 - t2
        parts["close"] += t4 - t3
        vals.append(t4 - t0)
    return vals, {k: v / n for k, v in parts.items()}


def main():
    dbp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kanbun.db")
    tmp = os.path.join(tempfile.gettempdir(), "d4_probe.db")
    for label, path in (("项目盘 D:", dbp), ("临时目录 %TEMP%", tmp)):
        vals, parts = bench(path)
        print("%-16s %s" % (label, path))
        print("   total min %.1f median %.1f max %.1f" % (min(vals), sorted(vals)[len(vals) // 2], max(vals)))
        print("   pragma %.1f | commit %.1f | close %.1f (ms/次)"
              % (parts["pragma"], parts["commit"], parts["close"]))
        for suf in ("", "-wal", "-shm"):
            p = path + suf
            if os.path.exists(p):
                print("   %s %d bytes" % (os.path.basename(p), os.path.getsize(p)))
        print()
    try:
        os.remove(tmp)
    except OSError:
        pass


if __name__ == "__main__":
    main()
