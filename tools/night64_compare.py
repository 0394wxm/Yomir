# -*- coding: utf-8 -*-
"""night64_compare.py — N64：真机归档 vs 离线模拟逐位对照 + 真机幂等复投。

检查三件事（全部要求 =0 不符）：
  1. 模拟改写行（656）：真机输出 == 模拟预测文本（逐位）；
  2. 其余行：真机输出 == night60 归档（逐位）；
  3. 逐行 dist 变化统计与模拟一致（改善/变差/持平），变差必须 0。
再加真机幂等：656 改写行原样重投 API，输出与归档逐位一致（链纯函数性）。
只读；输出 eval/night64_compare.txt。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    sim_rows = json.load(open(os.path.join(EV, "night64_combo_changed_rows.json"),
                              encoding="utf-8"))
    doc64 = json.load(open(os.path.join(EV, "night64_results_4000.json"), encoding="utf-8"))
    doc60 = json.load(open(os.path.join(EV, "night60_results_4000.json"), encoding="utf-8"))
    real = {r["id"]: r for r in doc64["results"] if r.get("udkundoku_kakikudashi") is not None}
    old = {r["id"]: r for r in doc60["results"] if r.get("udkundoku_kakikudashi") is not None}

    sim_ids = {r["id"] for r in sim_rows}
    lines = []

    # 1. 模拟改写行逐位核对
    mism = []
    for s in sim_rows:
        r = real.get(s["id"])
        if r is None:
            mism.append((s["id"], "real 行缺失"))
            continue
        if norm(r["udkundoku_kakikudashi"]) != norm(s["new_text"]):
            mism.append((s["id"], "text\n  sim=%s\n  real=%s" % (
                norm(s["new_text"])[:60], norm(r["udkundoku_kakikudashi"])[:60])))
    lines.append("1) 模拟改写 %d 行：文本逐位不符 %d" % (len(sim_rows), len(mism)))
    for m in mism[:10]:
        lines.append("   !! %s %s" % m)

    # 2. 其余行 == night60 归档
    untouched_mism = []
    checked = 0
    for rid, r in real.items():
        if rid in sim_ids:
            continue
        o = old.get(rid)
        if o is None or o.get("udkundoku_kakikudashi") is None:
            continue
        checked += 1
        if norm(r["udkundoku_kakikudashi"]) != norm(o["udkundoku_kakikudashi"]):
            untouched_mism.append(rid)
    lines.append("2) 未触及行 %d 条（有 night60 基线的）：文本不符 %d" % (checked, len(untouched_mism)))
    for rid in untouched_mism[:10]:
        lines.append("   !! %s\n      n60=%s\n      n64=%s" % (
            rid, norm(old[rid]["udkundoku_kakikudashi"])[:60],
            norm(real[rid]["udkundoku_kakikudashi"])[:60]))

    # 3. 逐行 dist 统计（真机前后）与模拟对照
    better = worse = same = 0
    worse_rows = []
    for rid in sim_ids:
        r, o = real.get(rid), old.get(rid)
        if not r or not o:
            continue
        d0, d1 = o["edit_distance"], r["edit_distance"]
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_rows.append((rid, d0, d1))
        else:
            same += 1
    lines.append("3) 改写行 dist：改善 %d / 变差 %d / 持平 %d（模拟预测 514/0/%d）"
                 % (better, worse, same, 656 - 514 - 0))
    for w in worse_rows[:10]:
        lines.append("   !! 变差 %s %d->%d" % w)

    # 全库 avgDist 前后
    tot60 = sum(r["edit_distance"] for r in old.values())
    tot64 = sum(r["edit_distance"] for r in real.values())
    n = len(real)
    lines.append("4) 全库 avgDist：%.3f → %.3f（Δ %+.3f，模拟预测 -0.170）"
                 % (tot60 / n, tot64 / n, (tot64 - tot60) / n))
    exact60 = sum(1 for r in old.values() if r.get("exact_match"))
    exact64 = sum(1 for r in real.values() if r.get("exact_match"))
    lines.append("5) 精确匹配：%d → %d" % (exact60, exact64))

    # 6. 真机幂等：656 改写行重投 API
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod
    golden = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    hb_of = {g["id"]: g["hakubun"] for g in golden}
    bad = []
    with TestClient(app) as client:
        real_save = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, s in enumerate(sim_rows, 1):
                r = client.post("/api/kundoku", json={"text": hb_of[s["id"]]})
                if r.status_code != 200:
                    bad.append((s["id"], "HTTP %d" % r.status_code))
                    continue
                if norm(r.json().get("kakikudashi", "")) != norm(s["new_text"]):
                    bad.append((s["id"], "text"))
                if i % 200 == 0:
                    print("  idem %d/%d" % (i, len(sim_rows)), flush=True)
        finally:
            dbmod.save_kundoku = real_save
    lines.append("6) 真机幂等复投 %d 行：不符 %d" % (len(sim_rows), len(bad)))
    for b in bad[:10]:
        lines.append("   !! %s %s" % b)

    ok = not mism and not untouched_mism and worse == 0 and not bad
    lines.append("\n=== 结论：%s ===" % ("全部逐位一致，可上线" if ok else "存在不符，见上"))

    txt = "\n".join(lines)
    open(os.path.join(EV, "night64_compare.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)


if __name__ == "__main__":
    main()
