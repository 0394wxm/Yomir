# -*- coding: utf-8 -*-
"""night50_order_rate.py — 顺序测量门的口径实现（NIGHT50 任务 B）。

**只测量、不判死刑**。回答一个问题：在最终扁平输出顺序里，
割注对的右半是否排在左半之前（右先率），以及相对 Night49 改后的
基线有没有**退化的页**。

口径来源（与 Night49 完全同源，不另立一套）：
  * 配对与排序直接 import tools/night49_final.py 的 `find_pairs` / `order_of`，
    连版面过滤、`_main_group`、wmed 的取法都走同一份代码——
    口径若分叉，这个门就没有可比性。
  * 分层判据沿用 Night49 `tools/night49_pair_quality.py`：
      A_strict：gap < 0.15*wmed ∧ |dy_top| <= 0.05*max(h) ∧ |dh| <= 0.15*max(h)
    这是「真割注」最保守子集，Night49 改后实测 100%。

两条线（与 Night49 报告一致）：
  off —— eval/night44_full/filter_off + **离线套版面过滤**（生产口径）
  on  —— eval/night44_full/filter_on 归档（生产默认输出的交叉核对）

用法:
    python -X utf8 tools/night50_order_rate.py          # 独立跑，打印并写 json
    python -X utf8 tools/night50_order_rate.py --json   # 只输出 json 到 stdout

被 tools/accept_night.py 的 check_order_rate 以 `measure()` 方式复用；
此时**不写任何文件**，结果进验收门自己的 accept_night_<n>.json。
"""
import importlib.util
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "eval", "night50_order_rate.json")

# Night49 改后基线（REPORT_NIGHT49.md / eval/night49_final.json）。
# 只用于在门里算「比基线低多少」，**不作为 FAIL 判据**（见 check_order_rate）。
BASELINE = {
    "off": {"tot": 488, "after": 481, "rate": 98.57},
    "on": {"tot": 510, "after": 503, "rate": 98.63},
    "strict": {"n": 296, "after": 296, "rate": 100.0},
}


_N49 = None


def _load_n49():
    """导入 night49_final（并保住本进程的 sys.argv），结果缓存。

    night49_final 在模块级做两件「脚本化」的事：
      * `sys.stdout.reconfigure(...)` —— 所以**不能在 redirect_stdout 之后**
        首次导入（StringIO 没有 reconfigure）；
      * `sys.argv = [sys.argv[0]]` —— 验收门带 night/--no-pytest 参数时
        会被一起截掉，这里存/取快照。
    """
    global _N49
    if _N49 is not None:
        return _N49
    saved = sys.argv[:]
    try:
        sys.argv = [sys.argv[0]]
        path = os.path.join(ROOT, "tools", "night49_final.py")
        spec = importlib.util.spec_from_file_location("n49_final", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _N49 = mod
        return mod
    finally:
        sys.argv = saved


def _tier(gap, wmed, r, l):
    """Night49 分层判据（与 night49_pair_quality.cls 逐字一致）。"""
    top_aligned = abs(l["y"] - r["y"]) <= 0.05 * max(r["h"], l["h"])
    tight = gap / float(wmed) < 0.15
    hclose = abs(l["h"] - r["h"]) <= 0.15 * max(r["h"], l["h"])
    if tight and top_aligned and hclose:
        return "A_strict"
    if tight and top_aligned:
        return "B_sidelined"
    return "C_loose"


def measure(directory, apply_filter, label):
    """跑一条线，返回口径与 Night49 `night49_final.measure` 同构的统计。

    额外给出严格层（A_strict）的分子/分母，这是「真割注」的可信子集。
    """
    n49 = _load_n49()
    off_struct = n49.measure(directory, apply_filter, label)
    # n49.measure 会 print；调用方若要安静，自己重定向 stdout。

    # 严格层：再遍历一次拿每对的几何（n49.measure 的 per_page 只有计数）。
    # 目录迭代很便宜（47 页 × 几 KB JSON，实测全流程 <1s），
    # 换来实现独立、不依赖 n49 内部结构的可读性。
    from backend.ocr_layout import (  # noqa: E402
        _main_group, _median, judge_headnote_strip, judge_layout,
    )
    strict_n = strict_ok = 0
    strict_bad = []
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".json"):
            continue
        q = json.load(open(os.path.join(directory, fn), encoding="utf-8"))
        bx = [dict(b) for b in q["line_boxes"]]
        if len(bx) < 4:
            continue
        ki = list(range(len(bx)))
        if apply_filter:
            _mi, jd = judge_layout(bx)
            ki = [i for i, (_b, r) in enumerate(jd) if r is None]
            kp = [bx[i] for i in ki]
            vt = [b for b in kp if b["h"] >= b["w"]]
            if not vt:
                continue
            hm = max(b["h"] for b in vt)
            _m3, mn = _main_group([dict(b) for b in kp])
            if not mn:
                continue
            bt = _median([b["y"] for b in mn])
            st = judge_headnote_strip(kp, body_top=bt, h_max=hm)
            skk = {(b["x"], b["y"], b["w"], b["h"]) for b in st}
            ki = [i for i in ki
                  if (bx[i]["x"], bx[i]["y"], bx[i]["w"], bx[i]["h"]) not in skk]
            kp = [bx[i] for i in ki]
        else:
            kp = bx
        vt = [b for b in kp if b["h"] >= b["w"]]
        if not vt:
            continue
        _m2, mn = _main_group([dict(b) for b in kp])
        if not mn:
            continue
        wmed = _median([b["w"] for b in mn])
        if wmed <= 0:
            continue
        thin = [dict(bx[i], index=i) for i in ki
                if bx[i]["w"] / float(wmed) < 0.6 and bx[i]["h"] >= bx[i]["w"]]
        prs = n49.find_pairs(thin, wmed)
        if not prs:
            continue
        kept = [dict(bx[i], index=i) for i in ki]
        pos = {i: p for p, i in enumerate(n49.order_of(kept, True))}
        for r, l, gap in prs:
            if _tier(gap, wmed, r, l) != "A_strict":
                continue
            strict_n += 1
            if pos[r["index"]] < pos[l["index"]]:
                strict_ok += 1
            else:
                strict_bad.append({"page": q["page"],
                                   "r": q["lines"][r["index"]][:26],
                                   "l": q["lines"][l["index"]][:26]})

    out = dict(off_struct)
    out.update({
        "label": label,
        "rate": round(100.0 * off_struct["after"] / max(1, off_struct["tot"]), 2),
        "rate_before": round(100.0 * off_struct["before"]
                             / max(1, off_struct["tot"]), 2),
        "strict_n": strict_n,
        "strict_after": strict_ok,
        "strict_rate": round(100.0 * strict_ok / max(1, strict_n), 2),
        "strict_bad": strict_bad,
        "regress_n": len(off_struct["regress"]),
    })
    return out


def main():
    only_json = "--json" in sys.argv
    import contextlib
    import io

    # 预导入：night49_final（及其导入的 night49_simulate）在模块级调用
    # sys.stdout.reconfigure()，必须发生在 redirect_stdout 之前。
    _load_n49()

    lines = [
        (os.path.join(ROOT, "eval", "night44_full", "filter_off"), True,
         "filter_off + 离线版面过滤（生产口径）"),
        (os.path.join(ROOT, "eval", "night44_full", "filter_on"), False,
         "filter_on 归档（生产默认输出，交叉核对）"),
    ]
    res = {}
    for directory, apply_filter, label in lines:
        if not os.path.isdir(directory):
            res["off" if apply_filter else "on"] = {"error": "缺归档 %s" % directory}
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m = measure(directory, apply_filter, label)
        res["off" if apply_filter else "on"] = m

    payload = {"baseline": BASELINE, "lines": res}
    if only_json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0

    print("== 顺序测量门（只测量，不判死刑）==")
    for key in ("off", "on"):
        m = res.get(key) or {}
        if "error" in m:
            print("  [%s] %s" % (key, m["error"]))
            continue
        print("\n[%s] %s" % (key, m["label"]))
        print("  右先率（改后，生产口径）: %d/%d = %.2f%%   （改前 %.2f%%）"
              % (m["after"], m["tot"], m["rate"], m["rate_before"]))
        print("  严格层 A_strict         : %d/%d = %.2f%%"
              % (m["strict_after"], m["strict_n"], m["strict_rate"]))
        print("  相对改前退化的页        : %d" % m["regress_n"])
        for p in m["regress"]:
            print("    %s %d/%d → %d/%d"
                  % (p["page"], p["before"], p["n"], p["after"], p["n"]))
        if m["strict_bad"]:
            print("  严格层仍颠倒 %d 对:" % len(m["strict_bad"]))
            for e in m["strict_bad"]:
                print("    %s %r | %r" % (e["page"], e["r"], e["l"]))

    print("\n== 与 Night49 改后基线对照（仅供参考，不作 FAIL 判据）==")
    for key in ("off", "on"):
        m = res.get(key) or {}
        if "rate" not in m:
            continue
        b = BASELINE[key]
        print("  %s: 当前 %.2f%% vs 基线 %.2f%% → 差 %+.2f 个百分点"
              % (key, m["rate"], b["rate"], m["rate"] - b["rate"]))
    m = res.get("off") or {}
    if "strict_rate" in m:
        b = BASELINE["strict"]
        print("  strict: 当前 %.2f%% vs 基线 %.2f%% → 差 %+.2f 个百分点"
              % (m["strict_rate"], b["rate"], m["strict_rate"] - b["rate"]))

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night50_order_rate.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
