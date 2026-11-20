# -*- coding: utf-8 -*-
"""night43_scan_md.py — 扫 book.md 找疑似页边噪音（书志/蔵書印/花押）行所在页（NIGHT43 测量用）。

只是**测量辅助**：用于圈定「拿框↔文本配对做分布统计」的选样页。
过滤器的实现红线是只用框几何、不用文本——本工具的启发式不进过滤器。
用法: python -X utf8 -I tools/night43_scan_md.py [book.md路径]
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_BOOK = os.path.join(ROOT, "eval", "import_pid_11892692", "book.md")

# Night42 §3 点名样例（文本样例仅用于测量期定位噪音行的框，不进过滤器）
NAMED = ["晴辰", "筒城君", "専列記", "早朝堀紀州岩朝不福指越", "愛利氏", "西側面",
         "一四十一冊", "新助麹町三丁"]
# 书志/蔵書印类常见字面（测量期圈页用，宽网）
SUSPECT = re.compile(r"氏|冊|蔵|藏|之印|珍書|跋|奥書|花押|墨付|目録数")

BODY_SKIP = ("#", "*", "`", "---", "耗时")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOOK
    with open(path, encoding="utf-8") as f:
        text = f.read()
    page = None
    body = []          # (page, line) 白文正文行
    for l in text.splitlines():
        if l.startswith("## p"):
            page = l.split()[1]
            continue
        if page and l and not l.startswith(BODY_SKIP):
            body.append((page, l))
    print("book:", os.path.basename(path))
    print("hakubun body lines:", len(body))

    print("-- named (night42 §3 examples) --")
    for p, l in body:
        if any(s in l for s in NAMED):
            print("  %s %s" % (p, l))

    # 每页命中 suspect 字面的行数，倒序看哪些页书志类行集中
    from collections import Counter
    cnt = Counter()
    for p, l in body:
        if SUSPECT.search(l):
            cnt[p] += 1
    print("-- pages by suspect-char line count (top 15) --")
    for p, n in cnt.most_common(15):
        print("  %s %d" % (p, n))


if __name__ == "__main__":
    main()
