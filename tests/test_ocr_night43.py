# -*- coding: utf-8 -*-
"""test_ocr_night43.py — NIGHT43：版面几何噪音过滤（页脚带手写/书志短行）。

判据依据 eval/night43_stats.json 的实测分布（6 个选样页、123 行标注）：
  noise 行 cy - y_max ∈ [+2, +24]、body 行最大 -54 → FOOTER_MARGIN=-12 居中。
样本坐标取自 eval/night43_boxes.json / night43_pair.json 实测（11892692）。
"""
from backend.ocr_layout import FOOTER_MARGIN, judge_layout


def _page(footer_rows=0, n_main=16, main_y=252, main_h=545, main_w=52, start_x=1149):
    """构造 GT 正文页样（p005 实测几何）：n_main 个主栏长框 + 可选页脚短行。"""
    boxes = []
    for i in range(n_main):
        boxes.append({"x": start_x - i * 54, "y": main_y, "w": main_w, "h": main_h})
    y_max = main_y + main_h
    for j in range(footer_rows):
        boxes.append({"x": 1063 - j * 19, "y": 800, "w": 16, "h": 50})
    return boxes, y_max


def test_footer_rows_removed_body_kept():
    boxes, y_max = _page(footer_rows=21)   # p020 实测：21 个页脚短行
    miban, judged = judge_layout(boxes, 1400, 978)
    assert miban is not None
    removed = [b for b, r in judged if r == "footer_band"]
    kept = [b for b, r in judged if r is None]
    assert len(removed) == 21
    assert len(kept) == 16
    # 被滤的全是页脚短行（h=50、cy>=y_max）
    assert all(b["h"] == 50 and b["y"] + b["h"] / 2 >= y_max for b in removed)


def test_gt_page_untouched():
    """GT 正文页（p005 实测 16 框，无页脚）：零过滤。"""
    boxes, _ = _page(footer_rows=0)
    _, judged = judge_layout(boxes, 1400, 978)
    assert all(r is None for _, r in judged)


def test_headnote_band_kept():
    """上部头注带（印刷注釈/手写条）不滤——含 Night42 点名的 2 个未滤样例位置。
    几何上印刷头注(h≈159-185)与手写条(h≈40-120)重合，不可分（实测放弃）。"""
    boxes, _ = _page(footer_rows=0)
    boxes.append({"x": 1012, "y": 56, "w": 16, "h": 168})   # 早朝堀紀州岩朝不福指越
    boxes.append({"x": 845, "y": 116, "w": 18, "h": 77})    # 新助麹町三丁
    boxes.append({"x": 425, "y": 42, "w": 22, "h": 185})    # 太野氏峯之長太夫様（印刷头注）
    _, judged = judge_layout(boxes, 1400, 978)
    assert all(r is None for _, r in judged)


def test_title_column_kept():
    """正文篇题短列（p003「論語序説」x=589 y=227 w=47 h=143，GT 9 行之一）必须保留。
    防 strip 类判据复辟：miban 内、h 只有主栏 27%。"""
    boxes, _ = _page(footer_rows=0)
    boxes.append({"x": 589, "y": 227, "w": 47, "h": 143})
    _, judged = judge_layout(boxes, 1400, 978)
    assert all(r is None for _, r in judged)


def test_blank_page_no_miban_keeps_all():
    """扉页/空白页（主栏候选 <3）：版心估不出，一律保留。"""
    boxes = [{"x": 100, "y": 100, "w": 50, "h": 120}]
    miban, judged = judge_layout(boxes, 1400, 978)
    assert miban is None
    assert all(r is None for _, r in judged)
    assert judge_layout([], 1400, 978) == (None, [])


def test_horizontal_boxes_never_filtered():
    """横書き框（w>h）不参与页脚判据。"""
    boxes, _ = _page(footer_rows=0)
    boxes.append({"x": 200, "y": 900, "w": 300, "h": 40})  # 页底横条
    _, judged = judge_layout(boxes, 1400, 978)
    assert all(r is None for _, r in judged)


def test_footer_margin_boundary():
    """阈值边界：cy = y_max + FOOTER_MARGIN 恰在界上 → 滤；再上 -1 → 保留。"""
    boxes, y_max = _page(footer_rows=0)
    cy_hit = y_max + FOOTER_MARGIN
    boxes.append({"x": 500, "y": int(cy_hit) - 25, "w": 16, "h": 50})
    boxes.append({"x": 470, "y": int(cy_hit) - 26, "w": 16, "h": 50})
    _, judged = judge_layout(boxes, 1400, 978)
    reasons = {b["x"]: r for b, r in judged}
    assert reasons[500] == "footer_band"
    assert reasons[470] is None


def test_narrow_strip_in_main_band_kept():
    """主栏带内窄条（p020「明吉本発有死」h=99 / p017「説左伝習録」h=100）保留。
    strip 判据在 p012/p017 误杀头注正文后被否决（见 ocr_layout 注释档）。"""
    boxes, _ = _page(footer_rows=0)
    boxes.append({"x": 1170, "y": 568, "w": 13, "h": 99})
    boxes.append({"x": 292, "y": 631, "w": 25, "h": 100})
    _, judged = judge_layout(boxes, 1400, 978)
    assert all(r is None for _, r in judged)
