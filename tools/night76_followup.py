# -*- coding: utf-8 -*-
"""Night 76 追补：golden_8165 内の個別照会（所謂達/貳弐/失す/止する/矣かな/而替换/牧す全行/愈れ全行）。"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
corpus = json.load(open(os.path.join(ROOT, 'eval', 'golden_8165.json'), encoding='utf-8'))
buf = []

def q(title, pred, limit=20, show_bun=True):
    buf.append('=== %s ===' % title)
    n = 0
    for ln in corpus:
        if pred(ln):
            buf.append('id=%s src=%s' % (ln['id'], ln.get('source_url', '')))
            if show_bun:
                buf.append('  bun: ' + ln['hakubun'])
            buf.append('  kkd: ' + ln['expected_kakikudashi'])
            n += 1
            if n >= limit:
                break
    buf.append('  (shown %d)' % n)

# 1) 所謂達 の白文行
q('SOGEKITATSU bun contains 所謂達', lambda l: '所謂達' in l['hakubun'])

# 2) kkd に 貳/弐 を含む行（全）
q('KKD contains 貳 or 弐', lambda l: ('貳' in l['expected_kakikudashi']) or ('弐' in l['expected_kakikudashi']))

# 3) kkd に 失す を含む行（全）
q('KKD contains 失す', lambda l: '失す' in l['expected_kakikudashi'])

# 4) kkd に 止する/止め/止ま を含むが や/む系 でない例 — 止する行
q('KKD contains 止する', lambda l: '止する' in l['expected_kakikudashi'])
q('KKD contains 止むる or 止むな', lambda l: ('止むる' in l['expected_kakikudashi']) or ('止むな' in l['expected_kakikudashi']), limit=8)

# 5) bun に 矣、かつ kkd が かな で終わる行（詠嘆助字 かな の例）
def tail_kana(l):
    k = l['expected_kakikudashi']
    b = l['hakubun']
    return ('矣' in b) and bool(re.search(r'(かな|しか|や)[。！]?\s*$', k))
q('bun 矣 & kkd tail かな/しか/や', tail_kana, limit=15)
# かな全般の行末（bun 矣有無別）
n = sum(1 for l in corpus if re.search(r'かな[。]\s*$', l['expected_kakikudashi']))
buf.append('=== kkd ends with かな。 total: %d ===' % n)

# 6) bun に 而、kkd に 而 無し の短行サンプル（而の置換形態を観察）
def eri(l):
    return ('而' in l['hakubun']) and ('而' not in l['expected_kakikudashi']) and len(l['hakubun']) <= 40
q('bun 而 & kkd no-而 short samples', eri, limit=25)

# 7) 牧す の kkd 行（全5）
q('KKD contains 牧す (all)', lambda l: '牧す' in l['expected_kakikudashi'], limit=10)

# 8) 愈れ を含む kkd 行（全19のうち短い方）
q('KKD contains 愛れ/愈れ', lambda l: ('愈れ' in l['expected_kakikudashi']), limit=25)

# 9) kkd 釈て/釈つ vs 釈す 分布
c1 = sum(l['expected_kakikudashi'].count('釈て') for l in corpus)
c2 = sum(l['expected_kakikudashi'].count('釈つ') for l in corpus)
c3 = sum(l['expected_kakikudashi'].count('釈す') for l in corpus)
buf.append('=== kkd 釈て=%d 釈つ=%d 釈す=%d ===' % (c1, c2, c3))
q('KKD contains 釈て', lambda l: '釈て' in l['expected_kakikudashi'], limit=10)

# 10) 貳す の関連: bun/kkd に 貳師/貳过 以外
q('bun contains 貳 or 弐', lambda l: ('貳' in l['hakubun']) or ('弐' in l['hakubun']), limit=10)

# 11) 三人成虎 系 kkd（ichinitora 全行）
q('id ichinitora', lambda l: l['id'].startswith('ichinitora'), limit=12)

# 12) kofuku-x15 の kkd（鼓腹の行）
q('id kofuku', lambda l: l['id'].startswith('kofuku'), limit=20)

# 13) mobodanki 全行
q('id mobodanki', lambda l: l['id'].startswith('mobodanki'), limit=12)

# 14) ikken 全行（一犬吠形）
q('id ikken', lambda l: l['id'].startswith('ikken'), limit=12)

# 15) akujisenri-2 / seia-2 / seia-3 / aogitesho-1 / asobunika-1 / toushisen453-4
ids = ['akujisenri-2', 'seia-2', 'seia-3', 'aogitesho-1', 'asobunika-1', 'toushisen453-4',
       'shimen-1', 'rongo1115-1', 'shushu-3', 'chosan-1', 'ichinenkoku-1', 'mizutsumori-1', 'gashin-x17']
for i in ids:
    q('id == %s' % i, lambda l, i=i: l['id'] == i, limit=2)

out = os.path.join(ROOT, 'eval', 'night76_followup.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('written', out, len(buf), 'lines')
