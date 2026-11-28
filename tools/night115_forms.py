# -*- coding: utf-8 -*-
"""night115_forms.py — Night 115 ③：夹注形态分类（实测为准・禁臆造形态）。

扫描面＝night111_results_8165.json 全行白文（corpus 実体）。探索扫描（eval/night115_forms_probe.txt）
先行的実測骨架を assert 化したもの。形态は实测に現れたものだけ列挙（割注・傍注・ASCII 括号・
嵌套・整行注记は実測 0＝設計に書かない）。

输出 eval/night115_forms.json + .txt。
用法: python -I tools/night115_forms.py
"""
import collections
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")

SPAN = re.compile(r"（([^（）]*)）")
KANA = "\u3041\u309f"  # ぁ-ゖ range marker (documented; real test below)


def has_kana(s):
    return any("\u3041" <= c <= "\u30ff" for c in s)


lines = []
FAIL = []


def pr(s=""):
    lines.append(s)
    print(s, flush=True)


def gate(cond, msg):
    if not cond:
        pr("[FAIL] %s → 停下报数" % msg)
        board["verdict"] = "FAIL"
        write_out()
        sys.exit(2)


def write_out():
    try:
        open(os.path.join(EV, "night115_forms.txt"), "w", encoding="utf-8",
             newline="\n").write("\n".join(lines) + "\n")
    except Exception:
        pass


board = {}


def main():
    t_start = time.time()
    board = {"script": "tools/night115_forms.py", "night": 115,
             "mode": "夹注形态分类（corpus 実測・未実測形態不記載）", "verdict": None}
    doc = json.load(open(os.path.join(EV, "night111_results_8165.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    gate(len(rows) == 8165, "行数 %d != 8165" % len(rows))
    from backend.main import detect_text_type, _ruby_tail_kanbun
    cls = {}
    for r in rows:
        raw = r["hakubun"] or ""
        if detect_text_type(raw) == "kana":
            t = _ruby_tail_kanbun(raw)
            cls[r["id"]] = "no_tail" if not t else ("echo" if len(t) <= 8 else "rerun")
        else:
            cls[r["id"]] = "engine"

    got = {r["id"]: re.sub(r"\s+", "", r["udkundoku_kakikudashi"] or "") for r in rows}
    hb = {r["id"]: (r["hakubun"] or "") for r in rows}

    # ---- 実測 0 を assert（未実測形態は設計に書かない根拠）----
    n_nokana_span = n_empty = n_ascii = n_whole = n_nested = 0
    n_unbalanced = 0
    for r in rows:
        s = hb[r["id"]]
        spans = SPAN.findall(s)
        if "（" in s:
            if not any(has_kana(sp) for sp in spans):
                n_nokana_span += 1
            if any(sp == "" for sp in spans):
                n_empty += 1
            if s.count("（") != s.count("）"):
                n_unbalanced += 1
        if "(" in s or ")" in s:
            n_ascii += 1
        if re.fullmatch(r"\s*（[^（）]*）\s*", s):
            n_whole += 1
        if "（（" in s or "））" in s:
            n_nested += 1
    pr("== 未実測形態 assert（corpus 8165 全行）==")
    pr("  （…）無仮名 span 行 %d・空 （） 行 %d・括号不釣合 行 %d・ASCII 括号 行 %d・"
       "整行=（…） 行 %d・嵌套 行 %d" % (n_nokana_span, n_empty, n_unbalanced,
                                        n_ascii, n_whole, n_nested))
    gate(n_nokana_span == 0 and n_empty == 0 and n_unbalanced == 0
         and n_ascii == 0 and n_whole == 0 and n_nested == 0,
         "実測 0 のはずの形態が 0 でない（分類前提崩れ）→ 停下报数")

    # ---- 形態 1：字級 ruby 夹注（漢字＋（読み仮名） juxtaposed）----
    pr("")
    pr("== 形態 1：ruby 夹注（漢字（読み仮名）交织形）==")
    f1_rows = [r["id"] for r in rows if has_kana(hb[r["id"]])
               and SPAN.search(hb[r["id"]]) and "（" in hb[r["id"]]]
    # 全（…）span が仮名含む行（＝形态 1 の純粋定義）
    f1_pure = []
    for r in rows:
        s = hb[r["id"]]
        if "（" not in s:
            continue
        spans = SPAN.findall(s)
        if spans and all(has_kana(sp) for sp in spans):
            f1_pure.append(r["id"])
    pr("  行数 %d（白文含（ 行と一致）・純粋定義（全 span 仮名含）%d 行"
       % (len(f1_rows), len(f1_pure)))
    gate(len(f1_rows) == 251 and len(f1_pure) == 251,
         "形态 1 行数 %d/%d != 251/251" % (len(f1_rows), len(f1_pure)))
    by_cls = collections.Counter(cls[i] for i in f1_rows)
    pr("  分類別内訳 %s" % dict(by_cls))
    # span 統計：直前字符（字級接続の証拠）・span 長
    n_span = n_after_kanji = 0
    span_len = collections.Counter()
    for i in f1_rows:
        s = hb[i]
        for m in SPAN.finditer(s):
            n_span += 1
            span_len[len(m.group(1))] += 1
            if m.start() > 0:
                prev = s[m.start() - 1]
                if "\u4e00" <= prev <= "\u9fff" or prev in "𠮷𡈽畵":
                    n_after_kanji += 1
    pr("  span 総数 %d・直前が漢字 %d（%.1f%%）・span 内容長 min %d/max %d"
       % (n_span, n_after_kanji, 100.0 * n_after_kanji / n_span,
          min(span_len), max(span_len)))
    multi_char_span = sum(v for k, v in span_len.items() if k > 3)
    pr("  span 内容長 >3 字（語注級）%d / %d" % (multi_char_span, n_span))
    board["form1"] = {"rows": len(f1_rows), "by_cls": dict(by_cls),
                      "spans": n_span, "after_kanji": n_after_kanji,
                      "span_len_max": max(span_len), "span_len_min": min(span_len)}

    # ---- 形態 2：rongo「N）」编号（dangling ）無（・非注记）----
    pr("")
    pr("== 形態 2：rongo「N）」编号（dangling ）・非注记＝剥対象外）==")
    f2_rows = [r["id"] for r in rows
               if "）" in hb[r["id"]] and "（" not in hb[r["id"]]]
    pr("  行数 %d・例行 %s" % (len(f2_rows), f2_rows))
    for i in f2_rows[:2]:
        pr("    例 %s hb %s" % (i, hb[i][:60]))
    gate(len(f2_rows) == 6, "形态 2 行数 %d != 6" % len(f2_rows))
    board["form2"] = {"rows": len(f2_rows), "ids": f2_rows}

    # ---- 形態 3：括号外混在（sonshi09-38 型・漢文＋書き下し＋現代語注记）----
    pr("")
    pr("== 形態 3：括号外混在行（sonshi09-38 型＝注记が括号外・剥夹注で救えない）==")
    son = [r for r in rows if r["id"] == "sonshi09-38"][0]
    s = son["hakubun"]
    last = s.rsplit("）", 1)[1] if "）" in s else ""
    tail_has_kana = has_kana(last)
    pr("  行 1（sonshi09-38）cls=%s・最後の） 後尾段仮名含 %s（＝no_tail の機構的理由）"
       % (cls["sonshi09-38"], tail_has_kana))
    gate(cls["sonshi09-38"] == "no_tail" and tail_has_kana,
         "sonshi09-38 状態変化（cls/tail）→ 停下报数")
    pr("  白文（头 120 字）%s" % s[:120])
    board["form3"] = {"rows": 1, "ids": ["sonshi09-38"], "tail_has_kana": tail_has_kana}

    # ---- got 側実測：引擎加工残渣（原样 echo ではない）----
    pr("")
    pr("== got 側：引擎加工残渣（送り仮名/助词が注记括号内に插入）==")
    got_span_rows = [i for i in f1_rows if SPAN.search(got[i])]
    pr("  got に（…）span が残る行 %d（=B9 残渣 2 行）" % len(got_span_rows))
    gate(len(got_span_rows) == 2, "got span 行数 %d != 2" % len(got_span_rows))
    verbatim = []
    for i in got_span_rows:
        hb_spans = set(SPAN.findall(hb[i]))
        got_spans = set(SPAN.findall(got[i]))
        verbatim_spans = [sp for sp in got_spans if sp in hb_spans]
        inserted = [sp for sp in got_spans if sp not in hb_spans]
        pr("  %s: got span %d 中白文原样 %d・引擎加工（挿入/変形）%d"
           % (i, len(got_spans), len(verbatim_spans), len(inserted)))
        for sp in sorted(inserted):
            pr("    加工 span %r（白文に無い＝okurigana 等の插入）" % sp)
        verbatim.append({"id": i, "got_spans": len(got_spans),
                         "verbatim": len(verbatim_spans),
                         "engine_processed": len(inserted)})
    board["got_residue"] = verbatim

    # ---- 分類サマリ ----
    pr("")
    pr("== 形態分類サマリ（実測のみ）==")
    pr("  形態 1 ruby 夹注（漢字（読み仮名））251 行 → 剥対象（Stage 1）・分類別 echo30/rerun218/engine2/no_tail1")
    pr("  形態 2 rongo「N）」编号 6 行 → 剥対象外（dangling・regex 不一致で自然保存）")
    pr("  形態 3 括号外混在（sonshi09-38 型）1 行 → 管線外（注记が括号外＝剥夹注で救えない・no_tail 維持）")
    pr("  got 側：引擎加工残渣 2 行（原样 echo ではなく送り仮名插入型）")
    pr("  未実測（0 行＝設計不記載）：割注・傍注・無仮名（…）・空（）・不釣合括号・ASCII・嵌套・整行注记")
    board["elapsed_sec"] = round(time.time() - t_start)
    board["verdict"] = "PASS"
    json.dump(board, open(os.path.join(EV, "night115_forms.json"), "w",
                          encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    open(os.path.join(EV, "night115_forms.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")
    pr("")
    pr("written: eval/night115_forms.json / night115_forms.txt")
    pr("elapsed %.0fs" % board["elapsed_sec"])


if __name__ == "__main__":
    main()
