# -*- coding: utf-8 -*-
"""day6_ocr_probe.py — 用真实样本图验证打包版 sidecar 的 OCR 仍可用。

D6 把 ocr_runtime/samples/（示例图）从包里剔掉了，必须证明剔掉的是素材、
不是运行必需。这里拿开发机上的样本图当输入，打真实 HTTP 请求。
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
IMG = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ocr_runtime", "samples", "ndl_10301438_R0000002_clean.jpg")


def post_file(url, path):
    data = open(path, "rb").read()
    boundary = "----kanbunD6"
    head = (
        "--%s\r\n"
        'Content-Disposition: form-data; name="file"; filename="%s"\r\n'
        "Content-Type: image/jpeg\r\n\r\n" % (boundary, os.path.basename(path))
    ).encode("utf-8")
    tail = ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    body = head + data + tail
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary},
        method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        payload = json.loads(r.read())
    return payload, (time.time() - t0)


def main():
    url = "http://127.0.0.1:%d/api/ocr" % PORT
    print("img:", IMG, os.path.getsize(IMG) // 1024, "KB")
    print("url:", url)
    j, sec = post_file(url, IMG)
    print("elapsed: %.1fs" % sec)
    print("status:", j.get("status"))
    print("line_count:", j.get("line_count"))
    print("elapsed_sec:", j.get("elapsed_sec"))
    hb = (j.get("hakubun") or "").strip()
    print("hakubun: %r" % (hb[:120] + ("…" if len(hb) > 120 else "")))
    if j.get("note"):
        print("note:", j["note"][:200])
    if j.get("status") != "ok":
        print("FAIL: status=%r" % j.get("status"))
        return 1
    if not hb:
        print("FAIL: hakubun 为空")
        return 1
    print("PASS: 精简包 OCR 可用（%d 字）" % len(hb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
