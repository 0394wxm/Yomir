# -*- coding: utf-8 -*-
"""run_eval_guwenbert.py — full_v4：guwenbert 依存解析 + udkundoku 训读管线。

Night 21 / D1 下半场：把 udkanbun 默认的 UDPipe (ud-kanbun.udpipe) 依存解析器
换成 guwenbert-base.supar（tools/load_guwenbert.py 手写加载器），其余全部不变：
  * MeCab(mecab-kanbun) 分词、xpos/feats 同一条路径；
  * udkundoku.translate() 的训读后处理（助词插入、活用、语序）不变；
  * 后端后处理规则（merge_proper_nouns / style_fix / normalize_shinjitai）不变。

用法:
    python tools/run_eval_guwenbert.py 200            # 200 条评测集
    python tools/run_eval_guwenbert.py 500            # night21 的 500 条
    python tools/run_eval_guwenbert.py 200 --out eval/night21_results_full_v4.json
"""

import argparse
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import load_guwenbert  # noqa: E402  (同目录)

import udkundoku  # noqa: E402
import udkanbun  # noqa: E402

from backend.kundoku_rules import merge_proper_nouns, normalize_shinjitai, style_fix  # noqa: E402


def levenshtein(a, b):
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


class GuwenbertAPI(object):
    """复刻 udkanbun.supar.SuParAPI.process 的接口，内部用 D1 手写加载的 parser。"""

    def __init__(self, ckpt=None, device="cpu"):
        kw = {} if ckpt is None else {"ckpt": ckpt}
        self.parser = load_guwenbert.load_parser(device=device, verbose=False, **kw)
        self.calls = 0

    def process(self, conllu):
        c = conllu.split("\n")
        u = []
        e = ""
        for s in c:
            if s.startswith("#"):
                continue
            if s == "":
                if e != "":
                    u.append(e.strip().split())
                    e = ""
            else:
                t = s.split("\t")
                i = t[9].find("Translit=")
                if i < 0:
                    j = t[1]
                    if t[4] == "n,名詞,*,*":
                        from udkanbun.simplify import simplify
                        if t[1] in simplify:
                            j = simplify[t[1]]
                else:
                    j = t[9][i + 9:]
                e += j + " "
        if not u:
            return conllu
        d = self.parser.predict(u, lang=None, verbose=False)
        self.calls += 1
        i = j = 0
        for k, s in enumerate(c):
            if s.startswith("#"):
                continue
            if s == "":
                i += 1
                j = 0
            else:
                t = s.split("\t")
                t[6] = str(d.sentences[i].values[6][j])
                t[7] = d.sentences[i].values[7][j]
                c[k] = "\t".join(t)
                j += 1
        return "\n".join(c)


def build_engine(ckpt=None):
    """udkanbun 引擎本体（MeCab 分词 + 默认 udpipe 先占位），再换掉 udpipe。"""
    eng = udkanbun.UDKanbun(True, False, None)
    eng.udpipe = GuwenbertAPI(ckpt)
    return eng


def kundoku_line(eng, line):
    entry = eng(line)
    entry = merge_proper_nouns(entry)
    conllu = udkundoku.translate(entry, raw=True)
    kk = "\n".join(l[9:] for l in conllu.split("\n") if l.startswith("# text = "))
    return normalize_shinjitai(style_fix(kk))


def run(items, limit, out_path, eng):
    results = []
    t0 = time.time()
    for n, g in enumerate(items[:limit], 1):
        t1 = time.time()
        try:
            kk = kundoku_line(eng, g["hakubun"])
            err = ""
        except Exception as e:  # 如实记录，不吞
            import traceback
            traceback.print_exc()
            kk = ""
            err = repr(e)
        got_norm = re.sub(r"\s+", "", kk)
        exp_norm = re.sub(r"\s+", "", g["expected_kakikudashi"])
        dist = levenshtein(got_norm, exp_norm) if not err else None
        results.append({
            "id": g["id"],
            "source_url": g.get("source_url", ""),
            "hakubun": g["hakubun"],
            "expected_kakikudashi": g["expected_kakikudashi"],
            "udkundoku_kakikudashi": kk,
            "udkundoku_kakikudashi_norm": got_norm,
            "exact_match": (got_norm == exp_norm) if not err else False,
            "edit_distance": dist,
            "error": err,
            "elapsed_sec": round(time.time() - t1, 2),
        })
        if n % 20 == 0 or n == min(limit, len(items)):
            done = [r for r in results if r["edit_distance"] is not None]
            avg = sum(r["edit_distance"] for r in done) / len(done) if done else -1
            print("[%d/%d] avgDist=%.2f  elapsed=%.0fs" % (n, min(limit, len(items)), avg, time.time() - t0), flush=True)

    done = [r for r in results if r["edit_distance"] is not None]
    exact = sum(1 for r in results if r["exact_match"])
    payload = {
        "exact_match_count": exact,
        "total": len(results),
        "errors": sum(1 for r in results if r["error"]),
        "avg_edit_distance": round(sum(r["edit_distance"] for r in done) / len(done), 2) if done else None,
        "engine": "guwenbert-base.supar + udkundoku rule pipeline (merge+ortho)",
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("exact %d/%d  avgDist %s  errors %d  written: %s"
          % (exact, len(results), payload["avg_edit_distance"], payload["errors"], out_path))
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=200, choices=[200, 500])
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条（冒烟测试用）")
    ap.add_argument("--from", dest="from_file", default=None,
                    help="从已有结果 JSON 取样本（保证同一批 id）；缺省用 golden.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--device", default="cpu")
    arg = ap.parse_args()

    if arg.from_file:
        with open(arg.from_file if os.path.isabs(arg.from_file) else os.path.join(ROOT, arg.from_file),
                  encoding="utf-8") as f:
            raw = json.load(f)
        items = raw["results"] if isinstance(raw, dict) else raw
        print("[data] %d items from %s (id 稳定)" % (len(items), arg.from_file), flush=True)
    elif arg.n == 200:
        with open(os.path.join(ROOT, "eval", "golden.json"), encoding="utf-8") as f:
            items = json.load(f)
    else:
        with open(os.path.join(ROOT, "eval", "night21_results_full.json"), encoding="utf-8") as f:
            items = json.load(f)["results"]

    default_out = "night21_results_full_v4.json" if arg.n == 200 else "night21_results_full_v4_500.json"

    out = arg.out or os.path.join(ROOT, "eval", default_out)
    print("[load] guwenbert parser ...", flush=True)
    t0 = time.time()
    eng = build_engine(arg.ckpt)
    print("[load] done in %.1fs" % (time.time() - t0), flush=True)
    run(items, arg.limit or arg.n, out, eng)
    return 0


if __name__ == "__main__":
    sys.exit(main())
