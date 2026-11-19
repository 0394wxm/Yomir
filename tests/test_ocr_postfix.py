# -*- coding: utf-8 -*-
"""test_ocr_postfix.py — NIGHT38 OCR 汉字混淆护栏校正的单元测试。"""
from backend.ocr_postfix import FIXES, fix_kanji_confusions


def test_fixes_known_confusions():
    assert fix_kanji_confusions("解還衛主遽伯玉家。見南子。") == "解還衛主蘧伯玉家。見南子。"
    assert fix_kanji_confusions("佛胖以中牟畔。召孔子。") == "佛肸以中牟畔。召孔子。"
    assert fix_kanji_confusions("一難欲殺之。又去適陳") == "桓魋欲殺之。又去適陳"
    assert fix_kanji_confusions("靈公巳卒衞君輙") == "靈公已卒衞君輙"
    assert fix_kanji_confusions("而再求爲季氏將") == "而冉求爲季氏將"
    assert fix_kanji_confusions("舟求。孔子如禁及葉。") == "冉求。孔子如蔡及葉。"
    assert fix_kanji_confusions("然嘗終不能用") == "然魯終不能用"
    assert fix_kanji_confusions("顏濁郷家。適陳過匡") == "顏濁鄒家。適陳過匡"
    assert fix_kanji_confusions("晏嬰不可公感之") == "晏嬰不可公惑之"
    assert fix_kanji_confusions("公山不紐以費畔") == "公山不狃以費畔"
    assert fix_kanji_confusions("孟氏不肯隨成圍之") == "孟氏不肯墮成圍之"
    assert fix_kanji_confusions("誅文正卯與聞國政") == "誅少正卯與聞國政"
    assert fix_kanji_confusions("適齋爲高昭子家臣") == "適齊爲高昭子家臣"
    assert fix_kanji_confusions("氏名鮮字頊吉") == "氏名解字頊吉"
    assert fix_kanji_confusions("邑爲見嬉戯常陳組豆") == "邑爲兒嬉戯常陳俎豆"
    assert fix_kanji_confusions("事塞基") == "事塞翁"
    assert fix_kanji_confusions("久間万") == "人間万"
    assert fix_kanji_confusions("教自刊我書") == "我自刊我書"


def test_correct_text_untouched():
    # 正确文本（含词典右项/近似词）一律不动
    samples = [
        "主蘧伯玉家", "佛肸召", "桓魋欲殺之", "冉求", "公惑之", "公山不狃",
        "陳俎豆", "事塞翁", "人間萬", "我自刊我書", "季氏", "李氏", "再求改良",
        "舟求劍", "適齋先生", "", "普通の文章", "桓魋欲殺之", "見嬉戲而作",
    ]
    for s in samples:
        assert fix_kanji_confusions(s) == s, s


def test_idempotent():
    for s in ["遽伯玉佛胖以一難欲殺公巳卒而再求舟求。孔子如禁及然嘗終濁郷家見嬉戯陳組豆誅文正卯適齋爲公感之不紐以隨成圍名鮮字事塞基久間万教自刊"]:
        once = fix_kanji_confusions(s)
        assert fix_kanji_confusions(once) == once


def test_fixes_shape():
    # 全部为长串精确替换（≥3 字），无单字对
    for wrong, right, _note in FIXES:
        assert len(wrong) >= 3, (wrong, right)
        assert wrong != right
