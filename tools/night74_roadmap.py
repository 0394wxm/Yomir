# -*- coding: utf-8 -*-
"""night74_roadmap.py — N74 专用：ROADMAP.md 末尾追加一行（二进制 UTF-8 追加，不动既有字节）。
CJK 内容硬编码在脚本里（cmd argv 传 CJK 会乱码，见 SHIFT_LOG N72 教训）。
"""
LINE = ("- 状态: DONE — Night 74（2026-11-22，分支 night74-lexicon，report-only）："
        "词库 500 条校对审计（OK 438／存疑 43／错 19／来源不可达 0；weblio 主源，kotobank 403 不可达，"
        "白文命中 359／零命中 141）；错 19 条修复清单见 REPORT_NIGHT74.md 与 eval/night74_lexicon_audit.md Top-20，"
        "修不修词库留用户拍板；backend 一字未改，pytest 307，accept 74 PASS fail=0 skip=1（skip=eval_integrity，"
        "report-only 夜无评测归档）。\n")


def main():
    with open("ROADMAP.md", "ab") as f:
        f.write(LINE.encode("utf-8"))
    print("appended 1 line to ROADMAP.md")


if __name__ == "__main__":
    main()
