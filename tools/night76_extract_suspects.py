# -*- coding: utf-8 -*-
"""Night 76 前置：合并 verdicts 缓存取存疑 43 条，与审计 entries 联接，落盘供审读。"""
import json, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
audit = json.load(open(os.path.join(ROOT, 'eval', 'night74_lexicon_audit.json'), encoding='utf-8'))
entries = {e['idx']: e for e in audit['entries']}

# 合并 verdicts（updates 文件后读，覆盖同名 idx）
verd = {}
files = sorted(glob.glob(os.path.join(ROOT, 'eval', 'night74_dict_cache', 'verdicts*.json')))
for fp in files:
    data = json.load(open(fp, encoding='utf-8'))
    for v in data:
        verd[int(v['idx'])] = v

cnt = {}
for v in verd.values():
    cnt[v['verdict']] = cnt.get(v['verdict'], 0) + 1
print('merged verdict counts:', {k.encode('unicode_escape').decode('ascii'): n for k, n in cnt.items()}, 'total', len(verd))

suspects = [v for v in sorted(verd.values(), key=lambda x: x['idx']) if v['verdict'] == '存疑']
print('suspect count =', len(suspects))
print('suspect idx:', ' '.join(str(v['idx']) for v in suspects))

buf = []
for v in suspects:
    e = entries.get(v['idx'], {})
    buf.append(json.dumps({
        'idx': v['idx'], 'word': e.get('word'), 'reading': e.get('reading'),
        'meaning': e.get('meaning'), 'kind': e.get('kind'),
        'bun_doc_hits': e.get('bun_doc_hits'), 'bun_occ': e.get('bun_occurrences'),
        'kkd_doc_hits': e.get('kkd_doc_hits'), 'kkd_occ': e.get('kkd_occurrences'),
        'n74_evidence': v.get('evidence'), 'n74_fix': v.get('fix'), 'url': v.get('url'),
    }, ensure_ascii=False))

out = os.path.join(ROOT, 'eval', 'night76_extract_suspects.txt')
open(out, 'w', encoding='utf-8').write('\n'.join(buf) + '\n')
print('written', out)
