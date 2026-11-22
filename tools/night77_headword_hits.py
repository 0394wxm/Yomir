# -*- coding: utf-8 -*-
"""night77_headword_hits.py — N77 词头改动 2 条（冀う／弐びす）修后语料命中验证。

对 golden_8165（eval/golden_8165.json）统计新旧词形在 hakubun（bun）与
expected_kakikudashi（kkd）的命中文书数/出现次数（机制同 tools/night76_suspect43.py），
并用 find_in_lexicon 在真实语料行上实测修后命中情况。
只读语料与词库，不评测、不改 backend。

用法: python -I tools/night77_headword_hits.py
输出: eval/night77_headword_hits.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import find_in_lexicon  # noqa: E402

GOLDEN = os.path.join(ROOT, "eval", "golden_8165.json")
OUT = os.path.join(ROOT, "eval", "night77_headword_hits.json")

# (词形, 说明)：旧词头（修前）+ 新词头（修后）+ 语料实际活用形（对照）
FORMS = [
    ("冀ふ", "旧词头（修前，N76 判语料非使用）"),
    ("冀う", "新词头（修后）"),
    ("貳す", "旧词头（修前，语料非使用——语料用字形「弐」）"),
    ("弐びす", "新词头（修后，终止形）"),
    ("弐びせず", "语料实际形（ayamachifu-1/ikariutsu-1）"),
    ("弐びせ", "语料活用词干（对照）"),
]

corpus = json.load(open(GOLDEN, encoding="utf-8"))

rows = []
for w, note in FORMS:
    bun_lines = [ln for ln in corpus if w in ln["hakubun"]]
    kkd_lines = [ln for ln in corpus if w in ln["expected_kakikudashi"]]
    row = {
        "form": w,
        "note": note,
        "bun_doc_hits": len(set(ln["id"] for ln in bun_lines)),
        "bun_occ": sum(ln["hakubun"].count(w) for ln in bun_lines),
        "kkd_doc_hits": len(set(ln["id"] for ln in kkd_lines)),
        "kkd_occ": sum(ln["expected_kakikudashi"].count(w) for ln in kkd_lines),
        "kkd_ids": [ln["id"] for ln in kkd_lines][:10],
    }
    rows.append(row)
    print("%s bun=%d/%d kkd=%d/%d" % (
        w.encode("unicode_escape").decode("ascii"),
        row["bun_doc_hits"], row["bun_occ"],
        row["kkd_doc_hits"], row["kkd_occ"]))

# find_in_lexicon 实测：真实语料行（kkd 全文）上的修后命中
find_tests = []
for pid in ["shushu-3", "ayamachifu-1", "ikariutsu-1"]:
    line = next((ln for ln in corpus if ln["id"] == pid or ln["id"].startswith(pid)), None)
    if line is None:
        print("corpus line not found:", pid)
        continue
    hits = find_in_lexicon(line["expected_kakikudashi"], max_hits=5)
    find_tests.append({
        "id": line["id"],
        "kakikudashi": line["expected_kakikudashi"],
        "lexicon_hit_words": [h["word"] for h in hits],
        "new_headword_hit": ("冀う" in [h["word"] for h in hits]) if pid == "shushu-3"
        else ("弐びす" in [h["word"] for h in hits]),
    })
    print("%s -> %s" % (pid, [h["word"] for h in hits]))

json.dump({
    "night": 77,
    "purpose": "headword-fix corpus hits (冀う / 弐びす) after N77 lexicon fix16",
    "corpus": "eval/golden_8165.json",
    "forms": rows,
    "find_in_lexicon_probes": find_tests,
}, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("written:", OUT)
