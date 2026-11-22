# -*- coding: utf-8 -*-
"""night74_digest2.py — N74 緊湊 digest：キャッシュから定義本体だけを抜く。

各行のナビ/ボイラープレートを除去し、条目あたり先頭 KEEP 行だけ残す。
用法: python -I tools/night74_digest2.py <start> <end> [keep_lines(既定35)]
出力: eval/night74_dict_cache/cdigest_<start>_<end>.txt
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "eval", "night74_dict_cache")
AUDIT = os.path.join(ROOT, "eval", "night74_lexicon_audit.json")

NAV = re.compile(
    r"^(索引トップ|用語の索引|凡例|を調べる|と一致する|で始まる|を含む|で終わる|を解説文に含む|"
    r"Weblio 辞書|ヘルプ|無料の翻訳|初めての方へ|ログイン|古語辞典|その他の辞書▼|フランス語辞典|"
    r"インドネシア語辞典|タイ語辞典|ベトナム語辞典|556の専門辞書|英和和英テキスト翻訳|英語⇒日本語|"
    r"日本語⇒英語|>>.*|>> |を含む用語の索引|のページへのリンク|を含む「.*」|カテゴリ|Weblio日本語例文用例辞書"
    r"|日本語活用形辞書|文語活用形辞書|隠語大辞典|ウィキペディア|Wiktionary日本語版|品詞の分類|※この「"
    r"|ウィクショナリー|出典: フリー百科事典|出典:『Wiktionary』|出典：漢字辞典|出典：Wiktionary|"
    r"発音\(\?\)|音読み|訓読み|呉音|漢音|慣用音|表外|常用漢字表内|常用漢字表外)$"
)


def main():
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    keep = int(sys.argv[3]) if len(sys.argv) > 3 else 35
    audit = json.load(open(AUDIT, encoding="utf-8"))
    entries = {e["idx"]: e for e in audit["entries"]}
    out = []
    for i in range(start, min(end, 500)):
        p = os.path.join(CACHE, "%03d.txt" % i)
        e = entries[i]
        meta = "===== idx %d | %s | %s | %s | kind=%s | bun=%d kkd=%d" % (
            e["idx"], e["word"], e["reading"], e["meaning"], e["kind"] or "-",
            e["bun_doc_hits"], e["kkd_doc_hits"])
        if not os.path.exists(p):
            out.append(meta + "\n-- CACHE MISSING --")
            continue
        with open(p, "r", encoding="utf-8") as f:
            raw = f.read().splitlines()
        lines = []
        for ln in raw[4:]:  # 先頭3行は #URL/#word/#status
            ln = ln.strip()
            if not ln:
                continue
            if NAV.match(ln):
                continue
            lines.append(ln)
        out.append(meta + "\n" + "\n".join(lines[:keep]))
    name = "cdigest_%03d_%03d.txt" % (start, min(end, 500) - 1)
    with open(os.path.join(CACHE, name), "w", encoding="utf-8") as f:
        f.write("\n\n".join(out))
    print("written", name)


if __name__ == "__main__":
    main()
