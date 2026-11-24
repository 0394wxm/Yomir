# -*- coding: utf-8 -*-
"""night89_build.py - N89 ⑤ assembler (append-mode): decisions -> append to
glossary_lexicon_extra2.py + excluded.json（night80_build.py の night89 版）。

N80 appends on top of the existing 824-entry file; N89 appends on top of 1085:
- group lists (PROPER/NOUNS/VERBS/MODIFIERS/FUNCTION) get new rows appended at
  their tail (freq 3-4 zone rank 500-965 sits after the N80 0-499, order kept);
- header docstring count line and source note gain an N89 note (the "N79"/"N80"
  tokens stay - tests/test_night79/80_lexicon_expand*.py require them);
- dual-evidence mechanical gate and duplicate-shape rejection, same as N79/N80;
- eval/night89_excluded.json with reasons.

Usage: python -I tools/night89_build.py
"""
import glob
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")
BACKEND = os.path.join(ROOT, "backend")
EXTRA2_PATH = os.path.join(BACKEND, "glossary_lexicon_extra2.py")

CATS = ["proper", "noun", "verb", "modifier", "function"]
CAT_LIST_NAME = {"proper": "PROPER", "noun": "NOUNS", "verb": "VERBS",
                 "modifier": "MODIFIERS", "function": "FUNCTION"}

MARK1_OLD = "词库扩充第二波（N79：500 → 824；N80 追加 261 条 → 1085；N82 追加 216 条 → 1301）。自动生成，请勿手改。"
MARK2_OLD = '"＋N82 追加 216 条（频次 3-4 区剩余 rank500-965，weblio＋语料双证据同款）")'


def load_decisions():
    decs = {}
    dup = []
    for path in sorted(glob.glob(os.path.join(EV, "night89_decisions_*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        for d in data.get("decisions", []):
            w = d["word"]
            if w in decs:
                dup.append(w)
            decs[w] = d
    return decs, dup


def validate(decs, existing):
    bad = []
    for w, d in decs.items():
        if d.get("verdict") == "include":
            for k in ("reading", "meaning", "cat", "dict_evidence", "corpus_evidence"):
                if not str(d.get(k, "")).strip():
                    bad.append((w, "missing %s" % k))
            if d.get("cat") not in CATS:
                bad.append((w, "bad cat %r" % d.get("cat")))
            if w in existing:
                bad.append((w, "duplicates existing %d" % len(existing)))
        elif d.get("verdict") == "exclude":
            if not str(d.get("exclude_reason", "")).strip():
                bad.append((w, "exclude without reason"))
        else:
            bad.append((w, "bad verdict %r" % d.get("verdict")))
    return bad


def py_str(s):
    return '"%s"' % str(s).replace("\\", "\\\\").replace('"', '\\"')


def append_to_extra2(groups, n_new):
    src = open(EXTRA2_PATH, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in src[:200] else "\n"
    for cat in CATS:
        rows = groups[cat]
        if not rows:
            continue
        name = CAT_LIST_NAME[cat]
        pat = re.compile(r"(?m)^%s = \[\r?\n" % name)
        m = pat.search(src)
        if not m:
            print("[FAIL] group block not found: %s" % name)
            sys.exit(2)
        insert = "".join("    (%s, %s, %s),%s" % (py_str(w), py_str(r), py_str(m), nl)
                         for w, r, m in rows)
        close = re.compile(r"(?m)^\]").search(src, m.end())
        if not close:
            print("[FAIL] group close not found: %s" % name)
            sys.exit(2)
        src = src[:close.start()] + insert + src[close.start():]
    if src.count(MARK1_OLD) != 1:
        print("[FAIL] header marker1 not unique: %d" % src.count(MARK1_OLD))
        sys.exit(2)
    src = src.replace(
        MARK1_OLD,
        "词库扩充第二波（N79：500 → 824；N80 追加 261 条 → 1085；N82 追加 216 条 → 1301；N89 追加 %d 条 → %d）。自动生成，请勿手改。"
        % (n_new, 1301 + n_new), 1)
    if src.count(MARK2_OLD) != 1:
        print("[FAIL] header marker2 not unique: %d" % src.count(MARK2_OLD))
        sys.exit(2)
    src = src.replace(
        MARK2_OLD,
        '"＋N82 追加 216 条（频次 3-4 区剩余 rank500-965，weblio＋语料双证据同款）"%s'
        '                         "＋N89 追加 %d 条（频次 2 区 top500，weblio＋语料双证据同款）")'
        % (nl, n_new), 1)
    with open(EXTRA2_PATH, "wb") as f:
        f.write(src.encode("utf-8"))


def main():
    decs, dup = load_decisions()
    from backend.glossary_lexicon import GLOSSARY_LEXICON
    from backend.glossary_lexicon_extra2 import LEXICON_EXTRA2
    existing = {e["word"] for e in GLOSSARY_LEXICON} | {e["word"] for e in LEXICON_EXTRA2}
    cands = json.load(open(os.path.join(EV, "night89_candidates.json"), encoding="utf-8"))
    cand_list = cands["candidates"]

    bad = validate(decs, existing)
    if dup:
        bad.extend((w, "duplicate decision") for w in dup)
    if bad:
        print("[FAIL] decision validation:")
        for w, why in bad[:30]:
            print("  - %s: %s" % (w, why))
        sys.exit(2)

    included = [d for d in decs.values() if d["verdict"] == "include"]
    excluded = [d for d in decs.values() if d["verdict"] == "exclude"]
    decided_words = set(decs)
    remaining = [c["word"] for c in cand_list if c["word"] not in decided_words]

    groups = {c: [] for c in CATS}
    for w, d in sorted(decs.items(), key=lambda kv: kv[1].get("rank", 10 ** 9)):
        if d["verdict"] == "include":
            groups[d["cat"]].append((w, d["reading"], d["meaning"]))

    append_to_extra2(groups, len(included))

    exc = {
        "generated": time.strftime("%Y-%m-%dT%H:%M"),
        "rule": "dual evidence gate: weblio dictionary + corpus (golden_8165 lines / kanbun.info ruby)",
        "excluded": [
            {"word": d["word"], "rank": d.get("rank"), "freq": d.get("freq"),
             "exclude_reason": d["exclude_reason"]}
            for d in sorted(excluded, key=lambda d: d.get("rank", 10 ** 9))
        ],
    }
    out_ex = os.path.join(EV, "night89_excluded.json")
    with open(out_ex, "w", encoding="utf-8", newline="\n") as f:
        json.dump(exc, f, ensure_ascii=False, indent=1)

    print("included=%d excluded=%d remaining=%d (1301 -> %d)" % (
        len(included), len(excluded), len(remaining), 1301 + len(included)))
    for cat in CATS:
        print("  %-9s %d" % (cat, len(groups[cat])))
    print("written: extra2 appended +", out_ex)
    if remaining:
        print("remaining candidates (first 15):", ", ".join(remaining[:15]))


if __name__ == "__main__":
    main()
