# -*- coding: utf-8 -*-
"""night111_eval_4000.py — N111 実施夜の golden_4000 全量真跑（TestClient 完整链・
night107 上线夜型・assert-only）。

機構収録後の pipeline 出力は night107 归档から発火 15 行のうち 4000 内 12 行だけが
変わる（5 行は変体改写＝follow_map・7 行は default こと莫き）:
  - diff 行集合 == 発火行集合（4000 内 12 行・計画外 0・欠落 0）
  - 変化行の got == 実装機構（style_guard_followup）を night107 归档 got に適用した
    文本と逐位一致（＝sim 予測と実跑の逐位一致・N73 方法論の最終確認）
  - avgDist 理論値 13.455（13.460−20 字/4000・±丸め幅 0.002）／exact 24／error 0
  - rikutou26-5（拍板行・53→54）を含む
不一致 → 即停止（EXIT 2）。night107 归档不触碰。
用法: python -I tools/night111_eval_4000.py
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

EXPECT = {"avg": 13.455, "avg_tol": 0.002, "exact": 24, "errors": 0}


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
    golden = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    arc107, base107 = load_rows("night107_results_4000.json")
    assert len(golden) == 4000 and len(base107) == 4000
    assert [g["id"] for g in golden] == [b["id"] for b in base107], "golden 与 night107 归档行序不一致"
    s = arc107["summary"]
    assert s["n"] == 4000 and s["errors"] == 0, "night107 归档 summary 异常"
    assert abs(s["avg_edit_distance"] - 13.460) < 5e-4 and s["exact"] == 24, \
        "night107 归档 summary %s != 13.460/24" % s
    old = {b["id"]: b for b in base107}
    print("golden_4000 %d | 基线 night107_results_4000.json（avgDist %.3f / exact %d / error %d）"
          % (len(golden), s["avg_edit_distance"], s["exact"], s["errors"]), flush=True)

    from backend.kundoku_rules import style_guard_followup
    from backend.main import detect_text_type, _ruby_tail_kanbun

    # 発火行の機構予測文本（night107 归档 got に機構適用＝sim と同一アルゴリズム）
    # ・4000 归档外の発火行（rikutou26-5/roushi46-2 等 3 行）は本ツールの対象外
    fired_all = json.load(open(os.path.join(EV, "night111_sim.json"), encoding="utf-8"))["per_row_follow"]
    fired_ids = [rid for rid in fired_all if rid in old]
    pred = {}
    for rid in fired_ids:
        b = old[rid]
        hb_raw = b["hakubun"] or ""
        if detect_text_type(hb_raw) == "kana":
            hb = norm(_ruby_tail_kanbun(hb_raw))
        else:
            hb = norm(hb_raw)
        pred[rid] = style_guard_followup(norm(b["udkundoku_kakikudashi"]), hb)

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

    # ---- diff 行集合 vs night107 归档（発火 15 行中 4000 内のみ変化・計画外 0・欠落 0） ----
    diffs107 = [r["id"] for r, b in zip(results, base107)
                if {k: r.get(k) for k in ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")}
                != {k: b.get(k) for k in ("id", "udkundoku_kakikudashi", "edit_distance", "exact_match")}]
    miss = [rid for rid in fired_ids if rid not in diffs107]           # 欠落
    extra = [rid for rid in diffs107 if rid not in fired_ids]          # 計画外
    got_of = dict((r["id"], r["udkundoku_kakikudashi"]) for r in results)
    mism = [rid for rid in fired_ids if rid in diffs107 and norm(got_of[rid]) != pred[rid]]

    print("\n=== night111_eval_4000（機構収録後・基线 night107 归档） ===", flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f" % (n, errors, exact, n, avg),
          flush=True)
    print("diff %d 行 %s | 発火(4000 内) %d 行 | 欠落 %s | 計画外 %s | 機構予測不一致 %d"
          % (len(diffs107), diffs107[:8], len(fired_ids), miss, extra, len(mism)),
          flush=True)

    fails = []
    if errors != EXPECT["errors"]:
        fails.append("error %d != %d" % (errors, EXPECT["errors"]))
    if exact != EXPECT["exact"]:
        fails.append("exact %d != %d" % (exact, EXPECT["exact"]))
    if avg is None or abs(avg - EXPECT["avg"]) > EXPECT["avg_tol"]:
        fails.append("avgDist %.3f != 理論値 %.3f±%.3f" % (avg, EXPECT["avg"], EXPECT["avg_tol"]))
    if sorted(diffs107) != sorted(fired_ids):
        fails.append("diff 行集合 != 発火行集合(4000 内): 欠落 %s・計画外 %s" % (miss, extra))
    if mism:
        fails.append("機構予測（sim 同一アルゴリズム）と実跑 got 不一致 %d 行: %s" % (len(mism), mism[:8]))
    if fails:
        print("\n[FAIL] 断言不通过（先查实现，不改 expected）:", flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("\n[OK] golden_4000 真跑＝diff 恰発火 %d 行（変体 5 行は sim 逐位一致・計画外 0・"
          "欠落 0）／avgDist %.3f / exact %d / error 0" % (len(diffs107), avg, exact), flush=True)

    # ---- 归档（N111 口径・NIGHT_ARTIFACTS[111] 登记源・night107 归档不触碰） ----
    out_doc = {"total": len(results),
               "results": results,
               "summary": {"n": n, "errors": errors, "exact": exact,
                           "avg_edit_distance": avg,
                           "expect": {"avg": EXPECT["avg"], "exact": EXPECT["exact"],
                                      "errors": EXPECT["errors"]},
                           "sim_expect": {"fired": len(fired_all), "fired_in_4000": len(fired_ids),
                                          "rewrite5": ["roushi46-2", "rikutou26-5",
                                                       "kagakujota-1", "rongo0732-1",
                                                       "p-danjoshitsu-1"],
                                          "delta_chars_4000": -20, "delta_chars_4000_vs_a": -6},
                           "label": "N111 守り字後继字機構（follow_map・ことなき guard 莫）収録後 golden_4000",
                           "changed_ids_vs_n107": diffs107}}
    out_path = os.path.join(EV, "night111_results_4000.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_doc, f, ensure_ascii=False, indent=1)
    print("archived: eval/night111_results_4000.json", flush=True)


if __name__ == "__main__":
    main()
