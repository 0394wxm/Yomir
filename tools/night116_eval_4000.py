# -*- coding: utf-8 -*-
"""night116_eval_4000.py — N116 実施夜の golden_4000 全量真跑（TestClient 完整链・
写新归档・night111 归档不触碰）。

剥夹注管線（N115 Stage 0/1・N116 backend 実施）の scope＝engine 分支注记行
（8165 実測恰 2 行）で golden_4000 内は 0 行＝期待：
  - vs night111_results_4000.json 全行 byte-identical（4 鍵 dict 比較・diff 0 行）
  - avgDist 13.455／exact 24／error 0（night111 値そのまま）
不一致 → 即停止（EXIT 2）。
用法: python -I tools/night116_eval_4000.py
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

EXPECT = {"avg": 13.455, "avg_tol": 0.002, "exact": 24, "errors": 0, "diff": 0}


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
    base_doc = json.load(open(os.path.join(EV, "night111_results_4000.json"),
                              encoding="utf-8"))
    base = base_doc["results"]
    assert len(golden) == 4000 and len(base) == 4000
    assert [g["id"] for g in golden] == [b["id"] for b in base], \
        "golden 与 night111 归档行序不一致"
    s = base_doc["summary"]
    assert abs(s["avg_edit_distance"] - 13.455) < 5e-4 and s["exact"] == 24 and \
        s["errors"] == 0, "night111 归档 summary %s != 13.455/24/0" % s
    print("golden_4000 %d | 基线 night111_results_4000.json（avgDist %.3f / exact %d / error %d）"
          % (len(golden), s["avg_edit_distance"], s["exact"], s["errors"]), flush=True)

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
                if i % 1000 == 0:
                    print("  %d/%d (%.0fs)" % (i, len(golden), time.time() - t0), flush=True)
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = round(sum(r["edit_distance"] for r in ok) / n, 3) if n else None
    errors = len(results) - n

    # ---- diff vs night111 归档（scope＝golden_4000 内 0 行 → 全行 byte-identical） ----
    keys = ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")
    diffs = [r["id"] for r, b in zip(results, base)
             if {k: r.get(k) for k in keys} != {k: b.get(k) for k in keys}]

    print("\n=== night116_eval_4000（剥夹注管線後・基线 night111 归档） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg),
          flush=True)
    print("diff %d 行 %s（期待 0＝scope 4000 内 0 行）" % (len(diffs), diffs[:8]), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg is None or abs(avg - EXPECT["avg"]) > EXPECT["avg_tol"]:
        fails.append("avgDist %.3f != 期待 %.3f±%.3f" % (avg, EXPECT["avg"], EXPECT["avg_tol"]))
    if len(diffs) != EXPECT["diff"]:
        fails.append("diff %d 行 != 0 行（scope 外变差・計画外）: %s" % (len(diffs), diffs[:8]))
    if fails:
        print("\n[FAIL] 断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_4000 真跑＝vs night111 全行 byte-identical（diff 0 行・scope 4000 内 0 行）"
          "／avgDist %.3f / exact %d / error 0" % (avg, exact), flush=True)

    # ---- 归档（N116 口径・NIGHT_ARTIFACTS[116] 登记源・night111 归档不触碰） ----
    out_doc = {"total": len(results),
               "results": results,
               "summary": {"n": n, "errors": errors, "exact": exact,
                           "avg_edit_distance": avg,
                           "expect": {"avg": EXPECT["avg"], "exact": EXPECT["exact"],
                                      "errors": EXPECT["errors"]},
                           "label": "N116 剥夹注管線（N115 Stage 0/1・engine 分支注记行剥離）収録後 golden_4000",
                           "changed_ids_vs_n111": diffs}}
    out_path = os.path.join(EV, "night116_results_4000.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_doc, f, ensure_ascii=False, indent=1)
    print("archived: eval/night116_results_4000.json", flush=True)


if __name__ == "__main__":
    main()
