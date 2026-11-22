# -*- coding: utf-8 -*-
"""night71_watchdog.py — N71 心跳看门狗：每小时把导入/管线进度写进 SHIFT_LOG（任务书心跳自动化）。

循环直到 night71_pipeline_log.txt 出现「night71_pipeline 结束」（管线全部完成）：
  每 3600s 追加一行心跳（当前阶段＝墨場导入中 p___/582 ／ 管线阶段）＋ byte807 自检值。
不碰任何产品文件；SHIFT_LOG 追加走二进制 UTF-8（.NET AppendAllText 同款、不碰 byte807）。
"""
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIFT_LOG = os.path.join(ROOT, "SHIFT_LOG.md")
IMPORT_LOG = os.path.join(ROOT, "eval", "night71_import_1033232_log.txt")
PIPE_LOG = os.path.join(ROOT, "eval", "night71_pipeline_log.txt")


def import_page():
    try:
        txt = open(IMPORT_LOG, encoding="utf-8", errors="replace").read()
        ms = re.findall(r"\[p(\d+)\] ", txt)
        return int(ms[-1]) if ms else 0, ("[done] ok=" + (re.search(r"\[done\] ok=[\d]+ skip=\d+", txt).group(0)
                                                        if "[done]" in txt else "导入中"))
    except Exception:
        return 0, "导入日志未生成"


def pipeline_phase():
    try:
        txt = open(PIPE_LOG, encoding="utf-8", errors="replace").read()
        if "night71_pipeline 结束" in txt:
            return "管线全部结束"
        if "guwenbert-full" in txt:
            return "管线③ guwenbert 全量跑中"
        if "verify-1033232" in txt:
            return "管线②-5 verify 阶段"
        return "管线① 等待墨場导入"
    except Exception:
        return "管线日志未生成"


def gwb_progress():
    try:
        txt = open(PIPE_LOG, encoding="utf-8", errors="replace").read()
        ms = re.findall(r"(\d+)/8165 avgDist ([\d.]+)", txt)
        return "%s/8165 avg %s" % (ms[-1][0], ms[-1][1]) if ms else "-"
    except Exception:
        return "-"


def main():
    print("watchdog 启动", flush=True)
    while True:
        pg, dl = import_page()
        ph = pipeline_phase()
        b807 = open(SHIFT_LOG, "rb").read()[807]
        line = ("| %s | N71 心跳（看门狗）：阶段=%s；墨場导入 %s（p%d/582）；gwb 进度 %s；byte807=%d。 |"
                % (time.strftime("%Y-%m-%d %H:%M"), ph, dl, pg, gwb_progress(), b807))
        with open(SHIFT_LOG, "ab") as f:
            f.write(line.encode("utf-8") + b"\r\n")
        print(line, flush=True)
        if ph == "管线全部结束":
            print("watchdog 退出（管线完成）", flush=True)
            return
        time.sleep(3600)


if __name__ == "__main__":
    main()
