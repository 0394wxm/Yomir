# -*- coding: utf-8 -*-
"""night30_sim40.py — 40 个新字体候选的整体离线模拟（1705 条，要求 0 变差才上线）。"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANDS = {
    "學": "学", "樂": "楽", "德": "徳", "號": "号", "發": "発", "廢": "廃",
    "莊": "荘", "乘": "乗", "讀": "読", "關": "関", "聲": "声", "黨": "党",
    "輕": "軽", "稱": "称", "斷": "断", "讓": "譲", "懷": "懐", "拜": "拝",
    "佛": "仏", "晉": "晋", "亂": "乱", "劍": "剣", "寶": "宝", "勞": "労",
    "龜": "亀", "齒": "歯", "閒": "間", "鄰": "隣", "帶": "帯", "殘": "残",
    "藝": "芸", "蟲": "虫", "蠻": "蛮", "恆": "恒", "臺": "台", "來": "来",
    "賣": "売", "條": "条", "默": "黙", "彌": "弥",
}


def norm(s):
    return re.sub(r"\s+", "", s)


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    with open(os.path.join(ROOT, "eval", "night29_results_parallel.json"), encoding="utf-8") as f:
        rows = json.load(f)["results"]
    imp = wor = fla = 0
    tot_o = tot_n = 0
    worse = []
    for r in rows:
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        new = "".join(CANDS.get(c, c) for c in got)
        d_o, d_n = lev(got, exp), lev(new, exp)
        tot_o += d_o
        tot_n += d_n
        if d_n < d_o:
            imp += 1
        elif d_n > d_o:
            wor += 1
            worse.append((r["id"], d_o, d_n, got[:20], exp[:20]))
        else:
            fla += 1
    n = len(rows)
    print("40 候选 × 1705 条：avgDist %.2f -> %.2f (%+.2f)  改善 %d / 变差 %d / 持平 %d"
          % (tot_o / n, tot_n / n, (tot_n - tot_o) / n, imp, wor, fla))
    for id_, d_o, d_n, g, e in worse[:10]:
        print("  变差 %s %+d (%d->%d) got=%r exp=%r" % (id_, d_n - d_o, d_o, d_n, g, e))
    # 幂等自检
    once = "".join(CANDS.get(c, c) for c in "".join(CANDS.get(c, c) for c in "學樂德號發"))
    print("幂等自检:", "OK" if once == "学楽德号発" else "NG %r" % once)


if __name__ == "__main__":
    main()
