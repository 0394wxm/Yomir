# -*- coding: utf-8 -*-
"""Night 76: weblio 補査（N74 未抓の词形のみ。既存 verdicts 底稿の再抓はしない）。"""
import os, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'eval', 'night76_dict_cache')
os.makedirs(OUTDIR, exist_ok=True)

WORDS = ['樹う', '失す', '過ぐ', '夏虫疑氷', '矣', '弗', '奚', '壁す', '一犬吠形']

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
      'Accept-Language': 'ja,en;q=0.8'}
import urllib.parse
ok, fail = 0, 0
for w in WORDS:
    url = 'https://www.weblio.jp/content/' + urllib.parse.quote(w)
    fp = os.path.join(OUTDIR, 'x_' + urllib.parse.quote(w) + '.txt')
    try:
        req = urllib.request.Request(url, headers=UA)
        html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')
        # 粗抽出:辞書本文まわりのテキスト
        import re
        m = re.search(r'<div class="wg-wph-main".*?(<div class="net-menu-top|<footer)', html, re.S)
        body = m.group(0) if m else html
        txt = re.sub(r'<script.*?</script>', '', body, flags=re.S)
        txt = re.sub(r'<style.*?</style>', '', txt, flags=re.S)
        txt = re.sub(r'<[^>]+>', '', txt)
        txt = re.sub(r'&nbsp;', ' ', txt)
        txt = re.sub(r'\n\s*\n+', '\n', txt)
        open(fp, 'w', encoding='utf-8').write(txt)
        ok += 1
        print('OK', w.encode('unicode_escape').decode()[:20], len(txt))
        time.sleep(1.0)
    except Exception as ex:
        open(fp, 'w', encoding='utf-8').write('FETCH-FAIL: %s' % ex)
        fail += 1
        print('FAIL', w.encode('unicode_escape').decode()[:20], str(ex)[:80])
        time.sleep(1.0)
print('done ok=%d fail=%d' % (ok, fail))
