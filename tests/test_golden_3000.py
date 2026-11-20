# -*- coding: utf-8 -*-
"""test_golden_3000.py — N57: golden_3000 完整性（D16 golden_2000 检查模式同款）。

锁住：
  1. 3000 条、id 唯一、白文唯一（golden_2000 自身 25 条内部重复原样保留，
     新增部分零重复）；
  2. 前 2000 条与 golden_2000 逐条相等且顺序一致（expected 一字不改的硬保证）；
  3. 新增 1000 条 expected 非空、白文非空。
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


def test_golden_3000_shape_and_uniqueness():
    g3 = _load("golden_3000.json")
    assert len(g3) == 3000
    ids = [x["id"] for x in g3]
    assert len(set(ids)) == 3000, "id 有重复"
    # 白文唯一性：新增段不得引入重复（前 2000 条内部重复原样保留，D10 遗留）
    hbs = [x["hakubun"].strip() for x in g3]
    base_dups = len(g3[:2000]) - len({x["hakubun"].strip() for x in g3[:2000]})
    assert len(set(hbs)) == 3000 - base_dups, "新增段引入了重复白文"


def test_golden_3000_prefix_is_golden_2000():
    g2 = _load("golden_2000.json")
    g3 = _load("golden_3000.json")
    assert g3[:2000] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in g2
    ], "golden_2000 前缀被改动"


def test_golden_3000_new_rows_nonempty():
    g2 = _load("golden_2000.json")
    g3 = _load("golden_3000.json")
    old_ids = {x["id"] for x in g2}
    new = [x for x in g3 if x["id"] not in old_ids]
    assert len(new) == 1000
    for x in new:
        assert x["hakubun"].strip() and x["expected_kakikudashi"].strip()
        assert x["source_url"], "新增条缺 source_url"
