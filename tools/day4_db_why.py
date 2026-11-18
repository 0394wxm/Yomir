# -*- coding: utf-8 -*-
"""day4_db_why.py — db.save_kundoku 内部的哪一段慢？逐段重复测 20 次。

怀疑点：
  1) 每次调用都新建 sqlite 连接 + 执行 `PRAGMA journal_mode=WAL`；
  2) 每次 INSERT 后 commit，且连接关闭时 SQLite 把 WAL 回写/清理；
  3) 库文件在 D: 盘（机械盘/杀软扫描）。

测法：把 save_kundoku 的 6 个动作逐个计时，对比「每次新建连接」与
「复用同一连接」两条路径，各 20 次。
"""
import os
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from datetime import datetime  # noqa: E402

from backend import db  # noqa: E402


def ms():
    return time.perf_counter() * 1000.0


def one_shot(tag):
    t = {}
    t0 = ms()
    conn = sqlite3.connect(db.DB_PATH)
    t["connect"] = ms() - t0
    t0 = ms()
    conn.execute("PRAGMA journal_mode=WAL")
    t["pragma_wal"] = ms() - t0
    now = datetime.now().isoformat(timespec="seconds")
    t0 = ms()
    cur = conn.execute(
        "INSERT INTO requests (hakubun, ocr_hakubun, prev_request_id, created_at) VALUES (?,?,?,?)",
        (tag, None, None, now))
    rid = cur.lastrowid
    t["insert1"] = ms() - t0
    t0 = ms()
    conn.execute(
        "INSERT INTO results (request_id, kaeriten_text, kakikudashi, created_at) VALUES (?,?,?,?)",
        (rid, "k", "kk", now))
    t["insert2"] = ms() - t0
    t0 = ms()
    conn.commit()
    t["commit"] = ms() - t0
    t0 = ms()
    conn.close()
    t["close"] = ms() - t0
    t["total"] = sum(t.values())
    return t


def main():
    print("DB:", db.DB_PATH, os.path.getsize(db.DB_PATH), "bytes")
    keys = ["connect", "pragma_wal", "insert1", "insert2", "commit", "close", "total"]
    acc = {k: 0.0 for k in keys}
    N = 20
    print("\n=== A. 每次新建连接（= 生产路径）%d 次 ===" % N)
    vals = []
    for i in range(N):
        t = one_shot("whyA-%d" % i)
        for k in keys:
            acc[k] += t[k]
        vals.append(t["total"])
    for k in keys:
        print("  %-10s avg %8.2f ms" % (k, acc[k] / N))
    print("  total  min %.1f  median %.1f  max %.1f"
          % (min(vals), sorted(vals)[N // 2], max(vals)))

    print("\n=== B. 复用同一连接 %d 次（对照） ===" % N)
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    acc2 = {k: 0.0 for k in keys}
    vals2 = []
    for i in range(N):
        now = datetime.now().isoformat(timespec="seconds")
        t0 = ms()
        cur = conn.execute(
            "INSERT INTO requests (hakubun, ocr_hakubun, prev_request_id, created_at) VALUES (?,?,?,?)",
            ("whyB-%d" % i, None, None, now))
        rid = cur.lastrowid
        conn.execute(
            "INSERT INTO results (request_id, kaeriten_text, kakikudashi, created_at) VALUES (?,?,?,?)",
            (rid, "k", "kk", now))
        t_ins = ms() - t0
        t0 = ms()
        conn.commit()
        t_com = ms() - t0
        acc2["insert1"] += t_ins
        acc2["commit"] += t_com
        vals2.append(t_ins + t_com)
    conn.commit()
    conn.close()
    print("  insert(both) avg %8.2f ms" % (acc2["insert1"] / N))
    print("  commit       avg %8.2f ms" % (acc2["commit"] / N))
    print("  total  min %.1f  median %.1f  max %.1f"
          % (min(vals2), sorted(vals2)[N // 2], max(vals2)))

    # 与 db.save_kundoku 对比（含 _LOCK）
    vals3 = []
    for i in range(N):
        t0 = ms()
        db.save_kundoku("whyC-%d" % i, "k", "kk")
        vals3.append(ms() - t0)
    print("\n=== C. db.save_kundoku 原样 %d 次 ===" % N)
    print("  min %.1f  median %.1f  avg %.1f  max %.1f"
          % (min(vals3), sorted(vals3)[N // 2], sum(vals3) / N, max(vals3)))


if __name__ == "__main__":
    main()
