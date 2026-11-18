# -*- coding: utf-8 -*-
"""
build_parallel_corpus.py — Night 28：全站平行语料库（Kanbun-LM 数据集思路复现，本地版）。

HF 镜像无 Kanbun-LM 数据集可取（night28_probe_kanbunlm.py 实测 0 hit），
「思路复现」落地为：用既有 build_golden 抓取器（一行不改）把 kanbun.info 故事名言
全站 1138 页的白文/書き下し文成对文本抓全，作为将来模型路线的本地平行语料。

安全约束同 Night 26：golden.json 字节级备份恢复；产物 eval/kanbun_parallel.json。
"""
import importlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
GOLDEN = os.path.join(ROOT, "eval", "golden.json")
OUT = os.path.join(ROOT, "eval", "kanbun_parallel.json")


def main():
    with open(GOLDEN, "rb") as f:
        orig = f.read()
    orig_ids = {x["id"] for x in json.loads(orig.decode("utf-8"))}

    os.environ["GOLDEN_TOTAL"] = "5000"
    os.environ["GOLDEN_PER_PAGE"] = "10"
    bg = importlib.import_module("build_golden")
    importlib.reload(bg)
    bg.main()

    with open(GOLDEN, "rb") as f:
        new = f.read()
    doc = json.loads(new.decode("utf-8"))
    with open(GOLDEN, "wb") as f:
        f.write(orig)  # 字节级恢复
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)

    ids = [x["id"] for x in doc]
    pages = {x["source_url"] for x in doc}
    print("=== 对账 ===")
    print("corpus %d 对，来自 %d 个页面；与 golden.json id 交集 %d"
          % (len(doc), len(pages), len(orig_ids & set(ids))))
    print("written:", OUT)


if __name__ == "__main__":
    main()
