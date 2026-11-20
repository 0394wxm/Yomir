# -*- coding: utf-8 -*-
"""test_golden_4000.py — N60: golden_4000 完整性（test_golden_3000 同款模式）。

锁住：
  1. 4000 条、id 唯一、新增段零重复（golden_2000 自身 25 条内部重复原样保留）；
  2. 前 3000 条与 golden_3000 逐条相等且顺序一致（expected 一字不改的硬保证）；
  3. 新增 1000 条 expected 非空、白文非空、带 source_url。
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


def test_golden_4000_shape_and_uniqueness():
    g4 = _load("golden_4000.json")
    assert len(g4) == 4000
    ids = [x["id"] for x in g4]
    assert len(set(ids)) == 4000, "id 有重复"
    hbs = [x["hakubun"].strip() for x in g4]
    base_dups = len(g4[:3000]) - len({x["hakubun"].strip() for x in g4[:3000]})
    assert len(set(hbs)) == 4000 - base_dups, "新增段引入了重复白文"


def test_golden_4000_prefix_is_golden_3000():
    g3 = _load("golden_3000.json")
    g4 = _load("golden_4000.json")
    assert g4[:3000] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in g3
    ], "golden_3000 前缀被改动"


def test_golden_4000_new_rows_nonempty():
    g3 = _load("golden_3000.json")
    g4 = _load("golden_4000.json")
    old_ids = {x["id"] for x in g3}
    new = [x for x in g4 if x["id"] not in old_ids]
    assert len(new) == 1000
    for x in new:
        assert x["hakubun"].strip() and x["expected_kakikudashi"].strip()
        assert x["source_url"], "新增条缺 source_url"
