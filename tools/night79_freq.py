# -*- coding: utf-8 -*-
"""night79_freq.py — N79 ② 频次挖矿：golden_8165 から漢字複合語候補を抽出する。

方法:
  - eval/golden_8165.json（8165 行: {id, source_url, hakubun, expected_kakikudashi}）の
    白文と書き下し文の両方から、漢字連続ラン（2〜8 字）を抽出する。
    書き下し文の漢字ランは送り仮名で区切られた語形、白文の漢字ランは
    訓読語の原文表記——両方を文書頻度（1 行内の重複は 1 と数える）で集計する。
  - 既存 500 条（glossary_lexicon.py 209 + glossary_lexicon_extra.py 291）の词形と
    完全一致するランは除外。純かな機能語は漢字ランでないため自動的に除外される。
  - N76 §3.5 の覆蓋缺口 3 条（而る後／而ち／利す）は漢字ラン抽出では取れない
    （而+る+後 / 而+ち / 利+す はかな混じり）ので、リテラル検索で別集計し
    候補リストの先頭に置く（タスク書の要求）。
  - 候補は頻度降順で上位 500 条を eval/night79_candidates.json に書き出す。
    サンプル行（golden の id と書き下し文断片、最大 3 行）を語料証拠として同梱する。

用法: python -I tools/night79_freq.py
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

# 漢字（＋反復記号 々〆〻）。ャゥヶ等は含めない。
KANJI_RUN = re.compile(r"[々〆〻\u3400-\u9fff\uf900-\ufaff]+")
MIN_LEN, MAX_LEN = 2, 8
TOP_N = 500

# N76 §3.5 覆蓋缺口（かな混じりで漢字ランに落ちない 3 条）。リテラル検索の対象。
N76_GAPS = ["而る後", "而ち", "利す"]


def docfreq_lines(golden):
    """各行の各フィールドについて、行内でユニークな漢字ランを文書頻度に集計する。

    戻り値: (freq_h, freq_k, samples)
      freq_h/freq_k: word -> 行数（白文 / 書き下し文）
      samples: word -> [(id, field, snippet), ...] 最大 3 件
    """
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


def literal_freq(golden, word):
    """N76 缺口語（かな混じり）の文書頻度とサンプル行（書き下し文）を返す。"""
    n = 0
    samples = []
    for g in golden:
        kkd = re.sub(r"\s+", "", g.get("expected_kakikudashi", ""))
        if word in kkd:
            n += 1
            if len(samples) < 3:
                pos = kkd.find(word)
                lo = max(0, pos - 20)
                samples.append({"id": g.get("id", ""), "field": "kakikudashi",
                                "snippet": kkd[lo:lo + 60]})
    return n, samples


def main():
    t0 = time.time()
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    from backend.glossary_lexicon import GLOSSARY_LEXICON
    existing = {e["word"] for e in GLOSSARY_LEXICON}
    print("golden_8165 %d lines | existing lexicon words %d" % (len(golden), len(existing)),
          flush=True)

    freq_h, freq_k, samples = docfreq_lines(golden)
    all_runs = set(freq_h) | set(freq_k)
    n_all = len(all_runs)
    cands = []
    for w in all_runs:
        if w in existing:
            continue
        f = freq_h.get(w, 0) + freq_k.get(w, 0)
        if f >= 1:
            cands.append({"word": w, "freq": f,
                          "freq_hakubun": freq_h.get(w, 0),
                          "freq_kakikudashi": freq_k.get(w, 0),
                          "len": len(w)})
    cands.sort(key=lambda c: (-c["freq"], -c["len"], c["word"]))
    top = cands[:TOP_N]

    # N76 缺口 3 条を先頭に（語料証拠はリテラル検索）
    gap_entries = []
    for w in N76_GAPS:
        n, smp = literal_freq(golden, w)
        gap_entries.append({"word": w, "freq": n, "freq_hakubun": None,
                            "freq_kakikudashi": n, "len": len(w),
                            "n76_gap": True, "samples": smp})
        print("N76 gap %-4s doc_freq=%d sample=%s" % (w, n, smp[0]["snippet"] if smp else "-"),
              flush=True)

    out = {
        "generated": time.strftime("%Y-%m-%dT%H:%M"),
        "source": "eval/golden_8165.json (%d lines)" % len(golden),
        "method": ("kanji-run (2-8 chars) doc-frequency from hakubun+expected_kakikudashi; "
                   "existing 500 lexicon words excluded; pure-kana words never appear in runs; "
                   "N76 gaps (kana-mixed) prepended by literal search"),
        "stats": {
            "distinct_runs_all": n_all,
            "distinct_runs_nonexisting_ge1": len(cands),
            "threshold_rank500_freq": top[-1]["freq"] if len(top) >= TOP_N else None,
            "freq_ge5_nonexisting": sum(1 for c in cands if c["freq"] >= 5),
            "freq_ge3_nonexisting": sum(1 for c in cands if c["freq"] >= 3),
            "freq_ge2_nonexisting": sum(1 for c in cands if c["freq"] >= 2),
            "elapsed_sec": round(time.time() - t0, 1),
        },
        "candidates": gap_entries + [
            {**c, "samples": samples.get(c["word"], [])} for c in top
        ],
    }
    path = os.path.join(EV, "night79_candidates.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("distinct runs(all)=%d nonexisting>=1=%d | >=5:%d >=3:%d >=2:%d"
          % (n_all, len(cands), out["stats"]["freq_ge5_nonexisting"],
             out["stats"]["freq_ge3_nonexisting"], out["stats"]["freq_ge2_nonexisting"]),
          flush=True)
    print("rank500 freq=%s | written %s (%d candidates incl. 3 N76 gaps)"
          % (out["stats"]["threshold_rank500_freq"], path, len(out["candidates"])),
          flush=True)
    print("top20:", ", ".join("%s:%d" % (c["word"], c["freq"]) for c in top[:20]), flush=True)


if __name__ == "__main__":
    main()
