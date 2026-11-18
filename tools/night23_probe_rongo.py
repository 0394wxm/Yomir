# -*- coding: utf-8 -*-
"""night23_probe_rongo.py — 探 kanbun.info 論語部页面结构（Night 21 §5 顺延项）。

Night 21 已记录：keibu 页是 rongo01.html → rongo0101-16.html 三级结构、
正文用 honbun02 class（非 genbun01/yomi02）。本探针确认：
  1) 索引页链接形态与章节页清单
  2) 章节页里 原文/書き下し文 的成对标记（类名、顺序、ruby 形态）
"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


idx = fetch("https://kanbun.info/keibu/rongo01.html")
print("=== rongo01.html links ===")
links = []
for m in re.finditer(r'href="([^"]*rongo[^"]*\.html)"', idx):
    u = m.group(1)
    if u not in links:
        links.append(u)
print("unique rongo links:", len(links))
for u in links[:12]:
    print("  ", u)

# 挑一章看结构
chap = links[0] if links else ""
if chap and not chap.startswith("http"):
    chap = "https://kanbun.info/keibu/" + chap.rsplit("/", 1)[-1]
print("\n=== chapter:", chap, "===")
page = fetch(chap)
# 全部 div class 出现次数
classes = re.findall(r'<div class="([^"]+)"', page)
from collections import Counter
print("div classes:", dict(Counter(classes)))
# ruby 用法
print("ruby tags:", len(re.findall(r"<ruby>", page)), "rt:", len(re.findall(r"<rt>", page)),
      "rp:", len(re.findall(r"<rp>", page)))
# 打印第一个 honbun02 附近的原始 HTML（前 900 字）
i = page.find("honbun02")
print("\n--- raw html around first honbun02 ---")
print(page[max(0, i - 400):i + 500])
# 找 yomi 类
for pat in ("yomi", "kakiku", "shodoku", "honbun"):
    ms = re.findall(r'class="([^"]*%s[^"]*)"' % pat, page)
    print("\nclass containing %r:" % pat, Counter(ms) if ms else "NONE")
