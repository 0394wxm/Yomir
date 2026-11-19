# -*- coding: utf-8 -*-
"""test_lifespan_migration.py — D12: on_event -> lifespan 迁移的回归测试。

为什么需要：FastAPI 0.93+ 里 `@app.on_event("startup")` 是 Deprecated，
运行时打 DeprecationWarning。D12 把它换成 `@asynccontextmanager` 的 lifespan，
行为要求**逐条不变**：

  1. 启动先 db.init_db()；
  2. KANBUN_LAZY_ENGINE=1（桌面壳 sidecar）时后台线程加载引擎，不占端口；
  3. 普通模式同步加载；
  4. 引擎加载失败不阻止服务启动（/health 仍 ok，ENGINE_ERROR 留错误）；
  5. 不再有任何 on_event 注册（否则警告会回来）。

另外锁住 D12 删掉的前端死代码：`window.__KANBUN_API_BASE__` 在 Rust 侧
从未注入（见 REPORT_DAY6.md §7.2），再从源码里长回来就是回归。
"""
import asyncio
import os
import subprocess
import sys
import threading

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _run_lifespan(m):
    """手动跑一遍 lifespan（等价于 TestClient 的 with 块，但可注入假依赖）。"""
    async def go():
        async with m.lifespan(None):
            pass

    asyncio.run(go())


def test_no_on_event_handlers_registered():
    """迁移后 app.router 上不能再有 on_event 注册的 startup/shutdown 回调。"""
    import backend.main as m

    assert list(m.app.router.on_startup) == [], "on_event(startup) 又长回来了"
    assert list(m.app.router.on_shutdown) == [], "on_event(shutdown) 又长回来了"


def test_lifespan_is_wired_into_app():
    """app 创建时确实把 lifespan 传进去了（不是定义了却没用）。"""
    import backend.main as m

    assert m.app.router.lifespan_context is m.lifespan


def test_lifespan_calls_init_db(monkeypatch):
    """启动钩子第一件事仍是建表。"""
    import backend.main as m

    calls = []
    monkeypatch.setattr(m.db, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(m, "_load_engine", lambda: calls.append("load_engine"))
    monkeypatch.delenv("KANBUN_LAZY_ENGINE", raising=False)

    _run_lifespan(m)

    assert calls == ["init_db", "load_engine"]


def test_lifespan_sync_mode_loads_engine(monkeypatch):
    """普通模式：请求可用前引擎已就绪（tests 依赖这一点）。"""
    import backend.main as m

    loaded = []
    monkeypatch.setattr(m.db, "init_db", lambda: None)
    monkeypatch.setattr(m, "_load_engine", lambda: loaded.append(1))
    monkeypatch.setattr(m, "ENGINE_ERROR", "")
    monkeypatch.delenv("KANBUN_LAZY_ENGINE", raising=False)

    _run_lifespan(m)

    assert loaded == [1]
    assert m.ENGINE_ERROR == ""


def test_lifespan_lazy_mode_loads_in_background(monkeypatch):
    """sidecar 模式：lifespan 立刻 yield，引擎在后台线程里加载。"""
    import backend.main as m

    done = threading.Event()
    monkeypatch.setattr(m.db, "init_db", lambda: None)
    monkeypatch.setattr(m, "_load_engine", lambda: done.set())
    monkeypatch.setenv("KANBUN_LAZY_ENGINE", "1")

    async def go():
        async with m.lifespan(None):
            # yield 时后台线程已经启动过（可能还没跑完，但不应阻塞到这里）
            pass

    asyncio.run(go())
    assert done.wait(timeout=5), "后台加载线程没有跑 _load_engine"


def test_lifespan_swallows_engine_failure(monkeypatch):
    """引擎加载失败：服务照常启动，错误写进 ENGINE_ERROR 供 /health 暴露。"""
    import backend.main as m

    def boom():
        raise RuntimeError("model missing")

    monkeypatch.setattr(m.db, "init_db", lambda: None)
    monkeypatch.setattr(m, "_load_engine", boom)
    monkeypatch.setattr(m, "ENGINE_ERROR", "")
    monkeypatch.delenv("KANBUN_LAZY_ENGINE", raising=False)

    _run_lifespan(m)  # 不抛

    assert "model missing" in m.ENGINE_ERROR


def test_lifespan_closes_cleanly(monkeypatch):
    """yield 之后没有异常（关停路径不残留裸 raise）。"""
    import backend.main as m

    monkeypatch.setattr(m.db, "init_db", lambda: None)
    monkeypatch.setattr(m, "_load_engine", lambda: None)
    monkeypatch.delenv("KANBUN_LAZY_ENGINE", raising=False)

    _run_lifespan(m)  # 正常返回即通过


def test_import_has_no_startup_deprecation_warning():
    """子进程里用 -W error 导入：DeprecationWarning 一旦回来就失败。

    不在本进程 import 是因为 backend.main 已经被别处导入过，警告只出一次。
    """
    code = (
        "import sys;"
        "sys.path.insert(0, %r);"
        "import backend.main;"
        "print('ok')"
    ) % ROOT
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("KANBUN_LAZY_ENGINE", None)
    p = subprocess.run([sys.executable, "-W", "error::DeprecationWarning", "-c", code],
                       capture_output=True, text=True, encoding="utf-8", timeout=120,
                       cwd=ROOT, env=env)
    assert p.returncode == 0, p.stderr[-2000:]
    assert "ok" in p.stdout


def test_frontend_has_no_kanbun_api_base_global():
    """D12: 前端源码里不能再读 window.__KANBUN_API_BASE__（Rust 从未注入）。

    只查代码行：删除时的说明性注释会提到这个名字，那是文档而不是死代码。
    """
    srcs = [os.path.join(ROOT, "frontend", "src", "App.tsx"),
            os.path.join(ROOT, "frontend", "src", "vite-env.d.ts")]
    checked = 0
    for path in srcs:
        if not os.path.isfile(path):
            continue
        checked += 1
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                code = line.split("//", 1)[0]
                assert "__KANBUN_API_BASE__" not in code, \
                    "%s:%d 里又出现死代码：%s" % (os.path.basename(path), lineno, line.strip())
    if not checked:
        pytest.skip("前端源码不在当前检出里")
