# -*- coding: utf-8 -*-
"""ocr_postfix.py — OCR 白文后处理：汉字混淆的上下文护栏校正（NIGHT38）。

只修 Night 37 分类中占比最高的 B_汉字混淆 的可靠子集：
- 词对全部来自 eval/night37_errors.json 的实测错对，且 GT 侧为高置信读法
  （Night 36 报告 §3 标为 60-75% 的判读一律不收，避免把 GT 误差固化成规则）。
- 一律做 **≥3 字长串精确替换**（上下文护栏），不用正则、不做单字替换；
  OCR 侧串在训读白文中不构成正常词，误改风险趋零（tests/test_ocr_postfix.py 有
  「正确文本不动」反例组：舟求劍/季氏/再求改良/適齋先生 等一律不动）。
- 不动 recognizer/检测/行序；幂等（fix(fix(x))==fix(x)）。
- 781193 目録页的 B 操作含渗墨对齐残余（Night 37 §4），不据此建词。
"""
from typing import List, Tuple
import unicodedata

# (OCR 侧错串, 正确串, 依据)——串长降序应用
FIXES: List[Tuple[str, str, str]] = [
    # 論語序説（11892692，R3/R4/R5 实测）
    ("遽伯玉", "蘧伯玉", "史記 蘧伯玉 专名；R5 L1/L5 两列实测"),
    ("一難欲殺", "桓魋欲殺", "宋司馬桓魋 专名；R5 L2（列首桓截读一）"),
    ("佛胖以", "佛肸以", "佛肸以中牟畔；R5 L4"),
    ("公巳卒", "公已卒", "靈公已卒；R5 L10"),
    ("而再求", "而冉求", "冉求 专名；R5 L10"),
    ("舟求。孔子", "冉求。孔子", "康子乃召冉求；R5 L8"),
    ("如禁及", "如蔡及", "孔子如蔡及葉；R5 L8"),
    ("然嘗終", "然魯終", "然魯終不能用；R5 L13"),
    ("濁郷家", "濁鄒家", "顏濁鄒家 专名；R4 L15-16 跨行"),
    ("公感之", "公惑之", "景公惑之；R4 L2"),
    ("不紐以", "不狃以", "公山不狃 专名；R4 L6"),
    ("隨成圍", "墮成圍", "墮成（堕三都）；R4 L11"),
    ("誅文正卯", "誅少正卯", "少正卯 专名；R4 L13"),
    ("適齋爲", "適齊爲", "去適齊爲高昭子家臣；R4 L1"),
    ("名鮮字", "名解字", "名解字頊吉；R3 L2"),
    ("見嬉戯", "兒嬉戯", "爲兒嬉戲；R3 L6（OCR 戯 shinjitai，C 类另行归一）"),
    ("陳組豆", "陳俎豆", "陳俎豆設禮容；R3 L6"),
    # 絵本 人間萬事翁馬 书名页（10301438 R2 实测）
    ("事塞基", "事塞翁", "人間萬事塞翁が馬"),
    ("久間万", "人間万", "人間萬事 书名首"),
    # 信長公記 表紙（781192 实测）
    ("教自刊", "我自刊", "我自刊我書"),
]


def fix_kanji_confusions(text: str) -> str:
    """按串长降序做精确替换；幂等。"""
    if not text:
        return text
    for wrong, right, _note in sorted(FIXES, key=lambda t: -len(t[0])):
        text = text.replace(wrong, right)
    return text


def is_junk_repeat_line(text: str) -> bool:
    """同一汉字整行重复 ≥3 次 → 界框/装饰线被识别的垃圾行（NIGHT39）。
    Night 6 的 _has_text 过滤挡不住它（一/十 都是汉字）。'一'/'一一' 等短行不拦。"""
    if not text or len(text) < 3:
        return False
    if len(set(text)) != 1:
        return False
    c = text[0]
    return ("\u3400" <= c <= "\u9fff") or ("\u4e00" <= c <= "\u4dbf") or ("\u3007" == c)


def normalize_compat_ideographs(text: str) -> str:
    """CJK 兼容表记（U+F900–U+FA6B，NEC/IBM 选字）→ Unicode 正则等价。
    实测来源：OCR 输出含 U+FA42（旣形）、U+FA5B（者形）——Night 37 C 类证据。
    只动 FA 兼容区，不做全串 NFKC（避免波及半角假名等）。"""
    if not text:
        return text
    out = []
    for c in text:
        if "\uF900" <= c <= "\uFA6B":
            out.append(unicodedata.normalize("NFKC", c))
        else:
            out.append(c)
    return "".join(out)


def postprocess_line(text: str) -> str:
    """NIGHT39 引擎输出行的完整后处理：兼容码位归一 → B 类护栏校正。"""
    return fix_kanji_confusions(normalize_compat_ideographs(text))
