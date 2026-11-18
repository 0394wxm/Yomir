# -*- coding: utf-8 -*-
"""
run_eval_rongo.py — 分文体评测：eval/golden_rongo.json（論語）逐条过当前生产线引擎。

与 tools/run_eval.py 同一把尺子（归一化：剥空白后逐字；编辑距离算法相同），
差异两处（如实声明）：
  1) 进程内 TestClient 走完整 HTTP 栈（不起 uvicorn、不走 D: 写库——
     monkeypatch db.save_kundoku，写库只持久化不改变输出，Day4 §3 已验证等价）；
  2) 数据源是 golden_rongo.json（論語），不是 golden.json（故事名言）。
输出 eval/night23_results_rongo.json，stdout 给分档统计。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def norm(s):
    return re.sub(r"\s+", "", s)


def levenshtein(a, b):
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
    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    with open(os.path.join(ROOT, "eval", "golden_rongo.json"), encoding="utf-8") as f:
        golden = json.load(f)
    print("golden_rongo entries:", len(golden))

    results = []
    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1  # 不写库（输出不受影响，Day4 §3）
        try:
            for i, g in enumerate(golden, start=1):
                r = client.post("/api/kundoku", json={"text": g["hakubun"]})
                if r.status_code != 200:
                    results.append({"id": g["id"], "pian": g["pian"], "hakubun": g["hakubun"],
                                    "expected_kakikudashi": g["expected_kakikudashi"],
                                    "udkundoku_kakikudashi": None, "error": repr(r.text)[:200]})
                    continue
                body = r.json()
                got = body.get("kakikudashi", "")
                a, b = norm(got), norm(g["expected_kakikudashi"])
                results.append({
                    "id": g["id"], "pian": g["pian"], "source_url": g["source_url"],
                    "hakubun": g["hakubun"], "expected_kakikudashi": g["expected_kakikudashi"],
                    "udkundoku_kakikudashi": got,
                    "edit_distance": levenshtein(a, b),
                    "exact_match": a == b,
                    "text_type": body.get("text_type"),
                })
                if i % 20 == 0:
                    print("  %d/%d" % (i, len(golden)))
        finally:
            dbmod.save_kundoku = real

    ok = [r for r in results if r.get("edit_distance") is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n if n else -1
    print("\n=== 論語 %d 条（engine OK %d, error %d）===" % (len(results), n, len(results) - n))
    print("精确匹配 %d/%d  平均编辑距离 %.2f" % (exact, n, avg))

    # 长度分档（与 Night21 同口径：白文字符数）
    buckets = {}
    for r in ok:
        ln = len(norm(r["hakubun"]))
        b = "<=20" if ln <= 20 else ("20-40" if ln <= 40 else ">40")
        buckets.setdefault(b, []).append(r)
    print("\n长度分档：")
    for bk in ("<=20", "20-40", ">40"):
        rs = buckets.get(bk, [])
        if not rs:
            continue
        print("  %-6s n=%3d avgDist %6.2f  精确 %d/%d"
              % (bk, len(rs), sum(r["edit_distance"] for r in rs) / len(rs),
                 sum(1 for r in rs if r["exact_match"]), len(rs)))

    # 按篇（分文体细节：各篇平均）
    pians = {}
    for r in ok:
        pians.setdefault(r["pian"], []).append(r)
    print("\n按篇（前 10 个有样本的篇）：")
    for p in sorted(pians)[:10]:
        rs = pians[p]
        print("  pian %02d n=%2d avgDist %6.2f" % (p, len(rs), sum(r["edit_distance"] for r in rs) / len(rs)))

    print("\n=== 变差最大的 5 条（参考）===")
    for r in sorted(ok, key=lambda r: -r["edit_distance"])[:5]:
        print("  %-12s dist=%3d | %s" % (r["id"], r["edit_distance"], r["hakubun"][:22]))

    out = {"total": len(results), "engine_ok": n, "exact_match": exact,
           "avg_edit_distance": round(avg, 3), "results": results}
    out_path = os.path.join(ROOT, "eval", "night23_results_rongo.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwritten:", out_path)


if __name__ == "__main__":
    main()
