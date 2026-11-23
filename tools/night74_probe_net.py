# -*- coding: utf-8 -*-
"""night74_probe_net.py — N74 辞書サイト到達性プローブ（軽量、GET のみ）。

对候选词典站点各发 1 个 GET（超时 15s），把状态码/字节数/前 300 字写成
eval/night74_dict_cache/probe.txt（UTF-8，CJK 落盘再读，不走控制台）。
只读探测，不写任何业务数据。
"""
import os
import ssl
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "eval", "night74_dict_cache")
OUT = os.path.join(OUTDIR, "probe.txt")
os.makedirs(OUTDIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Night74Audit/1.0"}
WORD = urllib.parse.quote("乃ち")

TARGETS = [
    ("kobun.weblio (古語辞典)", "https://kobun.weblio.jp/content/" + WORD),
    ("kotobank", "https://kotobank.jp/word/" + WORD),
    ("www.weblio", "https://www.weblio.jp/content/" + WORD),
    ("goo辞書", "https://dictionary.goo.ne.jp/word/" + WORD + "/"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE  # 审计用途，允许自签/老证书；只 GET 公开页

lines = []
for name, url in TARGETS:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            body = resp.read()
        text = body.decode("utf-8", "replace")
        lines.append("=== %s | %s | status=%d bytes=%d" % (name, url, resp.status if hasattr(resp, "status") else 200, len(body)))
        snippet = " ".join(text.split())[:300]
        lines.append("SNIPPET: " + snippet)
    except Exception as e:
        lines.append("=== %s | %s | ERROR: %r" % (name, url, e))
    lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("written", OUT)
