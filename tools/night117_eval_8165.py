# -*- coding: utf-8 -*-
"""night117_eval_8165.py — N117 合并夜の golden_8165 全量真跑（TestClient 完整链・
assert-only・不写任何归档）。

night116_eval_8165.py 方法论克隆（N114 eval クロン同款・ファイル名 token を
night117 に交換・基线を night111 から night116 归档に切替・归档書き出し削除）。
合并夜期待＝N116 归档そのまま（backend diff 0＝実施文件 blob 级同一）：
  - vs night116_results_8165.json 全行 byte-identical（4 鍵 dict 比較・diff 0 行）
  - sum 109852・avgDist 13.454／exact 30／error 0（night116 値そのまま）
不一致 → 即停止（EXIT 2）。
用法: python -I tools/night117_eval_8165.py
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

EXPECT = {"avg": 13.454, "avg_tol": 0.002, "exact": 30, "errors": 0,
          "sum": 109852,
          "diff_ids": [],
          "diff_d": {}}


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
    base_doc = json.load(open(os.path.join(EV, "night116_results_8165.json"),
                              encoding="utf-8"))
    base = base_doc["results"]
    assert len(golden) == 8165 and len(base) == 8165
    assert [g["id"] for g in golden] == [b["id"] for b in base], \
        "golden 与 night116 归档行序不一致"
    s = base_doc["summary"]
    assert abs(s["avg_edit_distance"] - 13.454) < 5e-4 and s["exact"] == 30 and \
        s["errors"] == 0, "night116 归档 summary %s != 13.454/30/0" % s
    base_sum = sum(b["edit_distance"] for b in base if b["edit_distance"] is not None)
    assert base_sum == 109852, "night116 归档 sum %s != 109852" % base_sum
    base_of = {b["id"]: b for b in base}
    print("golden_8165 %d | 基线 night116_results_8165.json（avgDist %.3f / exact %d / error %d / sum %d）"
          % (len(golden), s["avg_edit_distance"], s["exact"], s["errors"], base_sum), flush=True)

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
    total_sum = sum(r["edit_distance"] for r in ok)
    avg = round(total_sum / n, 3) if n else None
    errors = len(results) - n

    # ---- diff vs night116 归档（合并夜＝N116 口径そのまま → 全行 byte-identical） ----
    keys = ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")
    diffs = [r["id"] for r, b in zip(results, base)
             if {k: r.get(k) for k in keys} != {k: b.get(k) for k in keys}]
    d_detail = {rid: (base_of[rid]["edit_distance"],
                      next(r["edit_distance"] for r in results if r["id"] == rid))
                for rid in diffs}

    print("\n=== night117_eval_8165（合并夜 N115+N116 合流後・基线 night116 归档） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f | sum %d"
          % (n, errors, exact, n, avg, total_sum), flush=True)
    print("diff %d 行 %s | d 変化 %s" % (len(diffs), diffs, d_detail), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg is None or abs(avg - EXPECT["avg"]) > EXPECT["avg_tol"]:
        fails.append("avgDist %.3f != 期待 %.3f±%.3f" % (avg, EXPECT["avg"], EXPECT["avg_tol"]))
    if total_sum != EXPECT["sum"]:
        fails.append("sum %d != %d（Δ%+d・期待 0）" % (total_sum, EXPECT["sum"],
                                                      total_sum - base_sum))
    if sorted(diffs) != sorted(EXPECT["diff_ids"]):
        fails.append("diff 行集合 %s != 空（vs night116 全行 byte-identical 期待）" % (diffs,))
    for rid, (bd, nd) in EXPECT["diff_d"].items():
        got_pair = d_detail.get(rid)
        if got_pair != (bd, nd):
            fails.append("%s d %s != 期待 (%d, %d)" % (rid, got_pair, bd, nd))
    if fails:
        print("\n[FAIL] 断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_8165 真跑＝vs night116 全行 byte-identical（diff 0 行）"
          "／avgDist %.3f / exact %d / error 0 / sum %d（維持）"
          % (avg, exact, total_sum), flush=True)
    print("assert-only: no archive written（night116_results_8165.json 维持＝N112 先例）",
          flush=True)


if __name__ == "__main__":
    main()
