# -*- coding: utf-8 -*-
"""probe_supar_list_predict.py — supar 1.1.4 用「词列表」输入 predict 的适配探针（NIGHT5）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
import torch  # noqa: E402

_orig_load = torch.load


def _trusted_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _orig_load(*args, **kwargs)


torch.load = _trusted_load

from supar import Parser  # noqa: E402

SITE = os.environ.get("KANBUN_PYTHON_SITE", r"D:\Python312\Lib\site-packages")
f = os.path.join(SITE, "udkanbun", "supar-kanbun", "guwenbert-base.supar")
parser = Parser.load(f)
words = ["王", "顧", "左", "右", "而", "言", "他"]

for label, data in [
    ("list-of-token-lists", [words]),
    ("list-of-plain-strings", ["王顧左右而言他"]),
]:
    print("[probe]", label, flush=True)
    try:
        d = parser.predict(data, lang=None)
        arcs = d.arcs[0].tolist() if hasattr(d.arcs[0], "tolist") else list(d.arcs[0])
        print("  OK arcs=", arcs, "rels=", [r for r in d.rels[0]], flush=True)
    except Exception as e:
        print("  FAILED: %r" % (e,), flush=True)
