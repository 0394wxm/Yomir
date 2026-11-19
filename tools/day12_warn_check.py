# -*- coding: utf-8 -*-
"""day12_warn_check.py — D12 取证：on_event -> lifespan 前后 DeprecationWarning 计数。

做法：把 HEAD 版 backend/main.py 导出到仓外临时目录（副本），
在各自子进程里 import 并 catch_warnings 计数，互不污染。

  python tools\\day12_warn_check.py
"""
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE = r'''
import sys, warnings
sys.path.insert(0, ROOT)
sys.path.insert(0, EXTRA)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    import MODULE
dep = [str(x.message) for x in w if issubclass(x.category, DeprecationWarning)]
print("count=%d" % len(dep))
for d in dep:
    print("  " + d.replace("\n", " ")[:160])
'''


def probe(module, extra=""):
    code = (PROBE.replace("ROOT", repr(ROOT))
                .replace("EXTRA", repr(extra))
                .replace("MODULE", module))
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("KANBUN_LAZY_ENGINE", None)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, encoding="utf-8", timeout=180,
                       cwd=ROOT, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    # 1) 当前工作区
    rc, out = probe("backend.main")
    print("=== 当前工作区 backend.main ===")
    print(out.strip() or "(无输出)")
    print("rc=%d" % rc, flush=True)

    # 2) HEAD 版（旧 on_event 实现）
    tmp = tempfile.mkdtemp(prefix="day12_head_")
    p = subprocess.run(["git", "show", "HEAD:backend/main.py"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print("git show 失败，跳过对照：", p.stderr[:200])
        return
    path = os.path.join(tmp, "old_main.py")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(p.stdout)
    rc2, out2 = probe("old_main", extra=tmp)
    print("\n=== HEAD 版（@app.on_event）===")
    print(out2.strip() or "(无输出)")
    print("rc=%d" % rc2)


if __name__ == "__main__":
    main()
