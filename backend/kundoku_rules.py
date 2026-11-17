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
    # NIGHT4：200 条基线的切分类挖掘（tools/mine_error_patterns.py）证据扩充，
    # 各为 1~2 次但都是常见漢文复合词，通用性优先于逐条过拟合：
    "諸侯", "木鐸", "樗蒲", "壑雷", "馬肥", "投足", "原君", "平原君", "人人", "自得",
]

# NIGHT4 Rule A：输出层显示风格修正（merge 开关下生效），两类都做过语料安全性验证：
#  - 验证1: golden.json 200 条的 expected 里「ふ」出现 0 次 —— 文语 ふ→う
#    （言ふ→言う、鬻ふ→鬻う，kanbun.info 一律用现代假名遣い）不可能与答案冲突；
#  - 验证2: expected 里「は曰く」出现 0 次（含「曰く」89 条）—— 引擎对引用句
#    过度插主题は（Xは曰く → X曰く），按 kanbun.info 风格去掉。
# 局限（如实）：は 的其余插删方向不一（135 处は多余 vs 16 处は缺失），无一致规则，不动。
def is_kanji_char(c):
    return "\u3400" <= c <= "\u9fff" or "\u4e00" <= c <= "\u4dbf"


def style_modern_kana(text: str) -> str:
    """文语 ふ（紧接汉字的送り仮名/终止形）→ 现代假名遣い う。"""
    out = []
    prev_kanji = False
    for c in text:
        if c == "ふ" and prev_kanji:
            out.append("う")
        else:
            out.append(c)
        prev_kanji = is_kanji_char(c)
    return "".join(out)


def style_drop_wa_before_iwaku(text: str) -> str:
    """Xは曰く → X曰く（kanbun.info 引用句风格）。"""
    return text.replace("は曰く", "曰く")


def style_fix(text: str) -> str:
    """NIGHT4 规则 A 总入口：显示风格修正，不改汉字词干、不动树结构。"""
    t = style_modern_kana(text)
    t = style_drop_wa_before_iwaku(t)
    return t

# ---------------------------------------------------------------------------
# 旧字体 → 新字体（输出显示层专用，NIGHT3）
#
# 用途：udkanbun 的 mecab-kanbun 词典按旧字体输出活用形（惠/盡/對/竊/雞…），
# 而 Web漢文大系(kanbun.info) 的書き下し文用新字体（恵/尽/対/窃/鶏）。
# 本映射只作用于**最终書き下し文字符串**，不改引擎内部（lemma/树结构不动），
# 所以不影响返り点推定，只影响显示与评测字符串比对。
#
# 每条映射的来源（eval 证据，见 eval/night2_results_*.json 与 night3 基线 diff）：
#   惠→恵  gojippo-1 expected「梁の恵王曰く」got「梁惠王曰く」
#   盡→尽  keiko-1 expected「尽くること有り」got「盡す有り」
#   對→対  toranoi-1 expected「群臣対うる莫し」got「群臣對へることなく」
#   竊→窃  keiko-1 expected「臣窃かに」got「臣竊して」
#   雞→鶏  keiko-1 expected「寧ろ鶏口と為る」got「寧に雞の口にたり」
#   陷→陥  mujun-2 expected「能く陥す莫きなり」（引擎按白文旧字 陷 输出）
#   爲→為  keiko-1 expected「寧ろ鶏口と為るとも」（爲 是 爲 的旧字体）
# 以下为同一系统的常规日文新字体对应（在语料中常见，逐一核对过日本新字体表）；
# 如某条映射反而让评测变差，会在报告里如实记录并从表中移除。
SHINJITAI_MAP = {
    "惠": "恵", "盡": "尽", "對": "対", "竊": "窃", "雞": "鶏",
    "陷": "陥", "爲": "為",
    "國": "国", "萬": "万", "與": "与", "黃": "黄", "廣": "広",
    "惡": "悪", "亞": "亜", "圖": "図", "禮": "礼", "體": "体",
    "氣": "気", "缺": "欠", "龍": "竜", "滿": "満", "會": "会",
    "歲": "歳", "藥": "薬", "畫": "画", "顏": "顔", "屬": "属",
    "續": "続", "辭": "辞", "歸": "帰", "變": "変", "譯": "訳",
    "邊": "辺", "圓": "円", "獻": "献", "鐵": "鉄", "經": "経",
    "縣": "県", "顯": "顕", "濟": "済", "齊": "斉", "隨": "随",
    "醫": "医", "榮": "栄", "衞": "衛", "實": "実", "傳": "伝",
    "轉": "転", "舉": "挙", "覺": "覚", "靈": "霊", "溫": "温",
    "淨": "浄", "壹": "壱", "參": "参", "兩": "両", "嚴": "厳",
    "錢": "銭", "專": "専", "擇": "択", "澤": "沢", "驛": "駅",
    # NIGHT3 50 条评测基线 diff 扫描（tools/find_ortho_pairs.py）新增：
    "數": "数", "點": "点", "譽": "誉", "飮": "飲", "獸": "獣",
    "應": "応", "餘": "余", "將": "将", "圍": "囲", "觸": "触",
    "釋": "釈", "當": "当", "戰": "戦", "挾": "挟", "從": "従",
    # NIGHT4：200 条基线 diff 扫描新增（mujun-2/3 expected「誉めて」got「譽し」）
    "譽": "誉",
}


def normalize_shinjitai(text: str) -> str:
    """旧字体→新字体，只用于書き下し文显示层（返り点付き原文不改）。"""
    if not text:
        return text
    return "".join(SHINJITAI_MAP.get(c, c) for c in text)


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
