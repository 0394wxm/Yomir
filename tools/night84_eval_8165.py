# -*- coding: utf-8 -*-
"""night84_eval_8165.py — N84 修法夜：ruby 夹注 kana 分流 fallback 落地后的
golden_8165 全量真跑回归（TestClient 完整后端链）。

机制复用 night83_eval_8165.py。基线 = night83_results_8165.json（链尾归档，
其中 249 行 udkundoku_kakikudashi==""＝N78 §8 交班点名的空 got 行）。修法门槛：
  * 非目标行（基线非空串）输出与 night83 归档逐位一致；
  * 目标行（基线空串）：无 ruby 尾段者保持空串；有尾段者必须非空且
    edit_distance 不高于基线（变差即拒收）；
  * 目标集总距离必须下降（249 行集合改善）；
  * 聚合：avgDist ≤ 14.526、exact ≥ 30、error 0。

输出 eval/night84_results_8165.json（扩充归档，不登记默认口径；schema 同 night83）。
用法: python -I tools/night84_eval_8165.py
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

EXPECT = {"avg": 14.526, "exact": 30, "errors": 0}  # night83_results_8165.json 链尾值


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
    base = json.load(open(os.path.join(EV, "night83_results_8165.json"),
                          encoding="utf-8"))["results"]
    assert len(golden) == 8165 and len(base) == 8165
    assert [g["id"] for g in golden] == [b["id"] for b in base], "golden 与 night83 归档行序不一致"
    old = {b["id"]: b for b in base}
    n_target_base = sum(1 for b in base if (b.get("udkundoku_kakikudashi") or "") == "")
    print("golden_8165 %d | 基线 night83_results_8165.json（avgDist %.3f / exact %d / error %d / 空串 %d 行）"
          % (len(golden), EXPECT["avg"], EXPECT["exact"], EXPECT["errors"], n_target_base), flush=True)

    from fastapi.testclient import TestClient
    from backend.main import app, _ruby_tail_kanbun
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

    # 目标感知逐行对照 night83 归档
    target_ids, improved, worsened, target_kept_empty = [], [], [], []
    old_target_sum = new_target_sum = 0
    non_target_diff = []
    for r in results:
        o = old[r["id"]]
        old_got = o.get("udkundoku_kakikudashi") or ""
        old_d = o.get("edit_distance")
        new_d = r["edit_distance"]
        if old_got == "":
            target_ids.append(r["id"])
            old_target_sum += old_d if old_d is not None else len(norm(o["expected_kakikudashi"]))
            new_target_sum += new_d if new_d is not None else len(norm(r["expected_kakikudashi"]))
            if new_d is not None and old_d is not None:
                if new_d < old_d:
                    improved.append(r["id"])
                elif new_d > old_d:
                    worsened.append(r["id"])
                else:
                    target_kept_empty.append(r["id"])
            if _ruby_tail_kanbun(r["hakubun"]) and (r["udkundoku_kakikudashi"] or "") == "":
                worsened.append(r["id"] + "(tail未转换)")  # 有尾段却仍空串＝修法未生效
        else:
            if norm(r["udkundoku_kakikudashi"] or "") != norm(old_got):
                non_target_diff.append(r["id"])
            if new_d is not None and old_d is not None and new_d > old_d:
                worsened.append(r["id"])

    print("\n=== night84_eval_8165（修法夜：ruby 夹注 kana 分流 fallback 后） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg), flush=True)
    print("目标行 %d：改善 %d / 持平 %d / 变差 %d | 目标集距离 %d -> %d (%+d)"
          % (len(target_ids), len(improved), len(target_kept_empty), len(worsened),
             old_target_sum, new_target_sum, new_target_sum - old_target_sum), flush=True)
    print("非目标行输出变化 %d %s" % (len(non_target_diff), non_target_diff[:10]), flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact < EXPECT["exact"]:
        fails.append("exact %d < %d" % (exact, EXPECT["exact"]))
    if avg > EXPECT["avg"]:
        fails.append("avgDist %.3f > %.3f" % (avg, EXPECT["avg"]))
    if worsened:
        fails.append("变差行 %d: %s" % (len(worsened), worsened[:8]))
    if non_target_diff:
        fails.append("非目标行输出变化 %d: %s" % (len(non_target_diff), non_target_diff[:8]))
    if new_target_sum >= old_target_sum:
        fails.append("目标集未改善（%d -> %d）" % (old_target_sum, new_target_sum))
    if fails:
        print("\n[FAIL] 修法夜门槛不通过（拒收修法，先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_8165 修法夜门槛全过（avgDist %.3f <= %.3f / exact %d >= %d / error 0 / "
          "非目标行逐位一致 / 目标集 %d -> %d）"
          % (avg, EXPECT["avg"], exact, EXPECT["exact"], old_target_sum, new_target_sum), flush=True)

    out = os.path.join(EV, "night84_results_8165.json")
    json.dump({
        "total": len(results),
        "summary": {
            "label": "night84 fix regression vs night83 archive (N84 ruby-tail kana fallback)",
            "n": n, "errors": errors, "exact": exact, "avg_edit_distance": avg,
            "target_ids": target_ids,
            "improved": improved,
            "target_kept_empty": target_kept_empty,
            "worsened": worsened,
            "target_distance": {"old": old_target_sum, "new": new_target_sum},
            "diff_ids_vs_n83": non_target_diff,
            "expect": EXPECT,
        },
        "results": results,
    }, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out, flush=True)


if __name__ == "__main__":
    main()
