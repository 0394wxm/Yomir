# -*- coding: utf-8 -*-
"""test_web_mount.py — D6: 后端托管前端（桌面壳同源）的回归测试。

为什么需要：`/` 这个路径「在 _mount_web() 里再注册一个 @app.get("/")」是行不通的
（Starlette 按注册顺序匹配，文件靠前注册的 root() 永远赢）。真实实现是 root()
查模块级变量 _WEB_DIST 分流。这个文件锁住三点：
  1. 纯 API 模式（没有 dist）：/ 返回 JSON 服务信息，行为不变；
  2. 托管模式：/ 返回 index.html（而不是 JSON）；
  3. dist 缺失时 _mount_web() 返回 False 且不留下半开状态。
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


@pytest.fixture()
def dist_dir(tmp_path):
    """造一个最小 dist：index.html + assets/app.js。"""
    d = tmp_path / "dist"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text(
        '<!doctype html><html><body><div id="root"></div>'
        '<script src="/assets/app.js"></script></body></html>',
        encoding="utf-8")
    (d / "assets" / "app.js").write_text("console.log('kanbun')\n", encoding="utf-8")
    return str(d)


def test_api_only_mode_root_returns_json():
    """默认（未设置 KANBUN_SIDECAR）不挂前端，/ 还是 JSON。"""
    import backend.main as m
    assert m._WEB_DIST is None, "测试环境不该已有前端挂载"
    with TestClient(m.app) as c:
        r = c.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["service"] == "kanbun-kakikudashi"
        assert "/api/kundoku" in body["endpoints"]


def test_root_switches_to_index_when_web_dist_set(monkeypatch, dist_dir):
    """设了 _WEB_DIST 之后，/ 返回 index.html 而不是 JSON。

    这才是 D6 真正的分流点：同一个 root() 函数、同一个路由对象，
    行为随模块级变量变化。不去 mock os.path，只改两个变量。
    """
    import backend.main as m
    monkeypatch.setattr(m, "_WEB_DIST", dist_dir)
    monkeypatch.setattr(m, "_WEB_INDEX", os.path.join(dist_dir, "index.html"))

    with TestClient(m.app) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert '<div id="root">' in r.text
        # API 不受影响
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["ok"] is True


def test_mount_web_skips_when_dist_missing(monkeypatch, tmp_path):
    """dist 不存在时 _mount_web 返回 False，且不改 _WEB_DIST（不残留半开状态）。"""
    import backend.main as m
    monkeypatch.setattr(m, "_WEB_DIST", None)
    monkeypatch.setattr(m, "_WEB_INDEX", None)

    empty = str(tmp_path / "nope")
    monkeypatch.setattr(m.sys, "_MEIPASS", empty, raising=False)
    ok = m._mount_web()
    assert ok is False
    assert m._WEB_DIST is None
    assert m._WEB_INDEX is None


def test_web_index_unset_fails_loudly():
    """_web_index() 在未挂载时会抛错，而不是返回空响应骗人。"""
    import backend.main as m
    monkey_d = m._WEB_DIST
    if monkey_d is None:
        with pytest.raises(TypeError):
            m._web_index()
    else:
        pytest.skip("当前环境已挂载前端")
