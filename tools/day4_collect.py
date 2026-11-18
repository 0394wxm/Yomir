# -*- coding: utf-8 -*-
"""day4_collect.py — 汇总 D4 全部实测数据，供 REPORT_DAY4.md 引用（一次跑完）。"""
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
os.environ["KANBUN_TIMING"] = "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from datetime import datetime  # noqa: E402

SENTS = [
    "王顧左右而言他",
    "不入虎穴不得虎子",
    "欲治其國者先齊其家",
    "楚人有鬻楯與矛者。",
    "譽之曰、吾楯之堅、莫能陷也。",
    "宋人有耕田者。",
    "田中有株、兎走りて株に触る。",
    "項王軍壁垓下。",
    "孟子曰く、勢い行われざればなり。",
    "子曰く、學而時習之、不亦説乎。",
]

RX = re.compile(r"total=([\d.]+)ms \| engine ([\d.]+) \| merge ([\d.]+) \| kaeriten ([\d.]+) \| "
                r"translate ([\d.]+) \| style ([\d.]+) \| glossary ([\d.]+) \| db ([\d.]+)")


class Cap(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.rows = []

    def emit(self, r):
        m = r.getMessage()
        if m.startswith("TIMING "):
            self.rows.append(m)


def ms():
    return time.perf_counter() * 1000.0


def med(v):
    s = sorted(v)
    return s[len(s) // 2] if s else -1


def main():
    from fastapi.testclient import TestClient
    from backend.main import app

    cap = Cap()
    logging.getLogger("kanbun").addHandler(cap)
    logging.getLogger("kanbun").setLevel(logging.INFO)

    out = {}
    with TestClient(app) as c:
        c.post("/api/kundoku", json={"text": "王顧左右而言他"})
        rec = []
        for phase in ("unique", "cached"):
            for i, s in enumerate(SENTS):
                n0 = len(cap.rows)
                r = c.post("/api/kundoku", json={"text": s})
                assert r.status_code == 200
                if len(cap.rows) == n0:
                    continue
                m = RX.search(cap.rows[-1])
                if not m:
                    continue
                rec.append({"phase": phase, "i": i + 1,
                            "total": float(m.group(1)),
                            "engine": float(m.group(2)), "merge": float(m.group(3)),
                            "kaeriten": float(m.group(4)), "translate": float(m.group(5)),
                            "style": float(m.group(6)), "glossary": float(m.group(7)),
                            "db": float(m.group(8))})
        out["calls"] = rec
        for ph in ("unique", "cached"):
            sub = [x for x in rec if x["phase"] == ph]
            out[ph] = {
                "n": len(sub),
                "total": [x["total"] for x in sub],
                "engine": [x["engine"] for x in sub],
                "translate": [x["translate"] for x in sub],
                "db": [x["db"] for x in sub],
            }

        # 消融：跳过 db
        import backend.db as dbmod
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        nodb = []
        try:
            for s in SENTS:
                n0 = len(cap.rows)
                c.post("/api/kundoku", json={"text": s})
                if len(cap.rows) > n0:
                    m = RX.search(cap.rows[-1])
                    if m:
                        nodb.append(float(m.group(1)))
        finally:
            dbmod.save_kundoku = real
        out["no_db"] = nodb

    # db 分段
    from backend import db as dbm
    keys = ["connect", "pragma_wal", "insert1", "insert2", "commit", "close"]
    acc = {k: 0.0 for k in keys}
    tot = []
    N = 20
    for i in range(N):
        t0 = ms()
        conn = sqlite3.connect(dbm.DB_PATH)
        t1 = ms()
        conn.execute("PRAGMA journal_mode=WAL")
        t2 = ms()
        now = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute("INSERT INTO requests (hakubun, ocr_hakubun, prev_request_id, created_at)"
                           " VALUES (?,?,?,?)", ("d4-%d" % i, None, None, now))
        rid = cur.lastrowid
        t3 = ms()
        conn.execute("INSERT INTO results (request_id, kaeriten_text, kakikudashi, created_at)"
                     " VALUES (?,?,?,?)", (rid, "k", "kk", now))
        t4 = ms()
        conn.commit()
        t5 = ms()
        conn.close()
        t6 = ms()
        acc["connect"] += t1 - t0
        acc["pragma_wal"] += t2 - t1
        acc["insert1"] += t3 - t2
        acc["insert2"] += t4 - t3
        acc["commit"] += t5 - t4
        acc["close"] += t6 - t5
        tot.append(t6 - t0)
    out["db_parts"] = {k: v / N for k, v in acc.items()}
    out["db_total"] = {"min": min(tot), "median": med(tot), "max": max(tot)}

    # 磁盘对照
    def sqlite_probe(path, n=10):
        cn = sqlite3.connect(path)
        cn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY AUTOINCREMENT, a TEXT, b TEXT)")
        cn.commit()
        cn.close()
        vals = []
        for i in range(n):
            t0 = ms()
            x = sqlite3.connect(path)
            x.execute("PRAGMA journal_mode=WAL")
            x.execute("INSERT INTO t (a,b) VALUES (?,?)", ("x" * 40, "y" * 400))
            x.commit()
            x.close()
            vals.append(ms() - t0)
        return {"min": min(vals), "median": med(vals), "max": max(vals)}

    tmp = os.path.join(tempfile.gettempdir(), "d4_collect.db")
    out["disk_d"] = sqlite_probe(dbm.DB_PATH)
    out["disk_c"] = sqlite_probe(tmp)
    try:
        os.remove(tmp)
    except OSError:
        pass

    # 裸 fsync
    def fsync_probe(path, n=10):
        vals = []
        for i in range(n):
            fh = open(path, "wb")
            fh.write(b"x" * 4096)
            fh.flush()
            t0 = ms()
            os.fsync(fh.fileno())
            vals.append(ms() - t0)
            fh.close()
        return {"min": min(vals), "median": med(vals), "max": max(vals)}

    out["fsync_d"] = fsync_probe(os.path.join(ROOT, "d4_probe.bin"))
    out["fsync_c"] = fsync_probe(os.path.join(tempfile.gettempdir(), "d4_probe.bin"))
    for p in (os.path.join(ROOT, "d4_probe.bin"), os.path.join(tempfile.gettempdir(), "d4_probe.bin")):
        try:
            os.remove(p)
        except OSError:
            pass

    with open(os.path.join(ROOT, "eval", "day4_outlier_data.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== 20 次调用（10 unique + 10 cached） ===")
    for x in out["calls"]:
        print("%-7s#%02d total %8.1f | engine %6.1f | translate %5.1f | db %8.1f"
              % (x["phase"], x["i"], x["total"], x["engine"], x["translate"], x["db"]))
    for ph in ("unique", "cached"):
        d = out[ph]
        print("\n%s: n=%d total median %.1f max %.1f | db median %.1f max %.1f"
              % (ph, d["n"], med(d["total"]), max(d["total"]), med(d["db"]), max(d["db"])))
    print("\n跳过 db（10 次）: median %.1f max %.1f" % (med(out["no_db"]), max(out["no_db"])))
    print("\ndb 分段（20 次均值）: " + " | ".join("%s %.1f" % (k, v) for k, v in out["db_parts"].items()))
    print("db total: min %.1f median %.1f max %.1f" % (out["db_total"]["min"], out["db_total"]["median"], out["db_total"]["max"]))
    print("\nSQLite 写入 D::   median %.1f" % out["disk_d"]["median"])
    print("SQLite 写入 TEMP: median %.1f" % out["disk_c"]["median"])
    print("裸 fsync D::     median %.1f" % out["fsync_d"]["median"])
    print("裸 fsync TEMP:   median %.1f" % out["fsync_c"]["median"])
    print("\nwritten: eval/day4_outlier_data.json")


if __name__ == "__main__":
    main()
