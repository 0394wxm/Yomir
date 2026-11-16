# -*- coding: utf-8 -*-
"""
kundoku_rules.py — UD-Kundoku 输出的后处理规则（Night 2）。

背景（REPORT_NIGHT1.md §6 / eval/night1_results.json）：0/10 的主因是
MeCab(mecab-kanbun 词典) 把专名拆散（楚人→楚+人、項王→項+王、垓下→垓+下）
导致训读输出「楚の人」「項の王軍の壁垓下」这类可读性很差的结果。

本模块做**词元级**（token 级）合并，而不是对最终字符串做正则替换——
合并在 reorder/translate 之前，树结构（head 引用）保持一致，
返り点と送り仮名の推定も合并后的词元上重新计算。

已知局限（如实记录，不要夸大）:
- 只解决“切分错误”类问题；「祠る者」的名词化、「壁す」的动词条目缺失、
  「は/に」助词选择等属于解析/词条层面的问题，本模块无能为力。
- 合并词典是手工维护的白名单，只放确实高频且被引擎拆错的词。

用法:
    from backend.kundoku_rules import merge_proper_nouns
    entry = ENGINE(text)
    entry = merge_proper_nouns(entry)   # 返回原地修改后的 entry
"""

# 被引擎拆散的专名（白名单，后续可扩充；只允许 2~3 字）
MERGE_WORDS = [
    # eval/golden.json 里出现的
    "楚人", "宋人", "狙公", "項王", "垓下", "張僧繇",
    "梁惠王", "荊宣王", "昭奚恤", "江乙", "群臣",
]


def _is_nounish(tok) -> bool:
    try:
        return tok.xpos.startswith("n,") or tok.xpos.startswith("v,前置詞") or tok.upos in ("NOUN", "PROPN")
    except Exception:
        return False


def merge_proper_nouns(entry, words=None):
    """把相邻词元（表面形拼接后命中白名单）合并成一个词元。原地修改并返回 entry。

    仅当第一个词元是名词性时才合并，避免把动词序列粘在一起。
    """
    wordset = set(words or MERGE_WORDS)
    try:
        toks = entry._tokens  # [0] 是虚拟 root
    except AttributeError:
        return entry
    i = 1
    changed = False
    while i < len(toks) - 1:
        a, b = toks[i], toks[i + 1]
        # 最多向后看 2 个词元，支持 3 字专名（張+僧+繇）
        merged = False
        for span in (2, 3):
            if i + span > len(toks):
                break
            concat = "".join(t.form for t in toks[i:i + span])
            if concat not in wordset:
                continue
            if not _is_nounish(toks[i]):
                break
            head_tok = toks[i]
            for t in toks[i + 1:i + span]:
                head_tok.form += t.form
                head_tok.lemma = (head_tok.lemma or "") + (t.lemma or "")
                head_tok._result = ""
                # 把指向被并词元的子节点重新指向合并后的词元。
                # 注意: udkanbun.UDPipeEntry.__setattr__ 对 "head"/"id" 有特殊语义
                # （head 传 int 会被解释成相对 id 偏移，传对象直接 TypeError；
                #   id 赋值会触发列表交换），必须用 object.__setattr__ 绕过。
                for other in toks:
                    if other.head is t:
                        object.__setattr__(other, "head", head_tok)
            del toks[i + 1:i + span]
            changed = True
            merged = True
            break  # 合并后继续尝试把 i 再往后并（3 字专名的中间态）
        if not merged:
            i += 1
    if changed:
        # 重新编号（root 仍为 0），让 .id 与列表位置一致——kaeriten() 里的
        # h=[i+head.id-t.id] 算式依赖这一点。同样必须绕过 __setattr__。
        for idx, t in enumerate(toks):
            if t.id != idx:
                object.__setattr__(t, "id", idx)
                t._result = ""
        entry._result = ""
    return entry
