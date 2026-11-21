# -*- coding: utf-8 -*-
"""test_golden_8165.py — N67⑲: golden_8165 完整性（test_golden_7908 同款模式）。

锁住：
  1. 8165 条、id 唯一、新增段零重复（golden_2000 自身 25 条内部重复原样保留）；
  2. 前 7908 条与 golden_7908 逐条相等且顺序一致（expected 一字不改的硬保证）；
  3. 新增 257 条（N62 paren 对启用）expected 非空、白文非空、带 source_url，
     且 id 集合与 night62_scraped_10k.json 的 paren 标记完全一致（出处锁定）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

EV = os.path.join(ROOT, "eval")


def _load(name):
    with open(os.path.join(EV, name), encoding="utf-8") as f:
        return json.load(f)


def test_golden_8165_shape_and_uniqueness():
    g = _load("golden_8165.json")
    assert len(g) == 8165
    ids = [x["id"] for x in g]
    assert len(set(ids)) == 8165, "id 有重复"
    hbs = [x["hakubun"].strip() for x in g]
    base_dups = len(g[:7908]) - len({x["hakubun"].strip() for x in g[:7908]})
    assert len(set(hbs)) == 8165 - base_dups, "新增段引入了重复白文"


def test_golden_8165_prefix_is_golden_7908():
    g8 = _load("golden_7908.json")
    g = _load("golden_8165.json")
    assert g[:7908] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in g8
    ], "golden_7908 前缀被改动"


def test_golden_8165_new_rows_nonempty_and_paren_provenance():
    g8 = _load("golden_7908.json")
    g = _load("golden_8165.json")
    old_ids = {x["id"] for x in g8}
    new = [x for x in g if x["id"] not in old_ids]
    assert len(new) == 257
    for x in new:
        assert x["hakubun"].strip() and x["expected_kakikudashi"].strip()
        assert x["source_url"], "新增条缺 source_url"
    scraped = _load("night62_scraped_10k.json")
    paren_ids = {r["id"] for r in scraped if r.get("_quality") == "paren"}
    assert {x["id"] for x in new} == paren_ids, "新增段 id 与 N62 paren 标记集合不一致"
