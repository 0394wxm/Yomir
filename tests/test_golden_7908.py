# -*- coding: utf-8 -*-
"""test_golden_7908.py — N62: golden_7908 完整性（test_golden_4000 同款模式）。

方案A（用户拍板 2026-11-21）：kanbun.info 剩余干净文本对全部并入（无目标截断），
golden_7908 = golden_4000 前缀 4000 + 新增 3908（池剩 330 + 全站剩页 3579 − 重复）。
锁住：
  1. 7908 条、id 唯一、新增段零重复（golden_2000 自身 25 条内部重复原样保留）；
  2. 前 4000 条与 golden_4000 逐条相等且顺序一致（expected 一字不改的硬保证）；
  3. 新增 3908 条 expected 非空、白文非空、带 source_url。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

EV = os.path.join(ROOT, "eval")
N = 7908


def _load(name):
    with open(os.path.join(EV, name), encoding="utf-8") as f:
        return json.load(f)


def test_golden_7908_shape_and_uniqueness():
    g = _load("golden_%d.json" % N)
    assert len(g) == N
    ids = [x["id"] for x in g]
    assert len(set(ids)) == N, "id 有重复"
    hbs = [x["hakubun"].strip() for x in g]
    base_dups = len(g[:4000]) - len({x["hakubun"].strip() for x in g[:4000]})
    assert len(set(hbs)) == N - base_dups, "新增段引入了重复白文"


def test_golden_7908_prefix_is_golden_4000():
    g4 = _load("golden_4000.json")
    g = _load("golden_%d.json" % N)
    assert g[:4000] == [
        {"id": x["id"], "source_url": x.get("source_url", ""), "hakubun": x["hakubun"],
         "expected_kakikudashi": x["expected_kakikudashi"]} for x in g4
    ], "golden_4000 前缀被改动"


def test_golden_7908_new_rows_nonempty():
    g4 = _load("golden_4000.json")
    g = _load("golden_%d.json" % N)
    old_ids = {x["id"] for x in g4}
    new = [x for x in g if x["id"] not in old_ids]
    assert len(new) == N - 4000
    for x in new:
        assert x["hakubun"].strip() and x["expected_kakikudashi"].strip()
        assert x["source_url"], "新增条缺 source_url"
        assert "（" not in x["hakubun"] and "）" not in x["hakubun"], \
            "paren 对混进了 golden（约定未启用）: %s" % x["id"]
