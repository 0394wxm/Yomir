# -*- coding: utf-8 -*-
"""night89_judge.py — N89 新補助：紧凑判定入力 → N80 同款 decisions JSON 展開器。

判定入力 eval/night89_judge_<start>.txt（1 行 1 条、pipe 区切り 7 欄）:
  rank|word|V|cat|reading|meaning|note
  V = I(include) / X(exclude)。
  I は cat/reading/meaning 必須。note は任意で:
    - "DE:…" なら dict_evidence 全文を手差し採録（無ければキャッシュから自動抽出）
    - "CE:…" なら corpus_evidence 全文を手差し採録（無ければ候補 samples から自動組立）
  X は note が exclude_reason 本体（必須）。
展開先 eval/night89_decisions_<start>.json（N80 同 schema）。機械検証:
  - rank/word が night89_candidates.json と一致、重複・範囲外は拒否
  - I の必須欄非空・cat 正当、X の reason 非空
自動採証（auto_dict_evidence）は実在の国語辞書区からのみ引用し、
ウィキペディア小見出し辞書／例文用例辞書のみの頁では None を返す（人手 DE: のみ）。
用法: python -I tools/night89_judge.py <start_rank>
"""
import glob
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")
CACHE = os.path.join(EV, "night89_dict_cache")
BASE_RANK = 0
CATS = ("proper", "noun", "verb", "modifier", "function")

DICTNAMES = (
    "デジタル大辞泉", "精選版 日本国語大辞典", "古語辞典", "日本語古語辞典",
    "Weblio古語辞典", "故事ことわざの辞典", "Wiktionary日本語版",
    "日本語WordNet", "ウィキペディア小見出し辞書",
    "Weblio日本語例文用例辞書", "故事ことわざ辞典",
)
AUTO_NONE_DICTS = ("ウィキペディア小見出し辞書", "Weblio日本語例文用例辞書", "Wiktionary")
JUNK2 = ("索引トップ", "用語の索引", "ランキング", "凡例", "カテゴリー", "出典:",
         "この記事で示されている", "ご存知の方は", "関連することわざ", "関連する慣用句",
         "関連する英語表現", "急上昇のことば", "その他の辞書▼", "ログイン", "Weblio 辞書",
         "ヘルプ")


def safe_name(word):
    return "".join(ch if ch.isascii() or ch.isalnum() else "_" for ch in word)[:24] or "noname"


def cand_path(rank, word):
    return os.path.join(CACHE, "cand_%03d_%s.txt" % (rank, safe_name(word)))


def auto_dict_evidence(rank, word):
    """辞書条目区の冒頭（辞書名＋見出し＋読み方、≤150 字）をキャッシュから引用する。

    パンくズ「Weblio 辞書 >」以降を対象に、【…】見出しまたは読み方行を含む
    チャンクのみ採用（ページヘッダーメニューの辞書名リンク「古語辞典」等を
    誤採用しない——尚書/川原 での誤採証の教訓）。該当なけれは None（DE: 必要）。
    """
    path = cand_path(rank, word)
    if not os.path.exists(path):
        return None
    lines = open(path, encoding="utf-8").read().splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if ln.startswith("Weblio 辞書 >"):
            start = i
            break
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("#") or not s:
            continue
        if any(s == d or s.startswith(d) for d in DICTNAMES):
            if s.startswith(AUTO_NONE_DICTS):
                return None  # 機械区/Wiki区のみ＝自動採証しない
            chunk = []
            for ln2 in lines[i:i + 10]:
                t = ln2.strip()
                if t and not t.startswith("#") and not t.startswith(JUNK2):
                    chunk.append(t)
                if len(chunk) >= 3:
                    break
            joined = "；".join(chunk)
            if "【" in joined or "読み方：" in joined or "読み方:" in joined:
                return joined[:150]
    return None


def auto_corpus_evidence(c):
    smp = c.get("samples") or []
    if smp:
        s0 = smp[0]
        return "golden_8165 %d行。例 %s「%s」" % (c["freq"], s0.get("id", ""), s0.get("snippet", "")[:70])
    return "golden_8165 freq=%d（kkd 直証なし——CE: 上書き必須）" % c["freq"]


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    src = os.path.join(EV, "night89_judge_%03d.txt" % start)
    if not os.path.exists(src):
        print("[FAIL] no judge input: %s" % src)
        sys.exit(2)
    cands = json.load(open(os.path.join(EV, "night89_candidates.json"),
                           encoding="utf-8"))["candidates"]
    by_rank = {c["rank"]: c for c in cands}
    decisions = []
    problems = []
    seen = set()
    cat_n = {}
    n_in = n_out = 0
    for raw in open(src, encoding="utf-8").read().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 7:
            problems.append("列数!=7: %s" % line[:70])
            continue
        rank_s, word, v, cat, reading, meaning, note = (p.strip() for p in parts)
        rank = int(rank_s)
        c = by_rank.get(rank)
        if c is None or c["word"] != word:
            problems.append("rank/word 不一致: %s" % line[:70])
            continue
        if rank in seen:
            problems.append("rank 重複: %d" % rank)
            continue
        seen.add(rank)
        note = note.strip()
        if v == "I":
            if cat not in CATS:
                problems.append("bad cat: %s" % line[:70])
                continue
            if not reading or not meaning:
                problems.append("include 缺 reading/meaning: %s" % line[:70])
                continue
            if note.startswith("DE:"):
                dict_ev = note[3:].strip()
                de_src = "manual"
            else:
                dict_ev = auto_dict_evidence(rank, word)
                de_src = "auto"
            if not dict_ev:
                problems.append("dict_evidence 無（自動抽出不可・DE: 必要）: %d %s" % (rank, word))
                continue
            dict_ev = ("weblio " + dict_ev + "（cand_%03d_%s.txt）" % (rank, safe_name(word)))
            if note.startswith("CE:"):
                corpus_ev = note[3:].strip()
                ce_src = "manual"
            else:
                if c.get("freq_kakikudashi", 0) == 0:
                    problems.append("k=0 は CE: 手差し必須: %d %s" % (rank, word))
                    continue
                corpus_ev = auto_corpus_evidence(c)
                ce_src = "auto"
            decisions.append({"word": word, "rank": rank, "freq": c["freq"],
                              "verdict": "include", "cat": cat,
                              "reading": reading, "meaning": meaning,
                              "dict_evidence": dict_ev, "corpus_evidence": corpus_ev})
            n_in += 1
            cat_n[cat] = cat_n.get(cat, 0) + 1
            print("[I] %d %s %s %s (dict=%s corpus=%s)" % (rank, word, cat, reading, de_src, ce_src))
        elif v == "X":
            if not note:
                problems.append("exclude 缺 reason: %s" % line[:70])
                continue
            decisions.append({"word": word, "rank": rank, "freq": c["freq"],
                              "verdict": "exclude", "exclude_reason": note})
            n_out += 1
            print("[X] %d %s %s" % (rank, word, note[:60]))
        else:
            problems.append("bad verdict %r: %s" % (v, line[:70]))
    if problems:
        print("\n[FAIL] %d problems:" % len(problems))
        for q in problems[:20]:
            print("  - %s" % q)
        sys.exit(2)
    note = ("N89 batch rank %d-%d: %d in (noun %d/proper %d/verb %d/modifier %d/function %d) / %d out"
            % (start, start + len(decisions) - 1, n_in,
               cat_n.get("noun", 0), cat_n.get("proper", 0), cat_n.get("verb", 0),
               cat_n.get("modifier", 0), cat_n.get("function", 0), n_out))
    out = {"start": start, "note": note, "decisions": decisions}
    dst = os.path.join(EV, "night89_decisions_%03d.json" % start)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n%s\nwritten: %s (decisions=%d)" % (note, dst, len(decisions)))


if __name__ == "__main__":
    main()
