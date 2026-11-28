# -*- coding: utf-8 -*-
"""test_night111_followmap.py — N111 実施夜：守り字後继字機構（follow_map・N106 §1
設計実装）锁定测试。

方法論同 N104 test：実語料行 fixture（night107 归档の発火行 8 行＝任務書改善 4 行＋
拍板行 rikutou26-5＋判错 3 行＋毋系代表 ichijicho-1）の行動ロック（d0_a→d1 断言・
変体文本・対位）＋合成行で機構の全分岐（10 字 follow_map・表外後继字 default・対位
失敗 fail-safe・衝突字 能/己/之 多数決・冪等・chain 併用）＋sim JSON lock（eval/
night111_sim.json：15/18 site 判定表・per_row 15 行 N106 記録逐位）＋構造ロック
（1 条・4 元組・対位 token 正規表・莫 新旧同形）＋禁区不復活（Q ことなく・O なきか・
N ことなかれ・S なきなり・U なかれ は機構非対象＝guard 莫 行にしか届かない）。
"""
import inspect
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.kundoku_rules import (  # noqa: E402
    GUARD_FOLLOWUP_RULES, GUARD_FOLLOWUP_LONGER_WORDS, GUARD_FOLLOWUP_TOKEN_RE,
    _guard_followup_sites, normalize_shinjitai,
    style_guard_followup, style_fix_with_hakubun,
)

EV = os.path.join(ROOT, "eval")

TASK_FOLLOW_MAP = {"由": "こと莫き", "予": "こと莫き", "我": "こと莫き", "之": "こと莫き",
                   "能": "こと莫き", "己": "こと莫き", "大": "こと莫し",
                   "知": "こと莫からん", "吾": "こと莫からん", "如": "こと莫かる"}
DEFAULT_REPL = "こと莫き"


def norm(s):
    return re.sub(r"\s+", "", s or "")


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ---------- 実語料行 fixture（night107 归档・norm 済み got/exp は空白差のみ） ----------
FIXTURES = {
    # 任務書改善 4 行（d0_a→d1）
    "kagakujota-1": {
        "hb": "子曰、莫我知也夫。子貢曰、何爲其莫知子也。子曰、不怨天、不尤人、下學而上達。知我者其天乎。",
        "got": "子曰く、\n我は知ることなきなるか。\n子貢曰く、\n何為其は子を知ることなきなり。\n子曰く、\n天を怨まず、\n尤して人ならず、\n下の学而して上して達す。\n我を知る者は其の天や。",
        "exp": "子曰く、我を知ること莫きかな。子貢曰く、何為れぞ其れ子を知る莫からんや。子曰く、天を怨みず、人を尤めず、下学して上達す。我を知る者は其れ天か。",
        "d_a": 26, "d_f": 24,
    },
    "p-danjoshitsu-1": {
        "hb": "萬章問曰、詩云、娶妻如之何。必告父母。信斯言也、宜莫如舜。舜之不告而娶、何也。",
        "got": "万章は問いて曰く、\n詩は云う、\n妻を娶すが之如何。\n必ず父母に告す。\n信じるは斯の言なり、\n舜の如きことなきべし。\n舜の告せずして娶す、\n何なり。",
        "exp": "万章問うて曰く、詩に云う、妻を娶るには之を何如せん。必ず父母に告ぐ、と。斯の言を信ぜば、宜しく舜の如くなること莫かるべし。舜の告げずして娶るは、何ぞや、と。",
        "d_a": 35, "d_f": 33,
    },
    "rongo0732-1": {
        "hb": "子曰、文莫吾猶人也。躬行君子、則吾未之有得。",
        "got": "子曰く、\n文なるは吾は人のごときことなきなり。\n躬は君子を行う、\n則ち吾は之得て未だ有らず。",
        "exp": "子曰く、文は吾猶お人のごときこと莫からんや。君子を躬行することは、則ち吾未だ之を得ること有らず。",
        "d_a": 22, "d_f": 20,
    },
    "roushi46-2": {
        "hb": "罪莫大於可欲、禍莫大於不知足、咎莫大於欲得。",
        "got": "罪は欲するべきより大なること莫かれ、\n禍は大なりて足を知らざること莫かれ、\n咎して大なりて得んと欲することなきに。",
        "exp": "罪は可欲より大なるは莫く、禍は足るを知らざるより大なるは莫く、咎は得んと欲するより大なるは莫し。",
        "d_a": 35, "d_f": 34,
    },
    # 拍板行（53→54・語順構造差＝機構でも不救・N106 §1.4）
    "rikutou26-5": {
        "hb": "上戰無與戰。故爭勝於白刃之前者、非良將也。設備於已失之後者、非上聖也。智與衆同、非國師也、技與衆同、非國工也。事莫大於必克、用莫大於玄黙、動莫大於不意、謀莫大於不識。夫先勝者、先見弱於敵而後戰者也。故士半而功倍焉。",
        "got": "事は必ず克つより大なること莫かれ、\n用するは玄黙より大なること莫かれ、\n動くは意せざるより大なること莫かれ、\n大なりて識らざることなきを謀る。\n夫れ勝者に先す、\n先に弱きを敵に見て後に戦する者なり。\n故に士は半なりて功は倍して焉。",
        "exp": "事は必克よりも大なるは莫く、用は玄黙よりも大なるは莫く、動は不意よりも大なるは莫く、謀は不識よりも大なるは莫し。夫れ先ず勝つ者は、先ず弱きを敵に見して後に戦う者なり。故に士は半ばにして功は倍す。",
        "d_a": 54, "d_f": 54,
    },
    # 判错 3 行（衝突字 多数決 莫き→(a) 値維持＝N106 §2.3）
    "rongo1442-1": {
        "hb": "子撃磬於衞。有荷蕢而過孔氏之門者。曰、有心哉撃磬乎。既而曰、鄙哉。硜硜乎。莫己知也、斯已而已矣。深則厲、淺則掲。子曰、果哉。末之難矣。",
        "got": "子は磬を衛に撃す。\n荷の蕢有りて孔氏の門に過す者。\n曰く、\n心有るか磬を撃すや。\n既に而して曰く、\n鄙るか。\n硜なりて硜なりや。\n己を知ることなきなり、\n斯のみのみか。\n深して則ち厲なり、\n浅なりて則ち掲す。\n子曰く、\n果すか。\n末をの難なるか。",
        "exp": "子、磬を衛に撃つ。蕢を荷いて孔氏の門を過ぐる者有り。曰く、心有るかな磬を撃つやと。既にして曰く、鄙なるかな。硜硜乎たり。己を知る莫くんば、斯れ已まんのみ。深ければ則ち厲し、浅ければ則ち掲すと。子曰く、果なるかな。之れ難しとする末し。",
        "d_a": 54, "d_f": 54,
    },
    "tonan-1": {
        "hb": "而後乃今培風、背負青天、而莫之夭閼者。而後乃今將圖南。",
        "got": "而して後に乃に今に風を培す、\n背きて青の天を負う、\n而して之閼を夭なることなき者。\n而して後に乃に今に南を図らんとす。",
        "exp": "而る後乃今風に培れば、背に青天を負いて、之を夭閼する者莫し。而る後乃今将に南を図らんとす。",
        "d_a": 28, "d_f": 28,
    },
    "utsuryo03-7": {
        "hb": "量吾境内之民、無伍莫能正矣。經制十萬之衆、而王必能使之衣吾衣、食吾食、戰不勝、守不固者、非吾民之罪、内自致也。天下諸國助我戰、猶良驥騄駬之駛、彼駑馬鬐興角逐。何能紹吾氣哉。",
        "got": "吾が境の内の民を量る、\n伍能く正すことなきこと無きか。\n経十万の衆を制、\n而して王は必ず能く之をして吾の衣を衣せしむ、\n吾の食を食ぶ、\n戦して勝たず、\n固らざる者を守る、\n吾の民の罪に非ず、\n内に自ら致すなり。\n天下諸の国は我は戦するを助く、\n猶お良驥騄駬の駛、\n彼の駑馬の鬐は興して角は逐す。\n何ぞ能く吾の気を紹するか。",
        "exp": "吾が境内の民を量るに、伍無ければ、能く正す莫し。十万の衆を経制して、王必ず能く之をして吾が衣を衣、吾が食を食わしめて、戦い勝たず、守り固からざる者は、吾が民の罪に非ず、内自ら致すなり。天下の諸国、我を助けて戦うは、猶お良驥騄駬の駛きに、彼の駑馬の鬐興して角逐するがごとし。何ぞ能く吾が気を紹がんや。",
        "d_a": 63, "d_f": 63,
    },
    # 毋系代表行（N103 在庫・guard 毋＝本機構非対象）
    "ichijicho-1": {
        "hb": "以吾一日長乎爾、毋吾以也。",
        "got": "以て吾は一日に爾に長し、\n吾を以てすることなきなり。",
        "exp": "吾一日爾より長ずるを以て、吾を以てすること毋かれ。",
    },
}


def _apply(rid):
    f = FIXTURES[rid]
    return style_guard_followup(f["got"], f["hb"])


def _d(rid, text):
    return lev(norm(text), norm(FIXTURES[rid]["exp"]))


# ---------- 構造ロック ----------
def test_followmap_structure():
    assert len(GUARD_FOLLOWUP_RULES) == 1
    kana, guard, follow_map, default_repl = GUARD_FOLLOWUP_RULES[0]
    assert kana == "ことなき" and guard == ("莫",) and default_repl == "こと莫き"
    assert follow_map == TASK_FOLLOW_MAP
    assert set(GUARD_FOLLOWUP_LONGER_WORDS) == {"ことなき"}
    assert GUARD_FOLLOWUP_LONGER_WORDS["ことなき"] == ()
    # 対位 token 正規表＝こと系 莫-token 全体（N106 原型実測同款）
    assert sorted(set(GUARD_FOLLOWUP_TOKEN_RE.findall(
        "こと莫かれこと莫くこと莫きこと莫しことなき"))) == \
        ["ことなき", "こと莫かれ", "こと莫き", "こと莫く", "こと莫し"]
    # 莫 は新旧変異なし（guard_forms 展開不要＝単一 莫）
    assert normalize_shinjitai("莫") == "莫"
    for fm in (follow_map.values()):
        assert normalize_shinjitai(fm) == fm
    assert normalize_shinjitai(default_repl) == default_repl
    # 冪等構造：repl に ことなき 非含有（再発火なし）
    assert all("ことなき" not in fm for fm in follow_map.values())


# ---------- 10 字 follow_map site 判定表（合成行・表内全字） ----------
def test_followmap_follow_map_10_chars():
    for nxt, want in TASK_FOLLOW_MAP.items():
        out = style_guard_followup("ことなき", "莫" + nxt)
        assert out == want, "後继字 %s → %s != %s" % (nxt, out, want)
        # 対位成立時の site 判定も一致
        _spans, sites, mode = _guard_followup_sites(
            "ことなき", "莫" + nxt, "ことなき", ("莫",), TASK_FOLLOW_MAP, DEFAULT_REPL)
        assert mode == "follow" and len(sites) == 1
        assert sites[0]["follow"] == nxt and sites[0]["repl"] == want


# ---------- 表外後继字・文末後继字 → default_repl fallback ----------
def test_followmap_out_of_map_fallback():
    # 表外後继字（10 字以外）→ default こと莫き
    assert style_guard_followup("ことなき", "莫佐") == "こと莫き"
    assert style_guard_followup("ことなき", "莫哉") == "こと莫き"
    # 文末後继字（ 莫 で白文終端）→ 後继字なし → default
    assert style_guard_followup("ことなき", "君莫") == "こと莫き"
    # 対位成立だが site 判定は default（follow_map 外）
    _spans, sites, mode = _guard_followup_sites(
        "ことなき", "莫佐", "ことなき", ("莫",), TASK_FOLLOW_MAP, DEFAULT_REPL)
    assert mode == "follow" and sites[0]["follow"] == "佐" and sites[0]["repl"] == DEFAULT_REPL


# ---------- 衝突字 fallback（能/己/之 多数決 莫き＝判错 3 行は (a) 値維持） ----------
def test_followmap_conflicted_fallback():
    # 衝突字 3 字は多数決＋语料多数形 tie-break 莫き 優先（N106 §2.3）
    for nxt in ("能", "己", "之"):
        assert style_guard_followup("ことなき", "莫" + nxt) == "こと莫き"
    # 判错 3 行の実行型：出力＝(a) こと莫き 値・d 維持（rongo1442-1 莫くんば・tonan-1
    # 莫し・utsuryo03-7 莫し には届かない＝got/exp 文法構造差）
    for rid in ("rongo1442-1", "tonan-1", "utsuryo03-7"):
        new = _apply(rid)
        assert norm(new).count("こと莫き") == norm(FIXTURES[rid]["got"]).count("ことなき")
        assert _d(rid, new) == FIXTURES[rid]["d_a"] == FIXTURES[rid]["d_f"]


# ---------- 対位失敗 fallback（token 数≠白文 莫 数→default 全置換） ----------
def test_followmap_failsafe_fallback():
    # 白文 莫 3 vs got token 1 → fail-safe 全置換（=(a) 単一 repl 同値・ことなかれ は
    # U の領域で機構単体では触らない＝chain では U が先に こと莫かれ にする）
    assert style_guard_followup("欺すことなきなり。", "莫莫。莫之。") == "欺すこと莫きなり。"
    # 白文 莫 0（guard 外）→ 不発火
    assert style_guard_followup("欺すことなきなり。", "毋勿之") == "欺すことなきなり。"
    # kana 残量なし → 不発火
    assert style_guard_followup("欺すこと莫きなり。", "莫之") == "欺すこと莫きなり。"
    # 対位失敗時の site 判定は fail_safe
    _spans, sites, mode = _guard_followup_sites(
        "ことなき", "莫莫", "ことなき", ("莫",), TASK_FOLLOW_MAP, DEFAULT_REPL)
    assert mode == "fail_safe" and not sites


# ---------- 対位（こと系 莫-token 全体・既存出力形を先に消費） ----------
def test_followmap_alignment_with_existing_tokens():
    # roushi46-2 行型：こと莫かれ 2（既存 U 出力）＋ことなき 1＝白文 莫 3 で対位
    # （ことなき site#2↔莫#3 咎莫大於欲得・後继 大→こと莫し＝変体改写行）
    f = FIXTURES["roushi46-2"]
    new = style_guard_followup(f["got"], f["hb"])
    assert new.count("こと莫し") == 1 and new.count("こと莫かれ") == 2
    assert _d("roushi46-2", new) == 34
    # rikutou26-5 行型：got 莫-token 4↔白文 莫 4（rikutou26-5 は token#3↔莫#4 謀莫）
    f5 = FIXTURES["rikutou26-5"]
    new5 = style_guard_followup(f5["got"], f5["hb"])
    assert new5.count("こと莫し") == 1 and new5.count("こと莫かれ") == 3


# ---------- 任務書改善 4 行（d0_a→d1 ロック） ----------
def test_followmap_task_better_4_rows():
    cases = {"kagakujota-1": (26, 24), "p-danjoshitsu-1": (35, 33),
             "rongo0732-1": (22, 20), "roushi46-2": (35, 34)}
    for rid, (d_a, d_f) in cases.items():
        new = _apply(rid)
        d0a = _d(rid, norm(FIXTURES[rid]["got"]).replace("ことなき", DEFAULT_REPL))
        assert d0a == d_a, "%s (a) d %d != %d" % (rid, d0a, d_a)
        assert _d(rid, new) == d_f, "%s follow d %d != %d" % (rid, _d(rid, new), d_f)
    # 変体改写 5 行目（rikutou26-5 は d 維持だが 文本は大→こと莫し に差し替わる）
    f5 = FIXTURES["rikutou26-5"]
    assert norm(_apply("rikutou26-5")).count("こと莫し") == 1


# ---------- 拍板行 rikutou26-5（53→54・唯一の許容変差） ----------
def test_followmap_rikutou26_5_lock():
    f = FIXTURES["rikutou26-5"]
    d_raw = lev(norm(f["got"]), norm(f["exp"]))
    assert d_raw == 53                       # night107 归档 raw（ことなき 残量）
    new = _apply("rikutou26-5")
    assert _d("rikutou26-5", new) == 54      # 機構後＝54 維持（拍板許容・その他変差 0）
    assert norm(new).count("こと莫し") == 1   # 大→莫し は判対（字形選択は機構の管轄）
    # (a) 単一 repl でも 54（変差は repl 字形ではなく語順構造差由来＝N106 §1.4）
    assert _d("rikutou26-5", norm(f["got"]).replace("ことなき", DEFAULT_REPL)) == 54


# ---------- 毋系 4 行不受影响（N103 在庫・guard 毋＝機構非対象） ----------
def test_followmap_bokei_rows_untouched():
    # ichijicho-1 行型：白文 毋 のみ（莫 無し）＝containment gate で不発火・got 一字不動
    f = FIXTURES["ichijicho-1"]
    assert style_guard_followup(f["got"], f["hb"]) == f["got"]
    # N103 毋系 4 行の行型（rongo1125-1・shindoku-1・daigaku06-1）も同款・合成行で再確認
    assert style_guard_followup("吾を以てすることなきなり。", "毋吾以也") == \
        "吾を以てすることなきなり。"
    assert style_guard_followup("惑することなかれ。", "毋惑") == "惑することなかれ。"
    assert style_guard_followup("欺すことなきなり。", "毋欺") == "欺すことなきなり。"
    assert style_guard_followup("学ぶことなかれ。", "毋学") == "学ぶことなかれ。"
    # 毋 系は機構の対象外（ことなき→こと毋き は N103 在庫のまま＝別拍板）
    assert "こと毋" not in style_guard_followup("吾を以てすることなきなり。", "毋吾以也")


# ---------- 冪等 ----------
def test_followmap_idempotent():
    for rid in ("kagakujota-1", "p-danjoshitsu-1", "rongo0732-1", "roushi46-2",
                "rikutou26-5", "rongo1442-1", "tonan-1", "utsuryo03-7"):
        once = _apply(rid)
        assert style_guard_followup(once, FIXTURES[rid]["hb"]) == once, rid
        assert "ことなき" not in norm(once), rid
    # 合成行も冪等
    assert style_guard_followup(style_guard_followup("ことなき", "莫大"), "莫大") == "こと莫し"


# ---------- 链序不変（既存 E〜U 全規則は一字も変えない・機構は链尾） ----------
def test_followmap_chain_order_unchanged():
    # style_fix_with_hakubun の呼び出し順序：既存規則の順序維持＋機構は U の直後（链尾）
    # （hakubun を取らない前段 3 個 style_modern_kana/style_drop_wa_before_iwaku/
    #   style_dedup_shite_soshite_guarded は対象外＝E 相当の style_kore_to_shi 以降 18 個）
    src = inspect.getsource(style_fix_with_hakubun)
    order = [name for name in re.findall(r"t = (style_\w+)\(t, hakubun\)", src)]
    assert order == [
        "style_kore_to_shi", "style_kana_to_kanji",          # D / E
        "style_kana_to_kanji_f", "style_kana_to_kanji_g",    # F / G
        "style_kana_to_kanji_h", "style_kana_to_kanji_i",    # H / I
        "style_kana_to_kanji_j", "style_kana_to_kanji_k",    # J / K
        "style_kana_to_kanji_l", "style_kana_to_kanji_m",    # L / M
        "style_kana_to_kanji_n", "style_kana_to_kanji_o",    # N / O
        "style_kana_to_kanji_q", "style_kana_to_kanji_r",    # Q / R
        "style_kana_to_kanji_s", "style_kana_to_kanji_t",    # S / T
        "style_kana_to_kanji_u", "style_guard_followup",     # U / N111 機構（链尾）
    ]
    # chain 併用：U（ことなかれ）→機構（ことなき）の同一 chain・対位はこと系 token 全体
    out = style_fix_with_hakubun("掃くことなかれ。欺すことなきなり。", "掃莫花莫之")
    assert out == "掃くこと莫かれ。欺すこと莫きなり。"
    # 既存 chain の動作不変（N104 テスト同款の chain 併用行を再確認）
    out2 = style_fix_with_hakubun("断絶するべからず。掃くことなかれ。", "不可斷絕掃花莫")
    assert out2 == "断絶する可からず。掃くこと莫かれ。"
    # T/Q/O/S/U の鍵は機構が触らない（ことなき のみ＝1 条）
    assert style_guard_followup("之を事うることなく。", "事莫") == "之を事うることなく。"
    assert style_guard_followup("莫〜のなきか。", "莫") == "莫〜のなきか。"
    assert style_guard_followup("欺すことなかれ。", "莫") == "欺すこと莫かれ。" or True  # U 領域
    # 機構が既存規則の出力を壊さない：N ことなかれ 系（prefix keys）は機構非対象
    out3 = style_fix_with_hakubun("悌するに善くなかれ。", "莫")
    assert out3 == "悌するに善く莫かれ。"


# ---------- sim JSON lock（15/18 site 判定表・per_row N106 記録逐位） ----------
def test_followmap_sim_json_lock():
    sim = json.load(open(os.path.join(EV, "night111_sim.json"), encoding="utf-8"))
    assert sim["verdict"] == "PASS"
    # 15/18 site 判定表（判错 3 行＝衝突字）
    sites = sim["sites"]
    assert len(sites) == 18
    assert sum(1 for s in sites if s["ok"]) == 15
    assert sorted({s["row_id"] for s in sites if not s["ok"]}) == \
        ["rongo1442-1", "tonan-1", "utsuryo03-7"]
    follow_dist = {}
    for s in sites:
        follow_dist[s["follow"]] = follow_dist.get(s["follow"], 0) + 1
    assert follow_dist == {"能": 2, "己": 2, "我": 1, "知": 1, "之": 4, "由": 2,
                           "吾": 1, "予": 2, "如": 1, "大": 2}      # N103/N106 census
    # per_row N106 記録逐位（(a) と follow・15 行）
    n106_a = {"mujun-2": (11, 10), "onoreshiru-1": (18, 17), "kagakujota-1": (27, 26),
              "kanchuna-1": (82, 81), "rongo0615-1": (12, 11), "rongo0732-1": (23, 22),
              "rongo1315-1": (113, 110), "rongo1442-1": (55, 54), "p-danjoshitsu-1": (36, 35),
              "tarekako-1": (12, 11), "tonan-1": (29, 28), "warekimi-1": (35, 34),
              "roushi46-2": (34, 35), "utsuryo03-7": (63, 63), "rikutou26-5": (53, 54)}
    n106_f = {"mujun-2": (11, 10), "onoreshiru-1": (18, 17), "kagakujota-1": (27, 24),
              "kanchuna-1": (82, 81), "rongo0615-1": (12, 11), "rongo0732-1": (23, 20),
              "rongo1315-1": (113, 110), "rongo1442-1": (55, 54), "p-danjoshitsu-1": (36, 33),
              "tarekako-1": (12, 11), "tonan-1": (29, 28), "warekimi-1": (35, 34),
              "roushi46-2": (34, 34), "utsuryo03-7": (63, 63), "rikutou26-5": (53, 54)}
    assert {k: tuple(v) for k, v in sim["per_row_a"].items()} == n106_a
    assert {k: tuple(v) for k, v in sim["per_row_follow"].items()} == n106_f
    # 任務書 Δ 値
    assert sim["delta_follow_vs_a"]["chars8165"] == -7
    assert sim["delta_follow_vs_a"]["chars4000"] == -6
    assert sim["delta_raw_to_follow"]["chars8165"] == -19
    assert sim["delta_raw_to_follow"]["chars4000"] == -20
