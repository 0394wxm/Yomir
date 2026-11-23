# -*- coding: utf-8 -*-
"""night79_build.py — N79 ④ 装配器：判定ファイル → glossary_lexicon_extra2.py ＋ excluded.json。

判定ファイル eval/night79_decisions_<start>.json（研究ステップで人手で書く）:
  {"start": 0, "decisions": [
     {"word": "...", "rank": 0, "verdict": "include"|"exclude",
      "cat": "proper|noun|verb|modifier|function",   # include 時必須
      "reading": "...", "meaning": "...",            # include 時必須
      "dict_evidence": "...", "corpus_evidence": "...",  # include 時必須（双证据）
      "exclude_reason": "..."}]}                     # exclude 時必須

- 两条证据门：include は dict_evidence と corpus_evidence が両方非空でなければ機械的に拒む。
- 既存 500 条词形との重複は拒む。重複词形は拒む。
- 出力:
  backend/glossary_lexicon_extra2.py（extra.py 同形式: 分组元组 + as_dicts() + kind）
  ＋ 統合查找器 find_in_lexicon2()（本体 GLOSSARY_LEXICON を**変更せず**、
    500+N 条を同じ「内容词先→長词先」アルゴリズムで走査する。
    本体リストを extend/rebind すると tests/test_night75/77 の
    len(GLOSSARY_LEXICON)==500 断言が破れるため、llm 層合併查找方式を採る）
  eval/night79_excluded.json（排除清单＋理由）
用法: python -I tools/night79_build.py
"""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EV = os.path.join(ROOT, "eval")
BACKEND = os.path.join(ROOT, "backend")

CATS = ["proper", "noun", "verb", "modifier", "function"]
CAT_LIST_NAME = {"proper": "PROPER", "noun": "NOUNS", "verb": "VERBS",
                 "modifier": "MODIFIERS", "function": "FUNCTION"}
CAT_LABEL = {"proper": "固有名詞（人物・地名・書名）", "noun": "名詞",
             "verb": "動詞", "modifier": "形容詞・副詞", "function": "機能語（接続・助動等）"}


def load_decisions():
    decs = {}
    dup = []
    for path in sorted(glob.glob(os.path.join(EV, "night79_decisions_*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        for d in data.get("decisions", []):
            w = d["word"]
            if w in decs:
                dup.append(w)
            decs[w] = d
    return decs, dup


def validate(decs, existing):
    bad = []
    for w, d in decs.items():
        if d.get("verdict") == "include":
            for k in ("reading", "meaning", "cat", "dict_evidence", "corpus_evidence"):
                if not str(d.get(k, "")).strip():
                    bad.append((w, "missing %s" % k))
            if d.get("cat") not in CATS:
                bad.append((w, "bad cat %r" % d.get("cat")))
            if w in existing:
                bad.append((w, "duplicates existing 500"))
        elif d.get("verdict") == "exclude":
            if not str(d.get("exclude_reason", "")).strip():
                bad.append((w, "exclude without reason"))
        else:
            bad.append((w, "bad verdict %r" % d.get("verdict")))
    return bad


def py_str(s):
    """python 源码里的双引号字符串字面量（现有词库文件同款）。"""
    return '"%s"' % str(s).replace("\\", "\\\\").replace('"', '\\"')


HEADER = '''# -*- coding: utf-8 -*-
"""glossary_lexicon_extra2.py — 词库扩充第二波（N79：500 → %(total)d）。自动生成，请勿手改。

生成源：eval/night79_candidates.json（golden_8165 汉字复合词频次挖矿）
＋ eval/night79_decisions_*.json（逐条人工判定）＋ tools/night79_build.py（装配）。
每条两条证据缺一不可（tools/night79_build.py 机械校验）：
  ① 辞書：www.weblio.jp 聚合页（読み＋释义有据；缓存 eval/night79_dict_cache/，未跟踪目录）
  ② 语料：golden_8165 实例行（id＋書き下し文片段，见 eval/night79_candidates.json）
N76 §3.5 覆盖缺口 3 条（而る後／而ち／利す）在候选清单前部，全部收录。
读音/释义为 agent 依 weblio 辞书条目整理归纳（非逐字引用），未人工校对（README 同款声明）。

与 glossary_lexicon_extra.py 同格式：分组元组（词形／現代仮名遣い読み／簡明释义）
＋ as_dicts() 展开为 kind 标注的字典列表。
**本体 GLOSSARY_LEXICON（500 条）不动**：tests/test_night75/77 有
len(GLOSSARY_LEXICON)==500 断言，故合并查找在 llm 层完成——
llm.glossary() 经 find_in_lexicon2()（本文件）用同一套
「内容词先→长词先→已覆盖位置不重复命中」算法走查 500+%(n)d 条。
词库不进规则引擎，golden_4000 数字不受影响（N79 归档与 night77 逐位一致）。
"""

LEXICON_EXTRA2_SOURCE = ("agent 整理（N79 频次挖矿 golden_8165，逐条 weblio＋语料双证据，"
                         "非逐字引用，未人工校对）")

'''


def build_source(groups, n_total):
    out = [HEADER % {"total": 500 + n_total, "n": n_total}]
    out.append("# ---- 分组（extra.py 同款顺序；组内为频次降序）----\n")
    for cat in CATS:
        rows = groups[cat]
        out.append("%s = [" % CAT_LIST_NAME[cat])
        for w, r, m in rows:
            out.append("    (%s, %s, %s)," % (py_str(w), py_str(r), py_str(m)))
        out.append("]\n")
    out.append('''
def as_dicts():
    """按「内容词优先」顺序展开为 GLOSSARY_LEXICON 同构的字典列表（extra.py 同款）。"""
    rows = []
    for w, r, m in PROPER:
        rows.append({"word": w, "reading": r, "meaning": m, "kind": "content"})
    for w, r, m in NOUNS:
        rows.append({"word": w, "reading": r, "meaning": m, "kind": "content"})
    for w, r, m in VERBS:
        rows.append({"word": w, "reading": r, "meaning": m, "kind": "content"})
    for w, r, m in MODIFIERS:
        rows.append({"word": w, "reading": r, "meaning": m, "kind": "content"})
    for w, r, m in FUNCTION:
        rows.append({"word": w, "reading": r, "meaning": m, "kind": "function"})
    return rows


LEXICON_EXTRA2 = as_dicts()

# ---- N79 合并查找器（本体 GLOSSARY_LEXICON 不动，llm 层使用）----
# 算法与 backend/glossary_lexicon.find_in_lexicon 完全一致（glossary_lexicon.py
# 只读不改——N79 约束），仅把词条源换成 500+N 条合并列表。
# 内容词先→功能词后，同组内长词在前（稳定排序：等长时保持「本体先、extra2 后」）。
from backend.glossary_lexicon import GLOSSARY_LEXICON as _BASE_LEXICON  # noqa: E402


def _ordered_all():
    all_rows = list(_BASE_LEXICON) + LEXICON_EXTRA2
    content = [e for e in all_rows if e.get("kind") != "function"]
    function = [e for e in all_rows if e.get("kind") == "function"]
    key = lambda e: (-len(e.get("word", "")),)  # noqa: E731
    return sorted(content, key=key) + sorted(function, key=key)


_ORDERED_ALL = _ordered_all()


def find_in_lexicon2(text: str, max_hits: int = 5):
    """find_in_lexicon 的 500+N 条版：语义/返回结构与 find_in_lexicon 完全一致。"""
    hits = []
    if not text:
        return hits
    covered = [False] * len(text)
    seen = set()
    for item in _ORDERED_ALL:
        w = item.get("word", "")
        if not w or w in seen:
            continue
        start = text.find(w)
        if start < 0:
            continue
        # 跳过完全落在已命中词条内部的匹配（与 find_in_lexicon 同款）
        pos = start
        free = -1
        while pos >= 0:
            if not any(covered[pos:pos + len(w)]):
                free = pos
                break
            pos = text.find(w, pos + 1)
        if free < 0:
            continue
        for i in range(free, free + len(w)):
            covered[i] = True
        hits.append({
            "word": w,
            "reading": item.get("reading", ""),
            "meaning": item.get("meaning", ""),
            "source": "lexicon",
        })
        seen.add(w)
        if len(hits) >= max_hits:
            break
    return hits
''')
    return "\n".join(out)


def main():
    decs, dup = load_decisions()
    from backend.glossary_lexicon import GLOSSARY_LEXICON
    existing = {e["word"] for e in GLOSSARY_LEXICON}
    cands = json.load(open(os.path.join(EV, "night79_candidates.json"), encoding="utf-8"))
    cand_list = cands["candidates"]

    bad = validate(decs, existing)
    if dup:
        bad.extend((w, "duplicate decision") for w in dup)
    if bad:
        print("[FAIL] decision validation:")
        for w, why in bad[:30]:
            print("  - %s: %s" % (w, why))
        sys.exit(2)

    included = [d for d in decs.values() if d["verdict"] == "include"]
    excluded = [d for d in decs.values() if d["verdict"] == "exclude"]
    decided_words = set(decs)
    remaining = [c["word"] for c in cand_list if c["word"] not in decided_words]

    groups = {c: [] for c in CATS}
    for w, d in sorted(decs.items(), key=lambda kv: kv[1].get("rank", 10 ** 9)):
        if d["verdict"] == "include":
            groups[d["cat"]].append((w, d["reading"], d["meaning"]))

    src = build_source(groups, len(included))
    out_py = os.path.join(BACKEND, "glossary_lexicon_extra2.py")
    with open(out_py, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    exc = {
        "generated": __import__("time").strftime("%Y-%m-%dT%H:%M"),
        "rule": "dual evidence gate: weblio dictionary + corpus (golden_8165 lines / kanbun.info ruby)",
        "excluded": [
            {"word": d["word"], "rank": d.get("rank"), "freq": d.get("freq"),
             "exclude_reason": d["exclude_reason"]}
            for d in sorted(excluded, key=lambda d: d.get("rank", 10 ** 9))
        ],
    }
    out_ex = os.path.join(EV, "night79_excluded.json")
    with open(out_ex, "w", encoding="utf-8", newline="\n") as f:
        json.dump(exc, f, ensure_ascii=False, indent=1)

    print("included=%d excluded=%d remaining=%d" % (len(included), len(excluded), len(remaining)))
    for cat in CATS:
        print("  %-9s %d" % (cat, len(groups[cat])))
    print("written:", out_py)
    print("written:", out_ex)
    if remaining:
        print("remaining candidates (first 15):", ", ".join(remaining[:15]))


if __name__ == "__main__":
    main()
