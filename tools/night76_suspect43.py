# -*- coding: utf-8 -*-
"""Night 76: 存疑 43 条 × golden_8165 语料实例对照（N75 舎案的方法）。

对每条存疑词，在 golden_8165 中找白文与書き下し文的相关行，提取语料实际用的
送り仮名/活用形分布与对齐样本，落盘 eval/night76_matches.json 供逐条判定。
只读语料与词库，不评测、不改 backend。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GOLDEN = os.path.join(ROOT, 'eval', 'golden_8165.json')
OUT = os.path.join(ROOT, 'eval', 'night76_matches.json')

corpus = json.load(open(GOLDEN, encoding='utf-8'))

# ---------------------------------------------------------------- 每条定义
# bun: 白文搜索词（list，任一命中即算行命中）；kkd: 書き下し文搜索词
# suffix: (可选) 对 kkd 命中处取后方 2 字统计送り仮名分布
# pairs: 采样行数（取白文/書下成对样本；尽量选短行、单命中行）
# kkd_sample: 单独采样書下文（不要求白文也命中）
ENTRIES = [
    # ---- A 类：语料特有形/复合训读公式 ----
    dict(idx=61,  word='所謂達',   bun=['所謂達'], kkd=['所謂達', '所謂'], pairs=3, kkd_sample=5),
    dict(idx=69,  word='牧す',    bun=['牧す'], kkd=['牧す'], pairs=5, kkd_sample=8),
    dict(idx=71,  word='狙',      bun=['狙'], kkd=['狙'], pairs=5, kkd_sample=8),
    dict(idx=76,  word='釈て',    bun=['釈'], kkd=['釈'], pairs=6, kkd_sample=8),
    dict(idx=82,  word='壁す',    bun=['壁'], kkd=['壁'], pairs=5, kkd_sample=8),
    dict(idx=111, word='夏虫',    bun=['夏虫'], kkd=['夏虫'], pairs=3, kkd_sample=6),
    dict(idx=112, word='曲士',    bun=['曲士'], kkd=['曲士'], pairs=3, kkd_sample=6),
    dict(idx=116, word='三人虎',  bun=['三人虎', '三人成虎'], kkd=['三人虎', '三人成虎', '三人'], pairs=3, kkd_sample=5),
    dict(idx=117, word='一犬吠形', bun=['一犬吠形', '吠形'], kkd=['一犬', '吠'], pairs=3, kkd_sample=5),
    dict(idx=120, word='栖栖',    bun=['栖栖'], kkd=['栖栖'], pairs=3, kkd_sample=5),
    dict(idx=129, word='食ぶ',    bun=['食ぶ', '狐'], kkd=['食ぶ', '狐'], pairs=4, kkd_sample=6),
    dict(idx=131, word='貳す',    bun=['貳', '弐'], kkd=['貳', '弐'], pairs=4, kkd_sample=6),
    dict(idx=133, word='統理す',  bun=['統理'], kkd=['統理'], pairs=3, kkd_sample=5),
    dict(idx=134, word='崇飾す',  bun=['崇飾'], kkd=['崇飾'], pairs=3, kkd_sample=5),
    dict(idx=138, word='焚毀す',  bun=['焚毀'], kkd=['焚毀'], pairs=3, kkd_sample=5),
    dict(idx=139, word='洎び',    bun=['洎'], kkd=['洎'], pairs=3, kkd_sample=5),
    dict(idx=145, word='方有り',  bun=['方有'], kkd=['方有'], pairs=3, kkd_sample=5),
    dict(idx=166, word='奚',      bun=['奚'], kkd=['奚'], pairs=10, kkd_sample=14),
    dict(idx=169, word='愈れる',  bun=['愈'], kkd=['愈'], pairs=5, kkd_sample=6),
    dict(idx=172, word='噫',      bun=['噫'], kkd=['噫'], pairs=5, kkd_sample=7),
    # ---- B 类：读音差一拍（送り仮名分布为重点）----
    dict(idx=365, word='過',     bun=['過'], kkd=['過'], pairs=8, kkd_sample=10,
         suffix=r'過(.{0,2})', suffix_group=1),
    dict(idx=374, word='失',     bun=['失'], kkd=['失'], pairs=8, kkd_sample=10,
         suffix=r'失(.{0,2})', suffix_group=1),
    dict(idx=383, word='布',     bun=['布'], kkd=['布'], pairs=8, kkd_sample=10,
         suffix=r'布(.{0,2})', suffix_group=1),
    dict(idx=402, word='止',     bun=['止'], kkd=['止'], pairs=8, kkd_sample=10,
         suffix=r'止(.{0,2})', suffix_group=1),
    dict(idx=416, word='樹',     bun=['樹'], kkd=['樹'], pairs=8, kkd_sample=10,
         suffix=r'樹(.{0,2})', suffix_group=1),
    dict(idx=453, word='直',     bun=['直'], kkd=['直'], pairs=8, kkd_sample=10,
         suffix=r'直(.{0,2})', suffix_group=1),
    dict(idx=474, word='矣',     bun=['矣'], kkd=['矣'], pairs=10, kkd_sample=10, tail=True),
    dict(idx=480, word='而',     bun=['而'], kkd=['而'], pairs=12, kkd_sample=12,
         suffix=r'而(.{0,2})', suffix_group=1, tail=True),
    dict(idx=494, word='未',     bun=['未'], kkd=['未'], pairs=8, kkd_sample=10,
         suffix=r'未(.{0,2})', suffix_group=1),
    dict(idx=498, word='弗',     bun=['弗'], kkd=['弗'], pairs=8, kkd_sample=8, tail=True),
    # ---- C 类：释义附加语 ----
    dict(idx=0,  word='乃ち',   bun=['乃ち'], kkd=['乃ち'], pairs=10, kkd_sample=12),
    dict(idx=5,  word='且つ',   bun=['且つ'], kkd=['且つ'], pairs=8, kkd_sample=10),
    dict(idx=26, word='大いに', bun=['大いに'], kkd=['大いに'], pairs=8, kkd_sample=10),
    dict(idx=43, word='孰',     bun=['孰'], kkd=['孰'], pairs=8, kkd_sample=10),
    dict(idx=185, word='利し',  bun=['利し', '利き'], kkd=['利し', '利き'], pairs=8, kkd_sample=10),
    # ---- 死条目候选补查 ----
    dict(idx=75,  word='冀ふ',   bun=['冀'], kkd=['冀'], pairs=3, kkd_sample=3),
    dict(idx=104, word='鼓腹撃壌', bun=['鼓腹'], kkd=['鼓腹'], pairs=3, kkd_sample=3),
    dict(idx=127, word='㡯',     bun=['㡯'], kkd=['㡯'], pairs=1, kkd_sample=1),
    dict(idx=207, word='孟母断機', bun=['孟母', '断機'], kkd=['孟母', '断機'], pairs=3, kkd_sample=3),
]

def frag(text, pos, width=14):
    a = max(0, pos - width)
    b = min(len(text), pos + width)
    return ('…' if a > 0 else '') + text[a:b] + ('…' if b < len(text) else '')

results = []
for spec in ENTRIES:
    idx = spec['idx']
    res = dict(idx=idx, word=spec['word'], bun_words=spec['bun'], kkd_words=spec['kkd'])
    # 白文命中行
    bun_lines = []
    for ln in corpus:
        for w in spec['bun']:
            p = ln['hakubun'].find(w)
            if p >= 0:
                bun_lines.append((ln, w, p))
                break
    # 書下命中行
    kkd_lines = []
    for ln in corpus:
        for w in spec['kkd']:
            p = ln['expected_kakikudashi'].find(w)
            if p >= 0:
                kkd_lines.append((ln, w, p))
                break
    res['bun_doc_hits'] = len(set(l['id'] for l, _, _ in bun_lines))
    res['bun_occ'] = sum(l['hakubun'].count(w) for l, w, _ in bun_lines)
    res['kkd_doc_hits'] = len(set(l['id'] for l, _, _ in kkd_lines))
    res['kkd_occ'] = sum(l['expected_kakikudashi'].count(w) for l, w, _ in kkd_lines)

    # 送り仮名分布（kkd）
    if spec.get('suffix'):
        dist = {}
        rx = re.compile(spec['suffix'])
        for ln, _, _ in kkd_lines:
            for m in rx.finditer(ln['expected_kakikudashi']):
                dist[m.group(spec['suffix_group'])] = dist.get(m.group(spec['suffix_group']), 0) + 1
        res['kkd_suffix_dist'] = dict(sorted(dist.items(), key=lambda kv: -kv[1]))
    if spec.get('tail'):
        tails = {}
        for ln, _, _ in kkd_lines:
            t = ln['expected_kakikudashi'][-4:]
            tails[t] = tails.get(t, 0) + 1
        res['kkd_tail_dist'] = dict(sorted(tails.items(), key=lambda kv: -kv[1])[:12])

    # 成对样本：优先白文与書下都命中、行短、白文单命中
    bun_ids = dict((l['id'], (l, w, p)) for l, w, p in bun_lines)
    kkd_ids = dict((l['id'], (l, w, p)) for l, w, p in kkd_lines)
    cand = [lid for lid in bun_ids if lid in kkd_ids and len(bun_ids[lid][0]['hakubun']) <= 40]
    cand += [lid for lid in kkd_ids if lid not in bun_ids and len(kkd_ids[lid][0]['hakubun']) <= 40]
    cand += [lid for lid in bun_ids if lid not in kkd_ids]
    seen, samples = set(), []
    if not cand:  # 行全部超长时的回退：不筛长度
        cand = [lid for lid in bun_ids if lid in kkd_ids] + [lid for lid in kkd_ids if lid not in bun_ids] + list(bun_ids)
    for lid in cand:
        if lid in seen:
            continue
        seen.add(lid)
        l, bw, bp = bun_ids.get(lid, (kkd_ids.get(lid, (None, None, None))[0], None, None))
        ke = kkd_ids.get(lid)
        kw, kp = (ke[1], ke[2]) if ke else (None, None)
        s = dict(id=lid,
                 bun=frag(l['hakubun'], bp) if bp is not None else None,
                 kkd=frag(l['expected_kakikudashi'], kp) if kp is not None else None,
                 bun_word=bw, kkd_word=kw)
        if spec.get('tail'):
            s['kkd_tail'] = l['expected_kakikudashi'][-8:]
        samples.append(s)
        if len(samples) >= spec.get('pairs', 5):
            break
    res['samples'] = samples
    results.append(res)
    print('idx %3d %-10s bun=%4d/%4d kkd=%4d/%4d samples=%d' % (
        idx, spec['word'].encode('unicode_escape').decode('ascii'), res['bun_doc_hits'], res['bun_occ'],
        res['kkd_doc_hits'], res['kkd_occ'], len(samples)))

json.dump(results, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('written', OUT)
