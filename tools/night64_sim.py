# -*- coding: utf-8 -*-
"""night64_sim.py — N64 第三步：Rule I 候选离线模拟（基线 = night60 真机 4000，全链已上线）。

候选来源 = night64_mine.py / night64_probe.py：
  A. SHINJITAI 批量：第二遍计数判据（exp 全库写旧形 0 次 & got>=2）+ 标准新字体目标；
     数学上 0 变差保证（exp 无旧形 ⇒ 映射后的对齐代价只会持平或下降），
     但仍逐条真算 Levenshtein 验证；目标形要求 exp 全库出现过 >=1 次（exp 写过的新形才算）。
  B. kana→kanji 六候选（护栏 = 白文含对应汉字 + 更长词表，D14/E/F/G/H 同构）：
     けだし→蓋し / いずくんぞ→焉くんぞ / もし→如し / それ→夫れ / ただ→惟だ / なかれ→毋かれ
变差>0 一律不上线（任务书硬规则）。逐条真算 Levenshtein。
输出 eval/night64_sim.json + 改写行明细 night64_combo_changed_rows_*.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)
from backend.kundoku_rules import (  # noqa: E402
    E_LONGER_WORDS, H_LONGER_WORDS)

# SHINJITAI 批量候选（night64_probe.py 计数判据 + 标准新字体目标）。
# 注：night64_probe.py 票据里 被/廃/耳/擻/於/躍/為 等杂票是等长块逐位 zip 的对位噪音，
# 目标一律取标准新字体（每条都与票一致或为票中的正确形）。
SHINJITAI_N64 = {
    "聽": "聴", "觀": "観", "舍": "舎", "愼": "慎", "爭": "争", "搖": "揺",
    "髮": "髪", "擧": "挙", "藏": "蔵", "拂": "払", "繼": "継", "羣": "群",
    "祿": "禄", "寢": "寝", "沒": "没", "辯": "弁", "囘": "回", "卷": "巻",
    "靜": "静", "勸": "勧", "溪": "渓", "鷄": "鶏", "盜": "盗", "獵": "猟",
    "戲": "戯", "儉": "倹", "雜": "雑", "壯": "壮", "總": "総", "徑": "径",
    "峯": "峰", "悅": "悦", "壽": "寿", "竝": "並", "辨": "弁", "巖": "巌",
    "驅": "駆", "淚": "涙", "晝": "昼", "收": "収", "豫": "予", "爐": "炉",
    "彈": "弾", "緣": "縁", "墮": "堕", "卽": "即", "淺": "浅", "兔": "兎",
    "賴": "頼", "效": "効", "淸": "清", "假": "仮", "攝": "摂", "鎭": "鎮",
    "薰": "薫", "險": "険", "壤": "壌", "絕": "絶", "劒": "剣", "攜": "携",
    "增": "増", "彥": "彦", "黑": "黒", "潛": "潜", "寫": "写", "壓": "圧",
    "艷": "艶", "拔": "抜", "尙": "尚", "齡": "齢", "據": "拠", "碎": "砕",
    "嶽": "岳", "搜": "捜", "僞": "偽",
    # 票据 0 的等长块漏投票字（标准新字体，exp 侧出现次数脚本内核验）
    "卻": "却", "聰": "聡", "壞": "壊", "禪": "禅", "戶": "戸", "巢": "巣",
    "齋": "斎", "覽": "覧", "貳": "弐", "驗": "験", "螢": "蛍", "絲": "糸",
    "鬪": "闘", "麥": "麦", "窻": "窓", "辦": "弁", "單": "単", "每": "毎",
    "奧": "奥", "戀": "恋", "歷": "歴", "曆": "暦", "荆": "荊", "濕": "湿",
}

# kana 候选（与 E/F/G/H 同构：(kana, repl, guard, longer)）
KANA_CANDIDATES = {
    "kedashi":   {"kana": "けだし", "repl": "蓋し", "guard": ("蓋",), "longer": (),
                  "tag": "けだし→蓋し（白文含蓋）"},
    "izukunzo":  {"kana": "いずくんぞ", "repl": "焉くんぞ", "guard": ("焉",), "longer": (),
                  "tag": "いずくんぞ→焉くんぞ（白文含焉）【D14 拒裸焉，按 exp 词形复核】"},
    "moshi":     {"kana": "もし", "repl": "如し", "guard": ("如",),
                  "longer": ("もしも", "もしや", "もしか"),
                  "tag": "もし→如し（白文含如）"},
    "sore":      {"kana": "それ", "repl": "夫れ", "guard": ("夫",),
                  "longer": H_LONGER_WORDS["それ"],
                  "tag": "それ→夫れ（白文含夫）【H 的 只 分工之后】"},
    "tada":      {"kana": "ただ", "repl": "惟だ", "guard": ("惟",),
                  "longer": E_LONGER_WORDS["ただ"],
                  "tag": "ただ→惟だ（白文含惟）【E 的 唯 分工之后】"},
    "nakare":    {"kana": "なかれ", "repl": "毋かれ", "guard": ("毋",),
                  "longer": ("ことなかれ", "することなかれ"),
                  "tag": "なかれ→毋かれ（白文含毋）【D14 拒→勿，按 exp 词形复核】"},
}
# Combo 里 kana 规则的应用顺序（与未来 style 链序一致：H 之后追加）
COMBO_ORDER = ["kedashi", "izukunzo", "moshi", "sore", "tada", "nakare"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def is_kanji(c):
    return bool(c) and ("\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf")


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def apply_one(text, kana, repl, longer):
    longer = sorted(longer, key=len, reverse=True)
    out, i, n, cnt = [], 0, len(kana), 0
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        tail = text[j:]
        hit = next((w for w in longer if tail.startswith(w)), None)
        if hit:
            out.append(text[i:j + len(hit)])
            i = j + len(hit)
        else:
            out.append(text[i:j] + repl)
            i = j + n
            cnt += 1
    return "".join(out), cnt


def run(rows, kana_rules, shin_map=None, keep_changed=False):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        exp = norm(r["expected_kakikudashi"])
        d0 = lev(got, exp)
        new = got
        nchg = 0
        for kana, repl, guard, longer in kana_rules:
            if hb and not any(g in hb for g in guard):
                continue
            new, n = apply_one(new, kana, repl, longer)
            nchg += n
        if shin_map:
            nchg += sum(1 for c in new if c in shin_map)
            new = "".join(shin_map.get(c, c) for c in new)
        d1 = lev(new, exp)
        total_old += d0
        total_new += d1
        if nchg:
            changed_entries += 1
            if keep_changed:
                changed_rows.append({"id": r["id"], "old_dist": d0, "new_dist": d1,
                                     "old_text": got, "new_text": new, "expected": exp})
        if d1 < d0:
            better += 1
        elif d1 > d0:
            worse += 1
            worse_detail.append({"id": r["id"], "old": d0, "new": d1,
                                 "got": got[:120], "exp": exp[:120], "newtext": new[:120]})
        else:
            same += 1
    n = len(rows)
    out = {"entries": n, "changed_entries": changed_entries,
           "avg_old": round(total_old / n, 3), "avg_new": round(total_new / n, 3),
           "delta": round((total_new - total_old) / n, 3),
           "better": better, "worse": worse, "same": same,
           "worse_detail": worse_detail[:40]}
    if keep_changed:
        out["changed_rows"] = changed_rows
    return out


def idempotent(rows, kana_rules, shin_map):
    """与 night58 相同的显式两遍法：第二遍结果与第一遍不同 → 非幂等。"""
    bad = 0
    for r in rows:
        hb = norm(r["hakubun"])
        got = norm(r["udkundoku_kakikudashi"])
        new = got
        for kana, repl, guard, longer in kana_rules:
            if hb and not any(g in hb for g in guard):
                continue
            new, _ = apply_one(new, kana, repl, longer)
        if shin_map:
            new = "".join(shin_map.get(c, c) for c in new)
        twice = new
        for kana, repl, guard, longer in kana_rules:
            if hb and not any(g in hb for g in guard):
                continue
            twice, _ = apply_one(twice, kana, repl, longer)
        if shin_map:
            twice = "".join(shin_map.get(c, c) for c in twice)
        if twice != new:
            bad += 1
    return bad


def main():
    doc = json.load(open(os.path.join(EV, "night60_results_4000.json"), encoding="utf-8"))
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    golden_ids_new = {it["id"] for it in json.load(
        open(os.path.join(EV, "golden_4000.json"), encoding="utf-8"))[3000:]}
    rows_new = [r for r in rows if r["id"] in golden_ids_new]
    base = sum(lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
               for r in rows) / len(rows)
    print("样本 %d 条（新增段 %d）| 基线（全链真机 night60）avgDist %.3f" % (
        len(rows), len(rows_new), base), flush=True)

    out = {}
    lines = []

    # ---- 0. SHINJITAI 批量前置核验：exp 写过新形 / 旧形零出现 / 目标≠其他旧形键 ----
    exp_all = {}
    for r in rows:
        for c in norm(r["expected_kakikudashi"]):
            exp_all[c] = exp_all.get(c, 0) + 1
    old_keys = set(SHINJITAI_N64)
    dropped = []
    for o, n in SHINJITAI_N64.items():
        if exp_all.get(n, 0) == 0:
            dropped.append("%s→%s（exp 未写过新形）" % (o, n))
    cross = {o for o in old_keys if o in set(SHINJITAI_N64.values()) and o != ""}
    print("SHINJITAI 候选 %d 对；exp 新形核验掉 %d：%s；目标∩旧键: %s"
          % (len(SHINJITAI_N64), len(dropped), dropped, cross or "无"), flush=True)
    shin_map = {o: n for o, n in SHINJITAI_N64.items() if "%s→%s（exp 未写过新形）" % (o, n) not in dropped}

    # ---- A. SHINJITAI 单独模拟 ----
    s = run(rows, [], shin_map)
    s_new = run(rows_new, [], shin_map)
    out["shinjitai"] = {"sim": s, "sim_new1000": s_new, "pairs": shin_map}
    lines.append("=== A. SHINJITAI %d 对（全 3998）===" % len(shin_map))
    lines.append("  改写 %4d 行 | Δ %+7.3f | 改善 %4d / 变差 %3d / 持平 %4d" % (
        s["changed_entries"], s["delta"], s["better"], s["worse"], s["same"]))
    for d in s["worse_detail"][:8]:
        lines.append("    !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:40]))

    # ---- B. kana 候选逐个模拟 ----
    lines.append("\n=== B. kana 候选（全 3998 | 新增 1000 改写数）===")
    for k in COMBO_ORDER:
        c = KANA_CANDIDATES[k]
        rules = [(c["kana"], c["repl"], c["guard"], c["longer"])]
        s = run(rows, rules)
        s_new = run(rows_new, rules)
        out[k] = {"sim": s, "sim_new1000": s_new}
        verdict = "✅收" if (s["worse"] == 0 and s["changed_entries"] > 0) else \
                  ("（不收：0 改写）" if s["changed_entries"] == 0 else "❌拒（变差>0）")
        lines.append("  %-34s %6s 改写 %3d | Δ %+7.3f | 改善 %3d / 变差 %2d | 新段改 %2d" % (
            c["tag"], verdict, s["changed_entries"], s["delta"], s["better"],
            s["worse"], s_new["changed_entries"]))
        for d in s["worse_detail"][:6]:
            lines.append("      !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:46]))

    # ---- C. 组合（只收 0 变差 kana + SHINJITAI），幂等 + 改写行落盘 ----
    zero = [k for k in COMBO_ORDER
            if out[k]["sim"]["worse"] == 0 and out[k]["sim"]["changed_entries"] > 0]
    lines.append("\n=== C. 组合（0 变差 kana：%s）+ SHINJITAI %d 对 ===" % (
        ",".join(zero) if zero else "无", len(shin_map)))
    combo_rules = []
    for k in COMBO_ORDER:
        if k in zero:
            c = KANA_CANDIDATES[k]
            combo_rules.append((c["kana"], c["repl"], c["guard"], c["longer"]))
    s = run(rows, combo_rules, shin_map, keep_changed=True)
    idem = idempotent(rows, combo_rules, shin_map)
    out["combo"] = {"sim": {k: v for k, v in s.items() if k != "changed_rows"},
                    "idem_bad": idem,
                    "rules": [[x[0], x[1], x[2]] for x in combo_rules],
                    "shin_pairs": shin_map}
    json.dump(s["changed_rows"], open(
        os.path.join(EV, "night64_combo_changed_rows.json"), "w", encoding="utf-8",
        newline="\n"), ensure_ascii=False, indent=1)
    lines.append("  组合：改写 %4d 行 | Δ %+7.3f | 改善 %4d / 变差 %3d / 持平 %4d | 幂等坏 %d" % (
        s["changed_entries"], s["delta"], s["better"], s["worse"], s["same"], idem))
    for d in s["worse_detail"][:8]:
        lines.append("    !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:40]))

    txt = "\n".join(lines)
    open(os.path.join(EV, "night64_sim.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    json.dump(out, open(os.path.join(EV, "night64_sim.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    print(txt, flush=True)
    print("\nwritten: eval/night64_sim.json / night64_sim.txt / night64_combo_changed_rows.json",
          flush=True)


if __name__ == "__main__":
    main()
