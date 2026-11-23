# -*- coding: utf-8 -*-
"""night78_heartbeat_loop.py — 每小时调用 night78_heartbeat.py（后台运行，收工时杀掉）。"""
import subprocess
import sys
import time

PY = r"D:\Python312\python.exe"
TOOL = r"D:\kanbun-rulel\tools\night78_heartbeat.py"
MAX_HOURS = 14

for i in range(MAX_HOURS):
    time.sleep(3600)
    try:
        subprocess.run([PY, TOOL, "heartbeat auto (+%dh)" % (i + 1)], timeout=120)
    except Exception as e:
        print("heartbeat loop error:", e, file=sys.stderr)
