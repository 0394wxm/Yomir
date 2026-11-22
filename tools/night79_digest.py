# -*- coding: utf-8 -*-
"""night79_digest.py — N79 ③ 研究用 compact digest（人読用）。

eval/night79_dict_cache/cand_<rank3>_*.txt（night79_weblio.py の産物）から、
1 語あたり「辞書名行＋条目区の先頭 ~12 行（最大 700 字）」を切り出し、
eval/night79_digest_<start>.txt にまとめる。未取得の語は語料サンプルのみ表示。
判定（読み/意味/採録 or 排除）はこの digest を人が読んで別ファイルに書く。

用法: python -I tools/night79_digest.py <start_rank> [count]
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")
CACHE = os.path.join(EV, "night79_dict_cache")

DICTNAMES = (
    "デジタル大辞泉", "精選版 日本国語大辞典", "古語辞典", "日本語古語辞典",
    "Weblio古語辞典", "故事ことわざの辞典", "Wiktionary日本語版",
    "日本語WordNet", "ウィキペディア小見出し辞書",
    "Weblio日本語例文用例辞書", "故事ことわざ辞典",
)
MAX_LINES = 40
MAX_CHARS = 1400


def cand_path(rank, word):
    safe = "".join(ch if ch.isascii() or ch.isalnum() else "_" for ch in word)[:24]
    return os.path.join(CACHE, "cand_%03d_%s.txt" % (rank, safe or "noname"))


def compact(rank, word):
    """(status, digest_lines)。面包屑「Weblio 辞書 >」から辞書条目区を切る。

    ページ構造（実測）: メニュー→「Weblio 辞書 >」パンくず→各辞書セクション
    （デジタル大辞泉／文語活用形辞書 等）→ Weblio日本語例文用例辞書（機械例文）。
    機械例文区と索引ノイズ行は落とし、条目本体（見出し【…】＋読み方＋定義）を出す。
    """
    path = cand_path(rank, word)
    if not os.path.exists(path):
        return "NOCACHE", []
    lines = open(path, "r", encoding="utf-8").read().splitlines()
    status = ""
    for ln in lines[:5]:
        if ln.startswith("# status"):
            parts = ln.split(None, 2)
            status = parts[2] if len(parts) > 2 else ""
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("Weblio 辞書 >"):
            start = i
            break
    if start is None:
        return status or "EMPTY", []
    junk_prefixes = (
        "索引トップ", "用語の索引", "ランキング", "凡例", "カテゴリー",
        "出典:", "この記事で示されている", "ご存知の方は", "関連することわざ",
        "関連する慣用句", "関連する英語表現", "カテゴリー", "» ", "お問い合わせ",
    )
    out = []
    total = 0
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            continue
        low = s.lower()
        if s.startswith("Weblio日本語例文用例辞書") or low.startswith("英和和英テキスト翻訳"):
            break
        if s.startswith(">> 「") or s.startswith(">>"):
            break
        if any(s.startswith(j) for j in junk_prefixes):
            continue
        out.append(s)
        total += len(s)
        if total >= MAX_CHARS or len(out) >= MAX_LINES:
            break
    return status, out


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    cands = json.load(open(os.path.join(EV, "night79_candidates.json"),
                           encoding="utf-8"))["candidates"]
    batch = cands[start:start + count]
    out = ["# night79 digest rank %d..%d (count=%d)" % (start, start + len(batch) - 1, len(batch))]
    n_cached = 0
    for j, c in enumerate(batch):
        rank = start + j
        w = c["word"]
        smp = "; ".join(s.get("snippet", "")[:46] for s in c.get("samples", [])[:2])
        status, rows = compact(rank, w)
        if status not in ("NOCACHE", "EMPTY"):
            n_cached += 1
        out.append("")
        out.append("=== [%d] %s  freq=%d h=%s k=%s len=%d status=%s"
                   % (rank, w, c.get("freq", 0), c.get("freq_hakubun"),
                      c.get("freq_kakikudashi"), c.get("len"), status))
        if smp:
            out.append("corpus: %s" % smp)
        for r in rows:
            out.append("  | %s" % r)
        if status == "NOCACHE":
            out.append("  (no weblio cache)")
        elif not rows:
            out.append("  (no dictionary region found)")
    path = os.path.join(EV, "night79_digest_%03d.txt" % start)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("digest %d..%d written: %s (cached=%d)" % (start, start + len(batch) - 1, path, n_cached),
          flush=True)


if __name__ == "__main__":
    main()
