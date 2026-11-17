# -*- coding: utf-8 -*-
"""probe_supar_file_predict.py — 检验 supar 1.1.4 用文件路径 predict 是否能出 feats（NIGHT5）。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
import torch  # noqa: E402

_orig_load = torch.load


def _trusted_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _orig_load(*args, **kwargs)


torch.load = _trusted_load

import udkanbun  # noqa: E402
from udkanbun.supar import SuParAPI  # noqa: E402
from udkanbun.udkanbun import UDKanbun  # noqa: E402

SITE = os.environ.get("KANBUN_PYTHON_SITE", r"D:\Python312\Lib\site-packages")
f = os.path.join(SITE, "udkanbun", "supar-kanbun", "guwenbert-base.supar")

pipe = UDKanbun(True, False, "guwenbert-base")
spar = pipe.udpipe  # SuParAPI
print("[fields]", spar.supar.transform.fields, flush=True)

u = pipe("王顧左右而言他", raw=True)  # conllu 字符串（MeCab-kanbun 分词结果）
print("[conllu]", u.replace("\n", " | ")[:200], flush=True)

tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "supar_probe.conllu")
with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(u)

print("[probe] predict(data=FILE) ...", flush=True)
try:
    d = spar.supar.predict(tmp, lang=None, pred=tmp + ".pred")
    print("[probe] OK — arcs:", len(d["arcs"]), flush=True)
    with open(tmp + ".pred", encoding="utf-8") as fh:
        print(fh.read()[:400], flush=True)
except Exception as e:
    import traceback

    traceback.print_exc()
    print("[probe] FAILED: %r" % (e,), flush=True)
