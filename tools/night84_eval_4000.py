# -*- coding: utf-8 -*-
"""night84_eval_4000.py — N84 修法夜：ruby 夹注 kana 分流 fallback 落地后的
golden_4000 全量真跑回归（TestClient 完整后端链）。

机制复用 night83_eval_4000.py（TestClient 单进程全量真跑＋与链尾归档逐行对照）。
N84 修法只改 kana 分流（ruby 夹注尾段 fallback），golden_4000 内无空串目标行
（night83_results_4000.json 实测 0 行 got==""），所以本跑结果必须与
night83_results_4000.json **逐位一致**：avgDist 13.495 / exact 24 / error 0。
任一变差 → 拒收修法（EXIT 2）。

输出 eval/night84_results_4000.json（默认口径归档，NIGHT_ARTIFACTS[84]）。
用法: python -I tools/night84_eval_4000.py
"""
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

EXPECT = {"avg": 13.495, "exact": 24, "errors": 0}  # night83_results_4000.json 链尾值


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


def main():
    golden = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(EV, "night83_results_4000.json"),
                          encoding="utf-8"))["results"]
    assert len(golden) == 4000 and len(base) == 4000
    assert [g["id"] for g in golden] == [b["id"] for b in base], "golden 与 night83 归档行序不一致"
    old = {b["id"]: b for b in base}
    print("golden_4000 %d | 基线 night83_results_4000.json（avgDist %.3f / exact %d / error %d）"
          % (len(golden), EXPECT["avg"], EXPECT["exact"], EXPECT["errors"]), flush=True)

    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    results = []
    t0 = time.time()
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            for i, g in enumerate(golden, 1):
                r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                if r.status_code != 200:
                    results.append({"id": g["id"], "source_url": g.get("source_url", ""),
                                    "hakubun": g["hakubun"],
                                    "expected_kakikudashi": g["expected_kakikudashi"],
                                    "udkundoku_kakikudashi": None,
                                    "edit_distance": None, "exact_match": False,
                                    "error": repr(r.text)[:200]})
                    continue
                got = r.json().get("kakikudashi", "")
                a, b = norm(got), norm(g["expected_kakikudashi"])
                results.append({
                    "id": g["id"], "source_url": g.get("source_url", ""),
                    "hakubun": g["hakubun"],
                    "expected_kakikudashi": g["expected_kakikudashi"],
                    "udkundoku_kakikudashi": got,
                    "edit_distance": lev(a, b),
                    "exact_match": a == b,
                })
                if i % 2000 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(golden), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = round(sum(r["edit_distance"] for r in ok) / n, 3) if n else None
    errors = len(results) - n

    # 逐行对照 night83 归档（目标感知：N84 只允许空串行变化）
    diff_ids, target_ids, worsened = [], [], []
    for r in results:
        o = old[r["id"]]
        old_got = o.get("udkundoku_kakikudashi") or ""
        if old_got == "":
            target_ids.append(r["id"])
        if norm(r["udkundoku_kakikudashi"] or "") != norm(old_got):
            diff_ids.append(r["id"])
        if r["edit_distance"] is not None and o["edit_distance"] is not None \
                and r["edit_distance"] > o["edit_distance"]:
            worsened.append(r["id"])

    print("\n=== night84_eval_4000（修法夜：ruby 夹注 kana 分流 fallback 后） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg), flush=True)
    print("空串目标行 %d | 输出与 night83 归档不一致行 %d %s | 变差行 %d %s"
          % (len(target_ids), len(diff_ids), diff_ids[:10], len(worsened), worsened[:10]), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact < EXPECT["exact"]:
        fails.append("exact %d < %d" % (exact, EXPECT["exact"]))
    if avg > EXPECT["avg"]:
        fails.append("avgDist %.3f > %.3f" % (avg, EXPECT["avg"]))
    if worsened:
        fails.append("变差行 %d: %s" % (len(worsened), worsened[:8]))
    # N84 特有：非目标行（基线非空串）必须逐位一致
    base_empty = {r["id"] for r in results if (old[r["id"]].get("udkundoku_kakikudashi") or "") == ""}
    non_target_diff = [i for i in diff_ids if i not in base_empty]
    if non_target_diff:
        fails.append("非目标行输出变化 %d: %s" % (len(non_target_diff), non_target_diff[:8]))
    if fails:
        print("\n[FAIL] 修法夜门槛不通过（拒收修法，先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_4000 与 night83 归档逐位一致（avgDist %.3f / exact %d / error 0 / 变差 0 行）"
          % (avg, exact), flush=True)

    out = os.path.join(EV, "night84_results_4000.json")
    json.dump({
        "total": len(results),
        "summary": {
            "label": "night84 fix regression vs night83 archive (N84 ruby-tail kana fallback)",
            "n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
            "target_ids": target_ids,
            "improved": [], "worsened": worsened,
            "diff_ids_vs_n83": diff_ids,
            "expect": EXPECT,
        },
        "results": results,
    }, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
