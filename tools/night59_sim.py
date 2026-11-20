# -*- coding: utf-8 -*-
"""night59_sim.py — N59 第三步：「白文预处理 應→応」离线模拟（只模拟、不上线）。

对 golden_3000 里 hakubun 含「應」的 18 行：
  a) 原始 hakubun 走完整引擎（udkanbun + udkundoku.translate raw=True 全链）；
  b) 预处理後（應→応，含聲/黃 等同句其他旧形不动，只动 應）走同链；
  逐行对照：输出文本、异常、与 expected 的 Levenshtein。
再对 3 句语料外探针做副作用抽查。
输出 eval/night59_sim.txt / night59_sim.json。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)

import udkanbun  # noqa: E402
import udkundoku  # noqa: E402
from backend.kundoku_rules import (  # noqa: E402
    merge_proper_nouns, normalize_shinjitai, style_fix_with_hakubun)


def _extract_kakikudashi(conllu: str) -> str:
    """与 backend/main.py 同实现。"""
    return "\n".join(l[9:] for l in conllu.split("\n") if l.startswith("# text = "))


def norm(s):
    return re.sub(r"\s+", "", s or "")


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def full_pipeline(text, merge=True):
    """复刻 backend/main.py 的行链（merge 默认 True，与 /api/kundoku 一致）：
    ENGINE → merge_proper_nouns → udkundoku.translate(raw) 提取 # text =
    → style_fix_with_hakubun → normalize_shinjitai。返回 (kakikudashi, error)。"""
    try:
        entry = ENG(text)
        if merge:
            entry = merge_proper_nouns(entry)
        kk_raw = _extract_kakikudashi(udkundoku.translate(entry, raw=True))
        kk = normalize_shinjitai(style_fix_with_hakubun(kk_raw, text))
        return kk, None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


ENG = udkanbun.UDKanbun(True, False, None)

lines = []
out = lambda s="": (lines.append(s), print(s, flush=True))

golden = json.load(io.open(os.path.join(EV, "golden_3000.json"), encoding="utf-8"))
rows = [g for g in golden if "應" in g["hakubun"]]
out("=== 應→応 白文预处理模拟：hakubun 含應 %d 行 ===" % len(rows))

changed = []
still_error = []
new_error = []
for g in rows:
    exp = norm(g["expected_kakikudashi"])
    kk0, err0 = full_pipeline(g["hakubun"])
    hb2 = g["hakubun"].replace("應", "応")
    kk1, err1 = full_pipeline(hb2)
    d0 = lev(norm(kk0), exp) if kk0 is not None else None
    d1 = lev(norm(kk1), exp) if kk1 is not None else None
    diff = "不变" if (kk0 == kk1 and (err0 is None) == (err1 is None)) else "变化"
    out("\n[%s] %s" % (g["id"], g["hakubun"][:36]))
    out("  原始    : %s | dist=%s" % (kk0 if kk0 is not None else "!! " + str(err0),
                                      d0))
    out("  應→応後 : %s | dist=%s" % (kk1 if kk1 is not None else "!! " + str(err1),
                                      d1))
    out("  预处理效果: %s" % diff)
    if kk0 is None and kk1 is None and err0 == err1:
        still_error.append({"id": g["id"], "err": err0})
    elif kk0 is None and kk1 is not None:
        new_error.append({"id": g["id"], "fixed": True})
    elif kk0 != kk1:
        changed.append({"id": g["id"], "d0": d0, "d1": d1,
                        "kk0": kk0, "kk1": kk1})

out("\n=== 汇总 ===")
out("  仍 error（原始 error → 预处理后同 error）: %d 行 %s" % (
    len(still_error), [x["id"] for x in still_error]))
out("  error 被预处理修复: %d 行" % len(new_error))
out("  输出被预处理改变: %d 行 %s" % (len(changed), [x["id"] for x in changed]))
for x in changed:
    out("    %s dist %s → %s" % (x["id"], x["d0"], x["d1"]))

# 语料外探针（副作用抽查）：预处理是纯输入替换，理论上只影响含應输入
out("\n=== 语料外探针（原始 vs 預處理） ===")
probes = [
    "應對進退而無禮",           # 應+動詞用法
    "反應がある",               # 现代日语
    "應長思之",                 # 應=べき 类推
    "子曰く学而時習之",          # 控制组（无應）
]
for p in probes:
    kk0, e0 = full_pipeline(p)
    kk1, e1 = full_pipeline(p.replace("應", "応"))
    out("  %r\n    原始=%r%s\n    转换=%r%s" % (
        p, kk0, (" !!%s" % e0) if e0 else "", kk1, (" !!%s" % e1) if e1 else ""))

json.dump({"rows": len(rows), "still_error": still_error,
           "fixed_by_preprocess": new_error, "output_changed": changed},
          open(os.path.join(EV, "night59_sim.json"), "w", encoding="utf-8",
               newline="\n"), ensure_ascii=False, indent=1)
io.open(os.path.join(EV, "night59_sim_result.txt"), "w", encoding="utf-8",
        newline="\n").write("\n".join(lines) + "\n")
out("\nwritten: eval/night59_sim.json / night59_sim_result.txt")
