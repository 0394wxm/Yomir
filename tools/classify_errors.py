# -*- coding: utf-8 -*-
"""
classify_errors.py — 把评测结果里的错误按类别统计（NIGHT4）。

类别：切分错 / 助词错 / 动词活用错 / 专名错 / 旧字体 / 其他 / (EXACT=全对)

方法（启发式，诚实标注局限）：
1. 用 difflib.SequenceMatcher 在 got 与 expected 的字符序列上对齐；
2. 对每个 replace 块看 got/expected 两侧的片段性质：
   - 旧字体：got 片段含旧字体字（SHINJITAI_MAP 的 key）且按 map 转换后与 expected 片段一致；
   - 助词错：expected 片段全部是助词假名（はがをにとものへやかな）或 got/expected
     在 kanji 边界处差一个假名；
   - 动词活用错：expected 片段以文语活用尾（ず/ざる/ぬ/ば/れば/ん/む/たる/たり…）为主；
   - 专名错：expected 片段含 MERGE_WORDS 的词或 expected 把 got 里「XのY」合并成「XY」；
   - 切分错：两侧汉字序列不同（把「漢字+の+漢字」/词边界归到这里）；
3. 一条结果可能命中多类 → 每类都计数（报告里注明是多标签统计）；
4. 都不命中 → 其他。

用法: python -X utf8 tools/classify_errors.py eval/night4_results_baseline.json [eval/night4_results_full.json ...]
"""
import collections
import difflib
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.kundoku_rules import SHINJITAI_MAP, MERGE_WORDS  # noqa: E402

PARTICLE_KANA = set("はがをにとものへやかなで")
VERB_TAIL_RX = re.compile(r"(ざる|ず|ぬ|ば|れば|んと|たり|たる|し|き|けり|なり|べし|まし|よ|れ|さす|す|む|ん)$")
OLD2NEW = {old: new for new, old in {v: k for k, v in SHINJITAI_MAP.items()}.items()}


def kanji_only(s):
    return "".join(c for c in s if "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def classify_pair(got: str, expected: str) -> list:
    got, expected = got.strip(), expected.strip()
    cats = []
    sm = difflib.SequenceMatcher(a=got, b=expected)
    has_oldfont = has_particle = has_verb = has_proper = has_seg = False
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        g = got[i1:i2]
        e = expected[j1:j2]
        # 旧字体：把 got 片段里的旧字换新字后与 expected 相同
        if g and e and "".join(SHINJITAI_MAP.get(c, c) for c in g) == e:
            has_oldfont = True
            continue
        # 专名错：expected 侧出现白名单专名，而 got 侧没有该完整词
        hit_word = None
        for w in MERGE_WORDS:
            if w in e and w not in got:
                hit_word = w
                break
        if hit_word:
            has_proper = True
            continue
        # 助词错：expected 片段是 1~2 个助词假名
        if e and len(e) <= 2 and all(c in PARTICLE_KANA for c in e) and kanji_only(g) == kanji_only(e):
            has_particle = True
            continue
        # 动词活用错：expected 片段以文语活用尾结尾，且 got/expected 共享汉字词干
        if e and VERB_TAIL_RX.search(e) and kanji_only(e) and kanji_only(e) in kanji_only(g):
            has_verb = True
            continue
        # 其余：汉字序列有差异 → 切分错；纯假名差异 → 归活用/其他
        if kanji_only(g) != kanji_only(e):
            has_seg = True
        else:
            has_particle = True  # 同汉字、假名不同：多为助词/送り仮名差异，归助词
    if has_oldfont:
        cats.append("旧字体")
    if has_proper:
        cats.append("专名错")
    if has_particle:
        cats.append("助词错")
    if has_verb:
        cats.append("动词活用错")
    if has_seg:
        cats.append("切分错")
    if not cats:
        cats.append("其他")
    return cats


def main():
    paths = sys.argv[1:]
    if not paths:
        print("usage: classify_errors.py <results1.json> [results2.json ...]")
        return
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(ROOT, p)
        with open(full, encoding="utf-8") as f:
            d = json.load(f)
        counter = collections.Counter()
        per_entry = []
        exact = 0
        for r in d["results"]:
            got = r.get("udkundoku_kakikudashi_norm") or re.sub(r"\s+", "", r.get("udkundoku_kakikudashi", ""))
            exp = re.sub(r"\s+", "", r["expected_kakikudashi"])
            if got.strip() == exp.strip():
                exact += 1
                cats = ["EXACT"]
            else:
                cats = classify_pair(got, exp)
            for c in cats:
                counter[c] += 1
            per_entry.append({"id": r["id"], "cats": cats})
        n = len(d["results"])
        print("=== %s: %d 条, EXACT %d" % (os.path.basename(full), n, exact))
        for cat, cnt in counter.most_common():
            print("   %-8s %3d 条 (%.0f%%)" % (cat, cnt, 100.0 * cnt / n))
        out = full.replace(".json", "_classified.json")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"file": os.path.basename(full), "total": n, "exact": exact,
                       "counts": dict(counter), "per_entry": per_entry},
                      f, ensure_ascii=False, indent=2)
        print("   written:", out)


if __name__ == "__main__":
    main()
