# -*- coding: utf-8 -*-
"""night78_probe.py — N78 Rule N 候选行级取证（night73_probe 深化版）。

主靶＝ことな族（N73 B2 残量 26+6 行——N68 只试过 ことなく→莫き（活用不一致
repl・2 変差で拒）、活用一致形（ことなかれ→莫かれ 等）は未試）：
  * got 側全 ことな* 行：kana run 全形、SequenceMatcher replace 块 (got_seg, exp_seg)、
    白文守り字（莫/卪/勿/毋/無 新旧両形）、exp 自書 kana 検査、する/す 前置检查；
  * 聚合：got_form → exp_seg 分布（repl 字形設計の証拠）。
副靶＝A 切面大 Δ 字の逆向探查（不/無/与/令/必/曰/則/於/使/将——エンジン何書く？）
＋got 側 kana 候补计数（おいて/すなはち/かならず/いはく/なし）＋B2 長尾対（2〜4 行）。
另＝なかれ 莫 側残量 10 行の白文構文取证（N73 移交②・備選⑥データ）。
只读；输出 eval/night78_probe.txt / night78_probe.json。
"""
import collections
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

_KANA_RE = re.compile(r"[ぁ-ゖー]+")
_KANA_ONLY_RE = re.compile(r"^[ぁ-ゖー]+$")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    from backend.kundoku_rules import (SHINJITAI_MAP,
                                       E_KANA_TO_KANJI, F_KANA_TO_KANJI,
                                       G_KANA_TO_KANJI, H_KANA_TO_KANJI,
                                       I_KANA_TO_KANJI, J_KANA_TO_KANJI,
                                       K_KANA_TO_KANJI, L_KANA_TO_KANJI,
                                       M_KANA_TO_KANJI)
    old_to_new = dict(SHINJITAI_MAP)
    new_to_old = {}
    for o, n in old_to_new.items():
        new_to_old.setdefault(n, o)

    def guard_forms(chars):
        out = []
        for c in chars:
            for f in (c, new_to_old.get(c), old_to_new.get(c)):
                if f and f and f not in out:
                    out.append(f)
        return out

    doc = json.load(open(os.path.join(EV, "night73_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 不同序 %d" % i
    gmap = {g["id"]: g for g in golden}
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]

    lines = []
    out = {}

    # ---- 0. 引擎现状（kana keys 一览）----
    lines.append("=== 0. 引擎現行 kana keys（E〜M）===")
    for name, d in (("E", E_KANA_TO_KANJI), ("F", F_KANA_TO_KANJI),
                    ("G", G_KANA_TO_KANJI), ("H", H_KANA_TO_KANJI),
                    ("I", I_KANA_TO_KANJI), ("J", J_KANA_TO_KANJI),
                    ("K", K_KANA_TO_KANJI), ("L", L_KANA_TO_KANJI),
                    ("M", M_KANA_TO_KANJI)):
        keys = [k[0] for k in d]
        lines.append("  %s (%d): %s" % (name, len(keys), " / ".join(keys)))
    lines.append("")

    # ---- 1. ことな族（主靶）----
    lines.append("=== 1. ことな族 全行取证（got に ことな を含む行・M 後链尾）===")
    kotonna = []
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        if "ことな" not in got:
            continue
        exp = norm(r["expected_kakikudashi"])
        hb = norm(gmap[r["id"]]["hakubun"])
        runs = [w for w in _KANA_RE.findall(got) if "ことな" in w]
        blocks = []
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "replace" and "ことな" in got[a1:a2]:
                blocks.append((got[a1:a2], exp[b1:b2]))
        rec = {"id": r["id"], "got_runs": runs, "blocks": blocks,
               "guard": "/".join(guard_forms(["莫", "勿", "毋", "無"]) and
                                 [c for c in ["莫", "卽", "勿", "毋", "無"] if c in hb]),
               "exp_selfwrite": any(w in exp for w in runs),
               "exp": exp[:130], "hb": hb[:130], "got": got[:130]}
        kotonna.append(rec)
    form_cnt = collections.Counter()
    seg_cnt = collections.Counter()
    selfwrite = []
    noguard = []
    surefix = collections.Counter()
    for rec in kotonna:
        for w in rec["got_runs"]:
            form_cnt[w] += 1
            if w.startswith("する") or w.startswith("すことな"):
                surefix[w] += 1
        for g_seg, e_seg in rec["blocks"]:
            seg_cnt[(g_seg, e_seg)] += 1
        if rec["exp_selfwrite"]:
            selfwrite.append(rec["id"])
        if not any(c in rec["hb"] for c in ("莫", "卽", "勿", "毋", "無")):
            noguard.append(rec["id"])
    lines.append("  行数 %d | got_form: %s" % (len(kotonna), dict(form_cnt)))
    lines.append("  replace 块 (got_seg→exp_seg) 分布:")
    for (gs, es), n in seg_cnt.most_common():
        lines.append("    %s → %s  ×%d" % (gs, es, n))
    lines.append("  exp 自書 kana 行: %s" % (selfwrite or "無し"))
    lines.append("  白文無 莫/勿/毋/無 行: %s" % (noguard or "無し"))
    lines.append("  する/すことな 前置形: %s" % (dict(surefix) or "無し"))
    for rec in kotonna[:40]:
        lines.append("  %s 守り=%s 自書=%s" % (rec["id"], rec["guard"] or "-", rec["exp_selfwrite"]))
        lines.append("      got: %s" % rec["got"])
        lines.append("      exp: %s" % rec["exp"])
        lines.append("      白文: %s" % rec["hb"])
        lines.append("      块: %s" % ("; ".join("%s→%s" % b for b in rec["blocks"])))
    if len(kotonna) > 40:
        lines.append("  …（他 %d 行は night78_probe.json）" % (len(kotonna) - 40))
    lines.append("")
    out["kotonna"] = {"rows": len(kotonna), "got_form": dict(form_cnt),
                      "seg_dist": [["%s→%s" % (gs, es), n] for (gs, es), n in seg_cnt.most_common()],
                      "exp_selfwrite": selfwrite, "no_guard": noguard, "surefix": dict(surefix),
                      "records": kotonna}

    # ---- 2. なかれ 莫 側残量（N73 移交②・備選⑥データ）----
    lines.append("=== 2. なかれ 残量（莫 側・M 後）白文構文取证 ===")
    nakare = []
    for r in rows:
        got = norm(r["udkundoku_kakikudashi"])
        if "なかれ" not in got:
            continue
        exp = norm(r["expected_kakikudashi"])
        hb = norm(gmap[r["id"]]["hakubun"])
        ctx = ""
        i = hb.find("莫")
        if i >= 0:
            ctx = hb[max(0, i - 4):i + 5]
        runs = [w for w in _KANA_RE.findall(got) if "なかれ" in w]
        nakare.append({"id": r["id"], "runs": runs, "hb_moku_ctx": ctx,
                       "hb": hb[:110], "got": got[:110], "exp": exp[:110]})
    lines.append("  行数 %d" % len(nakare))
    for rec in nakare[:20]:
        lines.append("  %s 白文莫前後: 「%s」 got_runs: %s" % (rec["id"], rec["hb_moku_ctx"], rec["runs"]))
        lines.append("      got: %s" % rec["got"])
        lines.append("      exp: %s" % rec["exp"])
    lines.append("")
    out["nakare_moku"] = nakare

    # ---- 3. B2 長尾対（2〜4 行・head 非 ALREADY）----
    lines.append("=== 3. B2 長尾対（replace 块 got 純假名>=2 × exp 漢字头、2〜4 行）===")
    ALREADY_HEAD = set("皆既旣猶豈唯亦何可之又所以謂相復只須蓋焉如夫惟毋方若如苟盍奚曷莫勿毋無与與哉岂矣")
    pair_rows = collections.defaultdict(list)
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != "replace":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) < 2 or not _KANA_ONLY_RE.match(g):
                continue
            if not e or not ("\u3400" <= e[0] <= "\u9fff"):
                continue
            pair_rows[(g, e)].append(r["id"])
    pair_head = collections.defaultdict(list)
    for (g, e), ids in pair_rows.items():
        pair_head[(g, e[0])].append((e, ids))
    tail = []
    for (g, head), variants in sorted(pair_head.items(),
                                      key=lambda kv: -sum(len(v[1]) for v in kv[1])):
        total = sum(len(v[1]) for v in variants)
        if total < 2 or total >= 5:
            continue
        if head in ALREADY_HEAD:
            continue
        vstr = " / ".join("%s(%d)" % (v, len(ids)) for v, _ids in
                          sorted(variants, key=lambda x: -len(x[1]))[:4])
        tail.append({"kana": g, "head": head, "rows": total, "exp_seg": vstr})
    tail.sort(key=lambda x: -x["rows"])
    for t in tail[:80]:
        lines.append("  %-12s → %-2s %d 行 | %s" % (t["kana"], t["head"], t["rows"], t["exp_seg"]))
    lines.append("  （長尾対計 %d 組）" % len(tail))
    lines.append("")
    out["b2_tail"] = tail

    # ---- 4. A 切面大 Δ 字の逆向探查＋got 側 kana 候补计数 ----
    REV = ["不", "無", "与", "令", "必", "曰", "則", "於", "使", "将"]
    KANA_CANDS = ["おいて", "おひて", "すなはち", "すなわち", "かならず",
                  "いはく", "なし", "まさに", "まさに", "めして", "にもかかわらず"]
    lines.append("=== 4. 逆向探查（exp に漢字あり got に無し行・上位 6 行サンプル）===")
    rev_out = {}
    for ch in REV:
        recs = []
        for r in rows:
            exp = norm(r["expected_kakikudashi"])
            got = norm(r["udkundoku_kakikudashi"])
            if ch in exp and ch not in got:
                recs.append({"id": r["id"], "got": got[:110], "exp": exp[:110],
                             "hb": norm(gmap[r["id"]]["hakubun"])[:110]})
        lines.append("  [exp %s / got 無] 行数 %d" % (ch, len(recs)))
        for rec in recs[:6]:
            lines.append("    %s" % rec["id"])
            lines.append("      got: %s" % rec["got"])
            lines.append("      exp: %s" % rec["exp"])
        rev_out["rev_" + ch] = {"rows": len(recs), "sample": recs[:6]}
        lines.append("")
    kc_out = {}
    lines.append("=== 4b. got 側 kana 候补计数（M 後链尾）===")
    for w in KANA_CANDS:
        n = sum(1 for r in rows if w in norm(r["udkundoku_kakikudashi"]))
        ne = sum(1 for r in rows if w in norm(r["expected_kakikudashi"]))
        lines.append("  %-10s got %4d / exp %4d" % (w, n, ne))
        kc_out[w] = {"got": n, "exp": ne}
    lines.append("")
    out["reverse"] = rev_out
    out["kana_cands"] = kc_out

    print("\n".join(lines[:120]))
    json.dump(out, open(os.path.join(EV, "night78_probe.json"), "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night78_probe.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    print("written: eval/night78_probe.txt / night78_probe.json")


if __name__ == "__main__":
    main()
