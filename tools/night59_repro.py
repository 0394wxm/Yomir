# -*- coding: utf-8 -*-
"""night59_repro.py — N59 第一步：复现 toushisen135-12（應知黃綺心）KeyError 并定位缺失层。

只诊断、不改引擎。要点：
  1. 原生 MeCab（mecab-kanbun 词典）对 應知黃綺心 / 応知黄綺心 的切分与特征——
     区分「词典缺 token（UNK）」vs「词典有 token 但 udkundoku 活用表缺」；
  2. udkanbun 解析层 token（form/lemma/xpos/upos）；
  3. udkundoku AUX 活用表里 應/応 的键是否存在；
  4. 引擎全链复现异常（udkundoku.translate raw=True）。
输出 eval/night59_repro.txt。
"""
import io
import os
import re
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "eval")
sys.path.insert(0, ROOT)

SENT_OLD = "應知黃綺心"   # toushisen135-12 白文（舊字体）
SENT_NEW = "応知黄綺心"   # 新字体对照

lines = []


def out(s=""):
    lines.append(s)
    print(s, flush=True)


# ---- 1. 原生 MeCab ----
from tools.mecab_shim import tagger  # noqa: E402

for label, s in (("舊字体", SENT_OLD), ("新字体", SENT_NEW)):
    out("=== 1. 原生 MeCab %s「%s」 ===" % (label, s))
    node = tagger.parseToNode(s)
    while node:
        feat = node.feature
        out("  surface=%r  feature=%s" % (node.surface, feat))
        node = node.next
    out()

# ---- 2. udkanbun 解析层 ----
import udkanbun  # noqa: E402

eng = udkanbun.UDKanbun(True, False, None)
for label, s in (("舊字体", SENT_OLD), ("新字体", SENT_NEW)):
    out("=== 2. udkanbun token %s「%s」 ===" % (label, s))
    try:
        entry = eng(s)
        for t in entry._tokens:
            out("  id=%s form=%r lemma=%r xpos=%r upos=%r" % (
                t.id, t.form, t.lemma, t.xpos, t.upos))
    except Exception as e:
        out("  解析层异常: %r" % (e,))
    out()

# ---- 3. udkundoku AUX 活用表 ----
import udkundoku  # noqa: E402

out("=== 3. udkundoku AUX 活用表 ===")
aux = getattr(udkundoku, "AUX", None)
if aux is None:
    out("  udkundoku 模块级无 AUX（可能在函数内/别处）")
else:
    keys = [k for k in aux if "助動詞" in k]
    out("  助動詞类键 %d 个，含「応」的: %s" % (len(keys), [k for k in keys if "応" in k]))
    out("  含「應」的: %s" % [k for k in keys if "應" in k])
    probe = "応,v,助動詞,必要,*"
    out("  键 %r 存在: %s" % (probe, probe in aux))
    probe2 = "應,v,助動詞,必要,*"
    out("  键 %r 存在: %s" % (probe2, probe2 in aux))
    out()
    # AUX 里与 应/応 同 xpos 的邻居键（看活用表的键形状）
    near = [k for k in aux if ",v,助動詞,必要,*" in k]
    out("  xpos=v,助動詞,必要 的全部键: %s" % near)

# ---- 4. 全链复现 ----
out("\n=== 4. 引擎全链（udkundoku.translate raw=True）===")
for label, s in (("新字体", SENT_NEW), ("舊字体", SENT_OLD)):
    try:
        kk = udkundoku.translate(eng(s), raw=True)
        out("  %s「%s」 → %r" % (label, s, kk))
    except Exception as e:
        out("  %s「%s」 异常: %s: %s" % (label, s, type(e).__name__, e))
        tb = traceback.format_exc().strip().splitlines()[-3:]
        for l in tb:
            out("    " + l)

io.open(os.path.join(EV, "night59_repro.txt"), "w", encoding="utf-8",
        newline="\n").write("\n".join(lines) + "\n")
print("\nwritten: eval/night59_repro.txt", flush=True)
