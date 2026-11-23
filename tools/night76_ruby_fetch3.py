# -*- coding: utf-8 -*-
"""Night 76: ruby 補査（第3弾：老子・晏子・論語微生畝・正名）。"""
import os, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    'https://kanbun.info/shibu02/roushi08.html',    # 万物を利して（利す サ変?）
    'https://kanbun.info/shibu02/roushi81.html',    # 利して害せず
    'https://kanbun.info/koji/anshi.html',          # 乃ち人の僕御たり（晏子の御）
    'https://kanbun.info/keibu/rongo1217.html',     # 孰か敢えて正しからざらん
    'https://kanbun.info/keibu/rongo0315.html',     # 孰か鄹人の子を
]
RX = re.compile(r'<ruby>(.*?)<rp>.*?<rt>(.*?)</rt>', re.S)
buf = []
ok = fail = 0
for url in PAGES:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')
        pairs = RX.findall(html)
        buf.append('=== %s (%d ruby) ===' % (url, len(pairs)))
        for b, t in pairs:
            if len(b.strip()) <= 6:
                buf.append('%s=%s' % (b.strip(), t.strip()))
        ok += 1
        time.sleep(0.4)
    except Exception as ex:
        buf.append('=== %s FAIL: %s ===' % (url, ex))
        fail += 1
out = os.path.join(ROOT, 'eval', 'night76_ruby3.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('ok=%d fail=%d' % (ok, fail))
