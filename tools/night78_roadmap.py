# -*- coding: utf-8 -*-
"""night78_roadmap.py — ROADMAP.md 末尾に Night 78 CLOSED 一行を追加（'a' 追加のみ）。"""
import io

LINE = ("- 状态: CLOSED — Night 78（Rule N かな→漢字第 10 系列＋ことな族活用形分割＋現代語副詞族）："
        "13 条写入 kundoku_rules.py 接 M 链尾（ことな族 5 条——umbrella ことなかれ→こと莫かれ は死行 "
        "kokyo09-5（白文「嚴父莫大於配天」＝すことなかれ 行・15→16 変差）で拒＝N58/N68/N73 なかれ→莫かれ "
        "と同死因の機構境界実証、prefix keys（する/ざる/なる/う/る）は死行を避けて全 0 変差・"
        "ることなかれ 1 本で 61 行 substring 覆盖；現代語副詞族 8 条——はいよいよ/いよいよ→弥〻"
        "（守り字新旧両形 弥/彌：白文は旧字体 彌・単形 guard は 0 発火を sim が捕捉）、しばしば→屢〻、"
        "ほとんど→殆、はやや→稍く、やや→稍、たま→偶、なんぞ→胡（K 盍/奚/曷 の守り外 7 行））；"
        "tests/test_night78_rule_n.py 30 项（全量 337 passed）；TestClient 双口径真跑与离线模拟逐位一致——"
        "golden_4000 13.517→13.495（改写 55/改善 45/变差 0/exact 24）、golden_8165 14.546→14.526（97/85/0/30）；"
        "拒案 koto_full umbrella（変差 1）＋き/ぶ/く/つことなかれ（無益 Δ−0.000）＋落选字形 屢/弥/偶〻 実数归档；"
        "GT CER 结构性不变；README/verify 同步 18/18；NIGHT_ARTIFACTS[78] 登记、accept 78 PASS（fail=0 skip=0）；"
        "備選⑥なかれ→莫かれ復活条件調查（eval/night78_mokaku.md）——post-N 目標 16 行 12 改善/1 変差"
        "（kokyo09-5 のみ）、莫大 co-occurrence 判別式仮説を実測で否定。\n")

with io.open("ROADMAP.md", "a", encoding="utf-8", newline="") as f:
    f.write(LINE)
print("ROADMAP appended")
