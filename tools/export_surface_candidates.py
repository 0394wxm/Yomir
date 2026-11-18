# -*- coding: utf-8 -*-
"""export_surface_candidates.py — 按「实际出现在文本里的表面形」统计候选词（D3 用）。

词库是子串匹配，所以 word 必须是文本里真实出现的字符串。
本脚本统计：白文 + expected 書き下し文里，长度≥2、含汉字、出现≥2 次的表面形。
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


def main():
    with open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    have = {e["word"] for e in GLOSSARY_LEXICON}

    cnt = collections.Counter()
    info = {}
    for r in items:
        for seg, tag in ((r["hakubun"], "白文"), (r["expected_kakikudashi"], "訓読")):
            for line in re.sub(r"\s+", "", seg).split("。"):
                if not line.strip():
                    continue
                for tok in tagger.parse(line).splitlines():
                    if tok in ("EOS", "") or "\t" not in tok:
                        continue
                    form, feat = tok.split("\t")
                    if len(form) < 2 or not KANJI_RE.search(form):
                        continue
                    if form in have:
                        continue
                    cnt[form] += 1
                    info.setdefault(form, {"pos": feat.split(",")[0], "ex": [], "src": []})
                    if len(info[form]["ex"]) < 2:
                        info[form]["ex"].append(tag + ":" + line[:26])
                    if r["id"] not in info[form]["src"]:
                        info[form]["src"].append(r["id"])

    rows = cnt.most_common()
    out = os.path.join(ROOT, "eval", "lexicon_surface_candidates.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for w, c in rows:
            d = info[w]
            fh.write("%s\t%d\t%s\t%s\t%s\t%d\n"
                     % (w, c, d["pos"], " / ".join(d["ex"]), ",".join(d["src"][:3]), len(d["src"])))
    print("表面形候选：%d" % len(rows))
    print("≥5次：%d  ≥4次：%d  ≥3次：%d  ≥2次：%d"
          % (sum(1 for _, c in rows if c >= 5), sum(1 for _, c in rows if c >= 4),
             sum(1 for _, c in rows if c >= 3), sum(1 for _, c in rows if c >= 2)))
    print("written:", out)


if __name__ == "__main__":
    main()
