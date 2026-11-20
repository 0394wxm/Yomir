# -*- coding: utf-8 -*-
"""night44_book.py — 用 filter=ON 的全本 OCR 结果重建 book.md（NIGHT44 交付物）。

输入: eval/night44_full/filter_on/*.json（tools/night44_fullrun.py 产出，含 lines/text）
输出: eval/import_pid_11892692/book_filter_on.md
      —— 与 Night42 基线 eval/import_pid_11892692/book.md **同格式**（白文 + 書き下し文），
         便于逐页 diff。基线文件**不动**（红线：不改历史归档）。

训读走与 import_pid.py 完全相同的 `_kundoku_result_for(hakubun, merge=True, ortho=True)`。
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.main import _kundoku_result_for, _load_engine  # noqa: E402

FULL = os.path.join(ROOT, "eval", "night44_full", "filter_on")
OUT_DIR = os.path.join(ROOT, "eval", "import_pid_11892692")
OUT_MD = os.path.join(OUT_DIR, "book_filter_on.md")
PID = "11892692"
TITLE = "論語10卷.一"


def main():
    files = sorted(f for f in os.listdir(FULL) if f.endswith(".json"))
    if not files:
        print("[error] no filter_on results in %s" % FULL)
        return 1
    print("[plan] %d pages" % len(files), flush=True)
    t0 = time.time()
    _load_engine()
    print("[engine] load %.1fs" % (time.time() - t0), flush=True)

    doc = ["# 批量导入：%s（NDL %s）" % (TITLE, PID), ""]
    total_kun = 0.0
    n_ok = n_skip = 0
    for fn in files:
        with open(os.path.join(FULL, fn), encoding="utf-8") as f:
            p = json.load(f)
        pg = p["page"]
        hakubun = p["text"]
        if not hakubun.strip():
            n_skip += 1
            doc += ["## %s" % pg, "", "(0 行)", ""]
            print("[%s] 0 行" % pg, flush=True)
            continue
        t1 = time.time()
        _kaeriten, _raw, kakikudashi = _kundoku_result_for(hakubun, merge=True, ortho=True,
                                                           use_cache=True)
        kun_sec = time.time() - t1
        total_kun += kun_sec
        n_ok += 1
        print("[%s] lines=%d kundoku %.1fs" % (pg, p["line_count"], kun_sec), flush=True)
        doc += [
            "## %s" % pg, "",
            "**白文**",
            "", "```", hakubun, "```", "",
            "**書き下し文（merge+ortho）**",
            "", "```", kakikudashi, "```", "",
        ]

    doc += ["---", "",
            "耗时：训读 %.1fs；成功 %d 页，跳过/失败 %d 页（共 %d 页）"
            % (total_kun, n_ok, n_skip, len(files)), ""]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(doc))
    print("[done] ok=%d skip=%d kun=%.1fs -> %s" % (n_ok, n_skip, total_kun, OUT_MD))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
