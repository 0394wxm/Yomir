# -*- coding: utf-8 -*-
"""build_lexicon_extra.py — 由 eval/lexicon_extra_src.txt 生成 backend/glossary_lexicon_extra.py。

为什么要有这一步：D3 的硬约束是「只加在 200 条语料里真实出现过的词」。
人工写词表难免混入语料外的词，所以词表以纯文本（可 diff、可复核）维护，
由本脚本按下列规则过滤后再生成 Python 模块：

  1. word 必须出现在 eval/night5_results_full_v3.json 的 200 条语料
     （白文 + expected 書き下し文）中；
  2. 不与旧 209 条重复，内部不重复；
  3. reading / meaning 非空，meaning ≤ 60 字；
  4. 按 kind 分组输出：s 専名 → n 名詞 → v 動詞 → a 形容詞・副詞 → p 機能語；
     组内按词长降序（长词先匹配，避免「子」抢走「孔子」的名额）。

不足 TARGET 条时直接非零退出，绝不静默补空。

用法：python tools/build_lexicon_extra.py [--check]
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.glossary_lexicon import GLOSSARY_LEXICON  # noqa: E402

TARGET = 291
SRC = os.path.join(ROOT, "eval", "lexicon_extra_src.txt")
OUT = os.path.join(ROOT, "backend", "glossary_lexicon_extra.py")

KIND_ORDER = ["s", "n", "v", "a", "p"]
KIND_TITLE = {
    "s": "固有名詞（人物・地名・書名）",
    "n": "名詞（内容詞）",
    "v": "動詞（内容詞）",
    "a": "形容詞・副詞（内容詞）",
    "p": "機能語（内容詞の後に置く）",
}
VAR = {"s": "PROPER", "n": "NOUNS", "v": "VERBS", "a": "MODIFIERS", "p": "FUNCTION"}


def old_entries():
    """旧 209 条（不含扩充）。GLOSSARY_LEXICON 已合并扩充，故用 _OLD_SIZE 截断。"""
    import backend.glossary_lexicon as gl
    n = getattr(gl, "_OLD_SIZE", None)
    if n is None:
        raise SystemExit("glossary_lexicon 缺 _OLD_SIZE，无法区分旧条目与扩充")
    return gl.GLOSSARY_LEXICON[:n]


def load_src():
    rows = []
    with io.open(SRC, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) != 4:
                raise SystemExit("第 %d 行字段数不是 4：%r" % (ln, line))
            w, reading, meaning, kind = [x.strip() for x in p]
            if kind not in KIND_ORDER:
                raise SystemExit("第 %d 行 kind 非法：%s" % (ln, kind))
            rows.append((w, reading, meaning, kind))
    return rows


def main():
    check = "--check" in sys.argv
    with io.open(os.path.join(ROOT, "eval", "night5_results_full_v3.json"), encoding="utf-8") as f:
        items = json.load(f)["results"]
    corpus = "\n".join(r["hakubun"] + "\n" + r["expected_kakikudashi"] for r in items)

    old = {e["word"] for e in old_entries()}
    rows = load_src()
    seen = set()
    kept, dropped = [], []
    for w, reading, meaning, kind in rows:
        why = None
        if w in old:
            why = "与旧词库重复"
        elif w in seen:
            why = "内部重复"
        elif w not in corpus:
            why = "语料中未出现"
        elif not reading:
            why = "缺 reading"
        elif not meaning:
            why = "缺 meaning"
        elif len(meaning) > 60:
            why = "meaning 过长(%d)" % len(meaning)
        if why:
            dropped.append((w, why))
            continue
        seen.add(w)
        kept.append((w, reading, meaning, kind))

    print("源 %d 条 → 合格 %d 条，剔除 %d 条" % (len(rows), len(kept), len(dropped)))
    for w, why in dropped:
        print("  剔除 %s：%s" % (w, why))

    if len(kept) < TARGET:
        print("!! 合格条目不足：需要 %d，实得 %d，差 %d" % (TARGET, len(kept), TARGET - len(kept)))
        return 1
    if len(kept) > TARGET:
        print("提示：合格 %d 条 > 目标 %d，按源顺序截断（多余条目不会写入）" % (len(kept), TARGET))
        kept = kept[:TARGET]

    grouped = {k: [] for k in KIND_ORDER}
    for w, r, m, k in kept:
        grouped[k].append((w, r, m))
    for k in KIND_ORDER:
        grouped[k].sort(key=lambda t: -len(t[0]))

    if check:
        print("--check：不写文件。分组计数 " + " / ".join("%s=%d" % (k, len(grouped[k])) for k in KIND_ORDER))
        return 0

    out = []
    out.append("# -*- coding: utf-8 -*-")
    out.append('"""glossary_lexicon_extra.py — 词库扩充（D3：209 → 500）。自动生成，请勿手改。')
    out.append("")
    out.append("生成源：eval/lexicon_extra_src.txt（人工整理）+ tools/build_lexicon_extra.py（校验/排序）。")
    out.append("每个词形都经 tools/build_lexicon_extra.py 核验：真实出现于 200 条语料、与旧词库无重复。")
    out.append("")
    out.append("排序即优先级：専名 → 名詞 → 動詞 → 形容詞・副詞 → 機能語，组内按词长降序。")
    out.append("find_in_lexicon 按列表顺序取前 max_hits 条，故内容词长词优先于功能词。")
    out.append("读音/释义为 agent 依文语通识填写，未逐条人工校对。")
    out.append('"""')
    out.append("")
    out.append('LEXICON_EXTRA_SOURCE = ("agent 整理（文语法通识归纳，非逐字引用；收录词形经 200 条语料硬校验，'
               '未人工校对）")')
    out.append("")
    for k in KIND_ORDER:
        out.append("# ---- %s ----" % KIND_TITLE[k])
        out.append("%s = [" % VAR[k])
        for w, r, m in grouped[k]:
            out.append('    ("%s", "%s", "%s"),' % (w, r, m))
        out.append("]")
        out.append("")
    out.append("")
    out.append("def as_dicts():")
    out.append('    """按「内容词优先」顺序展开为 GLOSSARY_LEXICON 同构的字典列表。')
    out.append("")
    out.append('    kind="content" 的内容词先于 kind="function" 的功能词——')
    out.append("    find_in_lexicon 按列表顺序取前 max_hits 条，故本顺序即語釈优先级。")
    out.append('    """')
    out.append("    rows = []")
    for k in KIND_ORDER:
        out.append("    for w, r, m in %s:" % VAR[k])
        out.append('        rows.append({"word": w, "reading": r, "meaning": m, "kind": "%s"})'
                   % ("function" if k == "p" else "content"))
    out.append("    return rows")
    out.append("")
    out.append("")
    out.append("def extra_size():")
    out.append("    return sum(len(x) for x in (%s))" % ", ".join(VAR[k] for k in KIND_ORDER))
    out.append("")

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("写出 %s：%d 条（分组 %s）"
          % (OUT, sum(len(v) for v in grouped.values()),
             " / ".join("%s=%d" % (k, len(grouped[k])) for k in KIND_ORDER)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
