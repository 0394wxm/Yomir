# -*- coding: utf-8 -*-
"""night92_probe.py — N92 Rule Q 试替表（1 字块锚定长键手測・N86/N88 probe 制式）。

候补＝night92_mine A 表（1 字块枚举）から锚定した长键（活用形 full key／prefix 长键）：
  T1  は→将に        (は,将) 22 行 uniform 将に・guard 将/將（新旧両形）
  T2  は→未だ        (は,未) 16 行 uniform 未だ・guard 未（toushisen354-2 は未央 別対位＝
                     字形混在リスク確認）
  T3  ことなく→こと莫く  (な,莫) 9 行・guard 莫（rikutou08-3 rerun 行 含む）
  T4  ことなき→こと莫き  同上（ことなきなり→こと莫きや 型）
  T5  たる→為る       (た,為) 9 行・guard 為/爲（新旧両形・N86 たり bare 拒案の活用形再検）
  T6  すべからず→可からず (べ,可) 长键・N86 T4 るべからず 3 変差 同族の prefix 再検
  T7  うべきなるのみか→可なるのみか (べ,可) 7 行形态
  T8  以て→以為えらく   (て,為) 慣用句型（7 行中 5 行 以為えらく）

発火数＝guard 命中行中 got 含 key 行数；発火 ≫ pair 行数 ⇒ 語彙対応でない（N88 T3
5 pair vs 162 発火 scramble 実証例の判定基準）。
输出 eval/night92_probe.{json,txt}。只读。
"""
import collections
import json
import os
import re
import sys
import time
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

EXPECTED_CLASS = {"engine": 7916, "echo": 30, "rerun": 218, "no_tail": 1}

TRIALS = [
    {"id": "T1", "kana": "は", "repl": "将に", "guard": ("将", "將"),
     "note": "(は,将) 22 行 uniform 将に・guard 新旧両形"},
    {"id": "T2", "kana": "は", "repl": "未だ", "guard": ("未",),
     "note": "(は,未) 16 行 uniform 未だ・toushisen354-2 未央 別対位"},
    {"id": "T3", "kana": "ことなく", "repl": "こと莫く", "guard": ("莫",),
     "note": "(な,莫) 9 行・rikutou08-3 rerun ことなく→こと莫く"},
    {"id": "T4", "kana": "ことなき", "repl": "こと莫き", "guard": ("莫",),
     "note": "(な,莫) 9 行・rongo0615-1 ことなきなり→こと莫きや"},
    {"id": "T5", "kana": "たる", "repl": "為る", "guard": ("為", "爲"),
     "note": "(た,為) 9 行・たる→為る（N86 bare たり 拒案の活用形 full key 再検）"},
    {"id": "T6", "kana": "すべからず", "repl": "可からず", "guard": ("可",),
     "note": "(べ,可) 长键・N86 T4 るべからず 3 変差同族の prefix 再検"},
    {"id": "T7", "kana": "うべきなるのみか", "repl": "可なるのみか", "guard": ("可",),
     "note": "(べ,可) 7 行形态・べきなるのみか 长键"},
    {"id": "T8", "kana": "以て", "repl": "以為えらく", "guard": ("為", "爲"),
     "note": "(て,為) 慣用句型・以て→以為えらく"},
]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def _lev(a, b):
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
    doc = json.load(open(os.path.join(EV, "night91_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    n90 = json.load(open(os.path.join(EV, "night90_results_8165.json"), encoding="utf-8"))["results"]
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    assert len(rows) == 8165
    m90 = {b["id"]: b for b in n90}
    for r in rows:
        assert norm(r["udkundoku_kakikudashi"]) == norm(m90[r["id"]]["udkundoku_kakikudashi"]), \
            "night91 归档与 night90 链尾不一致: %s" % r["id"]

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
    assert dict(cc) == EXPECTED_CLASS, "行分类実数 %s != 期待 %s" % (dict(cc), EXPECTED_CLASS)
    reachable = [r for r in rows if cls[r["id"]] in ("engine", "rerun")]

    # 1 字块 pair 行集合（発火数比対用）
    _KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")
    one_rows = collections.defaultdict(list)
    for r in reachable:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g_, e = got[a1:a2], exp[b1:b2]
            if len(g_) == 1 and _KANA_ONLY_RE.match(g_) and e and not _KANA_ONLY_RE.match(e[0]) \
                    and "\u3400" <= e[0] <= "\u9fff":
                if r["id"] not in [x["id"] for x in one_rows[(g_, e[0])]]:
                    one_rows[(g_, e[0])].append(r)

    lines = []
    out_trials = []
    for t in TRIALS:
        t0 = time.time()
        guard_chars = t["guard"]
        fired = []
        for r in reachable:
            hb = hb_of[r["id"]]
            if guard_chars and not any(g in hb for g in guard_chars):
                continue
            if t["kana"] in norm(r["udkundoku_kakikudashi"]):
                fired.append(r)
        better = worse = same = 0
        fired_det = []
        for r in fired:
            got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
            d0 = _lev(got, exp)
            new = got.replace(t["kana"], t["repl"])
            d1 = _lev(new, exp)
            mark = "変差" if d1 > d0 else ("改善" if d1 < d0 else "same")
            fired_det.append({"id": r["id"], "cls": cls[r["id"]], "d0": d0, "d1": d1, "mark": mark})
            if d1 > d0:
                worse += 1
            elif d1 < d0:
                better += 1
            else:
                same += 1
        # pair 行锚定（该 key 相关 1 字块 pair 行）
        anchor_keys = {
            "T1": ("は", "将"), "T2": ("は", "未"), "T3": ("な", "莫"), "T4": ("な", "莫"),
            "T5": ("た", "為"), "T6": ("べ", "可"), "T7": ("べ", "可"), "T8": ("て", "為"),
        }
        ak = anchor_keys[t["id"]]
        n_pair = len(one_rows[ak])
        ratio = round(len(fired) / max(1, n_pair), 1)
        verdict = "——発火/pair=%.1f" % ratio + ("（≫1＝scramble リスク）" if ratio > 3 else "")
        out_trials.append({"id": t["id"], "kana": t["kana"], "repl": t["repl"],
                           "guard": list(guard_chars), "note": t["note"],
                           "pair_anchor": list(ak), "pair_rows": n_pair,
                           "fired": len(fired), "better": better, "worse": worse,
                           "same": same, "fired_detail": fired_det})
        lines.append("%s %s→%s（guard %s・%s）: pair %d 行 発火 %d 行 改善 %d 変差 %d same %d %s" % (
            t["id"], t["kana"], t["repl"], "/".join(guard_chars), t["note"],
            n_pair, len(fired), better, worse, same, verdict))
        for d in fired_det:
            if d["mark"] == "変差":
                r = next(x for x in reachable if x["id"] == d["id"])
                lines.append("    変差 %s [%s] %d→%d | got %s" % (
                    d["id"], d["cls"], d["d0"], d["d1"], norm(r["udkundoku_kakikudashi"])[:70]))
                lines.append("        exp %s" % norm(r["expected_kakikudashi"])[:70])
        lines.append("    (%.0fs)" % (time.time() - t0))
        lines.append("")

    print("\n".join(lines))
    json.dump({"baseline": "night91_results_8165.json", "trials": out_trials},
              open(os.path.join(EV, "night92_probe.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night92_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written: eval/night92_probe.json / night92_probe.txt")


if __name__ == "__main__":
    main()
