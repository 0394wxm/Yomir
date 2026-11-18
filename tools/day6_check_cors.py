# -*- coding: utf-8 -*-
"""day6_check_cors.py"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = io.open(os.path.join(ROOT, "backend", "main.py"), encoding="utf-8").read()
print("main.py lines:", len(s.split("\n")))
print("has CORSMiddleware:", "CORSMiddleware" in s)
print("has add_middleware:", "add_middleware" in s)
print("has StaticFiles:", "StaticFiles" in s)

# 前端是怎么调 API 的？相对路径 /api -> vite 代理
fe = io.open(os.path.join(ROOT, "frontend", "src", "App.tsx"), encoding="utf-8").read()
import re
print("fetch targets:", sorted(set(re.findall(r"fetch\(\s*[`'\"]([^`'\"]+)", fe))))
