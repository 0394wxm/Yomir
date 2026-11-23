# -*- coding: utf-8 -*-
"""night86_eval_8165.py — N86 Rule O 上线后の golden_8165 全量真跑回归（TestClient 完整后端链）。

机制复用 night85_eval_8165.py。Rule O（3 条：はざる者→わざる者・たりせ→為ら・
なきか→莫し）上线后の真跑出力は night86_sim 组合预测と**逐位一致**でなければならない：
  - 预测改写 15 行（night86_combo_changed_rows.json）は行 id・new_text とも一致；
  - 非预测行は night85_results_8165.json（N85 链尾）と一字不変；
  - avgDist 13.505→**13.502**／exact 30→**30**／error 0（N85 13.505/30/0 から改善）。
不一致 → 先查实现，绝不改 expected（EXIT 2）。

输出 eval/night86_results_8165.json（扩充归档；schema 同 night85）。
用法: python -I tools/night86_eval_8165.py
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

EXPECT = {"avg": 13.502, "exact": 30, "errors": 0}  # night86_sim full8165_predict


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
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(EV, "night85_results_8165.json"),
                          encoding="utf-8"))["results"]
    sim_changed = json.load(open(os.path.join(EV, "night86_combo_changed_rows.json"),
                                 encoding="utf-8"))
    assert len(golden) == 8165 and len(base) == 8165
    assert [g["id"] for g in golden] == [b["id"] for b in base], "golden 与 night85 归档行序不一致"
    old = {b["id"]: b for b in base}
    pred = {c["id"]: c for c in sim_changed}
    print("golden_8165 %d | 基线 night85_results_8165.json（avgDist %.3f / exact %d / error %d）"
          " | sim 预测改写 %d 行" % (len(golden), 13.505, 30, 0, len(pred)), flush=True)

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

    # ---- 与 sim 预测逐位对照 ----
    real_changed = {r["id"]: norm(r["udkundoku_kakikudashi"] or "") for r in results
                    if norm(r["udkundoku_kakikudashi"] or "") != norm(old[r["id"]]["udkundoku_kakikudashi"] or "")}
    pred_changed = {c["id"]: norm(c["new_text"]) for c in sim_changed}
    diff_pred = [rid for rid in pred_changed
                 if real_changed.get(rid) != pred_changed[rid]]
    unexpected = sorted(set(real_changed) - set(pred_changed))
    missing = sorted(set(pred_changed) - set(real_changed))

    print("\n=== night86_eval_8165（Rule O 上线后） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg), flush=True)
    print("真跑改写 %d 行（sim 预测 %d）| 预测不一致 %s | 计画外 %s | 欠落 %s" % (
        len(real_changed), len(pred_changed), diff_pred[:8], unexpected[:8], missing[:8]), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg != EXPECT["avg"]:
        fails.append("avgDist %.3f != %.3f" % (avg, EXPECT["avg"]))
    if diff_pred:
        fails.append("预测改写行の真跑出力不一致 %d: %s" % (len(diff_pred), diff_pred[:8]))
    if unexpected:
        fails.append("计画外改写行 %d: %s" % (len(unexpected), unexpected[:8]))
    if missing:
        fails.append("预测行が真跑で改写されず %d: %s" % (len(missing), missing[:8]))
    if fails:
        print("\n[FAIL] sim 逐位一致断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_8165 真跑＝night86_sim 组合预测逐位一致（avgDist %.3f / exact %d / error 0 / "
          "改写 %d 行・変差 0——N85 13.505 から改善）" % (avg, exact, len(real_changed)), flush=True)

    out = os.path.join(EV, "night86_results_8165.json")
    json.dump({
        "total": len(results),
        "summary": {
            "label": "night86 Rule O regression vs night85 archive (O 3 rules: はざる者/たりせ/なきか)",
            "n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
            "changed_ids_vs_n85": sorted(real_changed),
            "expect": EXPECT,
        },
        "results": results,
    }, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
