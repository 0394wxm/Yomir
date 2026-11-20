# -*- coding: utf-8 -*-
"""night45_e2e_check.py — 生产 OCR 路径上的开关验证（NIGHT45 端到端）。

离线原型（tools/night45_cluster_proto3.py）证明了语义正确；本脚本证明**引擎真的
走了这条路径**：对 p021（唯一应变化的页）+ p020（应完全不变）跑真实 OCR 两次，
一次 KANBUN_OCR_MAINCOL=1，一次 =0，逐行比对。

p021 的判据（正文可验证）：
  * 开关关：'久矣天将以夫子爲木鐸'（左列 x=1081）排在 '天下之無道也'（右列 x=1135）之前
  * 开关开：反过来 —— 因为原文是「天下之無道也久矣、天将以夫子爲木鐸」

产出: eval/night45_e2e.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

IMGDIR = os.path.join(ROOT, "eval", "import_pid_11892692", "pages")
OUT = os.path.join(ROOT, "eval", "night45_e2e.json")
PAGES = ["p020", "p021"]


def find_image(tag):
    path = os.path.join(IMGDIR, tag + ".jpg")
    return path if os.path.exists(path) else None


def run_engine(engine, path, maincol):
    os.environ["KANBUN_OCR_MAINCOL"] = "1" if maincol else "0"
    os.environ["KANBUN_OCR_ORDER"] = "cluster"
    with open(path, "rb") as f:
        data = f.read()
    res = engine.recognize_bytes(data)
    return res["lines"]


def main():
    from backend.ocr_engine import get_engine
    engine = get_engine()
    out = {"pages": []}
    for tag in PAGES:
        path = find_image(tag)
        if path is None:
            print("[skip] %s 找不到样张图" % tag)
            continue
        on = run_engine(engine, path, True)
        off = run_engine(engine, path, False)
        same = on == off
        print("%s lines on=%d off=%d  identical=%s"
              % (tag, len(on), len(off), same), flush=True)
        if not same:
            for k in range(max(len(on), len(off))):
                a = on[k] if k < len(on) else "<none>"
                b = off[k] if k < len(off) else "<none>"
                if a != b:
                    print("   [%2d] ON : %s" % (k, a[:44]))
                    print("        OFF: %s" % b[:44])
        out["pages"].append({"page": tag, "lines_on": len(on),
                             "lines_off": len(off), "identical": same,
                             "on": on, "off": off})

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n[written] eval/night45_e2e.json")


if __name__ == "__main__":
    main()
