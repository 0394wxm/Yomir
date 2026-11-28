# -*- coding: utf-8 -*-
"""night112_eval_8165.py — N112 合并夜の golden_8165 全量真跑回归（TestClient 完整链・
合并夜型・assert-only）。

最终校验只对 night111 归档（night111_results_8165.json）。合并＝N111 機構そのまま進
master（产品代码＝分支版原样），所以真跑出力は night111_results_8165.json（N111 上線
時の归档）と**全行逐位一致**：
  - diff 0 行・avgDist **13.464**／exact **30**／error 0。
不一致 → 即停止（EXIT 2）。本工具は归档に何も書かない（assert-only・night111 归档不触碰）。
用法: python -I tools/night112_eval_8165.py
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

EXPECT = {"avg": 13.464, "exact": 30, "errors": 0}   # night111_results_8165.json（合并前链尾・任务书数）


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


def load_rows(name):
    data = json.load(open(os.path.join(EV, name), encoding="utf-8"))
    return data, data["results"]


def main():
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    arc111, base111 = load_rows("night111_results_8165.json")
    _, base107 = load_rows("night107_results_8165.json")
    assert len(golden) == 8165 and len(base111) == 8165 and len(base107) == 8165
    assert [g["id"] for g in golden] == [b["id"] for b in base111], "golden 与 night111 归档行序不一致"
    s = arc111["summary"]
    assert s["n"] == 8165 and s["errors"] == 0, "night111 归档 summary 异常"
    assert abs(s["avg_edit_distance"] - EXPECT["avg"]) < 5e-4 and s["exact"] == EXPECT["exact"], \
        "night111 归档 summary %s != EXPECT %s" % (s, EXPECT)
    old = {b["id"]: b for b in base111}
    print("golden_8165 %d | 基线 night111_results_8165.json（avgDist %.3f / exact %d / error %d）"
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

    # ---- 全行逐位对照（night111 归档＝diff 0 行期待；night107 归档＝発火 15 行对照参照） ----
    diffs111 = [r["id"] for r, b in zip(results, base111)
                if {k: r.get(k) for k in ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")}
                != {k: b.get(k) for k in ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")}]
    diffs107 = [r["id"] for r, b in zip(results, base107)
                if {k: r.get(k) for k in ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")}
                != {k: b.get(k) for k in ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")}]

    print("\n=== night112_eval_8165（合并後・最终校验只对 night111 归档） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg),
          flush=True)
    print("vs night111 归档 diff %d 行 %s | vs night107 归档 diff %d 行（発火 15 行对照）"
          % (len(diffs111), diffs111[:8], len(diffs107)), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg is None or abs(avg - EXPECT["avg"]) > 5e-4:
        fails.append("avgDist %.3f != night111 归档 %.3f" % (avg, EXPECT["avg"]))
    if diffs111:
        fails.append("night111 归档と全行逐位不一致 %d 行: %s（合并＝機構原样実証失败）"
                     % (len(diffs111), diffs111[:8]))
    fired15 = ["mujun-2", "onoreshiru-1", "kagakujota-1", "kanchuna-1", "rongo0615-1",
               "rongo0732-1", "rongo1315-1", "rongo1442-1", "p-danjoshitsu-1", "tarekako-1",
               "tonan-1", "warekimi-1", "roushi46-2", "utsuryo03-7", "rikutou26-5"]
    if sorted(diffs107) != sorted(fired15):
        fails.append("night107 归档と不一致 %d 行 != N111 発火 15 行: %s"
                     % (len(diffs107), diffs107[:8]))
    if fails:
        print("\n[FAIL] 全行逐位一致断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_8165 真跑＝night111 归档全行逐位一致（avgDist %.3f / exact %d / error 0 / "
          "changed_ids_vs_n111=[]・vs night107 恰 N111 発火 15 行）＝合并零改动実証" % (avg, exact),
          flush=True)


if __name__ == "__main__":
    main()
