# -*- coding: utf-8 -*-
"""day16_probe_daigaku.py — 看大学/孝経索引页的章节链接与页面结构。"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (kanbun-eval-builder)"}


def get(u):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                      timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        print("[FAIL] %-44s %r" % (u, e), flush=True)
        return ""


def main():
    for pid in ("daigaku00", "kokyo00"):
        u = "https://kanbun.info/keibu/%s.html" % pid
        t = get(u)
        print("=== %s len %d ===" % (pid, len(t)), flush=True)
        links = re.findall(r'href="([^"]*?%s\d+[^"]*\.html)"' % pid[:4], t)
        print("  links:", sorted(set(links))[:20], flush=True)
        allh = sorted({h for h in re.findall(r'href="([^"]+\.html)"', t)})
        print("  all html links (%d):" % len(allh), allh[:30], flush=True)
        for cls in re.findall(r'class="([a-z0-9_]+)"', t):
            pass
        import collections
        c = collections.Counter(re.findall(r'class="([a-z0-9_]+)"', t))
        print("  classes:", c.most_common(12), flush=True)
        # 抓第一个子页看结构
        for h in allh:
            if re.search(r"\d{4}\.html$", h):
                sub = h if h.startswith("http") else "https://kanbun.info/keibu/" + h.lstrip("./")
                print("  --- subpage %s ---" % sub, flush=True)
                t2 = get(sub)
                print("      len %d genbun01 %d yomi02 %d yomi03 %d"
                      % (len(t2), t2.count('genbun01'), t2.count('yomi02'), t2.count('yomi03')),
                      flush=True)
                cc = collections.Counter(re.findall(r'class="([a-z0-9_]+)"', t2))
                print("      classes:", cc.most_common(12), flush=True)
                break


if __name__ == "__main__":
    main()
