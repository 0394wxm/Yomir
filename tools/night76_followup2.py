# -*- coding: utf-8 -*-
"""Night 76 追补2：漏れた4条（一朝一夕/凶なる/忿戻/子敬）の语料行と出处。"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
corpus = json.load(open(os.path.join(ROOT, 'eval', 'golden_8165.json'), encoding='utf-8'))
buf = []

def q(title, pred, limit=12):
    buf.append('=== %s ===' % title)
    n = 0
    for ln in corpus:
        if pred(ln):
            buf.append('id=%s src=%s' % (ln['id'], ln.get('source_url', '')))
            buf.append('  bun: ' + ln['hakubun'])
            buf.append('  kkd: ' + ln['expected_kakikudashi'])
            n += 1
            if n >= limit:
                break
    buf.append('  (shown %d)' % n)

q('一朝一夕 in bun or kkd', lambda l: ('一朝一夕' in l['hakubun']) or ('一朝一夕' in l['expected_kakikudashi']))
q('凶 in bun', lambda l: '凶' in l['hakubun'], limit=8)
q('凶 in kkd', lambda l: '凶' in l['expected_kakikudashi'], limit=8)
q('忿戻 in bun or kkd', lambda l: ('忿戻' in l['hakubun']) or ('忿戻' in l['expected_kakikudashi']))
q('子敬 in bun or kkd', lambda l: ('子敬' in l['hakubun']) or ('子敬' in l['expected_kakikudashi']))
out = os.path.join(ROOT, 'eval', 'night76_followup2.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('written', out, len(buf))
