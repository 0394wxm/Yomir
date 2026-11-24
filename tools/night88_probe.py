# -*- coding: utf-8 -*-
"""night88_probe.py — N88 Rule P 候选取证（Night 86 probe 同款・只读）。

B2 短名单の行级実証（基线 = night87_results_8165.json・N87 链尾）：
  T. 试替表（kana→repl、guard、长词）を現行分岐の guard 上下文（engine=全文／rerun=尾段）
     で per-row 実距測定：発火行（key 在 got ∧ guard 命中）の改善/変差/same、
     guard 外行（key 在 got ∧ guard 外＝実機非発火・無リスク）の计数；
     新鲜 T1〜T3（べきなり・して→問す）＋对照 T4〜T6（N86/N72 拒案の現基线維持確認）。
  D. 目标取证：べきなり 全行 got/exp/白文、して→問す 全行（語彙対応か scramble patch か
     の判別＝N86 過拟合拒案基準の適用）、べき 接続後 2 字分布。
输出 eval/night88_probe.txt / night88_probe.json。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, ".night72_deps"))  # Levenshtein C 库（隔离目录）
EV = os.path.join(ROOT, "eval")


def norm(s):
    return re.sub(r"\s+", "", s or "")


try:
    from Levenshtein import distance as _lev_c
except Exception:  # pragma: no cover
    _lev_c = None


def lev(a, b):
    if _lev_c is not None:
        return _lev_c(a, b)
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def apply_one(text, kana, repl, longer=()):
    longer = sorted(longer, key=len, reverse=True)
    out, i, n = [], 0, len(kana)
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
    return "".join(out)


TRIALS = [
    # (tag, kana, repl, guard, longer)
    ("T1 べきなり→可く guard 可（B2 4 行・新鲜）", "べきなり", "可く", ("可",), ()),
    ("T2 べきなり→可くんば guard 可（新鲜・字形 2）", "べきなり", "可くんば", ("可",), ()),
    ("T3 して→問す guard 問（B2 5 行・新鲜・語彙対応判別）", "して", "問す", ("問",), ()),
    ("T4 るべ→可 guard 可（N86 T1 拒案維持確認）", "るべ", "可", ("可",), ()),
    ("T5 べきか→可きか guard 可（N86 T5 拒案維持確認）", "べきか", "可きか", ("可",), ()),
    ("T6 べからず→可からず guard 可（N72 拒案維持確認・任务书复核）", "べからず", "可からず", ("可",), ()),
]


def main():
    doc = json.load(open(os.path.join(EV, "night87_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165

    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls, hb_of = {}, {}
    for r in rows:
        raw = r["hakubun"] or ""
        if detect_text_type(raw) == "kana":
            tail = _ruby_tail_kanbun(raw)
            if not tail:
                cls[r["id"]] = "no_tail"
                hb_of[r["id"]] = ""
            elif len(tail) <= 8:
                cls[r["id"]] = "echo"
                hb_of[r["id"]] = norm(tail)
            else:
                cls[r["id"]] = "rerun"
                hb_of[r["id"]] = norm(tail)
        else:
            cls[r["id"]] = "engine"
            hb_of[r["id"]] = norm(raw)
    cc = collections.Counter(cls.values())
    EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}
    assert dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS)
    reachable = [r for r in rows if cls[r["id"]] in ("engine", "rerun")]

    gmap = {g["id"]: g for g in golden}
    lines = []

    def pr(s=""):
        lines.append(s)
        print(s, flush=True)

    pr("== T. 试替表（発火行 per-row 実距・基线 night87）==")
    trial_out = {}
    for tag, kana, repl, guard, longer in TRIALS:
        fired, outside = [], []
        for r in reachable:
            got = norm(r["udkundoku_kakikudashi"])
            if kana not in got:
                continue
            hb = hb_of[r["id"]]
            if guard and not any(g in hb for g in guard):
                outside.append(r)
                continue
            fired.append(r)
        better = worse = same = 0
        detail = []
        for r in fired:
            got = norm(r["udkundoku_kakikudashi"])
            exp = norm(r["expected_kakikudashi"])
            d0 = lev(got, exp)
            new = apply_one(got, kana, repl, longer)
            d1 = lev(new, exp)
            detail.append({"id": r["id"], "cls": cls[r["id"]], "d0": d0, "d1": d1,
                           "delta": d1 - d0})
            if d1 < d0:
                better += 1
            elif d1 > d0:
                worse += 1
            else:
                same += 1
        verdict = "収候補" if (worse == 0 and better > 0) else ("拒（変差 %d）" % worse if worse else "拒（無益）")
        trial_out[tag] = {"kana": kana, "repl": repl, "guard": list(guard), "fired": len(fired),
                          "outside": len(outside), "better": better, "worse": worse,
                          "same": same, "verdict": verdict, "detail": detail}
        pr("  %-52s 発火 %4d 行（guard 外 %3d 行＝無リスク）改善 %3d 変差 %d same %3d → %s" % (
            tag, len(fired), len(outside), better, worse, same, verdict))
        for d in detail:
            if d["delta"] > 0:
                r = next(x for x in reachable if x["id"] == d["id"])
                pr("      変差 %s (%s) %d→%d | got: %s" % (
                    d["id"], d["cls"], d["d0"], d["d1"], norm(r["udkundoku_kakikudashi"])[:70]))
                pr("        exp: %s" % norm(r["expected_kakikudashi"])[:70])
        pr("")

    # ---- D1. べきなり 全行（got/exp/白文・字形確認）----
    pr("== D1. べきなり 全行（reachable・B2 4 行の内実）==")
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "べきなり" in got:
            exp = norm(r["expected_kakikudashi"])
            pr("  %s (%s)" % (r["id"], cls[r["id"]]))
            pr("    got: %s" % got[:110])
            pr("    exp: %s" % exp[:110])
            pr("    白文: %s" % hb_of[r["id"]][:110])
    pr("")

    # ---- D2. して→問す 全行（語彙対応か scramble patch かの判別）----
    pr("== D2. B2 pair (して→問す) 全行（5 行・語彙対応判別）==")
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "して" in got and "問" in hb_of[r["id"]]:
            exp = norm(r["expected_kakikudashi"])
            if "問す" in exp:
                pr("  %s (%s)" % (r["id"], cls[r["id"]]))
                pr("    got: %s" % got[:110])
                pr("    exp: %s" % exp[:110])
                pr("    白文: %s" % hb_of[r["id"]][:110])
    pr("")

    # ---- D3. べき 接続後 2 字分布 ----
    pr("== D3. べき 接続後 2 字分布（reachable got）==")
    suf = collections.Counter()
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        for m in re.finditer("べき", got):
            suf[got[m.end():m.end() + 2]] += 1
    pr("  %s" % dict(suf.most_common(14)))
    pr("")

    out = os.path.join(EV, "night88_probe.json")
    json.dump({"trials": trial_out, "beki_nari_rows": [r["id"] for r in reachable
               if "べきなり" in norm(r["udkundoku_kakikudashi"])],
               "beki_suffix": dict(suf)},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night88_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written:", out)


if __name__ == "__main__":
    main()
