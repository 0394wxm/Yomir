# -*- coding: utf-8 -*-
"""day6_startup_time.py — 测打包版 sidecar 的冷启动时间（写报告用）。

三个时间点：
  t_port   打印 KANBUN_PORT= 的时刻（窗口能开了）
  t_ready  /health 报 engine_loaded=true 的时刻（能訓読了）
  t_first  首次 /api/kundoku 返回的时刻（含引擎预热）

用法：python tools/day6_startup_time.py [exe路径]
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    exe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "dist", "kanbun-sidecar", "kanbun-sidecar.exe")
    if not os.path.isfile(exe):
        print("找不到:", exe)
        return 1

    env = dict(os.environ)
    env["KANBUN_LAZY_ENGINE"] = "1"   # 与桌面壳一致
    env.pop("KANBUN_PORT", None)

    print("exe:", exe)
    t0 = time.time()
    p = subprocess.Popen([exe], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         env=env, text=True, encoding="utf-8", errors="replace",
                         bufsize=1, cwd=str(ROOT))

    port = None
    t_port = None
    lines = []

    def reader():
        nonlocal port, t_port
        for line in p.stdout:
            lines.append(line.rstrip())
            if port is None and line.startswith("KANBUN_PORT="):
                port = int(line.split("=", 1)[1].strip())
                t_port = time.time() - t0

    th = threading.Thread(target=reader, daemon=True)
    th.start()

    deadline = t0 + 120
    while port is None and time.time() < deadline:
        time.sleep(0.05)
    if port is None:
        print("超时：没读到 KANBUN_PORT")
        p.kill()
        return 1

    base = "http://127.0.0.1:%d" % port
    print("KANBUN_PORT=%d after %.2fs" % (port, t_port))

    t_ready = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/health", timeout=2) as r:
                d = json.loads(r.read())
            if d.get("engine_loaded"):
                t_ready = time.time() - t0
                break
        except Exception:
            pass
        time.sleep(0.2)
    if t_ready is None:
        print("超时：引擎没就绪")
        p.kill()
        return 1
    print("engine_loaded after %.2fs" % t_ready)

    payload = json.dumps({"text": "王顧左右而言他", "cache": False}).encode()
    req = urllib.request.Request(base + "/api/kundoku", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    t_first = time.time() - t0
    print("first /api/kundoku after %.2fs -> %r" % (t_first, d.get("kakikudashi")))

    p.terminate()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

    out = {"port_ms": round(t_port * 1000),
           "engine_ready_ms": round(t_ready * 1000),
           "first_kundoku_ms": round(t_first * 1000),
           "request_elapsed_ms": round(float(d.get("elapsed_sec") or 0) * 1000) or None}
    print()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open(os.path.join(ROOT, "eval", "day6_startup.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("written eval/day6_startup.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
