# -*- coding: utf-8 -*-
"""night72_eval.py — N72：Rule L 上线后 golden_4000 / golden_8165 全量真跑（TestClient 完整后端链）。

night70_eval.py 同款机制（monkeypatch save_kundoku），一次进程双口径。
期望值**从 eval/night72_sim.json 读入**（不手抄）：combo_4000/combo_8165 的
changed_entries/better/worse/avg_new 与 exact_* 的 after；预测行集合从
eval/night72_combo_changed_rows.json 读入。基线 = night70_results_*.json。

断言（任一失败 → 非零退出，先查实现、不改 expected）：
  * 基线自检：night70 归档 avgDist == sim avg_old（离线基线与归档逐位一致）；
  * 逐位一致：avgDist / exact / 改写行集合（双向 0 差）／改善／变差 0；
  * error→恢复 / 仍 error 预期 0；
  * 每个改写行 new_dist ≤ old_dist（0 变差门在真机复现）；
  * 4000 与 8165 前 4000 行输出逐位一致（同进程确定性自证）。
输出 eval/night72_results_4000.json / eval/night72_results_8165.json（schema 同 night70）。
"""
import collections
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")


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


def bucket_of(hb):
    n = len(norm(hb))
    return "≤20字" if n <= 20 else "21-40字" if n <= 40 else "41-60字" if n <= 60 else ">60字"


def genre_of(url):
    u = (url or "").lower()
    if "/syubu/shikyo" in u:
        return "詩経"
    if "/syubu/" in u:
        return "漢詩"
    if "/keibu/daigaku" in u:
        return "大学"
    if "/keibu/kokyo" in u:
        return "孝経"
    if "/keibu/rongo" in u:
        return "論語"
    if "/koji/" in u:
        return "故事"
    return "その他"


def summarize(results, label):
    ok = [r for r in results if r["edit_distance"] is not None]
    n = len(ok)
    exact = sum(1 for r in ok if r["exact_match"])
    avg = sum(r["edit_distance"] for r in ok) / n if n else None
    print("\n=== %s ===" % label, flush=True)
    print("engine OK %d / error %d | 精确 %d/%d | avgDist %.3f"
          % (n, len(results) - n, exact, n, avg if avg is not None else -1), flush=True)
    by_b = collections.defaultdict(list)
    by_g = collections.defaultdict(list)
    for r in ok:
        by_b[bucket_of(r["hakubun"])].append(r)
        by_g[genre_of(r.get("source_url", ""))].append(r)
    print("%-10s %5s %9s %7s" % ("文体", "n", "avgDist", "精确"), flush=True)
    for g, rs in sorted(by_g.items(), key=lambda kv: -len(kv[1])):
        print("%-10s %5d %9.3f %7d"
              % (g, len(rs), sum(x["edit_distance"] for x in rs) / len(rs),
                 sum(1 for x in rs if x["exact_match"])), flush=True)
    return {
        "label": label, "n": n, "errors": len(results) - n, "exact": exact,
        "avg_edit_distance": round(avg, 3) if avg is not None else None,
        "by_bucket": {b: {"n": len(rs), "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                          "exact": sum(1 for x in rs if x["exact_match"])}
                      for b, rs in by_b.items()},
        "by_genre": {g: {"n": len(rs), "avg": round(sum(x["edit_distance"] for x in rs) / len(rs), 3),
                         "exact": sum(1 for x in rs if x["exact_match"])}
                     for g, rs in by_g.items()},
    }


def run_rule(client, items, label):
    results = []
    t0 = time.time()
    for i, g in enumerate(items, 1):
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
        if i % 500 == 0:
            print("  [%s] %d/%d (%.0fs)" % (label, i, len(items), time.time() - t0), flush=True)
    return results


def compare_and_assert(res, old_results, pred_ids, expect, sim_res, tag):
    old = {r["id"]: r for r in old_results}
    diff_ids = set()
    better, worse = [], []
    fixed, still_err = [], []
    for r in res:
        o = old.get(r["id"])
        if r["udkundoku_kakikudashi"] is None:
            still_err.append(r["id"])
            continue
        if o is not None and o.get("udkundoku_kakikudashi") is None:
            fixed.append(r["id"])
        elif o is not None and norm(o["udkundoku_kakikudashi"]) != norm(r["udkundoku_kakikudashi"]):
            diff_ids.add(r["id"])
            if r["edit_distance"] > o["edit_distance"]:
                worse.append((r["id"], o["edit_distance"], r["edit_distance"]))
            elif r["edit_distance"] < o["edit_distance"]:
                better.append(r["id"])
    same = sorted(diff_ids - set(better) - {w[0] for w in worse})
    miss = sorted(pred_ids - diff_ids)
    extra = sorted(diff_ids - pred_ids)
    s = summarize(res, "规则引擎 %s（A/C'/D/E〜K/L 全链 + SHINJITAI）" % tag)
    print("\n=== 确定性对照 vs night70_results_%s.json ===" % tag, flush=True)
    print("改写行: %d（模拟预测 %d）| 改善 %d / 变差 %d / 持平 %d"
          % (len(diff_ids), len(pred_ids), len(better), len(worse), len(same)), flush=True)
    print("预测有实跑无: %d %s" % (len(miss), miss[:10]), flush=True)
    print("实跑有预测无: %d %s" % (len(extra), extra[:10]), flush=True)
    print("error→恢复: %d | 仍 error: %d %s（预期 0）" % (len(fixed), len(still_err), still_err), flush=True)
    for i, od, nd in worse[:20]:
        print("  变差! %s %d→%d" % (i, od, nd), flush=True)

    fails = []
    if miss:
        fails.append("预测有实跑无 %d 行: %s" % (len(miss), miss[:8]))
    if extra:
        fails.append("实跑有预测无 %d 行: %s" % (len(extra), extra[:8]))
    if worse:
        fails.append("变差 %d 行（0 变差门）" % len(worse))
    if fixed or still_err:
        fails.append("error 变动: 恢复 %d 仍错 %d" % (len(fixed), len(still_err)))
    if s["exact"] != expect["exact"]:
        fails.append("exact %d != %d（模拟 %d）" % (s["exact"], expect["exact"], sim_res["exact_after"]))
    if s["avg_edit_distance"] != expect["avg"]:
        fails.append("avgDist %.3f != %.3f（模拟）" % (s["avg_edit_distance"], expect["avg"]))
    if len(diff_ids) != expect["changed"]:
        fails.append("改写 %d != %d" % (len(diff_ids), expect["changed"]))
    if len(better) != expect["better"]:
        fails.append("改善 %d != %d" % (len(better), expect["better"]))
    if fails:
        print("\n[FAIL] %s 逐位对照不通过:" % tag, flush=True)
        for f in fails:
            print("  - %s" % f, flush=True)
        sys.exit(2)
    print("[OK] %s 与 N72 离线模拟逐位一致（avg %.3f / exact %d / 改写 %d / 改善 %d / 变差 0）"
          % (tag, s["avg_edit_distance"], s["exact"], len(diff_ids), len(better)), flush=True)
    s["diff_ids_vs_n70"] = sorted(diff_ids)
    s["predicted_ids"] = sorted(pred_ids)
    s["missing_vs_pred"] = miss
    s["extra_vs_pred"] = extra
    s["improved"] = len(better)
    s["worsened"] = len(worse)
    s["worsened_detail"] = worse
    s["fixed_rows_vs_n70"] = sorted(fixed)
    s["still_error"] = still_err
    return s


def main():
    golden4 = json.load(open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))
    golden8 = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    assert [g["id"] for g in golden4] == [g["id"] for g in golden8[:4000]], \
        "golden_4000/8165 前 4000 行不同序"
    n70_4 = json.load(open(os.path.join(EV, "night70_results_4000.json"), encoding="utf-8"))["results"]
    n70_8 = json.load(open(os.path.join(EV, "night70_results_8165.json"), encoding="utf-8"))["results"]
    assert len(n70_4) == 4000 and len(n70_8) == 8165
    sim = json.load(open(os.path.join(EV, "night72_sim.json"), encoding="utf-8"))
    combo = json.load(open(os.path.join(EV, "night72_combo_changed_rows.json"), encoding="utf-8"))
    pred_all = {c["id"] for c in combo}
    ids4 = {g["id"] for g in golden4}
    pred4 = pred_all & ids4
    print("golden_4000 %d / golden_8165 %d | 组合预测（8165 口径）%d 行（4000 内 %d）| 收録 %s"
          % (len(golden4), len(golden8), len(pred_all), len(pred4), ",".join(sim["accepted"])),
          flush=True)

    # 基线自检：night70 归档 avgDist == sim avg_old（离线基线与归档一致）
    base_avg8 = round(sum(r["edit_distance"] for r in n70_8) / len(n70_8), 3)
    base_avg4 = round(sum(r["edit_distance"] for r in n70_4) / len(n70_4), 3)
    if base_avg8 != sim["combo_8165"]["avg_old"]:
        print("[FAIL] 基线 avgDist 不一致: night70 归档 %.3f vs sim avg_old %.3f"
              % (base_avg8, sim["combo_8165"]["avg_old"]), flush=True)
        sys.exit(2)
    if base_avg4 != sim["combo_4000"]["avg_old"]:
        print("[FAIL] 基线 avgDist(4000) 不一致: %.3f vs %.3f"
              % (base_avg4, sim["combo_4000"]["avg_old"]), flush=True)
        sys.exit(2)
    print("[OK] 基线自检: night70 归档 avgDist 4000=%.3f / 8165=%.3f == sim avg_old"
          % (base_avg4, base_avg8), flush=True)

    expect4 = {"exact": sim["exact_4000"]["after"], "avg": sim["combo_4000"]["avg_new"],
               "changed": sim["combo_4000"]["changed_entries"], "better": sim["combo_4000"]["better"]}
    expect8 = {"exact": sim["exact_8165"]["after"], "avg": sim["combo_8165"]["avg_new"],
               "changed": sim["combo_8165"]["changed_entries"], "better": sim["combo_8165"]["better"]}
    print("期望值（来自 night72_sim.json）: 4000 %s / 8165 %s" % (expect4, expect8), flush=True)

    from fastapi.testclient import TestClient
    from backend.main import app
    import backend.db as dbmod

    with TestClient(app) as client:
        real = dbmod.save_kundoku
        dbmod.save_kundoku = lambda *a, **k: 1
        try:
            res4 = run_rule(client, golden4, "4000")
            res8 = run_rule(client, golden8, "8165")
        finally:
            dbmod.save_kundoku = real

    # 同进程确定性自证：8165 的前 4000 行与 4000 单跑逐位一致
    for a, b in zip(res4, res8[:4000]):
        assert a["id"] == b["id"] and norm(a["udkundoku_kakikudashi"]) == norm(b["udkundoku_kakikudashi"]), \
            "4000/8165 前 4000 行输出不一致: %s" % a["id"]
    print("\n[OK] 4000 与 8165 前 4000 行输出逐位一致（进程内确定性）", flush=True)

    s4 = compare_and_assert(res4, n70_4, pred4, expect4, sim["exact_4000"], "4000")
    s8 = compare_and_assert(res8, n70_8, pred_all, expect8, sim["exact_8165"], "8165")

    out4 = os.path.join(EV, "night72_results_4000.json")
    out8 = os.path.join(EV, "night72_results_8165.json")
    json.dump({"total": len(res4), "summary": s4, "results": res4},
              open(out4, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"total": len(res8), "summary": s8, "results": res8},
              open(out8, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("written:", out4, out8, flush=True)


if __name__ == "__main__":
    main()
