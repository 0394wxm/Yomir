# -*- coding: utf-8 -*-
"""
db.py — SQLite 持久化（Night 2）。只两张表，字段按任务书要求，不加多余字段。

requests : id, hakubun, created_at          —— 每次 /api/kundoku 调用
results  : id, request_id, kaeriten_text, kakikudashi, created_at
"""
import os
import sqlite3
import threading
from datetime import datetime

DB_PATH = os.environ.get("KANBUN_DB", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kanbun.db"))

_LOCK = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with _LOCK:
        conn = get_conn()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS requests ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " hakubun TEXT NOT NULL,"
                " created_at TEXT NOT NULL)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS results ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " request_id INTEGER NOT NULL REFERENCES requests(id),"
                " kaeriten_text TEXT NOT NULL,"
                " kakikudashi TEXT NOT NULL,"
                " created_at TEXT NOT NULL)")
            conn.commit()
        finally:
            conn.close()


def save_kundoku(hakubun: str, kaeriten_text: str, kakikudashi: str) -> int:
    """一次訓読成功后落库，返回 request id。失败不影响 API 主流程。"""
    now = datetime.now().isoformat(timespec="seconds")
    with _LOCK:
        conn = get_conn()
        try:
            cur = conn.execute("INSERT INTO requests (hakubun, created_at) VALUES (?, ?)", (hakubun, now))
            rid = cur.lastrowid
            conn.execute(
                "INSERT INTO results (request_id, kaeriten_text, kakikudashi, created_at) VALUES (?, ?, ?, ?)",
                (rid, kaeriten_text, kakikudashi, now))
            conn.commit()
            return rid
        finally:
            conn.close()
