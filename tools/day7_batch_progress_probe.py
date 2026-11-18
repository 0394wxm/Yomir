# -*- coding: utf-8 -*-
r"""day7_batch_progress_probe.py — 用真模型跑 2 张本地样张，记录进度曲线。

不做假：每 2 秒轮询一次 GET /api/ocr/batch/<id>，把 (elapsed, done, percent,
phase, phase_done/phase_total) 全打到 stdout 并存 eval/day7_progress_curve.json。
验收点：percent 单调不减；phase 从 detect 切到 recognize；结束时 100%。

图片默认取 ocr_runtime/samples/batch20/ 下两张（已在 .gitignore 里，不入库）。
"""
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IMAGES = [
    os.path.join(ROOT, "ocr_runtime", "samples", "batch20", "ndl_1287221_R0000002.jpg"),
    os.path.join(ROOT, "ocr_runtime", "samples", "batch20", "ndl_11892692_R0000003.jpg"),
]


def main():
    from fastapi.testclient import TestClient
    from backend.main import app

    missing = [p for p in IMAGES if not os.path.isfile(p)]
    if missing:
        print("缺少样张: %s" % missing)
        return 1

    files = [("files", (os.path.basename(p), open(p, "rb").read(), "image/jpeg")) for p in IMAGES]
    curve = []
    out = {}
    with TestClient(app) as c:
        t0 = time.time()
        r = c.post("/api/ocr/batch/async", files=files)
        assert r.status_code == 200, r.text
        job = r.json()
        print("submit -> %s (elapsed %.2fs, 不阻塞)" % (job, time.time() - t0))
        out["submit_elapsed_sec"] = round(time.time() - t0, 2)

        jid = job["job_id"]
        last = None
        while True:
            s = c.get("/api/ocr/batch/%s" % jid).json()
            row = {"t": round(time.time() - t0, 1), "status": s["status"],
                   "done": s["done"], "percent": s["percent"],
                   "phase": s["phase"],
                   "phase_progress": "%d/%d" % (s["phase_done"], s["phase_total"]),
                   "current_file": s["current_file"]}
            if row != last:
                curve.append(row)
                print("%6.1fs  %-8s %d/%d %5.1f%%  %-9s %-9s %s"
                      % (row["t"], row["status"], row["done"], s["total"], row["percent"],
                         row["phase"] or "-", row["phase_progress"], row["current_file"]))
                last = row
            if s["status"] in ("done", "error"):
                out["final"] = s
                break
            time.sleep(2)

    out["curve"] = curve
    out["total_elapsed_sec"] = curve[-1]["t"] if curve else -1
    pcts = [x["percent"] for x in curve]
    out["monotonic"] = pcts == sorted(pcts)
    out["saw_recognize"] = any(x["phase"] == "recognize" for x in curve)
    print("\npercent 单调: %s | 见到 recognize 阶段: %s | 总耗时 %.1fs"
          % (out["monotonic"], out["saw_recognize"], out["total_elapsed_sec"]))
    for x in out["final"]["results"]:
        print("  %-34s %-5s lines=%-3s %ss  %s"
              % (x["file"], x["status"], x.get("line_count", "-"),
                 x.get("elapsed_sec", "-"), (x.get("hakubun") or "")[:28].replace("\n", "/")))

    with io.open(os.path.join(ROOT, "eval", "day7_progress_curve.json"), "w",
                 encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/day7_progress_curve.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
