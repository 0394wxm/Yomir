# -*- coding: utf-8 -*-
"""night37_classify.py — OCR 错因分类（NIGHT37，只诊断，不改任何引擎代码）。

输入: eval/night36_cer.json（92 行 GT/OCR/dist + shared/match 标记）
方法: norm 口径（两侧去标点）DP 对齐 + 回溯，把每个编辑操作归入一类：
  A_标点     — raw-norm 的差（OCR 读出的圈点句读；GT 口径本就不收）
  B_汉字混淆 — 汉字↔汉字 替换（含同旁/近似）
  C_旧字体   — 旧字体→新字体（码位级简繁/异体）替换表命中
  D_假名     — 假名↔假名 或 汉字↔假名 的替换/插删
  E_结构     — 界框垃圾（「一」串等 junk 框产物）、碎框错切、共享列串扰、漏列
  F_不可读   — OCR 输出 □（recognizer 无法辨认，如手写/印章）
  W_通配     — GT [?] 位置（不计分母，只计数）
产出: 控制台分布 + eval/night37_errors.json
"""
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_JSON = os.path.join(ROOT, "eval", "night36_cer.json")
OUT_JSON = os.path.join(ROOT, "eval", "night37_errors.json")

PUNCT = set("。、｡，．・「」『』（）()○◎…'\"")

# 旧字体→OCR 侧常见对应（码位级，C 类判定表；OCR 引擎倾向输出放宽/新字体形）
OLD2NEW = {
    "萬": "万", "國": "国", "來": "来", "眞": "真", "歲": "歳",
    "衞": "衛", "爲": "為", "內": "内", "雜": "雑", "團": "団",
    "樂": "楽", "彈": "弾", "當": "当", "條": "条", "廣": "広", "鐵": "鉄",
    "藝": "芸", "譯": "訳", "經": "経", "絕": "絶", "對": "対", "禮": "礼",
    "驛": "駅", "佛": "仏", "德": "徳", "隨": "随", "體": "体", "顏": "顔",
    "與": "与", "每": "毎", "强": "強", "旣": "既", "說": "説", "畫": "画",
    "晉": "晋", "徃": "往", "戲": "戯", "刋": "刊", "舖": "舗", "錢": "銭",
    "寇": "冦", "輒": "輙", "鄕": "郷", "鄉": "郷", "乘": "乗", "勸": "勧",
    "裏": "裡", "巻": "卷", "俎": "爼", "往": "徃", "旣": "\uFA42", "者": "\uFA5B",
}
# 观测到的码位变体对（GT 侧形, OCR 侧形）——证据来自本夜逐操作对齐
VARIANT_PAIRS = set((k, v) for k, v in OLD2NEW.items())


def strip_punct(s):
    out, i = [], 0
    while i < len(s):
        if s.startswith("[?]", i):
            out.append("[?]")
            i += 3
        else:
            if s[i] not in PUNCT:
                out.append(s[i])
            i += 1
        # no-op guard
    return "".join(out)


def parse_gt(s):
    toks, i = [], 0
    while i < len(s):
        if s.startswith("[?]", i):
            toks.append("[?]")
            i += 3
        else:
            toks.append(s[i])
            i += 1
    return toks


def is_kanji(ch):
    try:
        return "CJK" in unicodedata.name(ch, "")
    except Exception:
        return False


def align_ops(g, r):
    """norm 口径 DP 回溯，返回 ops 列表：
    ('=',gt,ocr) / ('sub',gt,ocr) / ('ins',ocr) / ('del',gt)。[?] 免费通配。
    back[i][j] 记「到达 (i,j) 的来源」：(kind, pi, pj)。"""
    n, m = len(g), len(r)
    INF = float("inf")
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for j in range(1, m + 1):
        dp[0][j] = j
        back[0][j] = ("ins", 0, j - 1)
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + (0 if g[i - 1] == "[?" else 1)
        back[i][0] = ("del", i - 1, 0)
        for j in range(1, m + 1):
            wild = g[i - 1] == "[?"
            c_sub = dp[i - 1][j - 1] + (0 if wild or g[i - 1] == r[j - 1] else 1)
            c_del = dp[i - 1][j] + (0 if wild else 1)
            c_ins = dp[i][j - 1] + 1
            best = min(c_sub, c_del, c_ins)
            dp[i][j] = best
            if best == c_sub:
                back[i][j] = ("sub", i - 1, j - 1)
            elif best == c_del:
                back[i][j] = ("del", i - 1, j)
            else:
                back[i][j] = ("ins", i, j - 1)
    ops = []
    i, j = n, m
    while (i, j) != (0, 0):
        kind, pi, pj = back[i][j]
        if kind == "sub":
            if g[pi] == "[?]" or g[pi] == r[pj]:
                ops.append(("=", g[pi], r[pj]))
            else:
                ops.append(("sub", g[pi], r[pj]))
        elif kind == "del":
            ops.append(("del", g[pi]))
        else:
            ops.append(("ins", r[pj]))
        i, j = pi, pj
    ops.reverse()
    return ops


def align_ops_sub(g, r):
    """共享列口径：GT 作为带编辑子串对齐（OCR 前后缀跳过免费）。
    返回 (ops, skips)；skips = 免费跳过的 OCR 字符数（邻条目/条目号）。"""
    n, m = len(g), len(r)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(1, m + 1):
        back[0][j] = ("skip", 0, j - 1)          # 免费 OCR 前缀
    for i in range(1, n + 1):
        wild = g[i - 1] == "[?"
        dp[i][0] = dp[i - 1][0] + (0 if wild else 1)
        back[i][0] = ("del", i - 1, 0)
        for j in range(1, m + 1):
            c_sub = dp[i - 1][j - 1] + (0 if wild or g[i - 1] == r[j - 1] else 1)
            c_del = dp[i - 1][j] + (0 if wild else 1)
            c_ins = dp[i][j - 1] + 1
            best = min(c_sub, c_del, c_ins)
            dp[i][j] = best
            if best == c_sub:
                back[i][j] = ("sub", i - 1, j - 1)
            elif best == c_del:
                back[i][j] = ("del", i - 1, j)
            else:
                back[i][j] = ("ins", i, j - 1)
    j_end = min(range(m + 1), key=lambda j: dp[n][j])
    ops, skips = [], 0
    i, j = n, j_end
    while (i, j) != (0, 0):
        kind, pi, pj = back[i][j]
        if kind == "skip":
            skips += 1
        elif kind == "sub":
            if g[pi] == "[?]" or g[pi] == r[pj]:
                ops.append(("=", g[pi], r[pj]))
            else:
                ops.append(("sub", g[pi], r[pj]))
        elif kind == "del":
            ops.append(("del", g[pi]))
        else:
            ops.append(("ins", r[pj]))
        i, j = pi, pj
    ops.reverse()
    return ops, skips


def classify_row(row):
    gt_n, ocr_n = strip_punct(row["gt"]), strip_punct(row["ocr"] or "")
    g, r = parse_gt(gt_n), list(ocr_n)
    cats = Counter()
    examples = defaultdict(list)

    def add(cat, gtch, och):
        cats[cat] += 1
        if len(examples[cat]) < 6:
            examples[cat].append("%s→%s" % (gtch if gtch is not None else "∅",
                                            och if och is not None else "∅"))

    if row["shared"]:
        # 共享列（一条 OCR 列文本对多条 GT 条目）：交叉对齐伪迹不作识别诊断，
        # 全部残余计入 E_结构（GT 覆盖缺口/条目号/邻条目串扰）。
        ops, skips = align_ops_sub(g, r)
        n_res = 0
        for op in ops:
            if op[0] == "=":
                if op[1] == "[?]":
                    cats["W_通配"] += 1
                continue
            n_res += 1
            if op[0] == "sub":
                add("E_结构", op[1], op[2])
            elif op[0] == "ins":
                add("E_结构", None, op[1])
            else:
                add("E_结构", op[1], None)
        if skips:
            cats["E_结构"] += skips
        examples.setdefault("E_结构", []).append("共享列残余×%d+跳过×%d" % (n_res, skips))
        return dict(cats), {k: v for k, v in examples.items()}
    ops = align_ops(g, r)

    for op in ops:
        kind = op[0]
        if kind == "=":
            if op[1] == "[?]":
                cats["W_通配"] += 1
            continue
        if kind == "sub":
            gtch, och = op[1], op[2]
        elif kind == "ins":
            gtch, och = None, op[1]
        else:
            gtch, och = op[1], None
        # 分类
        NUM_CHARS = set("一二三四五六七八九十廿百")
        if och == "□":
            add("F_不可读", gtch, och)
        elif gtch is None and och in NUM_CHARS:
            add("E_结构", gtch, och)      # 条目号/年月数字：GT 口径未收，非识别错
        elif och == "一" and row["file"].startswith("ndl_781193"):
            add("E_结构", gtch, och)      # 781193 界框碎片被读成「一」
        elif row["shared"] and (gtch is None or och is None):
            add("E_结构", gtch, och)      # 共享列：另一条目串扰/漏配
        elif gtch is not None and och is not None and (gtch, och) in VARIANT_PAIRS:
            add("C_旧字体码位", gtch, och)
        elif gtch is not None and och is not None and is_kanji(gtch) and is_kanji(och):
            add("B_汉字混淆", gtch, och)
        elif gtch is not None and och is not None:
            add("D_假名", gtch, och)
        elif gtch is None:
            add("D_假名" if not is_kanji(och) else "B_汉字混淆", gtch, och)
        else:
            add("D_假名" if not is_kanji(gtch) else "B_汉字混淆", gtch, och)
    return dict(cats), {k: v for k, v in examples.items()}


def main():
    with open(IN_JSON, encoding="utf-8") as f:
        cer = json.load(f)
    rows = cer["rows"]
    # A 类：raw-norm 差（标点操作数）
    total = Counter()
    per_page = defaultdict(Counter)
    row_details = []
    for row in rows:
        if row["ocr"] is None:
            row_details.append({**row, "cats": {"E_结构": 1}, "examples": {"E_结构": ["unmatched"]}})
            continue
        cats, examples = classify_row(row)
        # dist_norm 里不含标点；A 类 = dist(raw) - dist(norm)
        a_punct = max(0, (row["dist"] or 0) - (row["dist_norm"] or 0))
        if a_punct:
            cats["A_标点"] = cats.get("A_标点", 0) + a_punct
        for k, v in cats.items():
            total[k] += v
            per_page[row["file"]][k] += v
        row_details.append({**row, "cats": cats, "examples": examples})

    # 汇总输出
    print("== Night37 OCR 错因分类（92 行，norm 对齐 + raw-norm 标点差）==")
    order = ["A_标点", "B_汉字混淆", "C_旧字体码位", "D_假名", "E_结构", "F_不可读", "W_通配"]
    tot_ops = sum(total[k] for k in order if k != "W_通配")
    for k in order:
        n = total[k]
        pct = ("%.1f%%" % (100.0 * n / tot_ops)) if tot_ops and k != "W_通配" else "-"
        print("  %-8s %5d  %s" % (k, n, pct))
    print("\n-- 每页 top 错因 --")
    for fname, c in sorted(per_page.items()):
        top = ",".join("%s=%d" % (k, c[k]) for k in order if c.get(k))
        print("  %-28s %s" % (fname, top))
    print("\n-- 例证 --")
    for r in row_details:
        ex = r.get("examples") or {}
        if ex:
            flat = "; ".join("%s[%s]" % (k, ",".join(v[:4])) for k, v in ex.items())
            print("  %s L%-2d %s" % (r["file"], r["line_no"], flat[:150]))

    out = {"total": dict(total), "per_page": {k: dict(v) for k, v in per_page.items()},
           "rows": row_details,
           "note": "只诊断；分类口径见 tools/night37_classify.py 头注释"}
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n[done] written:", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
