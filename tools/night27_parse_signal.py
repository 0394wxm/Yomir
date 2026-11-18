# -*- coding: utf-8 -*-
"""night27_parse_signal.py — Night 27：guwenbert 句法信号 vs して系三路结果的预测力。

问题（Night 25 §4）：got 而して → exp して/にして/删除 三路同形、表面不可分。
本实验：对每处 got 而して，配对白文里第 k 个「而」，用 guwenbert 依存解析取
而 token 的 deprel / head 信息，检验句法特征能否切分三路（纯离线，不涉延迟决策）。

配对近似（如实）：got 而して 的第 k 处 ↔ 白文 而 的第 k 处；个数不等的行跳过并计数。
expected 侧结果判定复用 Night 25 v2 的字符映射法。
输出 eval/night27_parse_signal.json + stdout 交叉表。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import difflib


def norm(s):
    return re.sub(r"\s+", "", s)


def load(name):
    with open(os.path.join(ROOT, "eval", name), encoding="utf-8") as f:
        return json.load(f)["results"]


def char_map(got, exp):
    sm = difflib.SequenceMatcher(a=got, b=exp, autojunk=False)
    m = [None] * len(got)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                m[a1 + k] = b1 + k
    return m


def exp_outcome(got, exp, m, i):
    """got[i:i+3]=而して 的 exp 侧归类（v2：修掉三字切片恒 False 的 bug）。"""
    e0 = m[i]                     # 而 的映射（None=而 被删/改）
    e1 = m[i + 1] if i + 1 < len(m) else None   # し
    e2 = m[i + 2] if i + 2 < len(m) else None   # て
    # 而被删、して equal → exp=して
    if e0 is None and e1 is not None and e2 == e1 + 1 and exp[e1:e1 + 2] == "して":
        return "して"
    # 三字全 equal 且 exp 同位置也是而して → 保留
    if (e0 is not None and e1 == e0 + 1 and e2 == e0 + 2
            and exp[max(0, e0 - 1):e0 + 3] == "而して"):
        return "保留(而して)"
    # して equal 且其前一字符是 に（且该に不是 got 的而映射来的）→ exp=にして
    if (e0 is None and e1 is not None and e2 == e1 + 1
            and e1 > 0 and exp[e1 - 1] == "に"):
        return "にして"
    # 三字全 equal 但 exp 是 にして（に 是 got 而的位置本身？对不齐的情形）
    if (e0 is not None and e1 == e0 + 1 and e2 == e0 + 2
            and exp[e0:e0 + 2] == "して" and e0 > 0 and exp[e0 - 1] == "に"):
        return "にして"
    if e0 is None and e1 is None and e2 is None:
        return "删除"
    return "其它"


def main():
    rows_all = load("night26_results_full.json") + load("night23_results_rongo.json")
    rows = [r for r in rows_all if "而" in r["hakubun"]]
    print("含而的行：%d / %d" % (len(rows), len(rows_all)))

    import load_guwenbert as lg
    parser = lg.load_parser(verbose=False)

    recs = []
    skipped = 0
    for ri, r in enumerate(rows):
        hakubun = r["hakubun"]
        got = norm(r.get("udkundoku_kakikudashi") or "")
        exp = norm(r["expected_kakikudashi"])
        got_eres = list(re.finditer("而して", got))
        if not got_eres:
            continue  # 引擎没产出而して（して/にして侧，本轮不覆盖）
        try:
            words = lg.mecab_tokenize(hakubun)
        except Exception as e:
            skipped += 1
            continue
        buts = [i for i, w in enumerate(words) if w == "而"]
        if len(buts) != len(got_eres):
            skipped += 1
            continue
        try:
            _w, arcs, rels = lg.parse_words(parser, words, verbose=False)
        except Exception as e:
            skipped += 1
            continue
        m = char_map(got, exp)
        for k, mt in enumerate(got_eres):
            bi = buts[k]
            outcome = exp_outcome(got, exp, m, mt.start())
            rel = rels[bi]
            head_i = arcs[bi]
            recs.append({
                "id": r["id"], "k": k, "outcome": outcome,
                "guw_rel": rel,
                "guw_head_form": "ROOT" if head_i == 0 else words[head_i - 1],
                "guw_head_rel": "ROOT" if head_i == 0 else rels[head_i - 1],
                "guw_prev": words[bi - 1] if bi > 0 else "BOS",
                "guw_next": words[bi + 1] if bi + 1 < len(words) else "EOS",
                "prev_class": ("BOS" if bi == 0 else
                               ("kana" if re.match(r"[ぁ-ゖァ-ヺ]", words[bi - 1]) else
                                ("kanji" if re.match(r"[一-龠㐀-䶵]", words[bi - 1]) else "punct"))),
            })
        if (ri + 1) % 50 == 0:
            print("  parsed %d/%d" % (ri + 1, len(rows)))

    print("\n配对成功 %d 处，跳过 %d 行（个数不等/分词失败）" % (len(recs), skipped))
    # 交叉表
    tab = defaultdict(Counter)
    for x in recs:
        tab[x["guw_rel"]][x["outcome"]] += 1
    print("\n=== guwenbert 而 的 deprel × exp 结果 ===")
    for rel, c in sorted(tab.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        print("  %-10s n=%3d  %s" % (rel, tot, dict(c.most_common())))
    print("\n=== head deprel × exp 结果 ===")
    tab2 = defaultdict(Counter)
    for x in recs:
        tab2[x["guw_head_rel"]][x["outcome"]] += 1
    for rel, c in sorted(tab2.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        print("  head=%-10s n=%3d  %s" % (rel, tot, dict(c.most_common())))
    print("\n=== 前置token类别 × exp 结果（对照：表面信号基线）===")
    tab3 = defaultdict(Counter)
    for x in recs:
        tab3[x["prev_class"]][x["outcome"]] += 1
    for pc, c in sorted(tab3.items(), key=lambda kv: -sum(kv[1].values())):
        print("  %-6s n=%3d  %s" % (pc, sum(c.values()), dict(c.most_common())))

    with open(os.path.join(ROOT, "eval", "night27_parse_signal.json"), "w", encoding="utf-8") as f:
        json.dump({"paired": len(recs), "skipped_rows": skipped, "records": recs},
                  f, ensure_ascii=False, indent=1)
    print("\nwritten: eval/night27_parse_signal.json")


if __name__ == "__main__":
    main()
