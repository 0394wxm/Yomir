# -*- coding: utf-8 -*-
"""night74_digest.py — N74 ③ 批读用 digest 生成器。

把 eval/night74_dict_cache/<idx3>.txt 按 start..end 每 STEP 条合并成
digest_<start>_<end>.txt，每条前面带词库条目元数据（word/reading/meaning/kind/
覆盖率/机械标记），后面跟 weblio 抽取文本，供逐条人工判定。
用法: python -I tools/night74_digest.py <start> <end> [step]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "eval", "night74_dict_cache")
AUDIT = os.path.join(ROOT, "eval", "night74_lexicon_audit.json")


def main():
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    audit = json.load(open(AUDIT, encoding="utf-8"))
    entries = {e["idx"]: e for e in audit["entries"]}

    out = []
    missing = []
    for i in range(start, min(end, 500)):
        p = os.path.join(CACHE, "%03d.txt" % i)
        e = entries[i]
        meta = "===== idx %d | %s | %s | %s | kind=%s | bun=%d kkd=%d | issues=%s" % (
            e["idx"], e["word"], e["reading"], e["meaning"], e["kind"] or "-",
            e["bun_doc_hits"], e["kkd_doc_hits"], ",".join(e["issues"]) or "-")
        if not os.path.exists(p):
            missing.append(i)
            out.append(meta + "\n--- CACHE MISSING ---\n")
            continue
        with open(p, "r", encoding="utf-8") as f:
            body = f.read()
        out.append(meta + "\n" + body.strip()[:4500] + "\n")
        if (i - start + 1) % step == 0 or i == min(end, 500) - 1:
            name = "digest_%03d_%03d.txt" % (start, i)
            path = os.path.join(CACHE, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(out))
            print("written %s (%d entries)" % (name, (i - start + 1) % step or step))
            out = []
    if out:
        name = "digest_%03d_%03d.txt" % (start, min(end, 500) - 1)
        with open(os.path.join(CACHE, name), "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print("written %s (tail)" % name)
    if missing:
        print("missing idx:", ",".join(str(m) for m in missing))


if __name__ == "__main__":
    main()
