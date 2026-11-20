# -*- coding: utf-8 -*-
"""night59_scan.py — N59 第二步：全库扫描。

  A. golden_3000 全部 hakubun 过原生 MeCab：枚举 xpos 以 v,助動詞 开头的 token，
     按 (lemma, xpos) 对照 udkundoku AUX 表键 → 哪些 lemma 缺条目（潜在 KeyError）
  B. 含「應」的行清单（hakubun/expected/got 三侧计数 + toushisen135-12 全行）
  C. hakubun 里含 SHINJITAI_MAP 旧形字的行数盘点（这些行目前全部可解析）
输出 eval/night59_scan.json + txt。只读诊断。
"""
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)

from tools.mecab_shim import tagger  # noqa: E402
import importlib  # noqa: E402
from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402
import udkundoku  # noqa: E402

aux_mod = importlib.import_module("udkundoku.auxiliary")
AUX = aux_mod.AUX


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    golden = json.load(io.open(os.path.join(EV, "golden_3000.json"), encoding="utf-8"))
    results = json.load(io.open(os.path.join(EV, "night58_results_3000.json"),
                                encoding="utf-8"))["results"]
    got_by_id = {r["id"]: r.get("udkundoku_kakikudashi") for r in results}
    err_ids = [r["id"] for r in results if r.get("udkundoku_kakikudashi") is None]
    lines = []
    out = lambda s="": (lines.append(s), print(s, flush=True))

    out("golden_3000 %d 条 | engine error %d: %s" % (len(golden), len(err_ids), err_ids))

    # ---- A. 全部 hakubun 过 MeCab，枚举助動詞 token ----
    aux_tokens = collections.Counter()          # (lemma, xpos) -> 行数
    aux_missing = collections.Counter()         # AUX 表缺的 (lemma, xpos)
    rows_with_auxtok = 0
    seen_ids = []
    for g in golden:
        hb = g["hakubun"]
        hit_here = False
        node = tagger.parseToNode(hb)
        while node:
            feat = node.feature
            if feat.startswith("v,助動詞"):
                xpos = ",".join(feat.split(",")[:4]) if False else None
                # xpos 取前 4 段（udkanbun 的 xpos 形如 v,助動詞,必要,*）
                parts = feat.split(",")
                xpos = ",".join(parts[:4])
                lemma = node.surface  # 暂用 surface，udkanbun 的 lemma 由表给出
                hit_here = True
            node = node.next
        if hit_here:
            rows_with_auxtok += 1
    out("\n=== A. hakubun 含 v,助動詞 token 的行数: %d ===" % rows_with_auxtok)

    # 更精确：用 udkanbun 引擎逐条解析太慢；改用 MeCab surface+lemma 字段
    # （feature 第 7 段是 base，形如 應/应 —— udkanbun 的 lemma 取 / 前半）
    aux_pair_rows = collections.defaultdict(list)   # (lemma4, xpos4) -> [ids]
    for g in golden:
        hb = g["hakubun"]
        node = tagger.parseToNode(hb)
        while node:
            feat = node.feature
            if feat.startswith("v,助動詞"):
                parts = feat.split(",")
                xpos4 = ",".join(parts[:4])
                base = parts[6] if len(parts) > 6 else ""
                lemma = base.split("/")[0] if base else node.surface
                aux_pair_rows[(lemma, xpos4)].append(g["id"])
            node = node.next
    out("\n=== A2. 助動詞 (lemma, xpos) × 行数 × AUX 表有无 ===")
    missing_pairs = []
    for (lemma, xpos4), ids in sorted(aux_pair_rows.items(), key=lambda kv: -len(kv[1])):
        key = "%s,%s" % (lemma, xpos4)
        has = key in AUX
        out("  %-28s 行数 %4d  AUX %s" % (key, len(ids), "✅有" if has else "❌缺"))
        if not has:
            missing_pairs.append((key, len(ids), ids))
    out("\n缺条目的 (lemma,xpos): %s" % [m[0] for m in missing_pairs])
    for key, n, ids in missing_pairs:
        out("  %s 涉及 %d 行: %s%s" % (key, n, ids[:8], "…" if len(ids) > 8 else ""))

    # ---- B. 含「應」的行 ----
    out("\n=== B. 含「應」的行 ===")
    hb_rows = [g for g in golden if "應" in g["hakubun"]]
    exp_rows = [g for g in golden if "應" in g["expected_kakikudashi"]]
    got_rows = [g for g in golden if "應" in (got_by_id.get(g["id"]) or "")]
    out("  hakubun 含應: %d 行 | expected 含應: %d 行 | got 含應: %d 行"
        % (len(hb_rows), len(exp_rows), len(got_rows)))
    for g in hb_rows[:12]:
        out("  %s | hb=%s" % (g["id"], g["hakubun"][:40]))
    row = next((r for r in results if r["id"] == "toushisen135-12"), None)
    if row:
        out("  toushisen135-12: hb=%r" % row["hakubun"])
        out("  expected=%r" % row["expected_kakikudashi"])
        out("  got=%r (error)" % row.get("udkundoku_kakikudashi"))

    # ---- C. hakubun 含舊形字的行数盘点 ----
    out("\n=== C. hakubun 含 SHINJITAI_MAP 旧形字的行数（top 20）===")
    cnt = collections.Counter()
    rows_hit = collections.defaultdict(int)
    for g in golden:
        olds = [o for o in SHINJITAI_MAP if o in g["hakubun"]]
        for o in olds:
            cnt[o] += 1
            rows_hit[o] += 1
    for o, n in cnt.most_common(20):
        out("  %s→%s  %4d 行" % (o, SHINJITAI_MAP[o], n))
    total_rows_old = len([g for g in golden
                          if any(o in g["hakubun"] for o in SHINJITAI_MAP)])
    out("  合计至少含 1 个旧形字的行: %d / %d" % (total_rows_old, len(golden)))

    out_json = {
        "n_golden": len(golden),
        "error_ids": err_ids,
        "aux_pairs": {"%s,%s" % k: {"rows": len(v), "in_AUX": ("%s,%s" % k) in AUX}
                      for k, v in aux_pair_rows.items()},
        "missing_aux_pairs": [{"key": key, "rows": n, "ids": ids[:30]}
                              for key, n, ids in missing_pairs],
        "ying_rows": {"hakubun": len(hb_rows), "expected": len(exp_rows),
                      "got": len(got_rows),
                      "hakubun_ids": [g["id"] for g in hb_rows][:40]},
        "shinjitai_rows": {o: n for o, n in cnt.most_common()},
        "rows_with_old_form_any": total_rows_old,
    }
    json.dump(out_json, open(os.path.join(EV, "night59_scan.json"), "w",
                             encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    io.open(os.path.join(EV, "night59_scan.txt"), "w", encoding="utf-8",
            newline="\n").write("\n".join(lines) + "\n")
    out("\nwritten: eval/night59_scan.json / night59_scan.txt")


if __name__ == "__main__":
    main()
