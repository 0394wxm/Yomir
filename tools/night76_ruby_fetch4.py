# -*- coding: utf-8 -*-
"""Night 76: ruby 補査（最終：一朝一夕・凶・忿戻・子敬・晏子再試）。"""
import os, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    'https://kanbun.info/koji/icchoisseki.html',
    'https://kanbun.info/koji/gojippo.html',
    'https://kanbun.info/koji/inishiegu.html',
    'https://kanbun.info/koji/ippanwo.html',
    'https://kanbun.info/koji/anshi.html',
]
RX = re.compile(r'<ruby>(.*?)<rp>.*?<rt>(.*?)</rt>', re.S)
buf = []
ok = fail = 0
for url in PAGES:
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', errors='replace')
            pairs = RX.findall(html)
            buf.append('=== %s (%d ruby) ===' % (url, len(pairs)))
            for b, t in pairs:
                if len(b.strip()) <= 6:
                    buf.append('%s=%s' % (b.strip(), t.strip()))
            ok += 1
            break
        except Exception as ex:
            if attempt == 1:
                buf.append('=== %s FAIL: %s ===' % (url, ex))
                fail += 1
            time.sleep(1.5)
    time.sleep(0.4)
# icchoisseki の出典行（本文外のテキスト）も拾う
try:
    req = urllib.request.Request('https://kanbun.info/koji/icchoisseki.html', headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', errors='replace')
    m = re.search(r'出典：.{0,120}', html)
    if m:
        buf.append('=== icchoisseki 出典行 ===')
        buf.append(re.sub(r'<[^>]+>', '', m.group(0)))
except Exception as ex:
    buf.append('=== icchoisseki 出典行 FAIL: %s ===' % ex)
out = os.path.join(ROOT, 'eval', 'night76_ruby4.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('ok=%d fail=%d' % (ok, fail))
