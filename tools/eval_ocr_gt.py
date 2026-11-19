# -*- coding: utf-8 -*-
"""eval_ocr_gt.py — 用人工 GT 算 OCR 行级 CER（NIGHT36）。

GT: eval/ocr_gt_100.tsv（file, line_no, gt；gt 中 [?] 为不可辨字符，按通配计）
OCR: eval/night36_ocr_lines.json（night36_ocr_run.py 产出，行号口径=boxes.json canonical）
对齐: 按 file 分组；GT 行的 line_no 直接对应 OCR 行号；对 781193 这类碎框页，
  另按 x 中心聚类拼接 OCR 行后再做行内匹配（rep line_no 标注的 GT 与其所在列比对）。
CER: 编辑距离/GT长度；GT 中 [?] 与任何字符匹配代价 0、删除代价 0，且不计入分母。
产出: 控制台摘要 + eval/night36_cer.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_TSV = os.path.join(ROOT, "eval", "ocr_gt_100.tsv")
OCR_JSON = os.path.join(ROOT, "eval", "night36_ocr_lines.json")
BOX_DIR = os.path.join(ROOT, "eval", "ocr_samples", "gt36")
OUT = os.path.join(ROOT, "eval", "night36_cer.json")


def parse_gt(s):
    """拆 token：'[?]' 单 token，其余按字符。"""
    toks, i = [], 0
    while i < len(s):
        if s.startswith("[?]", i):
            toks.append("[?]")
            i += 3
        else:
            toks.append(s[i])
            i += 1
    return toks


def cer(gt, ocr):
    """(distance, denom)；[?] 通配。经典 DP。"""
    g, r = parse_gt(gt), list(ocr or "")
    n, m = len(g), len(r)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i if g[i - 1] != "[?" else 0] + [0] * m
        for j in range(1, m + 1):
            wild = g[i - 1] == "[?]"
            sub = prev[j - 1] + (0 if wild or g[i - 1] == r[j - 1] else 1)
            dele = prev[j] + (0 if wild else 1)      # GT 删（wild 免费）
            ins = cur[j - 1] + 1                     # OCR 多字
            cur[j] = min(sub, dele, ins)
        prev = cur
    denom = sum(1 for t in g if t != "[?]")
    return prev[m], denom


def cer_substring(gt, ocr):
    """GT 作为 OCR 的带编辑子串对齐：OCR 前后缀跳过免费（共享列：一条列文本含多条目）。
    返回 (dist, denom)，[?] 通配同 cer()。"""
    g, r = parse_gt(gt), list(ocr or "")
    n, m = len(g), len(r)
    prev = [0] * (m + 1)          # dp[0][j]=0：OCR 前缀免费跳
    for i in range(1, n + 1):
        cur = [prev[0] + (0 if g[i - 1] == "[?" else 1)] + [0] * m
        for j in range(1, m + 1):
            wild = g[i - 1] == "[?]"
            sub = prev[j - 1] + (0 if wild or g[i - 1] == r[j - 1] else 1)
            dele = prev[j] + (0 if wild else 1)
            ins = cur[j - 1] + 1
            cur[j] = min(sub, dele, ins)
        prev = cur
    denom = sum(1 for t in g if t != "[?]")
    return min(prev), denom


PUNCT = set("。、｡，．・「」『』（）○◎…'\"")


def strip_punct(s):
    """去标点（两侧同口径）；[?] 段保护，不拆散通配标记。"""
    out, i = [], 0
    while i < len(s):
        if s.startswith("[?]", i):
            out.append("[?]")
            i += 3
        else:
            if s[i] not in PUNCT:
                out.append(s[i])
            i += 1
    return "".join(out)


def cluster_ocr(lines, gap=14):
    """OCR 行按 x 中心聚类（右→左，gap 同 night36_xcols.py=14）。
    干净页：每簇=1 行；碎框页：一列的碎片并入同簇。列内按 y 升序拼接。"""
    cols = []
    for l in sorted(lines, key=lambda l: -(l["x"] + l["w"] / 2.0)):
        cx = l["x"] + l["w"] / 2.0
        if cols and abs(cx - cols[-1]["cx_last"]) < gap:
            cols[-1]["members"].append(l)
            cols[-1]["cx_last"] = cx
        else:
            cols.append({"cx_last": cx, "members": [l]})
    for c in cols:
        c["members"].sort(key=lambda l: l["y"])
        c["text"] = "".join(l["text"] for l in c["members"])
        c["x0"] = min(l["x"] for l in c["members"])
        c["x1"] = max(l["x"] + l["w"] for l in c["members"])
        c["y0"] = min(l["y"] for l in c["members"])
        c["y1"] = max(l["y"] + l["h"] for l in c["members"])
        c["cx"] = sum(l["x"] + l["w"] / 2.0 for l in c["members"]) / len(c["members"])
    return cols


def main():
    gt_rows = []
    with open(GT_TSV, encoding="utf-8") as f:
        header = f.readline()
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            file_, line_no, gt = line.split("\t", 2)
            gt_rows.append({"file": file_, "line_no": int(line_no), "gt": gt})

    ocr_path = sys.argv[1] if len(sys.argv) > 1 else OCR_JSON
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT
    with open(ocr_path, encoding="utf-8") as f:
        ocr = json.load(f)
    ocr_by_file = {r["file"].rsplit(".", 1)[0]: r for r in ocr["results"]}

    out_rows = []
    from collections import Counter
    key_counts = Counter((r["file"], r["line_no"]) for r in gt_rows)
    shared_keys = key_counts
    for row in gt_rows:
        res = ocr_by_file.get(row["file"])
        if res is None:
            out_rows.append({**row, "ocr": None, "dist": None, "denom": None, "cer": None,
                             "match": "no-ocr", "shared": False})
            continue
        # 统一口径：GT line_no → boxes.json 该框 → 先按 y 带相交过滤 OCR 行
        #（防不同 y 带的小注行混入聚类），再按 x 簇（gap=14）取整列拼接。
        box = None
        bpath = os.path.join(BOX_DIR, row["file"].rsplit(".", 1)[0], "boxes.json")
        if os.path.exists(bpath):
            with open(bpath, encoding="utf-8") as f:
                bb = json.load(f)
            box = next((l for l in bb["lines"] if l["line_no"] == row["line_no"]), None)
        ocr_text, match = None, "unmatched"
        if box is not None:
            def y_overlap(l):
                return l["y"] < box["y"] + box["h"] + 8 and l["y"] + l["h"] > box["y"] - 8
            band = [l for l in res["lines"] if y_overlap(l)]
            cols = cluster_ocr(band or res["lines"])
            bcx = box["x"] + box["w"] / 2.0
            xcols = [c for c in cols if c["x0"] - 6 <= bcx <= c["x1"] + 6]
            if not xcols:  # 簇间隙边界兜底：取最近的簇
                xcols = [min(cols, key=lambda c: abs(c["cx"] - bcx))]
            col = max(xcols, key=lambda c: len(c["text"]))
            ocr_text = col["text"]
            match = "xcluster" if len(col["members"]) > 1 else "line_no"
        else:
            direct = [l for l in res["lines"] if l["line_no"] == row["line_no"]]
            if direct:
                ocr_text = "".join(l["text"] for l in direct)
                match = "line_no-fallback"
        if ocr_text is None:
            out_rows.append({**row, "ocr": None, "dist": None, "denom": None, "cer": None,
                             "match": match, "shared": False})
            continue
        shared = shared_keys.get((row["file"], row["line_no"]), 1) > 1
        fn = cer_substring if shared else cer
        d, denom = fn(row["gt"], ocr_text)
        gt_n, ocr_n = strip_punct(row["gt"]), strip_punct(ocr_text)
        dn, denom_n = fn(gt_n, ocr_n)
        out_rows.append({**row, "ocr": ocr_text, "dist": d, "denom": denom,
                         "cer": round(d / denom, 4) if denom else None,
                         "dist_norm": dn, "denom_norm": denom_n,
                         "cer_norm": round(dn / denom_n, 4) if denom_n else None,
                         "match": match, "shared": shared})

    # 汇总（raw=含标点差异；norm=两侧去标点。[?] 通配不计分母）
    pages = {}
    for r in out_rows:
        pages.setdefault(r["file"], []).append(r)
    summary = {"n_gt_rows": len(out_rows), "pages": {}}
    tot = {"d": 0, "n": 0, "dn": 0, "nn": 0}
    for fname, rows in sorted(pages.items()):
        d = sum(r["dist"] or 0 for r in rows)
        n = sum(r["denom"] or 0 for r in rows)
        dn = sum(r["dist_norm"] or 0 for r in rows)
        nn = sum(r["denom_norm"] or 0 for r in rows)
        tot["d"] += d; tot["n"] += n; tot["dn"] += dn; tot["nn"] += nn
        summary["pages"][fname] = {
            "n_rows": len(rows),
            "cer_macro": round(sum(r["cer"] or 0 for r in rows) / len(rows), 4),
            "cer_micro": round(d / n, 4) if n else None,
            "cer_norm_macro": round(sum(r["cer_norm"] or 0 for r in rows) / len(rows), 4),
            "cer_norm_micro": round(dn / nn, 4) if nn else None,
        }
    summary["overall_cer_micro"] = round(tot["d"] / tot["n"], 4) if tot["n"] else None
    summary["overall_cer_macro"] = round(
        sum(v["cer_macro"] for v in summary["pages"].values()) / len(summary["pages"]), 4)
    summary["overall_cer_norm_micro"] = round(tot["dn"] / tot["nn"], 4) if tot["nn"] else None
    summary["overall_cer_norm_macro"] = round(
        sum(v["cer_norm_macro"] for v in summary["pages"].values()) / len(summary["pages"]), 4)
    summary["rows"] = out_rows

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("== Night36 OCR CER ==")
    print("GT rows: %d | [?] 通配不计分母 | raw=含标点差 / norm=两侧去标点 | src=%s" % (
        len(out_rows), os.path.basename(ocr_path)))
    for fname, v in summary["pages"].items():
        print("  %-28s rows=%-3d raw micro=%s macro=%s | norm micro=%s macro=%s" % (
            fname, v["n_rows"], v["cer_micro"], v["cer_macro"],
            v["cer_norm_micro"], v["cer_norm_macro"]))
    print("overall: raw micro=%s macro=%s | norm micro=%s macro=%s" % (
        summary["overall_cer_micro"], summary["overall_cer_macro"],
        summary["overall_cer_norm_micro"], summary["overall_cer_norm_macro"]))
    nomatch = [r for r in out_rows if r["ocr"] is None]
    if nomatch:
        print("[warn] unmatched rows: %d" % len(nomatch))
        for r in nomatch:
            print("   ", r["file"], r["line_no"], r["match"])
    print("[done] written:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
