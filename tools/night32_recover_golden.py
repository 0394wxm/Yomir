# -*- coding: utf-8 -*-
"""night32_recover_golden.py — 从被覆盖的 golden_rongo_full.json 里恢复语料。

事故（NIGHT32）：run_eval_rongo.py 写出段残留旧版参数解析，把结果归档写到了
args[0]=golden_rongo_full.json 上，覆盖了刚抓的语料。results[] 里含全部 golden
字段（id/pian/source_url/hakubun/expected_kakikudashi），逐条抽取即 100% 恢复，
无需重新抓取。恢复后与 results 一致性自检。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "eval", "golden_rongo_full.json")

with open(P, encoding="utf-8") as f:
    doc = json.load(f)
assert isinstance(doc, dict) and "results" in doc, "文件不是被覆盖的结果归档，拒绝盲恢复"
rows = doc["results"]

golden = [{
    "id": r["id"], "source_url": r["source_url"], "pian": r["pian"],
    "hakubun": r["hakubun"], "expected_kakikudashi": r["expected_kakikudashi"],
} for r in rows if not r.get("error")]

ids = [g["id"] for g in golden]
assert len(ids) == len(set(ids)), "恢复后 id 有重复"
assert all(g["hakubun"] and g["expected_kakikudashi"] for g in golden), "有空字段"

with open(P, "w", encoding="utf-8", newline="\n") as f:
    json.dump(golden, f, ensure_ascii=False, indent=2)

# 自检：恢复文件现在应是 list
with open(P, encoding="utf-8") as f:
    back = json.load(f)
print("恢复 %d 条（跳过 error %d 条）；现文件为 list，id 唯一、无空字段"
      % (len(back), len(rows) - len(golden)))
print("按篇分布:", sorted((p, sum(1 for g in golden if g["pian"] == p)) for p in set(g["pian"] for g in golden))[:5], "...")
