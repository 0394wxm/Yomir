# -*- coding: utf-8 -*-
"""Night 76: ruby 補査（第2弾）。第1弾で未カバーの页。"""
import os, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    'https://kanbun.info/keibu/rongo1441.html',     # 奚れ自りする
    'https://kanbun.info/syubu/kikyorainoji.html',  # 復た奚ぞ疑わん（正确路径 syubu）
    'https://kanbun.info/koji/seikokuwoiru.html',   # 正鵠に失すれば
    'https://kanbun.info/syubu/toushisen216.html',  # 山村を失す（正确路径 syubu）
    'https://kanbun.info/keibu/daigaku00a.html',    # 頗放失す
    'https://kanbun.info/shibu02/utsuryo12.html',   # 偸失す
    'https://kanbun.info/koji/garyo.html',          # 崇飾す
    'https://kanbun.info/koji/aetenei.html',        # 栖栖・乃ち佞を為すこと無からんや
    'https://kanbun.info/koji/roushi08.html',       # 万物を利して
    'https://kanbun.info/koji/mujun.html',          # 矛の利きこと
    'https://kanbun.info/koji/aogitesho.html',      # 統理す
    'https://kanbun.info/koji/ichinitora.html',     # 三人言えば虎を成す
    'https://kanbun.info/koji/mobodanki.html',      # 孟母断機
    'https://kanbun.info/koji/kofuku.html',         # 鼓腹（含哺鼓腹）
    'https://kanbun.info/koji/toranoi.html',        # 狐を食らう
    'https://kanbun.info/koji/narai.html',          # 予弗順に狎れしめず
    'https://kanbun.info/koji/katowoida.html',      # 吾已んぬるかな（矣）
    'https://kanbun.info/keibu/rongo0608.html',     # 命なるかな（矣夫）
    'https://kanbun.info/keibu/rongo0921.html',     # 有るかな（矣夫）
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
        for base, rt in pairs:
            if len(base.strip()) <= 6:
                buf.append('%s=%s' % (base.strip(), rt.strip()))
        ok += 1
        time.sleep(0.4)
    except Exception as ex:
        buf.append('=== %s FAIL: %s ===' % (url, ex))
        fail += 1
out = os.path.join(ROOT, 'eval', 'night76_ruby2.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('ok=%d fail=%d written %s' % (ok, fail, out))
