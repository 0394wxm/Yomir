# -*- coding: utf-8 -*-
"""night86_probe.py — N86 Rule O 候选取证（Night 72/73/78 probe 同款・只读）。

B2 短名单の行级実証：
  T. 试替表（kana→repl、guard、长词）を現行分岐の guard 上下文（engine=全文／rerun=尾段）
     で per-row 実距測定：発火行（key 在 got ∧ guard 命中）の改善/変差/same、
     guard 外行（key 在 got ∧ guard 外＝実機非発火・無リスク）の计数；
  D. 目标取证：B2 pair (るべ→可)/(べきか→可) の全行 got/exp/白文、べからず 全行
     （N72 拒案 5 変差行の特定＝exp 自写仮名か）、べき接続後 2 字分布、はざる接続後
     2 字分布＋はざる者 2 行、がため/何のごとく 残量 1 行ずつの身份（N84 rerun artifact 確認）。
输出 eval/night86_probe.txt / night86_probe.json。
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
    ("T1 るべ→可 blanket（B2 27 块/22 行の字形对照）", "るべ", "可", ("可",), ()),
    ("T2 べからず→可からず guard 可（N72 拒案の現基线再測）", "べからず", "可からず", ("可",), ()),
    ("T3 ざるべからず→ざる可からず（prefix 長 key・死行回避試行）", "ざるべからず", "ざる可からず", ("可",), ()),
    ("T4 るべからず→可からず（prefix 長 key）", "るべからず", "可からず", ("可",), ()),
    ("T5 べきか→可きか（guard 可）", "べきか", "可きか", ("可",), ()),
    ("T6 はざる者→わざる者（N72 拍板待ち・kanji 含み key＝M 何のごとし 前例）", "はざる者", "わざる者", (), ()),
    ("T7 はざる→わざる blanket（N69 拒案 24shihin10-4 对照再測）", "はざる", "わざる", (), ()),
    ("T8 しむ→使う guard 使（使役族・字形混在）", "しむ", "使う", ("使",), ()),
    ("T9 してしむる→使う guard 使", "してしむる", "使う", ("使",), ()),
    ("T10 してしむ→使う guard 使", "してしむ", "使う", ("使",), ()),
    ("T11 して→使う guard 使（artifact 对照）", "して", "使う", ("使",), ()),
    ("T12 とも→与に（N72 拒案 121 変差の再確認）", "とも", "与に", ("與", "与"), ()),
]


def main():
    doc = json.load(open(os.path.join(EV, "night85_results_8165.json"), encoding="utf-8"))
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
    reachable = [r for r in rows if cls[r["id"]] in ("engine", "rerun")]

    gmap = {g["id"]: g for g in golden}
    lines = []

    def pr(s=""):
        lines.append(s)
        print(s, flush=True)

    pr("== T. 试替表（発火行 per-row 実距）==")
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
        trial_out[tag] = {"kana": kana, "repl": repl, "guard": guard, "fired": len(fired),
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

    # ---- D1. B2 pair (るべ→可) 全行 ----
    from difflib import SequenceMatcher
    _KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")
    pair_rows = collections.defaultdict(list)
    for r in reachable:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if len(g_) >= 2 and _KANA_ONLY_RE.match(g_) and e and e[0] not in "ぁ-ゖー":
                pair_rows[(g_, e)].append(r["id"])
    pr("== D1. B2 pair (るべ→可) 全行（22 行・字形確認）==")
    for rid in sorted(set(pair_rows.get(("るべ", "可"), []))):
        r = next(x for x in reachable if x["id"] == rid)
        pr("  %s (%s)" % (rid, cls[rid]))
        pr("    got: %s" % norm(r["udkundoku_kakikudashi"])[:110])
        pr("    exp: %s" % norm(r["expected_kakikudashi"])[:110])
        pr("    白文: %s" % hb_of[rid][:110])
    pr("")

    # ---- D2. べからず 全行（N72 5 変差行の特定）----
    pr("== D2. べからず 全行（reachable・N72 拒案 5 変差の特定）==")
    bk = []
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        if "べからず" in got:
            exp = norm(r["expected_kakikudashi"])
            d0 = lev(got, exp)
            d1 = lev(apply_one(got, "べからず", "可からず"), exp)
            hb = hb_of[r["id"]]
            bk.append({"id": r["id"], "cls": cls[r["id"]], "hb_ke": "可" in hb,
                       "exp_kana": "べからず" in exp, "d0": d0, "d1": d1,
                       "delta": d1 - d0})
    pr("  計 %d 行 | 白文含可 %d | exp 自写仮名べからず %d | 試替 変差 %d" % (
        len(bk), sum(1 for x in bk if x["hb_ke"]), sum(1 for x in bk if x["exp_kana"]),
        sum(1 for x in bk if x["delta"] > 0)))
    for x in bk:
        r = next(y for y in reachable if y["id"] == x["id"])
        got = norm(r["udkundoku_kakikudashi"])
        i = got.find("べからず")
        ctx = got[max(0, i - 10):i + 8]
        pr("    %s (%s) 可=%s exp仮=%s %d→%d | …%s…" % (
            x["id"], x["cls"], x["hb_ke"], x["exp_kana"], x["d0"], x["d1"], ctx))
    pr("")

    # ---- D3. べき 接続後 2 字分布 ----
    pr("== D3. べき 接続後 2 字分布（reachable got）==")
    suf = collections.Counter()
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        for m in re.finditer("べき", got):
            suf[got[m.end():m.end() + 2]] += 1
    pr("  %s" % dict(suf.most_common(12)))
    pr("")

    # ---- D4. はざる 接続後 2 字分布＋はざる者 ----
    pr("== D4. はざる 接続後 2 字分布（reachable got）＋ はざる者行 ==")
    suf = collections.Counter()
    haz_mono = []
    for r in reachable:
        got = norm(r["udkundoku_kakikudashi"])
        for m in re.finditer("はざる", got):
            tail = got[m.end():m.end() + 2]
            suf[tail] += 1
            if tail.startswith("者"):
                haz_mono.append(r["id"])
    pr("  %s" % dict(suf.most_common(14)))
    pr("  はざる者 行: %s" % sorted(set(haz_mono)))
    pr("")

    # ---- D5. がため／何のごとく 残量 1 行ずつの身份 ----
    pr("== D5. 残量 1 行の身份（N84 rerun artifact 確認）==")
    for w in ("がため", "何のごとく"):
        for r in reachable:
            got = norm(r["udkundoku_kakikudashi"])
            if w in got:
                hb = hb_of[r["id"]]
                guard = "爲" if w == "がため" else "奈"
                pr("  %s 行 %s (%s) 白文(guard 上下文)含守り %s=%s" % (
                    w, r["id"], cls[r["id"]], guard, guard in hb))
                pr("    got: %s" % got[:90])
                pr("    白文: %s" % hb[:90])
    pr("")

    out = os.path.join(EV, "night86_probe.json")
    json.dump({"trials": trial_out, "bekarazu": bk, "hazaru_mono": sorted(set(haz_mono)),
               "beki_suffix": dict(suf) if "suf" in dir() else None},
              open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night86_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written:", out)


if __name__ == "__main__":
    main()
