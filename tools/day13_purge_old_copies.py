# -*- coding: utf-8 -*-
"""day13_purge_old_copies.py — D13 拍板项 2：删除两个未跟踪的旧 sidecar 拷贝。

删的是构建产物（`.gitignore` 第 13/17 行已忽略）：
  frontend/src-tauri/sidecar/_internal/
  frontend/src-tauri/target/release/sidecar/_internal/

它们里面是 **11-18 打包时复制进去的旧 backend/main.py（仍带 on_event）**
和旧 dist JS（仍带已删的 __KANBUN_API_BASE__ 死分支）。下次
`tools/day6_stage_sidecar.py` / `cargo build` 会重新生成。

本脚本先写证据 eval/day13_old_copies.json（文件数、体积、旧版特征命中），
再删目录。默认 dry-run，加 --apply 才真删。

  python tools\\day13_purge_old_copies.py            # 只测量
  python tools\\day13_purge_old_copies.py --apply    # 测量 + 删除
"""
import json
import os
import shutil
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "eval", "day13_old_copies.json")

TARGETS = [
    "frontend/src-tauri/sidecar/_internal",
    "frontend/src-tauri/target/release/sidecar/_internal",
]


def survey(rel):
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.isdir(path):
        return {"exists": False}
    n = 0
    size = 0
    for r, _d, files in os.walk(path):
        for f in files:
            n += 1
            try:
                size += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    info = {"exists": True, "files": n, "bytes": size,
            "mb": round(size / 1048576.0, 1)}

    # 旧版特征：打包进去的 backend/main.py 是否还带 on_event，
    # frontend_dist 的 JS 是否还带已删的全局名。
    main_py = os.path.join(path, "backend", "main.py")
    if os.path.isfile(main_py):
        with open(main_py, encoding="utf-8", errors="replace") as f:
            body = f.read()
        info["main_py_mtime"] = time.strftime(
            "%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(main_py)))
        info["main_py_has_on_event"] = "@app.on_event(" in body
        info["main_py_has_lifespan"] = "async def lifespan" in body

    js_hits = 0
    assets = os.path.join(path, "frontend_dist", "assets")
    if os.path.isdir(assets):
        for f in os.listdir(assets):
            if not f.endswith(".js"):
                continue
            with open(os.path.join(assets, f), encoding="utf-8", errors="replace") as fh:
                if "__KANBUN_API_BASE__" in fh.read():
                    js_hits += 1
    info["dist_js_with_dead_global"] = js_hits
    return info


def main():
    apply = "--apply" in sys.argv
    report = {"tool": "day13_purge_old_copies.py", "apply": apply,
              "gitignore": ["frontend/src-tauri/target/", "frontend/src-tauri/sidecar/"],
              "targets": {}}
    for rel in TARGETS:
        info = survey(rel)
        report["targets"][rel] = info
        if not info.get("exists"):
            print("%-58s (不存在，跳过)" % rel)
            continue
        print("%-58s files=%d MB=%.1f on_event=%s lifespan=%s deadjs=%d"
              % (rel, info["files"], info["mb"],
                 info.get("main_py_has_on_event"), info.get("main_py_has_lifespan"),
                 info.get("dist_js_with_dead_global", 0)))
        if apply:
            t0 = time.time()
            shutil.rmtree(os.path.join(ROOT, rel.replace("/", os.sep)), ignore_errors=False)
            report["targets"][rel]["deleted"] = True
            report["targets"][rel]["delete_sec"] = round(time.time() - t0, 1)
            print("    deleted in %.1fs" % (time.time() - t0))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day13_old_copies.json")


if __name__ == "__main__":
    main()
