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
import re

# 被引擎拆散的专名（白名单，后续可扩充；只允许 2~3 字）
MERGE_WORDS = [
    # eval/golden.json 里出现的
    "楚人", "宋人", "狙公", "項王", "垓下", "張僧繇",
    "梁惠王", "荊宣王", "昭奚恤", "江乙", "群臣",
    # NIGHT4：200 条基线的切分类挖掘（tools/mine_error_patterns.py）证据扩充，
    # 各为 1~2 次但都是常见漢文复合词，通用性优先于逐条过拟合：
    "諸侯", "木鐸", "樗蒲", "壑雷", "馬肥", "投足", "原君", "平原君", "人人", "自得",
    # NIGHT34 曾实验追加 15 个 count>=2 的复合词（忠信/辞気/疏食/門人/童子/多聞/佚遊/
    # 便辟/夜行/軍中/戦兢/大謀/孟嘗君/門下/以上），引擎级 1705 条实测 **+0.10 avgDist
    # （5 改善/25 变差，净 +163）**——全局合并语义下长句树手术连带效应再现（与 Night 21
    # merge_guard 失败同机制），已回退。候选清单与反例档案见 REPORT_NIGHT34.md 与
    # eval/night34_results_parallel.json；要启用必须先做「短句限定合并」的产品拍板。
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


def style_dedup_shite_soshite(text: str) -> str:
    """て而して → て（NIGHT5 规则 C）—— **已撤销，不要启用**。

    eval 语料里 26/26 方向一致（见 tools/measure_rule_candidate.py），但
    语料外的经典句「王顧左右而言他」的规范训读是「顧みて而して他を言ふ」，
    本规则把它破坏成「顧みて他を言う」（pytest test_kundoku_classic 抓出）。
    而 して 续接在文语里合法且常见，语料证据不足以支撑删改。保留函数与
    注释作为证据存档。
    """
    return text.replace("て而して", "て")


def style_dedup_shite_soshite_guarded(text: str) -> str:
    """て而して → て，护栏：顧みて而して 保留（NIGHT22 Rule C'，带护栏复活）。

    历史：NIGHT5 Rule C（无护栏）26/26 方向一致 → NIGHT7 因唯一反例「顧みて而して
    他を言う」（规范训读保留而して，pytest test_kundoku_classic 抓出）撤销。
    NIGHT22 用 500 条语料重新量化（tools/night22_rule_sim.py）：输出里「て而して」
    共 191 处（kana 前置），逐条核对 expected 无一处需要它；带护栏模拟
    107 改善 / 0 变差 / avgDist 27.02→26.21（-0.81）。护栏 = て 的前 2 字是
    「顧み」时不删——覆盖经典句，代价是放弃 archive 里 15 处「みて」中非经典
    部分的少量收益（见 REPORT_NIGHT22.md §3）。
    已撤销的无护栏版本见 style_dedup_shite_soshite（存档，不要启用）。
    """
    return re.sub(r"(?<!顧み)て而して", "て", text)


def style_kore_to_shi(text: str, hakubun: str = "") -> str:
    """これ → 之（汉文训读规范字形）。NIGHT/D11 Rule D。
    依据（D11，1000 条评测集）：
      * expected（kanbun.info 規範書き下し）里「これ」出现 **0 次**，「之」522 处；
      * 引擎输出「これ」527 处，93.4% 的条目两者计数 1:1；
      * 全替换在 1000 条上 **282 改善 / 0 变差**，avgDist 26.09 → 25.20（-0.89）。

    护栏（`hakubun` 非空时生效）：**白文里没有「之」就不动任何「これ」**。
      语料交叉表（1000 条）：
        白文无之 & 输出无これ : 514 条
        白文有之 & 输出无これ : 194 条
        白文有之 & 输出有これ : 292 条
        白文无之 & 输出有これ : **0 条**
      即「白文含之」是零成本护栏：语料内与全替换完全等价（同样 -0.889/0 变差），
      语料外保证「原文没有之」的和文句子不会被改动。
      验证脚本：tools/day11_align2.py（eval/day11_align2.json）。

    已知局限：一条白文里有多个「之」时不做配额分配（按出现顺序全换），
    个别句子可能换错位置（如 keiko-1 的引擎幻觉「これ」，全替换净收益仍为正）。
    """
    if hakubun and "之" not in hakubun:
        return text
    return text.replace("これ", "之")


# ---------------------------------------------------------------------------
# D14 Rule E：假名 → 汉字（kanbun.info 慣用表記）
#
# 与 Rule D 同一个模式：kanbun.info 的規範書き下し把某些汉语虚词写成**汉字**，
# 引擎一律写成**假名**。D11 只挖了「之」，D14 在 Rule D 之后的基线上系统性地
# 找同类，得到下面这张表。
#
# 数据（eval/day14_*.json，1000 条，基线 avgDist 25.201）：
#   字   expected 次数  引擎输出次数  输出里的假名   expected 里该字的真实词形
#   皆       36            0           みな 36       皆 裸 31 / 皆な 5
#   既       25            0           すでに 25     既に 20 / 既 3 / 既にし 2
#   猶       33            1           なお 21       猶お 29 / 猶しく 4
#   豈       10            0           あに 10       豈に 10
#   唯       17            0           ただ 17       唯だ 16 / 唯 1
#
# **词形按 expected 的真实形态，不是裸汉字替换**（tools/day14_shape2.py 实测）：
#   裸替 みな→皆 -0.058 / すでに→既 -0.033 / なお→猶 -0.004 / あに→豈 -0.002 / ただ→唯 -0.002
#   词形 みな→皆 -0.058 / すでに→既に -0.049 / なお→猶お -0.021 / あに→豈に -0.010 / ただ→唯だ -0.017
#
# 两道护栏（都是数据验证过的，不是猜的）：
#   1. 白文判据：白文里没有对应汉字（含异体，如 旣/既）就跳过该条。
#      交叉表（1000 条）这五条的「白文无此字 & 输出有假名」**全部为 0** →
#      语料内零成本，语料外保证现代和文不被改。
#   2. 词界判据：命中「更长词」清单时不替换（保护 みなす/なおす/ただいま/みんな）。
#      **不能用「后接假名就挡」**——相邻两个候选词会互相干扰（すでに+なお 的 な），
#      这是测试抓出来的（tools/day14_boundary.py）。
#
# 最终（tools/day14_boundary.py 逐条核对）：
#   改写 96 条 | avgDist 25.201 → 25.046（**-0.155**）| 改善 92 / **变差 0** / 持平 908
#   幂等 1000/1000；语料外 9 条探针全部一字不动。
#
# 被拒绝的候选（有变差，一律不上线，如实记录）：
#   なかれ→勿     全替换 12 改善/11 变差；白文护栏下仍 1/8（勿 也用于「勿論」等，
#                 白文有 勿 不等于输出该写 勿）
#   いずくんぞ→焉  全替换 6/21；护栏下 5/19（焉 的用法远多于疑问副词）
#   ごとし→如     全替换 5/1；护栏下 0 改写（白文有如 & 输出有ごとし 仅 1 条）
#   また→亦       全替换 9/2（亦/又 两个汉字都对应 また，无法二选一）
# ---------------------------------------------------------------------------
E_KANA_TO_KANJI = [
    # (假名, 替换成的汉字词形, 白文里可接受的写法)
    ("みな", "皆", ("皆",)),
    ("すでに", "既に", ("既", "旣")),
    ("なお", "猶お", ("猶",)),
    ("あに", "豈に", ("豈",)),
    ("ただ", "唯だ", ("唯",)),
]

# 词界护栏：以候选假名开头、但不是该副词的更长词（命中则不替换）
# 不能改成「后接假名就挡」——相邻候选词会互相干扰（如 すでになお… 里的 な）。
E_LONGER_WORDS = {
    "みな": ("みなす", "みなれた", "みなれる", "みなし", "みなもと", "みなぎる", "みなみ"),
    "すでに": ("すでにして",),
    "なお": ("なおす", "なおさ", "なおし", "なおく", "なおざり"),
    "あに": ("あにす",),
    "ただ": ("ただいま", "ただす", "ただし", "ただちに", "ただならぬ"),
}


def _replace_word_boundary(text: str, kana: str, repl: str, longer_map=None) -> str:
    """把 kana 换成 repl；命中更长词清单时整段保持不动。

    longer_map 默认用 E_LONGER_WORDS（Rule E）；Rule F 传入自己的清单，
    两张表分开维护，避免 F 的新词影响 E 的既有行为。
    """
    lm = E_LONGER_WORDS if longer_map is None else longer_map
    longer = sorted(lm.get(kana, ()), key=len, reverse=True)
    out = []
    i = 0
    n = len(kana)
    while True:
        j = text.find(kana, i)
        if j < 0:
            out.append(text[i:])
            break
        tail = text[j:]
        hit = next((w for w in longer if tail.startswith(w)), None)
        if hit:
            out.append(text[i:j + len(hit)])
            i = j + len(hit)
        else:
            out.append(text[i:j] + repl)
            i = j + n
    return "".join(out)


def style_kana_to_kanji(text: str, hakubun: str = "") -> str:
    """假名 → 汉字（kanbun.info 慣用表記）。D14 Rule E。

    两道护栏：白文没有对应汉字就跳过该条；命中更长词清单则不做替换。
    `hakubun` 为空时只做词界护栏（离线脚本沿用「无白文=纯函数」语义）。
    """
    hb = re.sub(r"\s+", "", hakubun) if hakubun else ""
    for kana, repl, guard in E_KANA_TO_KANJI:
        if hb and not any(g in hb for g in guard):
            continue
        text = _replace_word_boundary(text, kana, repl)
    return text


# ---------------------------------------------------------------------------
# D17 Rule F：假名 → 汉字（第二批，2000 条语料挖掘）
#
# 数据来源 eval/day17_charstat.json（2000 条，Rule E 之后）：
#   expected 里 亦 103 次 / got 0；又 56/0；何 208/176；可 285/41
# 1:1 交叉验证（eval/day17_kana.json，A=白文有字&输出有假名 / C=白文无字&输出有假名）：
#   また→亦た   A 85  C 68   白文含「亦」时改；含「又」时是另一個词（见下，被拒）
#   いかん→如何 A 28  C  0   白文含「何」时改（C=0，护栏零成本）
#   べし→可し   A 49  C  5   白文含「可」时改
#   べく→可く   A  7  C  3   白文含「可」时改
# 2000 条离线+真机核对（eval/day17_combo.json）：
#   改写 158 条 | avgDist 21.218 → 21.116（**-0.102**）| 改善 147 / **变差 0** / 持平 1853
#   幂等 PASS；语料外 12 条探针全部一字不动。
#
# 被拒绝的候选（变差 > 0，一律不上线，如实记录）：
#   また→又   白文含「又」时 47 条可改，但 38 改善 / **1 变差**（「又た/又」两种词形并存）
#   べき→可き 白文含「可」时 75 条可改，63 改善 / **4 变差**
#   べから→可から 77 条可改，67 改善 / **4 变差**（べからず 的上接词形不定）
#   なし→莫し 白文含「莫」时 A=0（引擎已写「無し」，莫/無 无法区分）
#   ごとく/ごとし/ごとき→若く/若し/若き  C=3~8（白文无若却会命中，护栏不干净）
# ---------------------------------------------------------------------------
F_KANA_TO_KANJI = [
    # (假名, 替换成的词形, 白文里可接受的写法)
    ("また", "亦た", ("亦",)),
    ("いかん", "如何", ("何",)),
    ("べし", "可し", ("可",)),
    ("べく", "可く", ("可",)),
]

# Rule F 的词界护栏（与 E_LONGER_WORDS 分开维护）
F_LONGER_WORDS = {
    "また": ("またたく", "またがり", "またがる", "またぎ", "またぐ",
             "またたき", "またしても", "またと", "またの"),
    "いかん": (),
    "べし": (),
    "べく": (),
}


def style_kana_to_kanji_f(text: str, hakubun: str = "") -> str:
    """假名 → 汉字（第二批）。D17 Rule F。

    与 Rule E 同构的两道护栏，但用 F 自己的更长词表。
    """
    hb = re.sub(r"\s+", "", hakubun) if hakubun else ""
    for kana, repl, guard in F_KANA_TO_KANJI:
        if hb and not any(g in hb for g in guard):
            continue
        text = _replace_word_boundary(text, kana, repl, F_LONGER_WORDS)
    return text


def style_fix(text: str) -> str:
    """规则总入口：显示风格修正（NIGHT4 Rule A + NIGHT22 Rule C'）。
    不改汉字词干、不动树结构。Rule C（て而して→て）以带护栏形式于 NIGHT22
    复活（style_dedup_shite_soshite_guarded），无护栏版本仍处撤销状态。
    注：D11 Rule D（これ→之）与 D14 Rule E（假名→汉字）需要白文，
    走 style_fix_with_hakubun。"""
    t = style_modern_kana(text)
    t = style_drop_wa_before_iwaku(t)
    t = style_dedup_shite_soshite_guarded(t)
    return t


def style_fix_with_hakubun(text: str, hakubun: str) -> str:
    """带白文上下文的规则总入口（D11 起后端实际调用这个）。

    Rule D 的白文护栏需要原始输入，所以不能只传输出串。
    D14 的 Rule E / D17 的 Rule F 同理（护栏也是白文判据）。
    """
    t = style_modern_kana(text)
    t = style_drop_wa_before_iwaku(t)
    t = style_dedup_shite_soshite_guarded(t)
    t = style_kore_to_shi(t, hakubun)
    t = style_kana_to_kanji(t, hakubun)
    t = style_kana_to_kanji_f(t, hakubun)   # D17 Rule F
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
    # NIGHT30：1705 对语料字符级热图（tools/night30_char_heatmap.py）——got/exp 1:1 替换
    # 中 count>=2 且表中没有的 40 个标准日本新字体对。离线模拟（night30_sim40.py）：
    # avgDist 24.77→24.38（-0.39），433 改善 / 0 变差；幂等 40/40（程序化验证）。
    # 逐条为当用/常用汉字表的标准简化，非逐条过拟合（rongo 语料的 學/樂/德 为主力）。
    "學": "学", "樂": "楽", "德": "徳", "號": "号", "發": "発", "廢": "廃",
    "莊": "荘", "乘": "乗", "讀": "読", "關": "関", "聲": "声", "黨": "党",
    "輕": "軽", "稱": "称", "斷": "断", "讓": "譲", "懷": "懐", "拜": "拝",
    "佛": "仏", "晉": "晋", "亂": "乱", "劍": "剣", "寶": "宝", "勞": "労",
    "龜": "亀", "齒": "歯", "閒": "間", "鄰": "隣", "帶": "帯", "殘": "残",
    "藝": "芸", "蟲": "虫", "蠻": "蛮", "恆": "恒", "臺": "台", "來": "来",
    "賣": "売", "條": "条", "默": "黙", "彌": "弥",
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
    NIGHT5 护栏（merge_guard）：调用方应只在短句上启用合并——200 条实测中
    6 条长句变差（toranoi-1/ichiji 系/bokutaku-1/ippai-2/keiko-2）均来自
    长句树手术的连带效应；`MAX_MERGE_LINE_LEN` 由调用方按行长度控制。
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
