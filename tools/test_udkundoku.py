# -*- coding: utf-8 -*-
"""Night1 UD-Kundoku 三句实测: import / load / 返り点 / 書き下し文 (-j 等价输出)."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

SENTENCES = [
    "王顧左右而言他",
    "不入虎穴不得虎子",
    "欲治其國者先齊其家",
]

t0 = time.time()
import udkundoku  # noqa: E402  (import 时会建 QKANA, 现在应走本地 shim 不再下载)
t1 = time.time()
print("[import] udkundoku imported in %.1fs" % (t1 - t0), flush=True)

t2 = time.time()
lzh = udkundoku.load(MeCab=True, Danku=False)
t3 = time.time()
print("[load] pipeline ready in %.1fs" % (t3 - t2), flush=True)

for s in SENTENCES:
    print("=" * 30)
    print("[input]", s)
    try:
        e = lzh(s)
        print("[kaeriten]", e.kaeriten(), end="")
    except Exception as ex:
        print("[kaeriten] ERROR: %r" % (ex,))
    try:
        j = ""
        for line in udkundoku.translate(lzh(s), raw=True).split("\n"):
            if line.startswith("# text = "):
                j += line[9:] + "\n"
        print("[kundoku -j]", j, end="")
    except Exception as ex:
        print("[kundoku -j] ERROR: %r" % (ex,))
