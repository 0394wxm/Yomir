# -*- coding: utf-8 -*-
"""night82_freq.py — N82 ② 频次挖矿第三波：N80 rank 500–965（466 条）候補抽出。

N80（tools/night80_freq.py）の第三波。相違点:
  - ベースラインは N80 と同一の 824 語形（本体 500＋extra 291＋extra2 N79 分 324）
    を再現する。現行語彙は 1085（N80 追加 261 を含む）なので、N80 判定 500 語のうち
    現行語彙に在る 261 語を差し引いて 824 に戻す（数が合わなければ即中断）。
  - ゾーン全量を再計算して 966 と照合（タスク書 §②：总数对不上 966 先停下报数）。
  - N80 と同一ソートを適用し、rank 0–499 が N80 候補
    （eval/night80_candidates.json）と完全一致することを検証（決定論チェック）して
    から、残り rank 500–965（466 語形）を eval/night82_candidates.json に出力する
    （rank は N80 絶対番号を維持）。
  - N79 実証済みパターン（X曰／2字X+有/無）は N80 同様 pre_exclude フラグのみ
    （fetch は 466 全件実施——N80「500 页全抓」同款、判定は人手）。
用法: python -I tools/night82_freq.py
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
FREQ_LO, FREQ_HI = 3, 4
BASE_RANK = 500  # N80 が判定済みの先頭 500 の直後


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
    existing_now = ({e["word"] for e in GLOSSARY_LEXICON} |
                    {e["word"] for e in LEXICON_EXTRA2})
    n80 = json.load(open(os.path.join(EV, "night80_candidates.json"), encoding="utf-8"))
    n80_words = [c["word"] for c in n80["candidates"]]
    if len(n80_words) != 500:
        print("[STOP] night80_candidates.json は 500 件ではない: %d" % len(n80_words))
        sys.exit(2)
    in_lex = [w for w in n80_words if w in existing_now]
    if len(in_lex) != 261:
        print("[STOP] N80 判定 500 語のうち現行語彙に在るのは %d（期待 261）——手順確認" % len(in_lex))
        sys.exit(2)
    baseline = existing_now - set(in_lex)
    if len(baseline) != 824:
        print("[STOP] 824 ベースライン再現失敗: %d" % len(baseline))
        sys.exit(2)
    print("golden_8165 %d lines | 現行語彙 %d → N80 追加分 %d 差し引き baseline %d"
          % (len(golden), len(existing_now), len(in_lex), len(baseline)), flush=True)

    freq_h, freq_k, samples = docfreq_lines(golden)
    all_runs = set(freq_h) | set(freq_k)
    zone = []
    for w in all_runs:
        if w in baseline:
            continue
        f = freq_h.get(w, 0) + freq_k.get(w, 0)
        if FREQ_LO <= f <= FREQ_HI:
            zone.append({"word": w, "freq": f,
                         "freq_hakubun": freq_h.get(w, 0),
                         "freq_kakikudashi": freq_k.get(w, 0),
                         "len": len(w)})
    zone.sort(key=lambda c: (-c["freq"], c["len"],
                             0 if c["freq_kakikudashi"] > 0 else 1, c["word"]))
    if len(zone) != 966:
        print("[STOP] ゾーン 3–4 非既存＝%d（期待 966）——タスク書 §② により中断報告" % len(zone))
        sys.exit(2)
    top_words = [c["word"] for c in zone[:500]]
    if top_words != n80_words:
        diff = [i for i, (a, b) in enumerate(zip(top_words, n80_words)) if a != b]
        print("[STOP] 再計算 rank0-499 が N80 候補と不一致（決定論崩れ）first=%s" % diff[:5])
        sys.exit(2)
    rest = zone[BASE_RANK:]
    pre = 0
    for c in rest:
        w = c["word"]
        if w.endswith("曰"):
            c["pre_exclude"] = "n79-pattern: X-yune citation fragment (~60 fetched in N79, all weblio 404)"
            pre += 1
        elif len(w) == 2 and w.endswith(("有", "無")):
            c["pre_exclude"] = ("n79-pattern: X+ari/nashi construction fragment "
                                "(gong-you/ri-you/mei-you/sin-nasi etc all 404 or reibun-only in N79)")
            pre += 1
    cands = [{**c, "rank": BASE_RANK + j, "samples": samples.get(c["word"], [])}
             for j, c in enumerate(rest)]
    out = {
        "generated": time.strftime("%Y-%m-%dT%H:%M"),
        "source": "eval/golden_8165.json (%d lines)" % len(golden),
        "method": ("N82 wave3: same kanji-run (2-8 chars) doc-frequency 3-4 zone; "
                   "baseline 824 reconstructed (current 1085 minus 261 N80-included); "
                   "zone recomputed == 966 and rank0-499 identical to night80 candidates "
                   "(determinism check); this file = rank 500-965 (466), absolute rank kept"),
        "stats": {
            "distinct_runs_all": len(all_runs),
            "zone_3_4_nonexisting": len(zone),
            "n80_rank0_499_verified_identical": True,
            "candidates_this_night": len(cands),
            "pre_exclude_flagged": pre,
            "freq4_in_remaining": sum(1 for c in cands if c["freq"] == 4),
            "kkd_attested_in_remaining": sum(1 for c in cands if c["freq_kakikudashi"] > 0),
            "len3plus_in_remaining": sum(1 for c in cands if c["len"] >= 3),
            "elapsed_sec": round(time.time() - t0, 1),
        },
        "candidates": cands,
    }
    path = os.path.join(EV, "night82_candidates.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("zone 966 verified, rank0-499 identical to N80 | remaining=%d (pre_exclude %d)"
          % (len(cands), pre), flush=True)
    print("freq4=%d kkd-attested=%d len>=3=%d | written %s"
          % (out["stats"]["freq4_in_remaining"], out["stats"]["kkd_attested_in_remaining"],
             out["stats"]["len3plus_in_remaining"], path), flush=True)
    print("first10:", ", ".join("%s:%d" % (c["word"], c["freq"]) for c in cands[:10]), flush=True)


if __name__ == "__main__":
    main()
