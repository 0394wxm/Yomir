# -*- coding: utf-8 -*-
"""night44_mark_verdicts.py — 把人工复核结论写回 night44_footer_review.json（NIGHT44）。

复核方式：tools/night44_review_footer.py 用 KANBUN_OCR_LAYOUT_FILTER=0 跑产品流，
把每页被判 footer_band 的框连文本打出来；本脚本按**逐行人工读过的结论**写 verdict。

判定标准（与 REPORT_NIGHT43 §2.3 同款）：
  ok_noise    —— 页脚插入物特征：人名/地名/册数/价格/日期/记事碎片，
                 且不接续任何正文列的句子。
  wrong_body  —— 经文连续句、割注、或能从邻列接续的正文。
  ambiguous   —— 短碎片无法从文本判断，但仍位于页脚带且不与正文列接续（记 note）。

**这是复核，不是改判据**：backend/ocr_layout.py 一个字不动；verdict 只写进测量归档。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "eval", "night44_footer_review.json")

# 逐框人工结论：text -> (verdict, note)
MANUAL = {
    # ---- p014（24 框，手写杂记带）----
    "敵ゐぬが": ("ok_noise", "手写杂记碎片"),
    "いつぎ孔子": ("ok_noise", "手写；『孔子』是斋名/人名语境，非经文接续"),
    "村田村": ("ok_noise", "人名（村田村）"),
    "非也、": ("ambiguous", "4 字短碎片；上邻列末字『尤』不接续，位置在正文列底缘以下"),
    "武士美麗と": ("ok_noise", "手写杂记"),
    "しかきないます": ("ok_noise", "手写杂记（口语体）"),
    "一同村伊勢守様": ("ok_noise", "人名+敬称（伊勢守様）"),
    "新田老": ("ok_noise", "人名（新田老）"),
    "県傾向": ("ok_noise", "手写碎片"),
    "なゐ": ("ok_noise", "假名碎片"),
    "曰る中田": ("ok_noise", "地名/人名"),
    "四巻惣や": ("ok_noise", "册数（四巻）"),
    "きはゝ絵の": ("ok_noise", "手写杂记"),
    "安府西は": ("ok_noise", "地名碎片"),
    "悲し感悲し": ("ok_noise", "手写杂记"),
    "水君様": ("ok_noise", "人名+敬称"),
    "名古館": ("ok_noise", "地名（名古屋系）"),
    "一猿葉寺": ("ok_noise", "寺名/册数"),
    "大学をつて": ("ok_noise", "手写杂记；『大学』在此为杂记用词，非《大学》经文"),
    "知布同": ("ok_noise", "手写碎片"),
    "鈴木佐美座候以上": ("ok_noise", "书信体（…座候以上），明确非经文"),
    "一同四十五軒": ("ok_noise", "轩数统计"),
    "此院向事故四丁": ("ok_noise", "书志记注（丁数）"),
    "可奉上候": ("ok_noise", "书信体（可奉上候）"),
    # ---- p015（24 框，同一手写带）----
    "武太郎": ("ok_noise", "人名"),
    "観音姫": ("ok_noise", "人名/杂记"),
    "いつきなる子": ("ok_noise", "手写杂记"),
    "やけるやける": ("ok_noise", "手写杂记（叠词）"),
    "〽まやうしいかな": ("ok_noise", "手写杂记（〽 记号）"),
    "同じやい": ("ok_noise", "手写杂记"),
    "保殿向": ("ok_noise", "人名+敬称"),
    "曲ゐ中田": ("ok_noise", "地名/人名"),
    "田是惣而": ("ok_noise", "手写碎片"),
    "三々刺波ア": ("ok_noise", "手写碎片"),
    "監へ刺越": ("ok_noise", "手写碎片"),
    "奥村也": ("ok_noise", "人名"),
    "非君臣": ("ok_noise", "3 字碎片；位于页脚带、与正文列不接续"),
    "西宿新": ("ok_noise", "地名"),
    "知本頃": ("ok_noise", "手写碎片"),
    "後葉寺": ("ok_noise", "寺名"),
    "大家を": ("ok_noise", "手写碎片"),
    "御大札を計る": ("ok_noise", "书信体（御大札）"),
    "岡等半石川": ("ok_noise", "地名/人名"),
    "此所様口事": ("ok_noise", "手写碎片"),
    "御本与三郎": ("ok_noise", "人名（与三郎）"),
    # ---- p044（21 框）----
    "ふ是": ("ambiguous", "2 字碎片；页脚带内、不与正文列接续"),
    "嘉次三": ("ok_noise", "人名/手写碎片"),
    "紺代、": ("ok_noise", "手写碎片"),
    "●金橋": ("ok_noise", "记号+地名"),
    "琵琶郡有様": ("ok_noise", "地名（琵琶郡）"),
    "金五余": ("ok_noise", "金额"),
    "大子景本": ("ok_noise", "手写碎片"),
    "に西其薬": ("ok_noise", "手写碎片"),
    "云未達": ("ok_noise", "手写碎片"),
    "夫子竹槙": ("ok_noise", "手写碎片"),
    "達候政": ("ok_noise", "书信体碎片"),
    "記事君": ("ok_noise", "手写碎片"),
    "はさいかつ": ("ok_noise", "假名碎片"),
    "或不対雲": ("ok_noise", "手写碎片"),
    "庄米一畝": ("ok_noise", "租税记事（庄米一畝）"),
    "の内地ま潰": ("ok_noise", "手写碎片"),
    "一廿四六文文": ("ok_noise", "钱数（文）"),
    "嘉永": ("ok_noise", "年号（嘉永）"),
    "名文如是": ("ok_noise", "手写碎片"),
    "不敢尤": ("ambiguous", "3 字碎片；与相邻正文列（…言寡尤）不在同一列，位置在页脚带"),
    "一銭壱匁": ("ok_noise", "金额（一銭壱匁）"),
}


def main():
    with open(P, encoding="utf-8") as f:
        d = json.load(f)
    n_ok = n_wrong = n_amb = n_missing = 0
    for pg in d["pages"]:
        for r in pg["filtered"]:
            v = MANUAL.get(r["text"])
            if v is None:
                n_missing += 1
                print("[MISSING] %s %r" % (pg["page"], r["text"]))
                continue
            r["verdict"], r["note"] = v
            n_ok += v[0] == "ok_noise"
            n_wrong += v[0] == "wrong_body"
            n_amb += v[0] == "ambiguous"
    d["verdict_summary"] = {"ok_noise": n_ok, "wrong_body": n_wrong,
                            "ambiguous": n_amb, "unmarked": n_missing,
                            "total": sum(len(p["filtered"]) for p in d["pages"])}
    with open(P, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print("summary: %s" % json.dumps(d["verdict_summary"], ensure_ascii=False))
    print("HARD GATE wrong_body = %d（必须 0）: %s"
          % (n_wrong, "PASS" if n_wrong == 0 and n_missing == 0 else "FAIL"))


if __name__ == "__main__":
    main()
