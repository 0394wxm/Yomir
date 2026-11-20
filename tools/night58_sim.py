# -*- coding: utf-8 -*-
"""night58_sim.py — N58 第二步：Rule H 候选离线模拟（基线 = night57 真机 3000，D/E/F/G 已上线）。

候选来源 = night58_mine.py / night58_probe_forms.py 解剖结果：
  A. SHINJITAI 批量：difflib 1:1 汉字→汉字替换（count>=2、表中无、且 exp 全库不写旧形）
  B. kana→kanji（沿用 F/G 分工模式，护栏=白文含对应汉字）：
     また→復た（復）| ことなかれ→莫かれ（莫）| なかれ→莫かれ（莫，D14 曾拒 なかれ→勿，复核）
     それ→只だ（只）| べし→須らく（須）| べからず→須いず（須）
变差>0 一律不上线（任务书硬规则）。逐条真算 Levenshtein。
输出 eval/night58_sim.json。
"""
import difflib
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)
from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402

KANA_CANDIDATES = {
    "mata_fukuta":   {"kana": "また", "repl": "復た", "guard": ("復",),
                      "tag": "また→復た（白文含復）"},
    "kotonakare":    {"kana": "ことなかれ", "repl": "莫かれ", "guard": ("莫",),
                      "tag": "ことなかれ→莫かれ（白文含莫）"},
    "nakare":        {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",),
                      "tag": "なかれ→莫かれ（白文含莫）【D14 拒绝复核】"},
    "sore_tada":     {"kana": "それ", "repl": "只だ", "guard": ("只",),
                      "tag": "それ→只だ（白文含只）"},
    "beshi":         {"kana": "べし", "repl": "須らく", "guard": ("須",),
                      "tag": "べし→須らく（白文含須）"},
    "bekarazu":      {"kana": "べからず", "repl": "須いず", "guard": ("須",),
                      "tag": "べからず→須いず（白文含須）"},
}


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


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


def apply_one(text, kana, repl, longer):
    longer = sorted(longer, key=len, reverse=True)
    out, i, n, cnt = [], 0, len(kana), 0
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        tail = text[j:]
        hit = next((w for w in longer if tail.startswith(w)), None)
        if hit:
            out.append(text[i:j + len(hit)])
            i = j + len(hit)
        else:
            out.append(text[i:j] + repl)
            i = j + n
            cnt += 1
    return "".join(out), cnt


def run(rows, kana_rules, shin_map=None, keep_changed=False):
    """kana_rules: list of (kana, repl, guard, longer)；shin_map: 旧→新 dict 或 None"""
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = got
        nchg = 0
        for kana, repl, guard, longer in kana_rules:
            if hb and not any(g in hb for g in guard):
                continue
            new, n = apply_one(new, kana, repl, longer)
            nchg += n
        if shin_map:
            nchg += sum(1 for c in new if c in shin_map)
            new = "".join(shin_map.get(c, c) for c in new)
        d1 = lev(new, exp)
        total_old += d0
        total_new += d1
        if nchg:
            changed_entries += 1
            if keep_changed:
                changed_rows.append({"id": r["id"], "old_dist": d0, "new_dist": d1,
                                     "old_text": got, "new_text": new,
                                     "expected": exp})
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": r["id"], "old": d0, "new": d1,
                                 "got": got[:120], "exp": exp[:120], "newtext": new[:120]})
        else:
            same += 1
    n = len(rows)
    out = {"entries": n, "changed_entries": changed_entries,
           "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
           "delta": round((total_new - total_old) / n, 3),
           "better": better, "worse": worse, "same": same,
           "worse_detail": worse_detail[:40]}
    if keep_changed:
        out["changed_rows"] = changed_rows
    return out


def idempotent(rows, kana_rules, shin_map):
    bad = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        new = got
        for kana, repl, guard, longer in kana_rules:
            if hb and not any(g in hb for g in guard):
                continue
            new, _ = apply_one(new, kana, repl, longer)
        if shin_map:
            new = "".join(shin_map.get(c, c) for c in new)
        twice = new
        for kana, repl, guard, longer in kana_rules:
            if hb and not any(g in hb for g in guard):
                continue
            twice, _ = apply_one(twice, kana, repl, longer)
        if shin_map:
            twice = "".join(shin_map.get(c, c) for c in twice)
        if twice != new:
            bad += 1
    return bad


def main():
    doc = json.load(open(os.path.join(EV, "night57_results_3000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    rows_new = rows[2000:]
    base = sum(lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
               for r in rows) / len(rows)
    print("样本 %d 条 | 基线（D/E/F/G 全链真机）avgDist %.3f" % (len(rows), base), flush=True)

    # ---------- A. SHINJITAI 1:1 扫描 ----------
    print("\n=== A. 1:1 汉字→汉字扫描（2999 条，未在 SHINJITAI_MAP 中）===", flush=True)
    pair_cnt = Counter()
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        sm = difflib.SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) == 1 and len(e) == 1 and is_kanji(g) and is_kanji(e) \
                    and SHINJITAI_MAP.get(g) != e:
                pair_cnt[(g, e)] += 1
    # 1:1 性核验：exp 全库不写旧形（got 是否已写新形不影响安全性——映射只转旧形）；
    # 另并入 night58_mine/probe 解剖出的多字对齐目标（difflib 1:1 块会漏），同一判据核验
    exp_all = Counter()
    got_all = Counter()
    for r in rows:
        exp_all.update(norm(r["expected_kakikudashi"]))
        got_all.update(norm(r["udkundoku_kakikudashi"]))
    DISSECT_PAIRS = [("靑", "青"), ("處", "処"), ("獨", "独"), ("遙", "遥"),
                     ("曉", "暁"), ("醉", "酔"), ("縱", "縦"), ("將", "将"),
                     ("橫", "横"), ("晚", "晩")]
    seen = set()
    # 第一遍：difflib 1:1 扫描对（count>=2 才进）
    shin_cand = {}
    for (g, e), n in pair_cnt.most_common():
        if n < 2 or g in SHINJITAI_MAP:
            continue
        exp_old, exp_new = exp_all.get(g, 0), exp_all.get(e, 0)
        got_old, got_new = got_all.get(g, 0), got_all.get(e, 0)
        ok = exp_old == 0 and got_old >= 2
        print("  %s→%s  %4d | exp 旧%d 新%d | got 旧%d 新%d %s"
              % (g, e, n, exp_old, exp_new, got_old, got_new,
                 "✅收" if ok else "（不收：exp写旧形/旧形不足2）"), flush=True)
        if ok:
            shin_cand[g] = e
        seen.add(g)
    # 第二遍：解剖对（night58_probe_forms 多字对齐目标，difflib 1:1 块会漏），
    # 同一判据 exp_old==0 && got_old>=2，全库计数核验
    print("  --- 解剖对（probe_forms，全库计数判据）---", flush=True)
    for g, e in DISSECT_PAIRS:
        if g in seen or g in SHINJITAI_MAP:
            continue
        exp_old, exp_new = exp_all.get(g, 0), exp_all.get(e, 0)
        got_old, got_new = got_all.get(g, 0), got_all.get(e, 0)
        ok = exp_old == 0 and got_old >= 2
        print("  %s→%s  difflib - | exp 旧%d 新%d | got 旧%d 新%d %s"
              % (g, e, exp_old, exp_new, got_old, got_new,
                 "✅收" if ok else "（不收）"), flush=True)
        if ok:
            shin_cand[g] = e
    print("SHINJITAI 候选 %d 对：%s" % (len(shin_cand), " ".join("%s→%s" % kv for kv in shin_cand.items())), flush=True)

    # ---------- exp 假名残留 ----------
    print("\n=== exp 假名残留（候选 kana 在 expected 自身出现的次数，全 3000）===", flush=True)
    for k, c in KANA_CANDIDATES.items():
        n = sum(norm(r["expected_kakikudashi"]).count(c["kana"]) for r in rows)
        print("  %-10s %d 次" % (c["kana"], n), flush=True)

    # ---------- B. 单条候选模拟 ----------
    out = {}
    print("\n=== B. 单条候选（全 2999）===", flush=True)
    print("%-30s %6s %8s %8s %8s %6s %6s %6s %6s" %
          ("候选", "改写条", "avg旧", "avg新", "Δ", "改善", "变差", "新段改", "旧段改"), flush=True)
    for k, c in KANA_CANDIDATES.items():
        rules = [(c["kana"], c["repl"], c["guard"], ())]
        s = run(rows, rules)
        s_new = run(rows_new, rules)
        out[k] = {"sim": s, "sim_new1000": s_new}
        print("%-30s %6d %8.3f %8.3f %+8.3f %6d %6d %6d %6d"
              % (c["tag"], s["changed_entries"], s["avg_old"], s["avg_new"],
                 s["delta"], s["better"], s["worse"],
                 s_new["changed_entries"], s["changed_entries"] - s_new["changed_entries"]),
              flush=True)
        if s["worse"]:
            for d in s["worse_detail"][:10]:
                print("    !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:40]), flush=True)

    # shinjitai 单独模拟
    s_shin = run(rows, [], shin_cand)
    s_shin_new = run(rows_new, [], shin_cand)
    out["shinjitai"] = {"sim": s_shin, "sim_new1000": s_shin_new, "pairs": shin_cand}
    print("%-30s %6d %8.3f %8.3f %+8.3f %6d %6d %6d %6d"
          % ("SHINJITAI %d 对" % len(shin_cand), s_shin["changed_entries"],
             s_shin["avg_old"], s_shin["avg_new"], s_shin["delta"],
             s_shin["better"], s_shin["worse"],
             s_shin_new["changed_entries"],
             s_shin["changed_entries"] - s_shin_new["changed_entries"]), flush=True)
    if s_shin["worse"]:
        for d in s_shin["worse_detail"][:10]:
            print("    !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:40]), flush=True)

    # ---------- C. 组合（0 变差候选，链顺序：kana 在前、shinjitai 显示层在后）----------
    zero = [k for k, c in KANA_CANDIDATES.items()
            if out[k]["sim"]["worse"] == 0 and out[k]["sim"]["changed_entries"] > 0]
    print("\n=== C. 组合（只收 0 变差：%s）===" % (",".join(zero) if zero else "无"), flush=True)
    combo_rules = []
    for k in ("kotonakare", "nakare", "sore_tada", "beshi", "bekarazu", "mata_fukuta"):
        if k in zero:
            c = KANA_CANDIDATES[k]
            combo_rules.append((c["kana"], c["repl"], c["guard"], ()))
    for cname, krules, smap in [
            ("kana_zero_worse", combo_rules, None),
            ("kana_zero+shinjitai", combo_rules, shin_cand)]:
        s = run(rows, krules, smap, keep_changed=True)
        idem = idempotent(rows, krules, smap)
        out[cname] = {"sim": {k: v for k, v in s.items() if k != "changed_rows"},
                      "idem_bad": idem, "rules": [list(x) for x in krules],
                      "shin_pairs": smap}
        # 改写行明细单独落盘（真函数核对/逐位对照用，不进 sim json 主键）
        json.dump(s["changed_rows"], open(
            os.path.join(EV, "night58_combo_changed_rows_%s.json" % cname.replace("+", "_")),
            "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
        print("%-22s 改写 %4d | Δ %+7.3f | 改善 %4d / 变差 %3d / 持平 %4d | 幂等坏 %d"
              % (cname, s["changed_entries"], s["delta"], s["better"], s["worse"],
                 s["same"], idem), flush=True)
        if s["worse"]:
            for d in s["worse_detail"][:8]:
                print("    !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:40]), flush=True)

    json.dump(out, open(os.path.join(EV, "night58_sim.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    print("\nwritten: eval/night58_sim.json", flush=True)


if __name__ == "__main__":
    main()
