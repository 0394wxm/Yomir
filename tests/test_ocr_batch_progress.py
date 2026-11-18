# -*- coding: utf-8 -*-
"""test_ocr_batch_progress.py — D7 批量 OCR 进度接口的自动化测试。

用桩引擎（每个文件 20 行、每行 10ms）验证进度语义，不加载真模型：
  - 提交后立即返回 job_id（不阻塞）
  - done 单调递增，percent 从 0 涨到 100
  - phase 在 detect/recognize 间推进
  - 最终 results 与文件一一对应
  - 404 / 取消 / 空上传
真模型跑一张图要 30~60 秒，留给 tools/day7_batch_progress_probe.py 手工验。
"""
import os
import sys
import tempfile
import time

_TMPDIR = tempfile.mkdtemp(prefix="kanbun_test_")
os.environ.setdefault("KANBUN_DB", os.path.join(_TMPDIR, "test.db"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class _StubEngine:
    """假引擎：模拟真实阶段的耗时与回调顺序。"""

    def __init__(self, lines=20, line_delay=0.01):
        self.lines = lines
        self.line_delay = line_delay

    def recognize_bytes(self, data, order=None, progress_cb=None):
        if progress_cb:
            progress_cb("detect", 0, 1)
            time.sleep(0.02)
            progress_cb("detect", 1, 1)
        out = []
        for i in range(self.lines):
            time.sleep(self.line_delay)
            out.append("行%d" % (i + 1))
            if progress_cb:
                progress_cb("recognize", i + 1, self.lines)
        return {"text": "\n".join(out), "lines": out, "line_count": len(out),
                "junk_filtered": 0, "order": "cluster", "elapsed_sec": 0.5}


@pytest.fixture(scope="module")
def client():
    from backend.main import app

    with TestClient(app) as c:
        yield c


def _submit(client, n=2):
    files = [("files", ("p%d.png" % i, b"\x89PNG fake bytes %d" % i, "image/png"))
             for i in range(n)]
    return client.post("/api/ocr/batch/async", files=files)


def test_async_batch_progress_monotonic(client, monkeypatch):
    import backend.main as m

    monkeypatch.setattr(m, "get_engine", lambda: _StubEngine(lines=20, line_delay=0.01))
    monkeypatch.setattr(m, "is_available", lambda: True)

    r = _submit(client, 2)
    assert r.status_code == 200, r.text
    job = r.json()
    assert job["total"] == 2 and job["job_id"]

    seen_done, seen_pct, phases = [], [], set()
    deadline = time.time() + 20
    while time.time() < deadline:
        p = client.get("/api/ocr/batch/%s" % job["job_id"])
        assert p.status_code == 200, p.text
        s = p.json()
        seen_done.append(s["done"])
        seen_pct.append(s["percent"])
        if s["phase"]:
            phases.add(s["phase"])
        if s["status"] == "done":
            break
        time.sleep(0.03)

    assert seen_done == sorted(seen_done), "done 必须单调不减: %r" % (seen_done,)
    assert seen_pct == sorted(seen_pct), "percent 必须单调不减: %r" % (seen_pct,)
    assert seen_pct[0] < 100.0, "刚提交就 100%% 说明没有真进度"
    assert seen_pct[-1] == 100.0
    assert seen_done[-1] == 2
    assert "recognize" in phases, "没观察到 recognize 阶段: %r" % (phases,)

    # 关键断言：单张图内部也要有中间值。旧实现只在整张图完成时跳变
    # （2 张图就是 0% → 50% → 100%），真机上表现为 47 秒不动。
    mid = [p for p in seen_pct if 0.0 < p < 50.0]
    assert len(set(mid)) >= 3, \
        "单张图内部没有可用的进度梯度（只有整图跳变）: %r" % (sorted(set(seen_pct)),)

    final = client.get("/api/ocr/batch/%s" % job["job_id"]).json()
    assert final["status"] == "done"
    assert [x["file"] for x in final["results"]] == ["p0.png", "p1.png"]
    assert all(x["status"] == "ok" and x["line_count"] == 20 for x in final["results"])
    assert final["results"][0]["hakubun"].startswith("行1")


def test_async_batch_reports_error_per_file(client, monkeypatch):
    import backend.main as m

    class _Boom:
        def recognize_bytes(self, data, order=None, progress_cb=None):
            raise RuntimeError("onnx exploded")

    monkeypatch.setattr(m, "get_engine", lambda: _Boom())
    monkeypatch.setattr(m, "is_available", lambda: True)

    job = _submit(client, 1).json()
    deadline = time.time() + 10
    s = None
    while time.time() < deadline:
        s = client.get("/api/ocr/batch/%s" % job["job_id"]).json()
        if s["status"] in ("done", "error"):
            break
        time.sleep(0.02)
    assert s["status"] == "done"          # 单文件失败不算作业失败
    assert s["results"][0]["status"] == "ocr_error"
    assert "onnx exploded" in s["results"][0]["note"]


def test_async_batch_missing_runtime_is_job_error(client, monkeypatch):
    import backend.main as m

    monkeypatch.setattr(m, "is_available", lambda: False)
    job = _submit(client, 1).json()
    deadline = time.time() + 10
    s = None
    while time.time() < deadline:
        s = client.get("/api/ocr/batch/%s" % job["job_id"]).json()
        if s["status"] in ("done", "error"):
            break
        time.sleep(0.02)
    assert s["status"] == "error"
    assert "OCR 运行目录缺失" in s["error"]


def test_progress_unknown_job_404(client):
    r = client.get("/api/ocr/batch/doesnotexist")
    assert r.status_code == 404
    assert "job 不存在" in r.json()["detail"]


def test_async_batch_no_files_422(client):
    """完全不传 files 时，FastAPI 在进入处理函数前就返回 422（与同步端点一致）。

    处理函数里的 `if not files: 400` 只在 multipart 里 segments 为空时兜底，
    属于既有行为，本次不改。
    """
    r = client.post("/api/ocr/batch/async", files=[])
    assert r.status_code == 422


def test_cancel_marks_job(client, monkeypatch):
    import backend.main as m

    monkeypatch.setattr(m, "get_engine", lambda: _StubEngine(lines=200, line_delay=0.01))
    monkeypatch.setattr(m, "is_available", lambda: True)

    job = _submit(client, 2).json()
    time.sleep(0.05)
    c = client.post("/api/ocr/batch/%s/cancel" % job["job_id"])
    assert c.status_code == 200
    assert c.json()["status"] == "cancelled"
    time.sleep(0.3)
    s = client.get("/api/ocr/batch/%s" % job["job_id"]).json()
    assert s["status"] == "cancelled"
    assert s["done"] < s["total"], "取消后不应继续跑完剩下的文件"
