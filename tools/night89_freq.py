# -*- coding: utf-8 -*-
"""night89_freq.py — N89 ② 频次 2 区挖矿（N79/N80/N82 同口径第四波）。

N82（tools/night82_freq.py）の第四波。相違点:
  - ゾーン＝文書頻度 **2** の漢字連続 run（2–8 字；hakubun＋kakikudashi 両欄、
    文書内重複は 1 回計上——N79/N80/N82 と同一口径）。
  - ベースライン＝現行語彙 1301 語形（本体 500＋extra 291＋extra2 801）＋
    N79/N80/N82 排除済み語形（excluded 3 文件、任务书「已判定排除形は候補から除く」
    の暗黙前提——排除形は语库に無いので明示排除しないと再浮上する）。
    数が合わなければ即中断。
  - ソート＝任务書 §②「按频次＋kkd 归属优先」：(-freq, kkd 直証先, len, word)
    ——N80/N82 の (-freq, len, kkd, word) と違い kkd を len より先に置く
    （任务書明記の優先順に従う。freq 2 区は全件同頻度なので実効順＝kkd 先）。
  - 先頭 500 を eval/night89_candidates.json に出力（区総量が 500 未満なら全取）。
  - N79 実証済みパターン（X曰／2字X+有/無）は pre_exclude フラグのみ
    （fetch は 500 全件実施——N80/N82 同款、判定は人手）。
用法: python -I tools/night89_freq.py
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
FREQ_TARGET = 2
TOP_N = 500


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
    from backend.glossary_lexicon_extra import extra_size
    import backend.glossary_lexicon_extra as _extra_mod
    from backend.glossary_lexicon_extra2 import LEXICON_EXTRA2
    extra_words = {e["word"] for e in _extra_mod.as_dicts()}
    existing = ({e["word"] for e in GLOSSARY_LEXICON} |
                extra_words |
                {e["word"] for e in LEXICON_EXTRA2})
    n_base = len({e["word"] for e in GLOSSARY_LEXICON})
    n_extra = len(extra_words)
    n_extra2 = len({e["word"] for e in LEXICON_EXTRA2})
    if not (n_base == 500 and n_extra2 == 801 and len(existing) == 1301):
        print("[STOP] 現行語彙数異常: base=%d extra=%d extra2=%d uniq=%d（期待 500/291/801/1301）"
              % (n_base, n_extra, n_extra2, len(existing)))
        sys.exit(2)
    print("現行語彙 %d（本体 %d＋extra %d＋extra2 %d）" % (len(existing), n_base, n_extra, n_extra2),
          flush=True)

    # ---- 已判定排除形（N79/N80/N82）----
    excluded_prev = set()
    for fn, expect in (("night79_excluded.json", 179), ("night80_excluded.json", 239),
                       ("night82_excluded.json", 250)):
        path = os.path.join(EV, fn)
        data = json.load(open(path, encoding="utf-8"))
        words = {x["word"] for x in data["excluded"]}
        if len(words) != expect:
            print("[STOP] %s 排除形 %d（期待 %d）——手順確認" % (fn, len(words), expect))
            sys.exit(2)
        overlap = words & existing
        if overlap:
            print("[STOP] %s に現行語彙と重複 %d 形: %s" % (fn, len(overlap), sorted(overlap)[:5]))
            sys.exit(2)
        excluded_prev |= words
        print("  %s: %d 形" % (fn, len(words)), flush=True)
    baseline = existing | excluded_prev
    print("ベースライン＝現行 %d＋排除済み %d＝%d 語形" % (len(existing), len(excluded_prev), len(baseline)),
          flush=True)

    freq_h, freq_k, samples = docfreq_lines(golden)
    all_runs = set(freq_h) | set(freq_k)
    zone = []
    for w in all_runs:
        if w in baseline:
            continue
        f = freq_h.get(w, 0) + freq_k.get(w, 0)
        if f == FREQ_TARGET:
            zone.append({"word": w, "freq": f,
                         "freq_hakubun": freq_h.get(w, 0),
                         "freq_kakikudashi": freq_k.get(w, 0),
                         "len": len(w)})
    # 任务書 §②「按频次＋kkd 归属优先」：freq → kkd 直証 → len → word
    zone.sort(key=lambda c: (-c["freq"],
                             0 if c["freq_kakikudashi"] > 0 else 1,
                             c["len"], c["word"]))
    n_zone = len(zone)
    print("频次 2 区（非既存・非排除済み）総量＝%d" % n_zone, flush=True)
    picked = zone[:TOP_N]
    pre = 0
    for c in picked:
        w = c["word"]
        if w.endswith("曰"):
            c["pre_exclude"] = "n79-pattern: X-yune citation fragment (N79 ~60 fetched, all weblio 404)"
            pre += 1
        elif len(w) == 2 and w.endswith(("有", "無")):
            c["pre_exclude"] = ("n79-pattern: X+ari/nashi construction fragment "
                                "(gong-you/ri-you/mei-you/sin-nasi etc all 404 or reibun-only in N79)")
            pre += 1
    cands = [{**c, "rank": j, "samples": samples.get(c["word"], [])}
             for j, c in enumerate(picked)]
    out = {
        "generated": time.strftime("%Y-%m-%dT%H:%M"),
        "source": "eval/golden_8165.json (%d lines)" % len(golden),
        "method": ("N89 wave4: kanji-run (2-8 chars) doc-frequency == 2 zone; "
                   "baseline = current lexicon 1301 forms + N79/N80/N82 excluded forms "
                   "(179+239+250=668); sort = (-freq, kkd-attested first, len, word) "
                   "per taskbook '频次＋kkd 归属优先'; top %d of zone %d" % (TOP_N, n_zone)),
        "stats": {
            "distinct_runs_all": len(all_runs),
            "zone_freq2_nonexisting": n_zone,
            "zone_shortfall_pct": n_zone < TOP_N,
            "candidates_this_night": len(cands),
            "pre_exclude_flagged": pre,
            "kkd_attested": sum(1 for c in cands if c["freq_kakikudashi"] > 0),
            "hakubun_only": sum(1 for c in cands if c["freq_kakikudashi"] == 0),
            "len3plus": sum(1 for c in cands if c["len"] >= 3),
            "len_distribution": {str(l): sum(1 for c in cands if c["len"] == l)
                                 for l in sorted({c["len"] for c in cands})},
            "elapsed_sec": round(time.time() - t0, 1),
        },
        "candidates": cands,
    }
    path = os.path.join(EV, "night89_candidates.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("候補 %d 条（区総量 %d・pre_exclude %d）" % (len(cands), n_zone, pre), flush=True)
    print("kkd 直証 %d／白文のみ %d／len>=3 %d" % (
        out["stats"]["kkd_attested"], out["stats"]["hakubun_only"], out["stats"]["len3plus"]),
        flush=True)
    print("len 分布: %s" % out["stats"]["len_distribution"], flush=True)
    print("first10:", ", ".join("%s(k%d)" % (c["word"], c["freq_kakikudashi"]) for c in cands[:10]),
          flush=True)
    print("written:", path, flush=True)


if __name__ == "__main__":
    main()
