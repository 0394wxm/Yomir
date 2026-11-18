# -*- coding: utf-8 -*-
"""day6_sidecar_e2e.py — 对已启动的 sidecar 做端到端验收（不启动任何进程）。

验收项（对应 D6 任务书「后端随壳启动、断网能跑訓読」）：
  1. /health 报 engine_loaded=True
  2. 后端托管的前端首页真的能被拿到（同源，免 CORS）
  3. /assets/* 静态资源可达
  4. /api/kundoku 返回真实書き下し文
  5. 前端首页里引用的 JS 里带有 /health 轮询代码（确认打的是新构建）
  6. 断网假设：整个请求只用 127.0.0.1，不出网

用法：python tools/day6_sidecar_e2e.py [port]
"""
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import urllib.request

BASE = None


def get(path, timeout=180):
    url = BASE + path
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=timeout) as r:
        body = r.read()
        return r.status, body, (time.time() - t0) * 1000.0


def main():
    global BASE
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    BASE = "http://127.0.0.1:%d" % port
    print("base:", BASE)
    fails = []

    # 1. /health
    try:
        st, body, ms = get("/health")
        d = json.loads(body)
        print("[1] /health %d %.0fms %s" % (st, ms, d))
        if not d.get("engine_loaded"):
            fails.append("engine_loaded=False (%r)" % d.get("engine_error"))
    except Exception as e:
        fails.append("/health 失败: %r" % e)
        print("[1] /health 失败: %r" % e)
        return 1

    # 2. 前端首页
    try:
        st, body, ms = get("/")
        html = body.decode("utf-8", "replace")
        print("[2] / %d %.0fms %d bytes" % (st, ms, len(body)))
        if "text/html" not in "x" and "<div id=\"root\">" not in html and "<div id=root>" not in html:
            # index.html 只要含 root 挂载点即可
            fails.append("首页不像 SPA index.html: %r" % html[:200])
    except Exception as e:
        fails.append("首页失败: %r" % e)
        print("[2] 首页失败: %r" % e)
        return 1

    # 3. 静态资源
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
    if not assets:
        fails.append("index.html 里找不到 /assets/ 引用")
    else:
        for a in sorted(set(assets)):
            try:
                st, body, ms = get(a)
                print("[3] %s %d %.0fms %d bytes" % (a, st, ms, len(body)))
                if st != 200 or not body:
                    fails.append("%s -> %d" % (a, st))
            except Exception as e:
                fails.append("%s 失败: %r" % (a, e))

    # 4. 真訓読
    payload = json.dumps({"text": "王顧左右而言他", "merge": True,
                          "ortho": True, "cache": False}).encode("utf-8")
    req = urllib.request.Request(BASE + "/api/kundoku", data=payload,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read())
        ms = (time.time() - t0) * 1000.0
        kk = (d.get("kakikudashi") or "").strip()
        print("[4] /api/kundoku %.0fms engine=%s text_type=%s"
              % (ms, d.get("engine"), d.get("text_type")))
        print("     白文: %r" % (d.get("hakubun") or ""))
        print("     返り点: %r" % (d.get("kaeriten_text") or ""))
        print("     書き下し: %r" % kk)
        if not kk:
            fails.append("/api/kundoku 書き下し为空（engine=%r err=%r）"
                         % (d.get("engine"), d.get("error")))
    except Exception as e:
        fails.append("/api/kundoku 失败: %r" % e)
        print("[4] /api/kundoku 失败: %r" % e)

    # 5. 打的是新前端：JS 里应有 /health 轮询与进度条字符串
    try:
        js_urls = [a for a in sorted(set(assets)) if a.endswith(".js")]
        found_health = found_progress = False
        for a in js_urls:
            st, body, _ = get(a)
            t = body.decode("utf-8", "replace")
            if "/health" in t:
                found_health = True
            if "识别文字" in t or "\u8bc6\u522b\u6587\u5b57" in t:
                found_progress = True
        print("[5] JS 含 /health=%s 含识别进度文案=%s" % (found_health, found_progress))
        if not found_health:
            fails.append("打包的 JS 里没有 /health（说明不是新构建？）")
        if not found_progress:
            fails.append("打包的 JS 里没有 D7 进度文案")
    except Exception as e:
        fails.append("检查 JS 失败: %r" % e)

    print()
    if fails:
        print("FAIL (%d):" % len(fails))
        for f in fails:
            print("  -", f)
        return 1
    print("PASS: 6/6 sidecar 端到端项通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
