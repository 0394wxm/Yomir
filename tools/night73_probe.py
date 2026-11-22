# -*- coding: utf-8 -*-
"""night73_probe.py — N73 Rule M 候选行级取证（night72_probe 同款＋新旧字体并查）。

守り字候补は N72 移交①成文规矩：新旧字体两形＋禁止同义词族（莫/毋/勿/無）一并検索。
另含反向探查（exp 側漢字 Δ 大・got 0〜低：奈/陣/将/不——引擎写啥假名？）。
只读；输出 eval/night73_probe.txt / night73_probe.json。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

_KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")

# 守り字候补（新旧两形＋禁止族）は guard_forms() で展開
CANDS = [
    ("ことなかれ", ["莫", "毋", "勿", "無"]),
    ("なかれ",     ["莫", "毋", "勿", "無"]),
    ("ことな",     ["勿", "莫"]),          # ことなかれ の got 側断片？
    ("そく",       ["即", "卽"]),
    ("はある",     ["或"]),
    ("ゆき",       ["之"]),
    ("はそ",       ["其"]),
    ("べきか",     ["可"]),
    ("るべ",       ["可"]),
    ("もし",       ["若", "如"]),
    ("なんぞ",     ["奈", "盍", "奚", "曷"]),
]
REVERSE = ["奈", "陣", "将", "不"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    from backend.kundoku_rules import SHINJITAI_MAP
    old_to_new = dict(SHINJITAI_MAP)
    new_to_old = {}
    for o, n in old_to_new.items():
        new_to_old.setdefault(n, o)

    def guard_forms(chars):
        out = []
        for c in chars:
            for f in (c, new_to_old.get(c), old_to_new.get(c)):
                if f and f not in out:
                    out.append(f)
        return out

    doc = json.load(open(os.path.join(EV, "night72_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 不同序 %d" % i
    gmap = {g["id"]: g for g in golden}
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    lines = []
    out = {}

    for kana, gchars in CANDS:
        gf = guard_forms(gchars)
        lines.append("=== %s（守り字候補 %s）===" % (kana, "/".join(gf)))
        recs = []
        for r in rows:
            got = norm(r["udkundoku_kakikudashi"])
            if kana not in got:
                continue
            exp = norm(r["expected_kakikudashi"])
            hb = norm(gmap[r["id"]]["hakubun"])
            hits = [f for f in gf if f in hb]
            recs.append({"id": r["id"], "guards": hits,
                         "got": got[:110], "exp": exp[:110], "hb": hb[:110]})
        # exp 側ターゲット（kana 直後の exp 対応形は取れないので、
        # 「kana を含む行の exp に現れる kana 直前後の候補字形」を简取）
        tgt = collections.Counter()
        for rec in recs:
            r = next(x for x in rows if x["id"] == rec["id"])
            exp = norm(r["expected_kakikudashi"])
            for c in gchars:
                if c in exp:
                    tgt[c] += 1
        nguard = collections.Counter("/".join(x["guards"]) or "-" for x in recs)
        lines.append("  行数 %d | 守り字組合せ: %s | exp 側字形: %s" % (
            len(recs), dict(nguard), dict(tgt) if tgt else "-"))
        for rec in recs[:12]:
            lines.append("  %s 守り=%s" % (rec["id"], "/".join(rec["guards"]) or "-"))
            lines.append("      got: %s" % rec["got"])
            lines.append("      exp: %s" % rec["exp"])
            lines.append("      白文: %s" % rec["hb"])
        if len(recs) > 12:
            lines.append("  …（他 %d 行は night73_probe.json）" % (len(recs) - 12))
        lines.append("")
        out[kana] = {"guard_forms": gf, "rows": len(recs),
                     "guard_combo": dict(nguard),
                     "exp_target_chars": dict(tgt),
                     "records": recs}

    for ch in REVERSE:
        lines.append("=== [逆向] exp 側 %s を含み got に無い行 ===" % ch)
        recs = []
        for r in rows:
            exp = norm(r["expected_kakikudashi"])
            got = norm(r["udkundoku_kakikudashi"])
            if ch in exp and ch not in got:
                recs.append({"id": r["id"], "got": got[:110], "exp": exp[:110],
                             "hb": norm(gmap[r["id"]]["hakubun"])[:110]})
        lines.append("  行数 %d" % len(recs))
        for rec in recs[:10]:
            lines.append("  %s" % rec["id"])
            lines.append("      got: %s" % rec["got"])
            lines.append("      exp: %s" % rec["exp"])
            lines.append("      白文: %s" % rec["hb"])
        if len(recs) > 10:
            lines.append("  …（他 %d 行）" % (len(recs) - 10))
        lines.append("")
        out["rev_" + ch] = {"rows": len(recs), "records": recs}

    print("\n".join(lines[:250]))
    json.dump(out, open(os.path.join(EV, "night73_probe.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night73_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written: eval/night73_probe.txt / night73_probe.json")


if __name__ == "__main__":
    main()
