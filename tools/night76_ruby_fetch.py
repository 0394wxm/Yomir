# -*- coding: utf-8 -*-
"""Night 76: 语料出处页 (kanbun.info) の振り仮名（ruby）を一括取得して落盘。
golden_8165 の source_url と同じ页。每页 (漢字, ruby) 対を抽出。"""
import json, os, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
corpus = json.load(open(os.path.join(ROOT, 'eval', 'golden_8165.json'), encoding='utf-8'))

# 対象页：43 条の判定に関わる行の出处
PAGES = [
    'https://kanbun.info/keibu/rongo1115.html',    # 愈れる
    'https://kanbun.info/koji/ichiwokiite.html',   # 愈れる
    'https://kanbun.info/koji/ayamachifu.html',    # 弐びせず
    'https://kanbun.info/koji/ishoku.html',        # 牧す（民を牧す）
    'https://kanbun.info/syubu/toushisen453.html', # 牧馬
    'https://kanbun.info/shibu02/rikutou08.html',  # 聖人之を牧す
    'https://kanbun.info/shibu02/sanryaku01.html', # 司牧す
    'https://kanbun.info/koji/shimen.html',        # 壁す
    'https://kanbun.info/koji/chosan.html',        # 狙公
    'https://kanbun.info/koji/seia.html',          # 夏虫・曲士
    'https://kanbun.info/koji/ichinenkoku.html',   # 樹うる
    'https://kanbun.info/koji/mizutsumori.html',   # 樹う
    'https://kanbun.info/koji/gashin.html',        # 樹えよ
    'https://kanbun.info/koji/asobunika.html',     # 方有り
    'https://kanbun.info/koji/ikken.html',         # 一犬吠形
    'https://kanbun.info/koji/shushu.html',        # 釈てて・冀う
    'https://kanbun.info/koji/akujisenri.html',    # 洎び・焚毀す
    'https://kanbun.info/koji/omonpaku.html',      # 所謂達
    'https://kanbun.info/keibu/rongo0302.html',    # 奚んぞ
    'https://kanbun.info/koji/ooshitoie.html',     # 奚を以て為さん
    'https://kanbun.info/shibu02/montai15.html',   # 奚（部族）
    'https://kanbun.info/koji/kikyorainoji.html',  # 奚ぞ疑わん
    'https://kanbun.info/keibu/rongo0918.html',    # 止む
    'https://kanbun.info/koji/uka.html',           # 止まる所
    'https://kanbun.info/shibu02/utsuryo10.html',  # 止むる（奸を止むる）
    'https://kanbun.info/shibu02/utsuryo11.html',  # 渇を止むる
    'https://kanbun.info/koji/kasei.html',         # 過ぐ（泰山の側を過ぐ）
    'https://kanbun.info/koji/moshisono.html',     # 失い
    'https://kanbun.info/koji/kyokutotsu.html',    # 火を失す
    'https://kanbun.info/shibu02/toushisen216.html',# 山村を失す
    'https://kanbun.info/keibu/rongo0617.html',    # 直し
    'https://kanbun.info/koji/intoku.html',        # 布き恵を施す
    'https://kanbun.info/koji/imadasei.html',      # 未だ人に事うること能わず
    'https://kanbun.info/koji/aatenware.html',     # 噫、天予を喪ぼせり
    'https://kanbun.info/koji/roraku.html',        # 雲のごとく布く
    'https://kanbun.info/koji/ryou.html',          # 耒を釈て
    'https://kanbun.info/koji/yokonou.html',       # 釈てて撃たざる
    'https://kanbun.info/koji/nawotada.html',      # 奚をか先にせん
]

RX = re.compile(r'<ruby>(.*?)<rp>.*?<rt>(.*?)</rt>', re.S)

buf = []
ok, fail = 0, 0
for url in PAGES:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')
        pairs = RX.findall(html)
        buf.append('=== %s (%d ruby) ===' % (url, len(pairs)))
        for base, rt in pairs:
            base = base.strip()
            rt = rt.strip()
            if len(base) <= 6:
                buf.append('%s=%s' % (base, rt))
        ok += 1
        time.sleep(0.4)
    except Exception as ex:
        buf.append('=== %s FAIL: %s ===' % (url, ex))
        fail += 1

out = os.path.join(ROOT, 'eval', 'night76_ruby.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('ok=%d fail=%d written %s' % (ok, fail, out))
