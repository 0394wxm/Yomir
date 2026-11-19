# -*- coding: utf-8 -*-
"""test_ocr_night39.py — NIGHT39 同字串垃圾行过滤 + CJK 兼容码位归一 的单元测试。"""
from backend.ocr_postfix import (
    is_junk_repeat_line,
    normalize_compat_ideographs,
    postprocess_line,
)


def test_junk_repeat_lines():
    assert is_junk_repeat_line("一一一一一一一")      # 781193 界框实形态
    assert is_junk_repeat_line("王王王")
    assert is_junk_repeat_line("口口口口口口")
    assert not is_junk_repeat_line("")                # 空行
    assert not is_junk_repeat_line("一")              # 单字行是合法内容
    assert not is_junk_repeat_line("一一")            # 两个不拦
    assert not is_junk_repeat_line("人生")
    assert not is_junk_repeat_line("一子一丑")        # 非全同
    assert not is_junk_repeat_line("aaa")             # ASCII 交给 Night6 _has_text


def test_compat_ideographs():
    assert normalize_compat_ideographs("\uFA5B七十二人") == "者七十二人"
    assert normalize_compat_ideographs("\uFA42") == "既"   # Unicode 正则等价为既
    assert normalize_compat_ideographs("漢字漢字") == "漢字漢字"  # 非FA区不动
    assert normalize_compat_ideographs("") == ""


def test_postprocess_line_combined():
    # FA 者形 + 词典命中，一条过
    assert postprocess_line("\uFA5B七十二人。然嘗終不能用") == "者七十二人。然魯終不能用"


def test_engine_wiring_importable():
    # 引擎模块能加载新函数（PROJECT_ROOT 入 sys.path 的导入方式可用）
    from backend import ocr_engine
    assert callable(ocr_engine.is_junk_repeat_line)
    assert callable(ocr_engine.normalize_compat_ideographs)
