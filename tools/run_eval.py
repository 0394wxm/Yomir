# -*- coding: utf-8 -*-
"""
run_eval.py — 把 eval/golden.json 的 10 条白文逐条 POST 到本地 /api/kundoku，
记录 UD-Kundoku 原始输出，不做任何改写。结果写 eval/night1_results.json。

对比完全按字符串相等判断（仅记录事实，不计分不修饰）。
"""
import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "http://127.0.0.1:8000/api/kundoku"

# 用法: python -I tools/run_eval.py [--no-merge] [输出文件名]
#   --no-merge  走后端基线路径（/api/kundoku?merge=0），验证 Night1 基线
MERGE = "--no-merge" not in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUTFILE = ARGS[0] if ARGS else ("night2_results_merge.json" if MERGE else "night2_results_baseline.json")


def post(text: str):
    url = API + ("" if MERGE else "?merge=0")
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8")), None
    except Exception as e:
        return None, repr(e)


def main():
    with open(os.path.join(ROOT, "eval", "golden.json"), encoding="utf-8") as f:
        golden = json.load(f)
    results = []
    exact = 0
    for g in golden:
        resp, err = post(g["hakubun"])
        if err is not None:
            results.append({**g, "error": err})
            print("[ERR] %s: %s" % (g["id"], err))
            continue
        got = resp.get("kakikudashi", "")
        exact_match = got.strip() == g["expected_kakikudashi"].strip()
        if exact_match:
            exact += 1
        results.append({
            "id": g["id"],
            "source_url": g["source_url"],
            "hakubun": g["hakubun"],
            "expected_kakikudashi": g["expected_kakikudashi"],
            "udkundoku_kakikudashi": got,
            "udkundoku_kaeriten_text": resp.get("kaeriten_text", ""),
            "exact_match": exact_match,
        })
        print("[%s] %s" % ("EXACT" if exact_match else "DIFF ", g["id"]))
        print("   expected: %s" % g["expected_kakikudashi"])
        print("   got     : %s" % got.strip())
    out = os.path.join(ROOT, "eval", OUTFILE)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"exact_match_count": exact, "total": len(results), "results": results},
                  f, ensure_ascii=False, indent=2)
    print("\nexact match: %d / %d" % (exact, len(results)))
    print("written:", out)


if __name__ == "__main__":
    main()
