# -*- coding: utf-8 -*-
"""night68_sim.py — N68 第三步：Rule J 候选离线模拟（照抄 night64_sim.py，基线 = night67 真机 8165）。

候选 = eval/night68_candidates.txt（J1-J11 收门候选 + R1-R3 预拒复核 + SHINJITAI 29 对）。
变差>0 一律不上线（任务书硬规则）。逐条真算 Levenshtein；両有行（白文如/若两有）的
目标顺序用 configA（如先）/configB（若先）双配置各跑一遍，取 0 变差的配置。
输出 eval/night68_sim.json / night68_sim.txt / night68_combo_changed_rows.json。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

# SHINJITAI 批量候选（night68_probe.py 计数判据 + 多数票 + exp 新形>=1；區/鬭 行级证据修正票噪）
SHINJITAI_N68 = {
    "擊": "撃", "歡": "歓", "虛": "虚", "壘": "塁", "筭": "算", "徃": "往",
    "吳": "呉", "穰": "穣", "髙": "高", "纖": "繊", "丗": "世", "决": "決",
    "劔": "剣", "艸": "草", "濱": "浜", "閱": "閲", "區": "区", "狀": "状",
    "皷": "鼓", "畱": "留", "步": "歩", "耻": "恥", "稻": "稲", "鬭": "闘",
    "價": "価", "繩": "縄", "敕": "勅", "爼": "俎", "涉": "渉",
}

# kana 候选 (kana, repl, guard, longer, tag)——guard 是「白文里可接受的写法」元组（E 系同构）
KANA_CANDIDATES = {
    "beki":     {"kana": "べき", "repl": "可き", "guard": ("可",), "longer": (),
                 "tag": "べき→可き（白文含可）【F 完族补漏】"},
    "bekara":   {"kana": "べから", "repl": "可から", "guard": ("可",), "longer": (),
                 "tag": "べから→可から（白文含可）【含べからざる；べからず残量同场裁决】"},
    "gotoshi_nyo": {"kana": "ごとし", "repl": "如し", "guard": ("如",), "longer": (),
                 "tag": "ごとし→如し（白文含如）【D14 拒裸如，词形复核】"},
    "gotoshi_jo":  {"kana": "ごとし", "repl": "若し", "guard": ("若",), "longer": (),
                 "tag": "ごとし→若し（白文含若）【漢詩段白文写若；D14 只试过如】"},
    "gotoku_nyo":  {"kana": "ごとく", "repl": "如く", "guard": ("如",), "longer": (),
                 "tag": "ごとく→如く（白文含如）"},
    "gotoku_jo":   {"kana": "ごとく", "repl": "若く", "guard": ("若",), "longer": (),
                 "tag": "ごとく→若く（白文含若）"},
    "gotoki_nyo":  {"kana": "ごとき", "repl": "如き", "guard": ("如",), "longer": (),
                 "tag": "ごとき→如き（白文含如）【证据弱，存疑】"},
    "gotoki_jo":   {"kana": "ごとき", "repl": "若く", "guard": ("若",), "longer": (),
                 "tag": "ごとき→若く（白文含若）【目标混写，存疑】"},
    "moshi_jo":    {"kana": "もし", "repl": "若し", "guard": ("若",),
                 "longer": ("もしも", "もしや", "もしか"),
                 "tag": "もし→若し（白文含若）【Rule I 如枝的残量补完】"},
    "masani":      {"kana": "まさに", "repl": "方に", "guard": ("方",), "longer": (),
                 "tag": "まさに→方に（白文含方）【kanbun.info 白文把將写作方】"},
    "nanzo":       {"kana": "なんぞ", "repl": "何ぞ", "guard": ("何", "奚", "盍", "曷"), "longer": (),
                 "tag": "なんぞ→何ぞ（白文含何/奚/盍/曷）【Xぞ 族】"},
    # 预拒复核（R1-R3，只为拒案表取实数，不进组合）
    "R_nakare_mokare": {"kana": "なかれ", "repl": "莫かれ", "guard": ("莫",), "longer": (),
                 "tag": "なかれ→莫かれ（白文含莫）【N58 拒案重测，预期混写拒】"},
    "R_kotonaku_moki": {"kana": "ことなく", "repl": "莫き", "guard": ("莫",), "longer": (),
                 "tag": "ことなく→莫き（白文含莫）【预期 0 收益拒】"},
    "R_gatame":     {"kana": "がため", "repl": "が為に", "guard": ("為", "爲"), "longer": (),
                 "tag": "がため→が為に（白文含為/爲）【预期目标混写拒】"},
}
COMBO_ORDER = ["beki", "bekara", "gotoshi_nyo", "gotoshi_jo", "gotoku_nyo", "gotoku_jo",
               "gotoki_nyo", "gotoki_jo", "moshi_jo", "masani", "nanzo"]


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


def seg_of(r):
    url = r.get("source_url", "") or ""
    return "shibu02" if "kanbun.info/shibu02/" in url.lower() else None


def run(rows, kana_rules, shin_map=None, keep_changed=False):
    better = worse = same = 0
    changed_entries = 0
    total_old = total_new = 0
    worse_detail = []
    changed_rows = []
    segs = {"s4000": [0, 0, 0], "s3908": [0, 0, 0], "s257": [0, 0, 0], "shibu02": [0, 0, 0]}
    for idx, r in enumerate(rows):
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
        if idx < 4000:
            sk = "s4000"
        elif idx < 7908:
            sk = "s3908"
        else:
            sk = "s257"
        if seg_of(r) == "shibu02":
            sk2 = "shibu02"
        else:
            sk2 = None
        if nchg:
            changed_entries += 1
            delta = d1 - d0
            for key in (sk, sk2):
                if key:
                    segs[key][0 if delta < 0 else (1 if delta > 0 else 2)] += 1
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
           "segs": {k: {"better": v[0], "worse": v[1], "same": v[2]} for k, v in segs.items()},
           "worse_detail": worse_detail[:40]}
    if keep_changed:
        out["changed_rows"] = changed_rows
    return out


def idempotent(rows, kana_rules, shin_map):
    """与 night58/64 相同的显式两遍法：第二遍结果与第一遍不同 → 非幂等。"""
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
    doc = json.load(open(os.path.join(EV, "night67_results_8165.json"), encoding="utf-8"))
    golden = json.load(open(os.path.join(EV, "golden_8165.json"), encoding="utf-8"))
    for i, (r, g) in enumerate(zip(doc["results"], golden)):
        assert r["id"] == g["id"], "results/golden 第 %d 行不同序" % i
    rows = [r for r in doc["results"] if r.get("udkundoku_kakikudashi") is not None]
    n = len(rows)
    base = sum(lev(norm(r["udkundoku_kakikudashi"]), norm(r["expected_kakikudashi"]))
               for r in rows) / n
    print("样本 %d 条 | 基线（⑬补丁后全链真机 night67）avgDist %.3f" % (n, base), flush=True)

    out = {}
    lines = []

    # ---- 0. SHINJITAI 前置核验：exp 写过新形 / 旧形零出现 / 目标≠其他旧形键 ----
    sys.path.insert(0, ROOT)
    from backend.kundoku_rules import SHINJITAI_MAP  # noqa: E402
    exp_all = {}
    for r in rows:
        for c in norm(r["expected_kakikudashi"]):
            exp_all[c] = exp_all.get(c, 0) + 1
    dropped = []
    for o, nn in SHINJITAI_N68.items():
        if exp_all.get(nn, 0) == 0:
            dropped.append("%s→%s（exp 未写过新形）" % (o, nn))
        if o in SHINJITAI_MAP:
            dropped.append("%s 已在表中？" % o)
    cross = {o for o in SHINJITAI_N68 if o in set(SHINJITAI_N68.values())}
    cross2 = {nn for nn in SHINJITAI_N68.values() if nn in SHINJITAI_MAP}
    print("SHINJITAI 候选 %d 对；核验掉 %d：%s；目标∩本批旧键: %s；目标∩既有表: %s"
          % (len(SHINJITAI_N68), len(dropped), dropped, cross or "无", cross2 or "无"), flush=True)
    shin_map = {o: nn for o, nn in SHINJITAI_N68.items()
                if "%s→%s（exp 未写过新形）" % (o, nn) not in dropped
                and "%s 已在表中？" % o not in dropped}

    # ---- A. SHINJITAI 单独模拟 ----
    s = run(rows, [], shin_map)
    out["shinjitai"] = {"sim": {k: v for k, v in s.items() if k != "changed_rows"}, "pairs": shin_map}
    lines.append("=== A. SHINJITAI %d 对（全 %d）===" % (len(shin_map), n))
    lines.append("  改写 %4d 行 | Δ %+7.3f | 改善 %4d / 变差 %3d / 持平 %4d" % (
        s["changed_entries"], s["delta"], s["better"], s["worse"], s["same"]))
    for d in s["worse_detail"][:8]:
        lines.append("    !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:40]))

    # ---- B. kana 候选逐个模拟（含预拒 R 系取实数）----
    lines.append("\n=== B. kana 候选（全 %d | 各段 改善/变差/持平）===" % n)
    for k in list(COMBO_ORDER) + ["R_nakare_mokare", "R_kotonaku_moki", "R_gatame"]:
        c = KANA_CANDIDATES[k]
        rules = [(c["kana"], c["repl"], c["guard"], c["longer"])]
        s = run(rows, rules)
        out[k] = {"sim": {kk: vv for kk, vv in s.items() if kk != "changed_rows"}}
        if k.startswith("R_"):
            verdict = "（预拒复核：变差 %d / 改善 %d）" % (s["worse"], s["better"])
        else:
            verdict = "✅收" if (s["worse"] == 0 and s["changed_entries"] > 0) else \
                      ("（不收：0 改写）" if s["changed_entries"] == 0 else "❌拒（变差>0）")
        sg = s["segs"]
        lines.append("  %-46s %s" % (c["tag"], verdict))
        lines.append("      改写 %4d | Δ %+7.3f | 改善 %4d / 变差 %2d / 持平 %4d | 段: [0:4000) %d/%d/%d [4000:7908) %d/%d/%d [7908:] %d/%d/%d shibu02 %d/%d/%d" % (
            s["changed_entries"], s["delta"], s["better"], s["worse"], s["same"],
            sg["s4000"]["better"], sg["s4000"]["worse"], sg["s4000"]["same"],
            sg["s3908"]["better"], sg["s3908"]["worse"], sg["s3908"]["same"],
            sg["s257"]["better"], sg["s257"]["worse"], sg["s257"]["same"],
            sg["shibu02"]["better"], sg["shibu02"]["worse"], sg["shibu02"]["same"]))
        for d in s["worse_detail"][:6]:
            lines.append("      !! 变差 %s %d->%d exp=%s" % (d["id"], d["old"], d["new"], d["exp"][:46]))

    # ---- C. 组合（0 变差 kana + SHINJITAI），如先/若先双配置 ----
    zero = [k for k in COMBO_ORDER
            if out[k]["sim"]["worse"] == 0 and out[k]["sim"]["changed_entries"] > 0]
    lines.append("\n=== C. 组合（0 变差 kana：%s）+ SHINJITAI %d 对 ===" % (
        ",".join(zero) if zero else "无", len(shin_map)))
    nyos = [k for k in zero if k.endswith("_nyo")]
    jos = [k for k in zero if k.endswith("_jo")]
    others = [k for k in zero if k not in nyos and k not in jos]
    for cfg, order in (("configA(如先)", nyos + jos), ("configB(若先)", jos + nyos)):
        combo_rules = []
        for k in others + order:
            c = KANA_CANDIDATES[k]
            combo_rules.append((c["kana"], c["repl"], c["guard"], c["longer"]))
        s = run(rows, combo_rules, shin_map, keep_changed=True)
        idem = idempotent(rows, combo_rules, shin_map)
        out.setdefault("combo", {})[cfg] = {
            "sim": {k2: v for k2, v in s.items() if k2 != "changed_rows"},
            "idem_bad": idem,
            "rules": [[x[0], x[1], x[2]] for x in combo_rules],
            "shin_pairs": shin_map}
        lines.append("  [%s] 组合：改写 %4d 行 | Δ %+7.3f | 改善 %4d / 变差 %3d / 持平 %4d | 幂等坏 %d" % (
            cfg, s["changed_entries"], s["delta"], s["better"], s["worse"], s["same"], idem))
        for d in s["worse_detail"][:10]:
            lines.append("    !! 变差 %s %d->%d" % (d["id"], d["old"], d["new"]))
            lines.append("        got: %s" % d["got"][:70])
            lines.append("        new: %s" % d["newtext"][:70])
            lines.append("        exp: %s" % d["exp"][:70])
        if cfg == "configA(如先)":
            json.dump(s["changed_rows"], open(
                os.path.join(EV, "night68_combo_changed_rows.json"), "w", encoding="utf-8",
                newline="\n"), ensure_ascii=False, indent=1)

    txt = "\n".join(lines)
    open(os.path.join(EV, "night68_sim.txt"), "w", encoding="utf-8",
         newline="\n").write(txt + "\n")
    json.dump(out, open(os.path.join(EV, "night68_sim.json"), "w", encoding="utf-8",
                        newline="\n"), ensure_ascii=False, indent=1)
    print(txt, flush=True)
    print("\nwritten: eval/night68_sim.json / night68_sim.txt / night68_combo_changed_rows.json",
          flush=True)


if __name__ == "__main__":
    main()
