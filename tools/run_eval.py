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

# 用法: python -I tools/run_eval.py [--no-merge] [--no-ortho] [输出文件名]
#   --no-merge  关闭专名合并（/api/kundoku?merge=0）
#   --no-ortho  关闭旧→新字体转换（/api/kundoku?ortho=0）
MERGE = "--no-merge" not in sys.argv
ORTHO = "--no-ortho" not in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUTFILE = ARGS[0] if ARGS else ("night3_results_full.json" if (MERGE and ORTHO) else "night3_results_custom.json")


def post(text: str):
    params = []
    if not MERGE:
        params.append("merge=0")
    if not ORTHO:
        params.append("ortho=0")
    url = API + (("?" + "&".join(params)) if params else "")
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8")), None
    except Exception as e:
        return None, repr(e)


def levenshtein(a: str, b: str) -> int:
    """编辑距离——作为“可读性/接近度”的客观指标（不替人工判断）。"""
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
        expected = g["expected_kakikudashi"]
        exact_match = got.strip() == expected.strip()
        dist = levenshtein(got.strip(), expected.strip())
        if exact_match:
            exact += 1
        results.append({
            "id": g["id"],
            "source_url": g["source_url"],
            "hakubun": g["hakubun"],
            "expected_kakikudashi": expected,
            "udkundoku_kakikudashi": got,
            "udkundoku_kaeriten_text": resp.get("kaeriten_text", ""),
            "text_type": resp.get("text_type", ""),
            "exact_match": exact_match,
            "edit_distance": dist,
        })
        print("[%s] %s dist=%d" % ("EXACT" if exact_match else "DIFF ", g["id"], dist))
        print("   expected: %s" % expected)
        print("   got     : %s" % got.strip())
    out = os.path.join(ROOT, "eval", OUTFILE)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"exact_match_count": exact, "total": len(results), "results": results},
                  f, ensure_ascii=False, indent=2)
    print("\nexact match: %d / %d" % (exact, len(results)))
    print("written:", out)


if __name__ == "__main__":
    main()
