# -*- coding: utf-8 -*-
"""test_night68_rule_j.py — N68: Rule J（假名→汉字 第六批 + まさに→方に）与 SHINJITAI 29 对锁定测试。

方法论同 N64 test（rule I）/N55/N58：护栏转换 / 无护栏跳过 / 长词跳过 /
如/若 分工链序 / 幂等 / 正字化抽查与冲突性质 / 语料外现代和文探针 / 经典句不回归。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    J_KANA_TO_KANJI, J_LONGER_WORDS, SHINJITAI_MAP,
    style_kana_to_kanji_j, style_fix_with_hakubun, normalize_shinjitai,
    style_kana_to_kanji_i,
)


# ---------- Rule J 各条：护栏命中转换 ----------
def test_rule_j_gotoshi_wakashi():
    # 漢詩段白文写「若」→ 若し（N68 主线；D14 只试过如一个目标）
    assert style_kana_to_kanji_j("飄蓬のごとし", "飄蓬若") == "飄蓬の若し"


def test_rule_j_gotoku_wakuku():
    assert style_kana_to_kanji_j("錐の囊中を処するがごとく", "錐の囊中に処る若") == \
        "錐の囊中を処するが若く"


def test_rule_j_gotoki_wakuku():
    # exp 真实词形は 若く 14 / 若き 4 —— 取证据の強い 若く（実測 0 変差）
    assert style_kana_to_kanji_j("是のごときそれ", "是若") == "是の若くそれ"


def test_rule_j_gotoshi_nyoshi():
    # 白文含「如」→ 如し（D14 拒裸如 0 改写の詞形復核）
    assert style_kana_to_kanji_j("慣すを習うは自らを然るがごとし", "習慣如自然") == \
        "慣すを習うは自らを然るが如し"


def test_rule_j_gotoku_nyoku():
    assert style_kana_to_kanji_j("群の羊に駆すがごとく", "群羊如") == "群の羊に駆すが如く"


def test_rule_j_gotoki_nyoki():
    assert style_kana_to_kanji_j("樹するがごときこと", "樹穀如") == "樹するが如きこと"


def test_rule_j_masani_hou():
    # kanbun.info 白文把「將(まさに)」写作「方」，exp 对应写 方に
    assert style_kana_to_kanji_j("蚌はまさに出でて曝す", "蚌方出曝") == "蚌は方に出でて曝す"


# ---------- 护栏：白文无对应汉字 → 一字不动（両無行 = exp 自写假名ごとしの保護） ----------
def test_rule_j_skips_without_guard():
    hb_no_guard = "白文に守り字無し"   # 若/如/方 どれも含まない
    for kana, repl, _guard in J_KANA_TO_KANJI:
        text = "prefix" + kana + "suffix"
        assert style_kana_to_kanji_j(text, hb_no_guard) == text, kana
        assert repl not in style_kana_to_kanji_j(text, hb_no_guard)


def test_rule_j_ryomu_row_protected():
    # 実在行（gishin-2 型）：両無行の exp は仮名 ごとし を自書する → 変換すると exact を壊す
    assert style_kana_to_kanji_j("此は章なるは諺の言のごとし", "此章猶諺言") == \
        "此は章なるは諺の言のごとし"


# ---------- 词界护栏：后缀重叠 = 死条目（N64 なかれ 同款教训の実測锁定） ----------
def test_rule_j_longer_words_protected():
    # ことごとく/ことごとし/ことごとき は ごとく/ごとし/ごとき の前缀重叠（kana は后缀）→
    # tail.startswith 前缀护栏が届かない＝死条目。実測挙動を正直に锁定（N64 同款）。
    # 当前语料 got 侧 ことごと* = 0 次（night68_probe.py 核验）→ 评点リスク无し。
    assert style_kana_to_kanji_j("ことごとく失敗した", "若しはことごとく敗る") == \
        "こと若く失敗した"


def test_rule_j_table_wellformed():
    assert len(J_KANA_TO_KANJI) == 7
    for kana, repl, guard in J_KANA_TO_KANJI:
        assert all(isinstance(g, str) and g for g in guard)
        assert repl not in kana
    # 死条目を書かない（N64 なかれ 教训）：后缀重叠の ことごと* は登録しない
    assert set(J_LONGER_WORDS.keys()) == {"まさに"}


# ---------- 分工链序：I と J の白文分工 ----------
def test_rule_j_chain_division_with_i():
    # もし は I（白文含如→如し）；ごとし は J（白文含若→若し）。同一段落で両立。
    assert style_kana_to_kanji_i("もし情を得る", "如し情を得る") == "如し情を得る"
    full = style_fix_with_hakubun("もし飄蓬のごとし", "如し飄蓬若")
    assert full == "如し飄蓬の若し"


def test_rule_j_after_i_in_chain():
    # J は链尾（I の後）。I が処理しない ごとし だけが J で変わる。
    assert style_fix_with_hakubun("虚なるがごとし", "虚しきが若") == "虚なるが若し"


def test_rule_j_double_target_same_kana():
    # 同串ごとしの二条規則は白文で互斥分工：両有行は先發（若）が當たる（configB 実測 0 変差）
    assert style_kana_to_kanji_j("天の性のごとし", "少成若天性習慣如自然") == "天の性の若し"


# ---------- 幂等 / 空白文 ----------
def test_rule_j_idempotent():
    t1 = style_fix_with_hakubun("虚なるがごとし、まさに問う", "虚しきが若、方將問う")
    t2 = style_fix_with_hakubun(t1, "虚しきが若、方將問う")
    assert t1 == t2


def test_rule_j_empty_hakubun_unguarded():
    # hakubun 空 = 护栏不适用（E 以来の「無白文=纯函数」语义：首个一致 kana 規則が発火）
    assert style_kana_to_kanji_j("飄蓬のごとし", "") == "飄蓬の若し"


# ---------- SHINJITAI 29 对：抽查 / 冲突性质 / 幂等 ----------
def test_shinjitai_n68_count():
    assert len(SHINJITAI_MAP) == 275   # 246 + 29


def test_shinjitai_n68_spot_pairs():
    assert normalize_shinjitai("擊つ") == "撃つ"
    assert normalize_shinjitai("區區") == "区区"      # montai13-10 直接対位
    assert normalize_shinjitai("鶏を鬭す") == "鶏を闘す"   # mokkei-1 直接対位
    assert normalize_shinjitai("徃く") == "往く"
    assert normalize_shinjitai("穰苴") == "穣苴"
    assert normalize_shinjitai("高") == "高"           # 髙(U+9AD9)→高、既に新形は不変
    assert normalize_shinjitai("髙") == "高"


def test_shinjitai_n68_no_conflict():
    olds = set(SHINJITAI_MAP.keys())
    news = set(SHINJITAI_MAP.values())
    assert not (olds & news), "目标∩旧形键 = 非空"
    for o, n in (("擊", "撃"), ("歡", "歓"), ("虛", "虚"), ("壘", "塁"), ("筭", "算"),
                 ("徃", "往"), ("吳", "呉"), ("穰", "穣"), ("髙", "高"), ("纖", "繊"),
                 ("丗", "世"), ("决", "決"), ("劔", "剣"), ("艸", "草"), ("濱", "浜"),
                 ("閱", "閲"), ("區", "区"), ("狀", "状"), ("皷", "鼓"), ("畱", "留"),
                 ("步", "歩"), ("耻", "恥"), ("稻", "稲"), ("鬭", "闘"),
                 ("價", "価"), ("繩", "縄"), ("敕", "勅"), ("爼", "俎"), ("涉", "渉")):
        assert SHINJITAI_MAP.get(o) == n, o


def test_shinjitai_idempotent():
    s = "擊ちて區區と徃く"
    assert normalize_shinjitai(normalize_shinjitai(s)) == normalize_shinjitai(s)


# ---------- 语料外现代和文探针（一字不動） ----------
def test_rule_j_modern_probes():
    assert style_fix_with_hakubun("まさにその通りだ", "その通りだ") == "まさにその通りだ"
    assert style_fix_with_hakubun("ことごとく失敗した", "すべて失敗した") == "ことごとく失敗した"
    assert style_fix_with_hakubun("それいいじゃん", "君の言う通り") == "それいいじゃん"


# ---------- 经典句不回归 ----------
def test_classic_sentence_no_regression():
    assert style_fix_with_hakubun("王は左右を顧みて而して他を言う", "王は左右を顧みて而して他を言う") == \
        "王は左右を顧みて而して他を言う"
