# -*- coding: utf-8 -*-
"""fetch_github_file.py — 经 api.github.com contents API（base64）下载仓库文件。
用法: python -I tools/fetch_github_file.py <owner/repo> <path> <outfile>
（raw.githubusercontent.com 在本机被墙，api.github.com 可达）
"""
import base64
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")


def main():
    repo, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    req = urllib.request.Request(url, headers={"User-Agent": "kanbun-fetch", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("encoding") != "base64":
        print("encoding=%s size=%s — too big for contents API?" % (data.get("encoding"), data.get("size")))
        return 1
    blob = base64.b64decode(data["content"])
    with open(out, "wb") as f:
        f.write(blob)
    print("saved %d bytes -> %s (%s)" % (len(blob), out, data.get("name")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
