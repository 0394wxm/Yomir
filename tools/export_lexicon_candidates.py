# -*- coding: utf-8 -*-
"""export_lexicon_candidates.py — 导出候选词清单（含频次/词性/例句），供人工挑选。

输出 eval/lexicon_candidates.txt（UTF-8），格式：word \t freq \t pos \t example1
只保留含汉字的实词（名词/动词/形容词/副词/接续词/连体词/感动词），排除单字假名碎片。
"""
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from mecab_shim import tagger  # noqa: E402
from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402

KANJI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
KEEP_POS = ("n", "v", "a", "ad", "c", "cn", "p-助詞")  # 名词/动词/形容(动)词/副词/接续/连体


def main():
    with open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]

    have = {e["word"] for e in GLOSSARY_LEXICON}
    cnt = collections.Counter()
    info = {}

    for r in items:
        for seg in (r["expected_kakikudashi"], r["hakubun"]):
            for line in seg.replace("\n", "").split("。"):
                if not line.strip():
                    continue
                for tok in tagger.parse(line).splitlines():
                    if tok in ("EOS", "") or "\t" not in tok:
                        continue
                    form, feat = tok.split("\t")
                    f = feat.split(",")
                    pos = f[1] if len(f) > 1 else ""
                    upos = f[7] if len(f) > 7 else ""
                    lemma = f[6] if len(f) > 6 and f[6] != "*" else form
                    if not KANJI_RE.search(lemma):
                        continue
                    if upos not in ("NOUN", "PROPN", "VERB", "ADJ", "ADV", "CCONJ", "NUM", "PRON"):
                        if not (upos == "PART" and lemma in ("者", "所", "而", "也", "矣", "哉", "乎", "焉")):
                            continue
                    if lemma in have or form in have:
                        continue
                    key = lemma
                    cnt[key] += 1
                    info.setdefault(key, {"pos": f[0] + "-" + pos, "upos": upos,
                                          "src": [], "ex": ""})
                    if r["id"] not in info[key]["src"]:
                        info[key]["src"].append(r["id"])
                    if not info[key]["ex"]:
                        info[key]["ex"] = r["id"] + "|" + r["expected_kakikudashi"][:48].replace("\n", "")

    rows = [(w, c) for w, c in cnt.most_common()]
    out = os.path.join(ROOT, "eval", "lexicon_candidates.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for w, c in rows:
            d = info[w]
            fh.write("%s\t%d\t%s\t%d\t%s\t%s\n"
                     % (w, c, d["pos"], len(d["src"]), d["ex"], ",".join(d["src"][:4])))

    print("候选词条：%d（已排除词库已有 %d 条）" % (len(rows), len(have)))
    print("频次≥5：%d；≥3：%d；≥2：%d"
          % (sum(1 for _, c in rows if c >= 5),
             sum(1 for _, c in rows if c >= 3),
             sum(1 for _, c in rows if c >= 2)))
    print("written:", out)


if __name__ == "__main__":
    main()
