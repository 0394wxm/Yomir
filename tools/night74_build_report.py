# -*- coding: utf-8 -*-
"""night74_build_report.py — N74 判定合并 → eval/night74_lexicon_audit.md 生成器。

读 eval/night74_lexicon_audit.json（机械自查）+ eval/night74_dict_cache/verdicts_*.json
（逐条人工判定），输出：
  - 逐条表（idx/词形/读音/判定/证据要点/建议改法）
  - 汇总（OK/存疑/错/来源不可达）
  - 「最该修的前 20 条」（错优先，按语料命中数降序；不足用存疑补足）
词库一字不改。
用法: python -I tools/night74_build_report.py
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "eval", "night74_lexicon_audit.json")
CACHE = os.path.join(ROOT, "eval", "night74_dict_cache")
OUT = os.path.join(ROOT, "eval", "night74_lexicon_audit.md")


def main():
    audit = json.load(open(AUDIT, encoding="utf-8"))
    entries = {e["idx"]: e for e in audit["entries"]}

    verdicts = {}
    for p in sorted(glob.glob(os.path.join(CACHE, "verdicts_*.json"))):
        for v in json.load(open(p, encoding="utf-8")):
            verdicts[v["idx"]] = v
    print("verdicts loaded:", len(verdicts))

    counts = {"OK": 0, "存疑": 0, "错": 0, "来源不可达": 0}
    unjudged = []
    for i in range(500):
        v = verdicts.get(i)
        if not v:
            unjudged.append(i)
            continue
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1

    # Top-20: 错を優先（语料命中数降序）、足りなければ存疑
    def hits(i):
        e = entries[i]
        return e["bun_doc_hits"] + e["kkd_doc_hits"]

    wrong = [i for i in verdicts if verdicts[i]["verdict"] == "错"]
    wrong.sort(key=lambda i: -hits(i))
    dubious = [i for i in verdicts if verdicts[i]["verdict"] == "存疑"]
    dubious.sort(key=lambda i: -hits(i))
    top20 = (wrong + dubious)[:20]

    lines = []
    lines.append("# Night 74 词库 500 条校对审计（逐条判定）")
    lines.append("")
    lines.append("- 审计对象: backend/glossary_lexicon.py（209 条）+ backend/glossary_lexicon_extra.py（291 条）＝500 条；本夜一字未改")
    lines.append("- 主要来源: www.weblio.jp（デジタル大辞泉／Wiktionary／文語活用形辞書／実用日本語表現辞典等の聚合页）")
    lines.append("- 来源不可达: kotobank.jp（全站 403 反爬拒绝）、goo辞書（超时）——凡仅凭通识、无辞书页佐证的条目按「存疑」计")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| 判定 | 条数 |")
    lines.append("|---|---|")
    for k in ("OK", "存疑", "错", "来源不可达"):
        lines.append("| %s | %d |" % (k, counts.get(k, 0)))
    lines.append("| 未判定 | %d |" % len(unjudged))
    lines.append("")
    lines.append("覆盖率（语料命中，golden_8165）: 白文命中 %d 条／零命中 %d 条；書き下し文命中 %d 条／零命中 %d 条（机械自查详见 night74_lexicon_audit.json）"
                 % (audit["summary"]["coverage_bun_positive"], audit["summary"]["coverage_bun_zero"],
                    audit["summary"]["coverage_kkd_positive"], audit["summary"]["coverage_kkd_zero"]))
    lines.append("")
    lines.append("## 最该修的前 20 条")
    lines.append("")
    lines.append("| # | idx | 词形 | 现读音 | 判定 | 语料命中(白文+書下) | 要点 |")
    lines.append("|---|---|---|---|---|---|---|")
    for n, i in enumerate(top20, 1):
        e = entries[i]
        v = verdicts[i]
        point = (v.get("fix") or v.get("evidence") or "").replace("|", "／").replace("\n", " ")[:120]
        lines.append("| %d | %d | %s | %s | %s | %d | %s |" % (
            n, i, e["word"], e["reading"], v["verdict"], hits(i), point))
    lines.append("")
    lines.append("## 逐条判定表")
    lines.append("")
    lines.append("| idx | 词形 | 读音 | 释义 | kind | 白文命中 | 書下命中 | 判定 | 证据 | 建议改法 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i in range(500):
        e = entries[i]
        v = verdicts.get(i)
        if v:
            ev = v.get("evidence", "").replace("|", "／").replace("\n", " ")
            fx = v.get("fix", "").replace("|", "／").replace("\n", " ")
            lines.append("| %d | %s | %s | %s | %s | %d | %d | **%s** | %s | %s |" % (
                i, e["word"], e["reading"], e["meaning"].replace("|", "／"), e["kind"] or "-",
                e["bun_doc_hits"], e["kkd_doc_hits"], v["verdict"], ev, fx))
        else:
            lines.append("| %d | %s | %s | %s | %s | %d | %d | (未判定) | - | - |" % (
                i, e["word"], e["reading"], e["meaning"].replace("|", "／"), e["kind"] or "-",
                e["bun_doc_hits"], e["kkd_doc_hits"]))
    lines.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written:", OUT)
    # 控制台 cp1252：判定档名是 CJK，落盘到 JSON 侧注里
    with open(os.path.join(CACHE, "_counts.json"), "w", encoding="utf-8") as f:
        json.dump({"counts": counts, "unjudged": unjudged}, f, ensure_ascii=False)
    print("counts_ascii: OK=%d dubious=%d wrong=%d unreachable=%d unjudged=%d" % (
        counts.get("OK", 0), counts.get("存疑", 0), counts.get("错", 0),
        counts.get("来源不可达", 0), len(unjudged)))


if __name__ == "__main__":
    main()
