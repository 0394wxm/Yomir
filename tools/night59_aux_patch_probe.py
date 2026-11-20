# -*- coding: utf-8 -*-
"""night59_aux_patch_probe.py — N59 第四步（内存内对照，不改任何文件/引擎）：

把 udkundoku.auxiliary.AUX 补上「應,v,助動詞,必要,*」条目（值 = 同 xpos 的 須），
量化这一行补丁对 toushisen135-12 与全库的潜在收益与风险：
  1. 单行：toushisen135-12 修复后输出 vs expected 的 dist；
  2. 全库 2999 条：内存补丁后重跑（走完整行链），对照 night58 归档逐行 diff——
     「补丁只影响含助動詞應的行」是否有实证、其他行是否逐字节不变。
进程结束补丁即消失，site-packages 不落任何改动。
输出 eval/night59_aux_patch_probe.txt。
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
import udkundoku.auxiliary as aux_mod  # noqa: E402
from backend.kundoku_rules import (  # noqa: E402
    merge_proper_nouns, normalize_shinjitai, style_fix_with_hakubun)


def _extract_kakikudashi(conllu: str) -> str:
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


ENG = udkanbun.UDKanbun(True, False, None)


def full_pipeline(text, merge=True):
    try:
        entry = ENG(text)
        if merge:
            entry = merge_proper_nouns(entry)
        kk = _extract_kakikudashi(udkundoku.translate(entry, raw=True))
        return normalize_shinjitai(style_fix_with_hakubun(kk, text)), None
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


lines = []
out = lambda s="": (lines.append(s), print(s, flush=True))

# ---- 1. 单行修复效果（补丁前）----
golden = json.load(io.open(os.path.join(EV, "golden_3000.json"), encoding="utf-8"))
row = next(g for g in golden if g["id"] == "toushisen135-12")
exp = norm(row["expected_kakikudashi"])
kk0, err0 = full_pipeline(row["hakubun"])
out("=== 1. toushisen135-12（补丁前）===")
out("  hakubun : %r" % row["hakubun"])
out("  expected: %r (norm=%r)" % (row["expected_kakikudashi"], exp))
out("  输出    : %s" % (kk0 if kk0 is not None else "!! " + str(err0)))

# ---- 2. 内存补丁（不落盘）----
KEY = "應,v,助動詞,必要,*"
REF = aux_mod.AUX["須,v,助動詞,必要,*"]
assert KEY not in aux_mod.AUX
aux_mod.AUX[KEY] = REF
out("\n=== 2. 内存补丁 AUX[%r] = %r（同 xpos 的須；进程结束即消失）===" % (KEY, REF))

kk1, err1 = full_pipeline(row["hakubun"])
out("  补丁后输出: %s" % (kk1 if kk1 is not None else "!! " + str(err1)))
if kk1 is not None:
    d = lev(norm(kk1), exp)
    out("  dist vs expected: %d | 逐字节一致: %s" % (d, norm(kk1) == exp))
    d_unpatched_row_dist = None

# 幂等：补丁后重跑一次
kk2, _ = full_pipeline(row["hakubun"])
out("  幂等: %s" % (kk1 == kk2))

# ---- 3. 全库回归（补丁是否只影响这一行）----
out("\n=== 3. 全库 3000 条内存补丁回归（逐行 vs night58 归档）===")
results = json.load(io.open(os.path.join(EV, "night58_results_3000.json"),
                            encoding="utf-8"))["results"]
old_by_id = {r["id"]: r.get("udkundoku_kakikudashi") for r in results}
diff_rows = []
err_rows = []
for g in golden:
    kk, err = full_pipeline(g["hakubun"])
    if err:
        err_rows.append((g["id"], err))
        continue
    if norm(kk) != norm(old_by_id.get(g["id"]) or ""):
        diff_rows.append((g["id"], old_by_id.get(g["id"]), kk))
out("  输出与 night58 归档不同的行: %d（预期 = 只有 toushisen135-12 从 error 变可解析）"
    % len(diff_rows))
for rid, old, new in diff_rows[:10]:
    out("    %s\n      旧: %s\n      新: %s" % (rid, (old or "")[:60], (new or "")[:60]))
out("  补丁后仍 error 的行: %d %s" % (len(err_rows), [e[0] for e in err_rows]))

kkx, errx = full_pipeline(row["hakubun"])
dx = lev(norm(kkx), exp) if kkx else None
out("\n=== 4. 汇总 ===")
out("  toushisen135-12：error → dist %s%s" % (
    dx, "（逐字节命中 expected）" if kkx and norm(kkx) == exp else ""))
out("  其余 2999 行输出逐字节不变" if len(diff_rows) == 0 else
    "  其余行有 %d 行变化（需人审）" % len(diff_rows))

# ---- 5. 撤销补丁（恢复进程内原状，防御性）----
del aux_mod.AUX[KEY]
assert KEY not in aux_mod.AUX
out("  内存补丁已撤销（AUX 恢复原状）")

io.open(os.path.join(EV, "night59_aux_patch_probe.txt"), "w", encoding="utf-8",
        newline="\n").write("\n".join(lines) + "\n")
out("\nwritten: eval/night59_aux_patch_probe.txt")
