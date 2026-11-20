# -*- coding: utf-8 -*-
"""
db.py — SQLite 持久化（Night 2 建表 / Night 7 历史记录扩展）。

requests : id, hakubun(提交白文), ocr_hakubun(OCR 原始白文，纠错基线，可为 NULL),
           prev_request_id(上一条请求，用于翻回), created_at
results  : id, request_id, kaeriten_text, kakikudashi, created_at

历史翻回：GET /api/history（main.py）按 id 倒序返回 requests⋈results。
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


def _column_exists(conn, table, column):
    cur = conn.execute("PRAGMA table_info(%s)" % table)
    return any(row[1] == column for row in cur.fetchall())


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
            # Night 7 迁移：纠错工作流需要的两列（存在则跳过）
            if not _column_exists(conn, "requests", "ocr_hakubun"):
                conn.execute("ALTER TABLE requests ADD COLUMN ocr_hakubun TEXT")
            if not _column_exists(conn, "requests", "prev_request_id"):
                conn.execute("ALTER TABLE requests ADD COLUMN prev_request_id INTEGER")
            conn.commit()
        finally:
            conn.close()


def save_kundoku(hakubun: str, kaeriten_text: str, kakikudashi: str,
                 ocr_hakubun=None, prev_request_id=None) -> int:
    """一次訓読成功后落库，返回 request id。失败不影响 API 主流程。"""
    now = datetime.now().isoformat(timespec="seconds")
    with _LOCK:
        conn = get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO requests (hakubun, ocr_hakubun, prev_request_id, created_at) VALUES (?, ?, ?, ?)",
                (hakubun, ocr_hakubun, prev_request_id, now))
            rid = cur.lastrowid
            conn.execute(
                "INSERT INTO results (request_id, kaeriten_text, kakikudashi, created_at) VALUES (?, ?, ?, ?)",
                (rid, kaeriten_text, kakikudashi, now))
            conn.commit()
            return rid
        finally:
            conn.close()


def get_history(limit: int = 20):
    """按 id 倒序返回最近请求及其訓読结果（翻回上一条用）。"""
    with _LOCK:
        conn = get_conn()
        try:
            cur = conn.execute(
                "SELECT r.id, r.hakubun, r.ocr_hakubun, r.prev_request_id, r.created_at,"
                " s.kaeriten_text, s.kakikudashi"
                " FROM requests r LEFT JOIN results s ON s.request_id = r.id"
                " ORDER BY r.id DESC LIMIT ?", (int(limit),))
            rows = cur.fetchall()
        finally:
            conn.close()
    return [
        {
            "id": row[0], "hakubun": row[1], "ocr_hakubun": row[2],
            "prev_request_id": row[3], "created_at": row[4],
            "kaeriten_text": row[5], "kakikudashi": row[6],
        }
        for row in rows
    ]


def get_requests_by_ids(ids):
    """NIGHT52: 按 id 列表取请求（id 升序，EPUB 导出用）。

    与 get_history 同一投影；找不到的 id 不在返回里（调用方据此报 404）。
    """
    ids = [int(i) for i in ids]
    if not ids:
        return []
    with _LOCK:
        conn = get_conn()
        try:
            qmarks = ",".join("?" * len(ids))
            cur = conn.execute(
                "SELECT r.id, r.hakubun, r.ocr_hakubun, r.prev_request_id, r.created_at,"
                " s.kaeriten_text, s.kakikudashi"
                " FROM requests r LEFT JOIN results s ON s.request_id = r.id"
                " WHERE r.id IN (%s) ORDER BY r.id ASC" % qmarks, ids)
            rows = cur.fetchall()
        finally:
            conn.close()
    return [
        {
            "id": row[0], "hakubun": row[1], "ocr_hakubun": row[2],
            "prev_request_id": row[3], "created_at": row[4],
            "kaeriten_text": row[5], "kakikudashi": row[6],
        }
        for row in rows
    ]
