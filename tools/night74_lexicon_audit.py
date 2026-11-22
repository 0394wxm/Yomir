# -*- coding: utf-8 -*-
"""night74_lexicon_audit.py — N74 词库 500 条确定性自查（报告-only，只读词库）。

检查项（机器可判的部分）:
  A. 总条数 / 重复词形 / 空 word・reading・meaning
  B. 编码异常: U+FFFD、疑似简体字混入、reading 含汉字或 ASCII、word 首尾空白、
     meaning 含 ASCII 字母、半角片假名
  C. 程序可判的矛盾启发式（仅标 review，语义判断在逐条人工校对步骤做）:
     - word 纯假名但 reading 与 word 不一致
     - word 含打消系字(不/非/未/莫/毋/勿/无/亡/否) 而 meaning 无打消系词
     - word 含疑问系字(何/孰/誰/焉/奚) 而 meaning 无疑问系词
  D. 覆盖率: 词条在 eval/golden_8165.json 白文(hakubun) 的命中文档数/出现次数;
     并附 書き下し文(expected_kakikudashi) 命中数作参考。

输出: eval/night74_lexicon_audit.json（UTF-8）。
词库 backend/glossary_lexicon.py 一字不改（本夜只审计）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import GLOSSARY_LEXICON, lexicon_size  # noqa: E402

OUT = os.path.join(ROOT, "eval", "night74_lexicon_audit.json")
GOLDEN = os.path.join(ROOT, "eval", "golden_8165.json")

# 疑似简体字 → 日文常用形（仅作混入检测；与(与える)・亦・乃・曾・將・余・云 等
# 日文本身使用的字不在表内）
SIMP = {
    "两": "両", "爱": "愛", "车": "車", "东": "東", "贝": "貝", "页": "頁",
    "门": "門", "长": "長", "马": "馬", "术": "術", "书": "書", "语": "語",
    "记": "記", "论": "論", "训": "訓", "设": "設", "谈": "談", "变": "変",
    "让": "譲", "议": "議", "财": "財", "货": "貨", "质": "質", "贵": "貴",
    "买": "買", "卖": "賣", "钱": "錢", "银": "銀", "钟": "鐘", "钢": "鋼",
    "铁": "鉄", "鸟": "鳥", "鸡": "鶏", "鱼": "魚", "龙": "龍", "凤": "鳳",
    "兰": "蘭", "简": "簡", "单": "単", "输": "輸", "后": "後", "并": "併",
    "为": "為", "于": "於", "汉": "漢", "属": "屬", "数": "數", "声": "聲",
    "优": "優", "会": "會", "体": "體", "传": "傳", "众": "眾", "价": "價",
    "从": "從", "仓": "倉", "仅": "僅", "儿": "兒", "兑": "兌", "关": "關",
    "兴": "興", "养": "養", "写": "寫", "军": "軍", "农": "農", "况": "況",
    "净": "浄", "凉": "涼", "减": "減", "凤": "鳳", "刘": "劉", "则": "則",
    "刚": "剛", "创": "創", "卫": "衛", "击": "撃", "华": "華", "协": "協",
    "历": "歷", "厅": "廳", "县": "縣", "号": "號", "响": "響", "备": "備",
    "复": "復", "头": "頭", "妈": "媽", "妇": "婦", "儿": "兒", "亿": "億",
    "亲": "親", "们": "們", "伟": "偉", "伤": "傷", "伪": "偽", "侠": "俠",
    "侧": "側", "俭": "倹", "债": "債", "倾": "傾", "偿": "償", "凭": "憑",
    "凯": "凱", "凿": "鑿", "划": "劃", "则": "則", "刚": "剛", "凯": "凱",
    "压": "壓", "县": "縣", "双": "雙", "发": "發", "叙": "敘", "叶": "葉",
    "号": "號", "吁": "籲", "后": "後", "吓": "嚇", "向": "嚮", "吓": "嚇",
    "吕": "呂", "呗": "唄", "员": "員", "哟": "喲", "唤": "喚", "啸": "嘯",
    "圆": "圓", "图": "圖", "圆": "圓", "团": "團", "园": "園", "围": "圍",
    "园": "園", "圆": "圓", "坏": "壞", "块": "塊", "坚": "堅", "坛": "壇",
    "垒": "壘", "坚": "堅", "声": "聲", "壳": "殼", "壶": "壺", "处": "處",
    "备": "備", "复": "復", "够": "夠", "头": "頭", "夹": "夾", "奋": "奮",
    "奖": "獎", "妆": "妝", "妇": "婦", "妈": "媽", "姗": "姍", "娲": "媧",
    "婴": "嬰", "婶": "嬸", "媒": "媒", "孪": "攣", "宁": "寧", "宝": "寶",
    "实": "實", "宠": "寵", "审": "審", "层": "層", "居": "居", "属": "屬",
    "岁": "歲", "岗": "崗", "岛": "島", "币": "幣", "师": "師", "帝": "帝",
    "带": "帶", "帮": "幫", "常": "常", "干": "乾", "广": "廣", "庄": "莊",
    "庆": "慶", "床": "床", "库": "庫", "应": "應", "弃": "棄", "张": "張",
    "弹": "彈", "强": "強", "归": "歸", "当": "當", "录": "錄", "彻": "徹",
    "征": "徵", "径": "徑", "忆": "憶", "忧": "憂", "怀": "懷", "态": "態",
    "总": "總", "恋": "戀", "恒": "恆", "恳": "懇", "恶": "惡", "惊": "驚",
    "惧": "懼", "惨": "慘", "惯": "慣", "愿": "願", "戏": "戲", "战": "戰",
    "户": "戶", "扑": "撲", "执": "執", "扩": "擴", "扫": "掃", "扬": "揚",
    "扰": "擾", "抚": "撫", "抛": "拋", "拒": "拒", "护": "護", "报": "報",
    "担": "擔", "拟": "擬", "拢": "攏", "拣": "揀", "拥": "擁", "拦": "攔",
    "拧": "擰", "挂": "掛", "挚": "摯", "挠": "撓", "挡": "擋", "挣": "掙",
    "挤": "擠", "挥": "揮", "损": "損", "换": "換", "捣": "搗", "据": "據",
    "掷": "擲", "捞": "撈", "摆": "擺", "摊": "攤", "撑": "撐", "撤": "撤",
    "播": "播", "撮": "撮", "撑": "撐", "扑": "撲", "坟": "墳", "坠": "墜",
    "垫": "墊", "执": "執", "块": "塊", "坛": "壇", "垒": "壘", "垦": "墾",
    "边": "邊", "动": "動", "勋": "勳", "勤": "勤", "势": "勢", "勇": "勇",
    "勋": "勳", "匀": "勻", "区": "區", "医": "醫", "华": "華", "协": "協",
    "单": "單", "南": "南", "占": "佔", "卢": "盧", "卫": "衛", "却": "卻",
    "厂": "廠", "厅": "廳", "历": "歷", "厉": "厲", "压": "壓", "厌": "厭",
    "厕": "廁", "厢": "廂", "厚": "厚", "原": "原", "厨": "廚", "县": "縣",
    "参": "參", "叉": "叉", "发": "發", "叠": "疊", "只": "隻", "号": "號",
    "叹": "嘆", "吁": "籲", "后": "後", "吓": "嚇", "吕": "呂", "员": "員",
    "咽": "嚥", "响": "響", "哑": "啞", "哟": "喲", "唤": "喚", "啼": "啼",
    "善": "善", "喇": "喇", "喉": "喉", "喊": "喊", "喋": "喋", "喝": "喝",
    "圆": "圓", "团": "團", "园": "園", "围": "圍", "图": "圖", "圆": "圓",
    "国": "國", "图": "圖", "围": "圍", "园": "園", "圆": "圓", "坏": "壞",
}

NEG_KANJI = set("不非未莫毋勿无亡否")
NEG_HINTS = ("打消", "禁止", "ない", "ず", "あらず", "なし", "なかれ", "まだ", "無")
Q_KANJI = set("何孰誰焉奚")
Q_HINTS = ("疑問", "反語", "どうして", "どこ", "だれ", "なに", "何")


def kana_only(s):
    return all(
        ("\u3040" <= c <= "\u309F") or ("\u30A0" <= c <= "\u30FF") or c in "ー・々ゝゞ"
        for c in s
    ) if s else False


def check_entry(i, e):
    w = e.get("word", "")
    r = e.get("reading", "")
    m = e.get("meaning", "")
    issues = []

    if not w:
        issues.append("empty_word")
    if not r:
        issues.append("empty_reading")
    if not m:
        issues.append("empty_meaning")

    if w and (w != w.strip()):
        issues.append("word_whitespace_around")
    if r and (r != r.strip()):
        issues.append("reading_whitespace_around")
    if m and (m != m.strip()):
        issues.append("meaning_whitespace_around")

    for c in set(w + r + m):
        if c == "\ufffd":
            issues.append("replacement_char_U+FFFD")
        if "\uFF66" <= c <= "\uFF9F":
            issues.append("halfwidth_katakana")
        if c in SIMP:
            issues.append("simplified_char:%s(→%s)" % (c, SIMP[c]))

    if r:
        bad = [c for c in r if not ("\u3040" <= c <= "\u30FF") and c not in "ー・々ゝゞ "]
        if bad:
            issues.append("reading_non_kana:%s" % "".join(sorted(set(bad))))
    if m and any(c.isascii() and c.isalpha() for c in m):
        issues.append("meaning_contains_ascii_letters")

    # 启发式矛盾（review 级，非断言）
    if w and kana_only(w) and r and w != r:
        issues.append("review_kana_word_vs_reading")
    if w and any(c in NEG_KANJI for c in w) and m:
        if not any(h in m for h in NEG_HINTS):
            issues.append("review_neg_word_without_neg_meaning")
    if w and any(c in Q_KANJI for c in w) and m:
        if not any(h in m for h in Q_HINTS):
            issues.append("review_question_word_without_q_meaning")
    return issues


def main():
    entries = list(GLOSSARY_LEXICON)
    n = len(entries)
    print("lexicon_size() =", lexicon_size(), "len(GLOSSARY_LEXICON) =", n)
    assert n == lexicon_size()

    # A. 重复词形（保留出现位置）
    dup = {}
    for i, e in enumerate(entries):
        w = e.get("word", "")
        if w:
            dup.setdefault(w, []).append(i)
    dup_words = {w: idxs for w, idxs in dup.items() if len(idxs) > 1}

    # D. 覆盖率（golden_8165 白文 + 書き下し文参考）
    with open(GOLDEN, "r", encoding="utf-8") as f:
        golden = json.load(f)
    buns = [d.get("hakubun", "") or "" for d in golden]
    kkds = [d.get("expected_kakikudashi", "") or "" for d in golden]
    print("golden docs =", len(buns))

    per_entry = []
    bun_pos = bun_zero = kkd_pos = kkd_zero = 0
    zero_bun_words = []
    for i, e in enumerate(entries):
        issues = check_entry(i, e)
        w = e.get("word", "")
        b_doc = b_occ = k_doc = k_occ = 0
        if w:
            for h, k in zip(buns, kkds):
                c1 = h.count(w)
                c2 = k.count(w)
                b_occ += c1
                k_occ += c2
                if c1:
                    b_doc += 1
                if c2:
                    k_doc += 1
        if b_doc:
            bun_pos += 1
        else:
            bun_zero += 1
            zero_bun_words.append(w)
        if k_doc:
            kkd_pos += 1
        else:
            kkd_zero += 1
        per_entry.append({
            "idx": i,
            "word": w,
            "reading": e.get("reading", ""),
            "meaning": e.get("meaning", ""),
            "kind": e.get("kind", ""),
            "issues": issues,
            "bun_doc_hits": b_doc,
            "bun_occurrences": b_occ,
            "kkd_doc_hits": k_doc,
            "kkd_occurrences": k_occ,
        })

    n_empty = sum(1 for p in per_entry if any(
        s in ("empty_word", "empty_reading", "empty_meaning") for s in p["issues"]))
    n_anomaly = sum(1 for p in per_entry if any(
        not s.startswith("review_") for s in p["issues"]))
    n_review = sum(1 for p in per_entry if any(s.startswith("review_") for s in p["issues"]))

    result = {
        "meta": {
            "script": "tools/night74_lexicon_audit.py",
            "night": 74,
            "branch": "night74-lexicon",
            "lexicon_file": "backend/glossary_lexicon.py (+ backend/glossary_lexicon_extra.py)",
            "golden_file": "eval/golden_8165.json",
            "golden_docs": len(buns),
            "note": "报告-only 自查；词库未改。issues 以 review_ 开头者为启发式复核标记，非断言。",
        },
        "summary": {
            "entries_total": n,
            "dup_word_count": len(dup_words),
            "dup_words": {w: idxs for w, idxs in dup_words.items()},
            "empty_field_entries": n_empty,
            "anomaly_entries": n_anomaly,
            "review_flag_entries": n_review,
            "coverage_bun_positive": bun_pos,
            "coverage_bun_zero": bun_zero,
            "coverage_kkd_positive": kkd_pos,
            "coverage_kkd_zero": kkd_zero,
            "zero_bun_words": zero_bun_words,
        },
        "entries": per_entry,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("written:", OUT)
    # 控制台是 cp1252：只打 ASCII 计数，CJK 细节走 JSON 文件
    s = result["summary"]
    print("summary_ascii: total=%d dup=%d empty=%d anomaly=%d review=%d "
          "bun_pos=%d bun_zero=%d kkd_pos=%d kkd_zero=%d" % (
              s["entries_total"], s["dup_word_count"], s["empty_field_entries"],
              s["anomaly_entries"], s["review_flag_entries"],
              s["coverage_bun_positive"], s["coverage_bun_zero"],
              s["coverage_kkd_positive"], s["coverage_kkd_zero"]))


if __name__ == "__main__":
    main()
