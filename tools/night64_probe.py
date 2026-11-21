# -*- coding: utf-8 -*-
"""night64_probe.py — N64 第二步：候选取证。

  A. SHINJITAI 第二遍「计数判据」（N58 教训：difflib 1:1 块会漏多字对齐里的对）：
     全部汉字（不在表中）exp 全库写 0 次 && got 全库 >=2 次 → 候选；
     目标形 = 对含该字的行做 difflib 对齐、取 1:1 替换块的多数票。
  B. kana 候选取证（D14 教训：词形按 expected 真实形态，不是裸汉字替换）：
     每个 kana 候选：got/exp 计数 + 白文护栏字命中行数 + exp 侧对应词形逐条采样。
只读；输出 eval/night64_probe.json / night64_probe.txt。
"""
import collections
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)
from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402

KANA_CANDS = ["けだし", "すなわち", "なほ", "ゆゑに", "ゆえに", "いずくんぞ",
              "もし", "それ", "なかれ", "ことなかれ", "のみ", "ただ"]
KANA_GUARDS = {
    "けだし": "蓋", "すなわち": "即", "なほ": "猶", "ゆゑに": "故", "ゆえに": "故",
    "いずくんぞ": "焉", "もし": "如", "それ": "夫", "なかれ": "毋",
    "ことなかれ": "莫", "のみ": "只", "ただ": "惟",
}


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def main():
    doc = json.load(open(os.path.join(EV, "night60_results_4000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    exp_all = collections.Counter()
    got_all = collections.Counter()
    for r in rows:
        exp_all.update(norm(r["expected_kakikudashi"]))
        got_all.update(norm(r["udkundoku_kakikudashi"]))
    lines = []

    # ---- A. SHINJITAI 计数判据 + 多数票定目标形 ----
    votes = collections.defaultdict(collections.Counter)  # old -> Counter(target)
    for r in rows:
        got, exp = norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"])
        sm = SequenceMatcher(a=got, b=exp, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            g, e = got[a1:a2], exp[b1:b2]
            if len(g) == len(e):  # 等长替换块内逐位取 1:1（多字块也不漏）
                for gc, ec in zip(g, e):
                    if is_kanji(gc) and is_kanji(ec):
                        votes[gc][ec] += 1
    shin2 = []
    for c in set(list(got_all) + list(exp_all)):
        if not is_kanji(c) or c in SHINJITAI_MAP:
            continue
        if exp_all.get(c, 0) == 0 and got_all.get(c, 0) >= 2:
            vc = votes.get(c)
            tgt, n = vc.most_common(1)[0] if vc else (None, 0)
            shin2.append({"old": c, "new": tgt, "vote": n, "got_old": got_all[c],
                          "all_votes": vc.most_common(3) if vc else []})
    shin2.sort(key=lambda x: -x["got_old"])
    lines.append("=== A. SHINJITAI 计数判据（exp 全库 0 次 & got>=2 次，不在表中）===")
    for x in shin2:
        lines.append("  %s→%s vote %d/%d | 全票 %s" % (
            x["old"], x["new"], x["vote"], x["got_old"],
            " ".join("%s:%d" % kv for kv in x["all_votes"])))

    # ---- B. kana 候选取证 ----
    lines.append("\n=== B. kana 候选（got/exp 计数 | 白文含护栏字且 got 含 kana 的行数 | exp 词形采样）===")
    probe = {}
    for k in KANA_CANDS:
        g_cnt = sum(norm(r["udkundoku_kakikudashi"]).count(k) for r in rows)
        e_cnt = sum(norm(r["expected_kakikudashi"]).count(k) for r in rows)
        guard = KANA_GUARDS[k]
        hit = []
        for r in rows:
            hb = norm(r["hakubun"])
            if guard in hb and k in norm(r["udkundoku_kakikudashi"]):
                hit.append(r)
        probe[k] = {"got": g_cnt, "exp": e_cnt, "guard": guard,
                    "guard_hit_rows": len(hit)}
        lines.append("  %-8s got %4d exp %3d | 白文含%s & got含kana: %3d 行" % (
            k, g_cnt, e_cnt, guard, len(hit)))
        for r in hit[:6]:
            lines.append("      %s | got: %s" % (r["id"], norm(r["udkundoku_kakikudashi"])[:46]))
            lines.append("      %s | exp: %s" % (" " * len(r["id"]), norm(r["expected_kakikudashi"])[:46]))

    out = {"shinjitai_count": shin2, "kana_probe": probe}
    json.dump(out, open(os.path.join(EV, "night64_probe.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    txt = "\n".join(lines)
    open(os.path.join(EV, "night64_probe.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    print(txt, flush=True)
    print("\nwritten: eval/night64_probe.json / night64_probe.txt", flush=True)


if __name__ == "__main__":
    main()
