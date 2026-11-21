# -*- coding: utf-8 -*-
"""test_night67_aux_ying.py — N67⑬: udkundoku AUX「應,v,助動詞,必要,*」runtime 补丁锁定。

N59 实证：udkundoku/auxiliary.py 的 AUX 25 键中「v,助動詞,必要」组只有 儀/宜/須、缺 應，
缺键 = 任何含助動詞「應」的输入整条 500（KeyError('應,v,助動詞,必要,*')）；
golden_4000 的 toushisen135-12 / toushisen043-16 与 golden_7908 的 zasshi-2 三条
评测 error 同源。backend/main.py _load_engine 启动时以同 xpos 的「須」值
runtime 补 1 条（幂等；site-packages 一行不动）。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import udkundoku.auxiliary as aux_mod  # noqa: E402

KEY = "應,v,助動詞,必要,*"


def test_ying_necessary_aux_patched_and_api_ok():
    """⑬: 引擎加载后 AUX 必要组含「應」；含應输入 200 且出訓読（N59 对照输出含 べし）。"""
    from fastapi.testclient import TestClient

    from backend.main import _load_engine, app

    _load_engine()
    assert KEY in aux_mod.AUX, "AUX 缺「應,v,助動詞,必要,*」——⑬ runtime 补丁未生效"
    assert aux_mod.AUX[KEY] == aux_mod.AUX["須,v,助動詞,必要,*"]

    with TestClient(app) as client:
        r = client.post("/api/kundoku", json={"text": "應知黃綺心"})
        assert r.status_code == 200, r.text
        kk = r.json().get("kakikudashi", "")
        assert "べし" in kk, kk  # N59 内存补丁对照：黄の綺心を知るべし
        for text in ("應照離人粧鏡臺", "應知故鄉事"):
            r2 = client.post("/api/kundoku", json={"text": text})
            assert r2.status_code == 200, "%s -> %s" % (text, r2.text)
            assert r2.json().get("kakikudashi"), text
