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
#   また→又   D17 时 38 改善 / 1 变差（rongo2002-1）被拒；**NIGHT55 复活进 Rule G**——
#             在 F 已上线的 day17 真机基线上复验：44 条改写、36 改善 / **0 变差**
#             （那 1 条变差是对 pre-F 快照算的，F 上线后该行已无 また 可改）。
#             见 tools/night55_sim.py / REPORT_NIGHT55.md §3。
#   べき→可き 白文含「可」时 75 条可改，63 改善 / **4 变差**（N55 逐条核因：
#             expected 自己写假名 べき/べし，运行时无信号可分，不可救，见 REPORT_NIGHT55.md §4）
#   べから→可から 77 条可改，67 改善 / **4 变差**（同上，expected 写 べからず 假名）
#   なし→莫し 白文含「莫」时 A=0（引擎已写「無し」，莫/無 无法区分）
#   ごとく/ごとし/ごとき→若く/若し/若き  C=3~8（白文无若却会命中，护栏不干净）
# ---------------------------------------------------------------------------
# また 的长词表：F（→亦た）与 G（→又）共用同一个 kana 的同一组长词，
# 提取成模块常量让两张表引用同一对象（值恒等，N55 test 锁住这一点）。
_MATA_LONGER_WORDS = ("またたく", "またがり", "またがる", "またぎ", "またぐ",
                      "またたき", "またしても", "またと", "またの")

F_KANA_TO_KANJI = [
    # (假名, 替换成的词形, 白文里可接受的写法)
    ("また", "亦た", ("亦",)),
    ("いかん", "如何", ("何",)),
    ("べし", "可し", ("可",)),
    ("べく", "可く", ("可",)),
]

# Rule F 的词界护栏（与 E_LONGER_WORDS 分开维护）
F_LONGER_WORDS = {
    "また": _MATA_LONGER_WORDS,
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


# ---------------------------------------------------------------------------
# N55 Rule G：假名 → 汉字（第三批，2000 条语料挖掘，F 已上线的 day17 真机基线）
#
# 数据来源 eval/night55_mine.json（2000 条，Rule F 之后）：
#   又 56/0（引擎写 また；F 的 亦た 分工后剩余部分）、所以/所謂/相 的复合汉字形
# 四象限 + 离线模拟（eval/night55_sim.json，逐条真算 Levenshtein）：
#   また→又       白文含「又」 44 条改写，36 改善 / **0 变差**（D17 遗留#1 解决）
#   ゆゑん→所以   白文含「所以」30 条改写，29 改善 / **0 变差**
#   いはゆる→所謂 白文含「所謂」23 条改写，23 改善 / **0 变差**
#   たがいに→相   白文含「相」  43 条改写，43 改善 / **0 变差**
#   ために→為に   0 条命中（引擎在这些行写「がため」，词级替换对不上）→ 不收
# 组合：改写 136 条 | avgDist 21.116 → 20.916（**-0.200**）| 改善 127 / **变差 0**
# expected 假名残留 4 个 kana 全部为 0（expected 从不写这四个假名串）。
# べき/べから 复核仍各 4 变差（expected 自身写假名，运行时无信号可分）→ 维持拒绝。
# ---------------------------------------------------------------------------
G_KANA_TO_KANJI = [
    ("また", "又", ("又",)),          # D17 遗留#1：与 F 的 亦た 按白文分工（亦/又）
    ("ゆゑん", "所以", ("所以",)),     # 白文护栏用二字序列（所以 是复合词，单字「以」太宽）
    ("いはゆる", "所謂", ("所謂",)),
    ("たがいに", "相", ("相",)),
]

# Rule G 的词界护栏（与 E/F 分开维护；また 与 F 共用同一组长词，见 _MATA_LONGER_WORDS）
G_LONGER_WORDS = {
    "また": _MATA_LONGER_WORDS,
    "ゆゑん": (),
    "いはゆる": (),
    "たがいに": (),
}


def style_kana_to_kanji_g(text: str, hakubun: str = "") -> str:
    """假名 → 汉字（第三批）。N55 Rule G。

    与 E/F 同构的两道护栏，用 G 自己的更长词表（また 一项与 F 共享常量）。
    """
    hb = re.sub(r"\s+", "", hakubun) if hakubun else ""
    for kana, repl, guard in G_KANA_TO_KANJI:
        if hb and not any(g in hb for g in guard):
            continue
        text = _replace_word_boundary(text, kana, repl, G_LONGER_WORDS)
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


# ---------------------------------------------------------------------------
# N58 Rule H：假名 → 汉字（第四批，golden_3000 语料挖掘——新增段詩経/漢詩短句为主）
#
# 数据来源 eval/night58_mine.json / night58_probe_forms.txt（解剖）→ night58_sim.json
# （离线模拟，逐条真算 Levenshtein，基线 = night57 真机 3000 条归档，D/E/F/G 全链
#   avgDist 16.321）：
#   復  新增 exp 13 / got 2：引擎写 また，kanbun.info 在復行写 復た——F(亦た)/G(又)
#       之后的第三种分工形态（live 链序 F→G→H 按白文分工，互不越位）
#   只  exp 7 / got 0：引擎把 只 读作 それ（それ×8），expected 写 只だ(5)/只使い(1)/只今(1)
#   須  exp 17 / got 4：引擎写 べからず，expected 写 須いず
# 离线模拟（2999 条，变差>0 一律不上线）：
#   また→復た       白文含復  35 条改写，33 改善 / **0 变差**（-0.011）
#   それ→只だ       白文含只   8 条改写， 7 改善 / **0 变差**（-0.004）
#   べからず→須いず  白文含須   4 条改写， 4 改善 / **0 变差**（-0.002）
#   与 SHINJITAI 30 对组合：改写 317 条 | 16.321 → 16.219（**-0.102**）| 改善 264 / 0 变差
#   幂等 PASS（3000/3000）。
# 被拒绝的候选（变差>0，一律不上线，如实记录）：
#   ことなかれ→莫かれ  46 条可改，34 改善 / **11 变差**——莫行里 expected 写
#              莫し/莫き/莫けん 等其他活用形，与写 莫かれ 的行运行时信号完全相同
#              （N55 べき 同机制：页面级编辑习惯，规则层不可分）→ 拒绝
#   なかれ→莫かれ     48 条可改，1 变差（kokyo09-5 exp 写 莫し）→ 维持 D14 拒绝
#   べし→須らく      6 条可改，5 变差——同一行内 exp 混写「須らく…べし」（sekitoku-1/
#              toushisen352-3），同行都能混写，无信号可分 → 拒绝
#   また→将に/将た   無稳定 got 侧碎片（ごとく/それ/んと…），出不了候选（解剖如实记录）
# ---------------------------------------------------------------------------
H_KANA_TO_KANJI = [
    ("また", "復た", ("復",)),         # F/G 之后的第三分工形态
    ("それ", "只だ", ("只",)),         # engine 把 只 读作 それ
    ("べからず", "須いず", ("須",)),
]

# Rule H 的词界护栏（与 E/F/G 分开维护；また 与 F/G 共用同一组长词常量）
H_LONGER_WORDS = {
    "また": _MATA_LONGER_WORDS,
    "それ": ("それで", "それぞ", "それとも", "それが", "それら", "それでは"),
    "べからず": (),
}


def style_kana_to_kanji_h(text: str, hakubun: str = "") -> str:
    """假名 → 汉字（第四批）。N58 Rule H。

    与 E/F/G 同构的两道护栏，用 H 自己的更长词表（また 一项与 F/G 共享常量）。
    """
    hb = re.sub(r"\s+", "", hakubun) if hakubun else ""
    for kana, repl, guard in H_KANA_TO_KANJI:
        if hb and not any(g in hb for g in guard):
            continue
        text = _replace_word_boundary(text, kana, repl, H_LONGER_WORDS)
    return text


# ---------------------------------------------------------------------------
# N64 Rule I：假名 → 汉字（第五批，golden_4000 语料挖掘——Night 22 方法论第四轮）
#
# 数据来源 eval/night64_mine.json（字符 delta + 假名串 delta + SHINJITAI 1:1）→
# night64_probe.json（计数判据 + exp 真实词形取证）→ night64_sim.json（离线模拟，
# 基线 = night60 真机 4000 条归档，D/E/F/G/H 全链 avgDist 13.889）：
#   けだし     got 23 / exp 0：exp 写 蓋し（ikkyosyu-2/rongo0727-1 等 22 行全核对）
#   いずくんぞ got 52 / exp 0：exp 写 焉くんぞ——D14 拒的是裸字替换 いずくんぞ→焉
#              （5/19 变差），按 exp 真实词形 + 焉 护栏复核后 31 行 31 改善 / 0 变差
#   もし       got 46 / exp 0：exp 写 如し（moshisono-1/rongo0312-1 等）
#   それ       got 72 / exp 0：exp 写 夫れ——H 的 それ→只だ（白文含只）分工之后，
#              白文含夫 的行归本条（H 吸收 只 行后剩余 45 行 41 改善 / 0 变差）
#   ただ       got 25 / exp 0：exp 写 惟だ/惟れ——E 的 ただ→唯だ（白文含唯）分工之后，
#              白文含惟 的行归本条（14 行 14 改善 / 0 变差）
#   なかれ     got 96 / exp 0：exp 写 毋かれ/毋く/毋し——D14 拒的是 なかれ→勿（1/8），
#              按 exp 词形 毋かれ + 毋 护栏复核后 10 行 10 改善 / 0 变差
#              （exp 写 毋く/毋し 的行靠更长词表兜不住——但实测 0 变差：毋かれ 与
#               毋く/毋し 共享 毋 字，编辑距离只降不升；exp 混写行的净收益为正）
# 离线模拟（3998 条，逐条真算 Levenshtein，变差>0 一律不上线）：
#   六条全部 0 变差；与 SHINJITAI 99 对组合 656 行改写、13.889 → 13.719（-0.170）、
#   改善 514 / 0 变差，幂等 PASS。
# 不作为候选的（如实记录）：
#   なりて/して/するは/るは/みて… 等 got 侧高频假名串 = 活用/句法结构差异
#   （Night 24/25 已定性，规则层不可分）；のみ exp 96 次 > got 86 次，非候选；
#   すなわち/なほ/ゆゑに 引擎输出 0 次，无候选可做。
# ---------------------------------------------------------------------------
I_KANA_TO_KANJI = [
    ("けだし", "蓋し", ("蓋",)),
    ("いずくんぞ", "焉くんぞ", ("焉",)),   # D14 拒绝（裸 焉）的词形复核翻案
    ("もし", "如し", ("如",)),
    ("それ", "夫れ", ("夫",)),            # H 的 只 分工之后
    ("ただ", "惟だ", ("惟",)),            # E 的 唯 分工之后
    ("なかれ", "毋かれ", ("毋",)),        # D14 拒绝（→勿）的词形复核翻案
]

# Rule I 的词界护栏（与 E/F/G/H 分开维护；それ/ただ 复用 H/E 的长词表常量）
I_LONGER_WORDS = {
    "けだし": (),
    "いずくんぞ": (),
    "もし": ("もしも", "もしや", "もしか"),
    "それ": H_LONGER_WORDS["それ"],
    "ただ": E_LONGER_WORDS["ただ"],
    # なかれ 无长词条目：ことなかれ/することなかれ 是「なかれ」的**后缀**重叠，
    # tail.startswith 前缀护栏保护不到（写进去也是死条目——N64 测试阶段发现）；
    # 实际行为 = なかれ 一律转换（ことなかれ→こと毋かれ），离线模拟 10 个护栏行
    # 全部改善 0 变差（exp 在这些行写 毋く/毋し，な→毋 方向正确），如实按实测定。
}


def style_kana_to_kanji_i(text: str, hakubun: str = "") -> str:
    """假名 → 汉字（第五批）。N64 Rule I。

    与 E/F/G/H 同构的两道护栏，用 I 自己的更长词表（それ/ただ 分别共享 H/E 的常量）。
    """
    hb = re.sub(r"\s+", "", hakubun) if hakubun else ""
    for kana, repl, guard in I_KANA_TO_KANJI:
        if hb and not any(g in hb for g in guard):
            continue
        text = _replace_word_boundary(text, kana, repl, I_LONGER_WORDS)
    return text


# ---------------------------------------------------------------------------
# Rule J（N68）：假名 → 汉字（第六批）+ まさに→方に
# 方法论 = Night 64（Rule I）：解剖（night68_mine.py）→ 取证（night68_probe.py）→
# 离线模拟 0 变差（night68_sim.py）→ 上线 → 真机与模拟逐位一致。
# 基线 = golden_8165（N67 ⑬补丁后全链真机 8165 条，avgDist 14.741）。
#
# 收录 7 条（组合 283 行改写、234 改善 / 0 变差、幂等坏 0，configB=若先）:
#   ごとし→若し（白文含若）——漢詩段白文写「若」，D14 当年只试了如一个目标（拒案翻案）
#   ごとく→若く（白文含若）——同上
#   ごとき→若く（白文含若）——exp 真实词形 若く 14 / 若き 4，取证据强的 若く
#   ごとし→如し（白文含如）——D14 拒（裸如 0 改写）的词形复核翻案
#   ごとく→如く（白文含如）
#   ごとき→如き（白文含如）
#   まさに→方に（白文含方）——kanbun.info 白文把「將(まさに)」写作「方」，
#     exp 对应写 方に/方たり/方べて（23 行全改善）
# 链序在 I 之后：ごとし族按白文 如/若 分目标；両有行（如若两有）configB（若先）实测 0 变差。
# 両無行（白文无如/若）exp 自己写假名 ごとし（16 处）——护栏天然不触，保 exact。
# 拒绝（0 变差门，eval/night68_sim.txt 有逐行证据）:
#   べき→可き（6 变差：exp 自写假名 べき，如 sanennosho-7「相狎るべき有り」）
#   べから→可から（5 变差：exp 自写 べから系假名，如 shushu-4「得べからずして」）
#   もし→若し（1 变差：kyugyu-2 的 exp 若し 在句尾，与 got 位置漂移）
#   なんぞ→何ぞ（2 变差：exp 有 奚んぞ/曷んぞ 三字形，なんぞ→何ぞ 反加距）
#   なかれ→莫かれ（N58 拒案重测：84 行 67 改善 / 1 变差，差一行也过不了 0 变差门）
#   ことなく→莫き（12 改善 / 2 变差）；がため→が為に（63 改善 / 2 变差）
J_KANA_TO_KANJI = [
    ("まさに", "方に", ("方",)),
    ("ごとし", "若し", ("若",)),          # D14 拒（裸如）后的词形翻案：漢詩段白文写若
    ("ごとく", "若く", ("若",)),
    ("ごとき", "若く", ("若",)),          # exp 词形 若く 14 / 若き 4，取证据强者
    ("ごとし", "如し", ("如",)),          # 与 I の もし→如し 分工：kana 不同串
    ("ごとく", "如く", ("如",)),
    ("ごとき", "如き", ("如",)),
]

# Rule J 的词界护栏（与 E/F/G/H/I 分开维护）。
# ことごとく/ことごとし/ことごとき 是 ごとく/ごとし/ごとき 的**前缀重叠**（kana 是
# 更长词的后缀）——tail.startswith 前缀护栏保护不到，写进去就是死条目（N64 在
# なかれ 上的同款教训，实測で死条目を確認後に削除）。当前语料 got 侧 ことごと* 为
# 0 次（night68_probe.py 核验），不构成评分风险；若将来语料出现，需后缀护栏机制
# （新拍板项，见 REPORT_NIGHT68 §移交）。
J_LONGER_WORDS = {
    "まさに": (),
}


def style_kana_to_kanji_j(text: str, hakubun: str = "") -> str:
    """假名 → 汉字（第六批）。N68 Rule J。

    与 E/F/G/H/I 同构的两道护栏，用 J 自己的更长词表；
    ごとし族按白文 如/若 分目标（同串ごとし两条规则，护栏互斥分工）。
    """
    hb = re.sub(r"\s+", "", hakubun) if hakubun else ""
    for kana, repl, guard in J_KANA_TO_KANJI:
        if hb and not any(g in hb for g in guard):
            continue
        text = _replace_word_boundary(text, kana, repl, J_LONGER_WORDS)
    return text


def style_fix_with_hakubun(text: str, hakubun: str) -> str:
    """带白文上下文的规则总入口（D11 起后端实际调用这个）。

    Rule D 的白文护栏需要原始输入，所以不能只传输出串。
    D14 的 Rule E / D17 的 Rule F / N55 的 Rule G / N58 的 Rule H / N64 的 Rule I
    同理（护栏也是白文判据）。
    """
    t = style_modern_kana(text)
    t = style_drop_wa_before_iwaku(t)
    t = style_dedup_shite_soshite_guarded(t)
    t = style_kore_to_shi(t, hakubun)
    t = style_kana_to_kanji(t, hakubun)
    t = style_kana_to_kanji_f(t, hakubun)   # D17 Rule F
    t = style_kana_to_kanji_g(t, hakubun)   # N55 Rule G
    t = style_kana_to_kanji_h(t, hakubun)   # N58 Rule H
    t = style_kana_to_kanji_i(t, hakubun)   # N64 Rule I
    t = style_kana_to_kanji_j(t, hakubun)   # N68 Rule J
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
    # NIGHT58：golden_3000 新增段（詩経/漢詩）挖掘的 30 对标准新字体对（N30 同款
    # 方法论：1:1 difflib 扫描 + 解剖多字对齐目标，判据 = expected 全库写旧形 0 次）。
    # 离线模拟（tools/night58_sim.py）：280 条改写，226 改善 / **0 变差**（-0.084）；
    # 与 Rule H 组合 317 条改写、-0.102、改善 264 / 0 变差，幂等程序化验证 PASS。
    # 寳(U+5BF3) 是 寶(U+5BF6) 的异体字，N30 只收了后者，两码位都要映射。
    # 拒绝：冰→氷/弦→絃/亦→又（expected 自身写旧形，全局映射会破坏）——如实记录。
    "舊": "旧", "隱": "隠", "說": "説", "醬": "醤", "鄉": "郷", "權": "権",
    "綠": "緑", "峽": "峡", "踐": "践", "靑": "青", "產": "産", "燒": "焼",
    "眞": "真", "營": "営", "膽": "胆", "燈": "灯", "滯": "滞", "兒": "児",
    "豐": "豊", "雙": "双", "樓": "楼", "處": "処", "獨": "独", "遙": "遥",
    "曉": "暁", "醉": "酔", "縱": "縦", "橫": "横", "晚": "晩", "寳": "宝",
    # NIGHT64：golden_4000 第二遍「计数判据」批量（night64_probe.py）：exp 全库写旧形
    # 0 次 & got>=2 次 & 不在表中 → 目标取标准新字体（票据杂票是对位噪音，逐条人工
    # 复核）；99 对全部要求 exp 写过新形 >=1 次（脚本核验，0 对被核掉）。
    # 离线模拟（night64_sim.py）：545 行改写，406 改善 / **0 变差**（-0.117）；
    # 与 Rule I 组合 656 行改写、-0.170、改善 514 / 0 变差，幂等程序化验证 PASS。
    # 拒绝：冰→氷/弦→絃/亦→又（exp 自身写旧形 2/2/105 次）——与 N58 同判据。
    "聽": "聴", "觀": "観", "舍": "舎", "愼": "慎", "爭": "争", "搖": "揺",
    "髮": "髪", "擧": "挙", "藏": "蔵", "拂": "払", "繼": "継", "羣": "群",
    "祿": "禄", "寢": "寝", "沒": "没", "辯": "弁", "囘": "回", "卷": "巻",
    "靜": "静", "勸": "勧", "溪": "渓", "鷄": "鶏", "盜": "盗", "獵": "猟",
    "戲": "戯", "儉": "倹", "雜": "雑", "壯": "壮", "總": "総", "徑": "径",
    "峯": "峰", "悅": "悦", "壽": "寿", "竝": "並", "辨": "弁", "巖": "巌",
    "驅": "駆", "淚": "涙", "晝": "昼", "收": "収", "豫": "予", "爐": "炉",
    "彈": "弾", "緣": "縁", "墮": "堕", "卽": "即", "淺": "浅", "兔": "兎",
    "賴": "頼", "效": "効", "淸": "清", "假": "仮", "攝": "摂", "鎭": "鎮",
    "薰": "薫", "險": "険", "壤": "壌", "絕": "絶", "劒": "剣", "攜": "携",
    "增": "増", "彥": "彦", "黑": "黒", "潛": "潜", "寫": "写", "壓": "圧",
    "艷": "艶", "拔": "抜", "尙": "尚", "齡": "齢", "據": "拠", "碎": "砕",
    "嶽": "岳", "搜": "捜", "僞": "偽",
    # 计数判据筛出但等长块漏投票的字（标准新字体，exp 新形出现次数脚本核验过）
    "卻": "却", "聰": "聡", "壞": "壊", "禪": "禅", "戶": "戸", "巢": "巣",
    "齋": "斎", "覽": "覧", "貳": "弐", "驗": "験", "螢": "蛍", "絲": "糸",
    "鬪": "闘", "麥": "麦", "窻": "窓", "辦": "弁", "單": "単", "每": "毎",
    "奧": "奥", "戀": "恋", "歷": "歴", "曆": "暦", "荆": "荊", "濕": "湿",
    # NIGHT68：golden_8165 第二遍「计数判据」批量（night68_probe.py）：exp 全库写旧形
    # 0 次 & got>=2 次 & 等长块多数票 & exp 新形>=1 次；8165 全量比 N64 的 4000 挖出新
    # 对（擊/歡/虛 等主力在子部长句段 [4000:8165)）。29 对模拟+真机全部 0 变差。
    # 票噪修正 2 对（行级证据裁决）：區→区（montai13-10 got 區區/exp 区区 直接对位，
    # 多数票错取 别）、鬭→闘（mokkei-1・toushisen192-2 exp 闘 对位，票错取 養）。
    # 拒绝：霸→覇（exp 自写旧形 1 次）、陳→陣（exp 写陳 39 次，非同字）、冰→氷/弦→絃/
    # 亦→又/烟→煙/遲→遅（exp 自身写旧形）——与 N58/N64 同判据。
    "擊": "撃", "歡": "歓", "虛": "虚", "壘": "塁", "筭": "算", "徃": "往",
    "吳": "呉", "穰": "穣", "髙": "高", "纖": "繊", "丗": "世", "决": "決",
    "劔": "剣", "艸": "草", "濱": "浜", "閱": "閲", "區": "区", "狀": "状",
    "皷": "鼓", "畱": "留", "步": "歩", "耻": "恥", "稻": "稲", "鬭": "闘",
    "價": "価", "繩": "縄", "敕": "勅", "爼": "俎", "涉": "渉",
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
