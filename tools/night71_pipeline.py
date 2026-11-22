# -*- coding: utf-8 -*-
"""night71_pipeline.py — N71 剩余流程链式驱动（防会话中断的可续跑管线）。

步骤（全部顺序执行，不并行）：
  1. 等待 1033232 墨場必携导入进程结束（轮询其日志 [done]/Traceback，2h 超时保底）；
  2. tools/night71_verify_book.py 1033232 → eval/night71_verify_1033232.json；
  3. SHIFT_LOG 记一笔（②-5 完成/失败 + verify 数）；
  4. tools/night71_guwenbert_full.py 全量 8165（自身每 500 条写 SHIFT_LOG 进度）；
  5. tools/night71_h2h.py → eval/night71_h2h.txt；
  6. SHIFT_LOG 记一笔（③ 完成 + h2h 数字）。
每步日志落盘 eval/night71_pipeline_log.txt（本驱动 stdout）；任何一步失败不阻断后续
（记一笔继续），最终以日志与归档为准。重跑安全：已完成的步骤按产物存在性跳过。
"""
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
SHIFT_LOG = os.path.join(ROOT, "SHIFT_LOG.md")
PY = sys.executable
IMPORT_LOG = os.path.join(EV, "night71_import_1033232_log.txt")
PIPE_LOG = os.path.join(EV, "night71_pipeline_log.txt")


def plog(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(PIPE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def shift_log(msg):
    with open(SHIFT_LOG, "ab") as f:
        f.write(("| %s | %s |\r\n" % (time.strftime("%Y-%m-%d %H:%M"), msg)).encode("utf-8"))


def run_step(cmd, log_tag):
    """subprocess 跑一步，stdout/stderr 追加到 pipeline log；返回 exit code。"""
    plog("开始: %s" % cmd)
    t0 = time.time()
    with open(PIPE_LOG, "a", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=ROOT, shell=True, stdout=f, stderr=subprocess.STDOUT)
    plog("结束: exit=%d (%.0f 分钟) [%s]" % (p.returncode, (time.time() - t0) / 60.0, log_tag))
    return p.returncode


def main():
    plog("night71_pipeline 启动")

    # ---- 1. 等待墨場必携导入结束 ----
    done = False
    if os.path.exists(os.path.join(EV, "import_pid_1033232", "book.md")):
        raw = open(os.path.join(EV, "import_pid_1033232", "book.md"), encoding="utf-8").read()
        done = "[done]" in raw or "## p582" in raw
    if not done:
        plog("等待导入进程结束（轮询 %s）" % IMPORT_LOG)
        t0 = time.time()
        while time.time() - t0 < 12 * 3600:
            time.sleep(60)
            if not os.path.exists(IMPORT_LOG):
                continue
            txt = open(IMPORT_LOG, encoding="utf-8", errors="replace").read()
            if "[done]" in txt:
                done = True
                break
            if "Traceback" in txt:
                plog("导入进程 Traceback——重试一次（resume 版，页级续跑）")
                run_step('"%s" tools/night71_import_resume.py 1033232 *>> eval\\night71_import_1033232_log.txt'
                         % PY, "retry-import")
                txt = open(IMPORT_LOG, encoding="utf-8", errors="replace").read()
                done = "[done]" in txt
                break
        else:
            plog("等待超时（12h）——按失败处理")
    plog("导入结束标记: %s" % done)
    m = re.search(r"\[done\] ok=(\d+) skip=(\d+) ocr=([\d.]+)s", open(
        IMPORT_LOG, encoding="utf-8", errors="replace").read()) if os.path.exists(IMPORT_LOG) else None
    plog("导入摘要: %s" % (m.group(0) if m else "无 [done] 行"))

    # ---- 2/3. verify + 记一笔 ----
    rc = run_step('"%s" tools/night71_verify_book.py 1033232' % PY, "verify-1033232")
    vsum = {}
    vfn = os.path.join(EV, "night71_verify_1033232.json")
    if os.path.exists(vfn):
        vsum = json.load(open(vfn, encoding="utf-8"))
    ok = vsum.get("ok", "?")
    n = vsum.get("book_md_pages", "?")
    sha = vsum.get("book_md_sha256_16", "?")
    shift_log("N71②-5：1033232 墨場必携新註（582 页）导完%s（%s）→ verify %s（ok=%s/%s、0行=%s、ocr_fail=%s、noise %s 行、sha16 %s）；OCR 合计 %s s。⑤ 管线转 ③ guwenbert 全量。"
              % ("完成" if m else "异常（见日志）", m.group(0) if m else "-",
                 "PASS" if rc == 0 else "FAIL", ok, n,
                 vsum.get("zero_line", "?"), vsum.get("ocr_fail", "?"),
                 vsum.get("ascii_noise_total_lines", "?"), sha,
                 m.group(3) if m else "?"))

    # ---- 4. guwenbert 全量（大头，自身每 500 条写 SHIFT_LOG） ----
    gwb_out = os.path.join(EV, "night71_guwenbert_8165.json")
    if not os.path.exists(gwb_out):
        rc_g = run_step('"%s" tools/night71_guwenbert_full.py' % PY, "guwenbert-full")
        if rc_g != 0:
            shift_log("N71③ guwenbert 全量异常退出 exit=%d——见 eval/night71_pipeline_log.txt（一次重试后仍失败则如实记录）。" % rc_g)
            rc_g = run_step('"%s" tools/night71_guwenbert_full.py' % PY, "guwenbert-full-retry")
    else:
        plog("night71_guwenbert_8165.json 已存在——跳过重跑")
        rc_g = 0

    # ---- 5/6. h2h + 记一笔 ----
    if os.path.exists(gwb_out):
        rc_h = run_step('"%s" tools/night71_h2h.py' % PY, "h2h")
        htxt = open(os.path.join(EV, "night71_h2h.txt"), encoding="utf-8").read() if os.path.exists(
            os.path.join(EV, "night71_h2h.txt")) else ""
        mm = re.search(r"逐条对决：规则更好 (\d+) \| guwenbert 更好 (\d+) \| 持平 (\d+)", htxt)
        ma = re.search(r"规则\s+avgDist ([\d.]+) \| 精确 (\d+)", htxt)
        mb = re.search(r"guwenbert avgDist ([\d.]+) \| 精确 (\d+)", htxt)
        gsum = json.load(open(gwb_out, encoding="utf-8"))["summary"]
        shift_log("N71③完成：guwenbert 全量 8165（OK %d/error %d/exact %d/avgDist %s/总耗时 %.1f 分钟）；h2h 全量：规则更好 %s／gwb 更好 %s／平 %s，规则 avgDist %s vs gwb %s。管线全部结束。"
                  % (gsum["n"], gsum["errors"], gsum["exact"], gsum["avg_edit_distance"],
                     gsum.get("total_elapsed_sec", 0) / 60.0,
                     mm.group(1) if mm else "?", mm.group(2) if mm else "?",
                     mm.group(3) if mm else "?",
                     ma.group(1) if ma else "?", mb.group(1) if mb else "?"))
    else:
        shift_log("N71③ guwenbert 全量未产出归档（两次尝试失败）——如实记录，待续跑。")
    plog("night71_pipeline 结束")


if __name__ == "__main__":
    main()
