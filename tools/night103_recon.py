# -*- coding: utf-8 -*-
"""night103_recon.py — Night 103 recon：原规则 ことなき→こと莫き（guard 莫）の 15 発火行
全文 dump（got/exp 全文＋site 対位＋exp 莫-形 census＋got 莫かれ 行数）。只读。
用法: python -I tools/night103_recon.py
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


def norm(s):
    return re.sub(r"\s+", "", s or "")


def _apply_count(text, kana, repl, longer=()):
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
    doc8 = json.load(open(os.path.join(EV, "night101_results_8165.json"), encoding="utf-8"))
    rows8 = [r for r in doc8["results"] if r.get("udkundoku_kakikudashi") is not None]
    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls, hb_of = {}, {}
    for r in rows8:
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

    rule = ("ことなき", "こと莫き", ("莫",))
    changed = []
    for r in rows8:
        rid = r["id"]
        if cls[rid] not in ("engine", "rerun"):
            continue
        hb = hb_of[rid]
        got0 = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got0, exp)
        new, n = _apply_count(got0, rule[0], rule[1])
        if n:
            changed.append({"id": rid, "cls": cls[rid], "n_sites": n,
                            "guard_hit": [g for g in rule[2] if g in hb],
                            "d0": d0, "d1": lev(new, exp),
                            "got": got0, "exp": exp,
                            "new": new})

    pr = print
    pr("== 原规则 ことなき→こと莫き（guard 莫）発火 %d 行 ==" % len(changed))
    b = sum(1 for c in changed if c["d1"] < c["d0"])
    w = sum(1 for c in changed if c["d1"] > c["d0"])
    s = sum(1 for c in changed if c["d1"] == c["d0"])
    pr("  better %d / worse %d / same %d" % (b, w, s))
    for c in changed:
        pr("-" * 100)
        pr("%s [%s・sites %d・guard %s] d0=%d d1=%d %s" % (
            c["id"], c["cls"], c["n_sites"], "".join(c["guard_hit"]),
            c["d0"], c["d1"],
            "BETTER" if c["d1"] < c["d0"] else ("WORSE" if c["d1"] > c["d0"] else "SAME")))
        pr("  got: %s" % c["got"])
        pr("  exp: %s" % c["exp"])
        # site 対位（anchor 検索）
        idx = 0
        for _ in range(c["n_sites"]):
            j = c["got"].find("ことなき", idx)
            prefix = c["got"][max(0, j - 8):j]
            k = c["exp"].find(prefix, max(0, j - 60)) if prefix else -1
            if k >= 0:
                pr("    site@%d got前缀=%r → exp対位 …%s" % (
                    j, prefix, c["exp"][max(0, k):k + len(prefix) + 22]))
            else:
                pr("    site@%d got前缀=%r → exp anchor 未命中" % (j, prefix))
            idx = j + 4
        # exp 莫-形 census
        forms = {}
        for f in ("莫き", "莫く", "莫し", "莫かれ", "莫からん", "莫けん", "莫然"):
            n_f = c["exp"].count(f)
            if n_f:
                forms[f] = n_f
        pr("    exp 莫-形 census: %s" % forms)

    # got 莫かれ 行数（N98=72）
    mk = sum(1 for r in rows8 if "莫かれ" in norm(r["udkundoku_kakikudashi"] or ""))
    pr("")
    pr("== got に 莫かれ を含む行数（全 8165）: %d（N98 記録 72）==" % mk)
    # ことなき guard 外残量（reachable・got に ことなき 残存・guard 勿/無し）
    resid = []
    for r in rows8:
        rid = r["id"]
        if cls[rid] not in ("engine", "rerun"):
            continue
        if "ことなき" in norm(r["udkundoku_kakikudashi"] or ""):
            resid.append((rid, cls[rid], "".join(g for g in ("莫", "勿", "毋") if g in hb_of[rid]) or "(無)"))
    fired_ids = {c["id"] for c in changed}
    pr("== reachable で got に ことなき 残存 %d 行（発火 %d 行・guard 外 %d 行）==" % (
        len(resid), len(fired_ids), len(resid) - len(fired_ids)))
    for rid, c_, g in resid:
        if rid not in fired_ids:
            pr("    guard 外: %s [%s・guard %s]" % (rid, c_, g))


if __name__ == "__main__":
    main()
