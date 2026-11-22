# -*- coding: utf-8 -*-
"""night80_freq.py — N80 ② 频次挖矿第二波：频次 3–4 区から漢字複合語候補を抽出。

N79（tools/night79_freq.py）の方法の第二波。違い:
  - 既存語彙は 824 条（本体 209＋extra 291＋extra2 324。GLOSSARY_LEXICON 500＋extra2）。
  - 頻度ゾーンは 3〜4（N79 は ≥5 の上位 500）。頻度降序で約 500 条。
  - 同頻度内の順序は「kkd 証拠あり（freq_kakikudashi>0）を先」——語料証拠は
    書き下し文行で取るのが本流（N79 実績: 全 include が k≥1）。
  - N79 で ~60 語 fetch して全部 404 だった「X曰」型と、「X＋有り／X＋無し」型の
    構文断片は候補に残すが pre_exclude フラグを付ける（研究段で fetch なしで
    排除——排除に証拠は不要、パターンは N79 バッチ実証済み、理由を記録）。
用法: python -I tools/night80_freq.py
"""
import json
import os
import re
import sys
import time
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

KANJI_RUN = re.compile(r"[々〆〻\u3400-\u9fff\uf900-\ufaff]+")
MIN_LEN, MAX_LEN = 2, 8
TOP_N = 500
FREQ_LO, FREQ_HI = 3, 4


def docfreq_lines(golden):
    freq_h = defaultdict(int)
    freq_k = defaultdict(int)
    samples = defaultdict(list)
    for g in golden:
        gid = g.get("id", "")
        for field, text, counter in (
            ("hakubun", g.get("hakubun", ""), freq_h),
            ("kakikudashi", g.get("expected_kakikudashi", ""), freq_k),
        ):
            seen = set()
            for run in KANJI_RUN.findall(text):
                if MIN_LEN <= len(run) <= MAX_LEN and run not in seen:
                    seen.add(run)
                    counter[run] += 1
                    if len(samples[run]) < 3 and field == "kakikudashi":
                        snip = re.sub(r"\s+", "", text)
                        if len(snip) > 60:
                            pos = snip.find(run)
                            lo = max(0, pos - 20)
                            snip = snip[lo:lo + 60]
                        samples[run].append({"id": gid, "field": field, "snippet": snip})
    return freq_h, freq_k, samples


def main():
    t0 = time.time()
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    from backend.glossary_lexicon import GLOSSARY_LEXICON
    from backend.glossary_lexicon_extra2 import LEXICON_EXTRA2
    existing = {e["word"] for e in GLOSSARY_LEXICON} | {e["word"] for e in LEXICON_EXTRA2}
    print("golden_8165 %d lines | existing lexicon words %d" % (len(golden), len(existing)),
          flush=True)

    freq_h, freq_k, samples = docfreq_lines(golden)
    all_runs = set(freq_h) | set(freq_k)
    zone = []
    for w in all_runs:
        if w in existing:
            continue
        f = freq_h.get(w, 0) + freq_k.get(w, 0)
        if FREQ_LO <= f <= FREQ_HI:
            zone.append({"word": w, "freq": f,
                         "freq_hakubun": freq_h.get(w, 0),
                         "freq_kakikudashi": freq_k.get(w, 0),
                         "len": len(w)})
    # 同頻度内は「短い語を先」（2 字複合語が本命。N79 実績：include はほぼ 2 字。
    # 3-4 区の 4 字以上は長七尺五寸以上・冠者五六人 型の数詞公式断片が大半）。
    # 理由は method フィールドと REPORT_NIGHT80.md に記録。
    zone.sort(key=lambda c: (-c["freq"], c["len"],
                             0 if c["freq_kakikudashi"] > 0 else 1, c["word"]))

    # N79 バッチ実証済みパターンの pre_exclude マーク（研究段で fetch なし排除）
    pre = 0
    for c in zone:
        w = c["word"]
        if w.endswith("曰"):
            c["pre_exclude"] = "n79-pattern: X-yune citation fragment (~60 fetched in N79, all weblio 404)"
            pre += 1
        elif len(w) == 2 and w.endswith(("有", "無")):
            c["pre_exclude"] = ("n79-pattern: X+ari/nashi construction fragment "
                                "(gong-you/ri-you/mei-you/sin-nasi etc all 404 or reibun-only in N79)")
            pre += 1
    top = zone[:TOP_N]

    out = {
        "generated": time.strftime("%Y-%m-%dT%H:%M"),
        "source": "eval/golden_8165.json (%d lines)" % len(golden),
        "method": ("N79 wave2: kanji-run (2-8 chars) doc-frequency 3-4 zone from "
                   "hakubun+expected_kakikudashi; existing 824 words excluded; "
                   "within-freq order puts kkd-attested (freq_kakikudashi>0) first; "
                   "N79-verified junk patterns (X-yune, X+ari/nashi) flagged pre_exclude"),
        "stats": {
            "distinct_runs_all": len(all_runs),
            "zone_3_4_nonexisting": len(zone),
            "pre_exclude_flagged": pre,
            "rank500_freq": top[-1]["freq"] if len(top) >= TOP_N else None,
            "kkd_attested_in_top": sum(1 for c in top if c["freq_kakikudashi"] > 0),
            "elapsed_sec": round(time.time() - t0, 1),
        },
        "candidates": [{**c, "samples": samples.get(c["word"], [])} for c in top],
    }
    path = os.path.join(EV, "night80_candidates.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("zone 3-4 nonexisting=%d (pre_exclude %d) | kkd-attested in top=%d"
          % (len(zone), pre, out["stats"]["kkd_attested_in_top"]), flush=True)
    print("rank500 freq=%s | written %s (%d candidates)"
          % (out["stats"]["rank500_freq"], path, len(top)), flush=True)
    print("top15:", ", ".join("%s:%d%s" % (c["word"], c["freq"],
                                           "" if c["freq_kakikudashi"] else "(h-only)")
                              for c in top[:15]), flush=True)


if __name__ == "__main__":
    main()
