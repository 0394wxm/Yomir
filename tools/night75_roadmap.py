# -*- coding: utf-8 -*-
"""night75_roadmap.py — N75 专用：ROADMAP.md 末尾追加一行（二进制 UTF-8 追加，不动既有字节）。
CJK 内容硬编码在脚本里（cmd argv 传 CJK 会乱码，见 SHIFT_LOG N72 教训）。
终值（accept 提交号）在主提交后由 night75_roadmap2.py 补，或本行先写主提交号。
"""
LINE = ("- 状态: DONE — Night 75（2026-11-22，分支 night75-lexicon-fix）：修词库 19 条错项"
        "（17 条按 N74 审计证据修改 + 舎/玷く 2 条核验后不改，diff 只动两个词库文件共 17 行）；"
        "回归 tests/test_night75_lexicon_fix.py 24 passed，死条目異端/収拾す复活，"
        "golden_4000 真跑与 night73 归档逐位一致（avgDist 13.517/exact 24/error 0）；"
        "accept 75 PASS fail=0 skip=0（pytest 331=331）。详见 REPORT_NIGHT75.md。\n")


def main():
    with open("ROADMAP.md", "ab") as f:
        f.write(LINE.encode("utf-8"))
    print("appended 1 line to ROADMAP.md")


if __name__ == "__main__":
    main()
