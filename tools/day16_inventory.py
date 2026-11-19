# -*- coding: utf-8 -*-
"""day16_inventory.py — D16 第一步：盘点可用语料，规划 1000 条新增。

不许造数据、不许改 expected。只从仓内已有的 kanbun.info 语料里取。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")

FILES = ["golden.json", "golden_1000.json", "golden_rongo_full.json",
         "kanbun_parallel.json", "golden_rongo.json", "day10_new_entries.json"]


def load(name):
    p = os.path.join(EV, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, list):
        return d
    for k in ("results", "entries", "items", "data"):
        if isinstance(d.get(k), list):
            return d[k]
    return None


def keys_of(rows):
    ks = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        for k in ("id", "hakubun", "expected_kakikudashi", "expected", "source_url", "genre"):
            if k in r:
                ks.add(k)
    return sorted(ks)


def main():
    print("%-26s %6s  %s" % ("file", "rows", "keys"), flush=True)
    seen = {}
    for name in FILES:
        rows = load(name)
        if rows is None:
            print("%-26s  MISSING" % name, flush=True)
            continue
        print("%-26s %6d  %s" % (name, len(rows), ",".join(keys_of(rows))), flush=True)
        seen[name] = rows

    base = seen.get("golden_1000.json") or []
    print("\n--- golden_1000 组成 ---", flush=True)
    if base:
        print("  样例:", json.dumps(base[0], ensure_ascii=False)[:300], flush=True)
        pref = {}
        for r in base:
            i = str(r.get("id", ""))
            pref[i.split("-")[0]] = pref.get(i.split("-")[0], 0) + 1
        print("  id 前缀分布:", pref, flush=True)
        print("  唯一 hakubun:", len({r.get("hakubun", "") for r in base}), flush=True)

    used_hb = {r.get("hakubun", "").strip() for r in base}
    print("\n--- 其他语料 vs golden_1000 的重叠 ---", flush=True)
    for name, rows in seen.items():
        if name in ("golden_1000.json", "golden.json"):
            continue
        hbs = [r.get("hakubun", "").strip() for r in rows]
        uniq = set(hbs)
        new = uniq - used_hb
        print("%-26s 总 %4d | 唯一 %4d | 与1000不重叠 %4d"
              % (name, len(rows), len(uniq), len(new)), flush=True)

    # 合计可新增
    pool = set()
    for name, rows in seen.items():
        if name == "golden_1000.json":
            continue
        for r in rows:
            hb = r.get("hakubun", "").strip()
            exp = (r.get("expected_kakikudashi") or r.get("expected") or "").strip()
            if hb and exp:
                pool.add(hb)
    print("\n去重后可新增池（不在 golden_1000 里、有 expected 的 hakubun）：%d" % len(pool - used_hb),
          flush=True)


if __name__ == "__main__":
    main()
