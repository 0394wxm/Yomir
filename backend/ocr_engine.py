# -*- coding: utf-8 -*-
r"""
ocr_engine.py — NDL 古典籍 OCR-Lite 进程内包装（Night 2）。

来源与许可:
  引擎代码/模型来自 国立国会図書館 ndl-lab/ndlkotenocr-lite（CC BY 4.0），
  本文件只是把它的推理流程（GUI main.py 的 ocr_button_result 路径）原样
  搬进后端进程内调用，未改动其算法。

运行前提（本机）:
  1. `D:\dlkotenocr-lite\site-packages`（onnxruntime/numpy/PIL/lxml/yaml/...
     等 cp312 包，随官方 Windows 版 GUI 分发，直接复用，不另装）；
  2. 项目根 `ocr_runtime\`：从 `D:\dlkotenocr-lite\data\flutter_assets\app\app.zip`
     解压出来的 src/（含 src\model\*.onnx 两个模型）。
     解压命令:
       python -I -m zipfile -e "D:\dlkotenocr-lite\data\flutter_assets\app\app.zip" ocr_runtime
     （ocr_runtime/ 已在 .gitignore，模型不入库）

路径可用环境变量覆盖: KANBUN_OCR_SITE / KANBUN_OCR_SRC。
"""
import io
import os
import sys
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR_SITE = os.environ.get("KANBUN_OCR_SITE", r"D:\dlkotenocr-lite\site-packages")
OCR_SRC = os.environ.get("KANBUN_OCR_SRC", os.path.join(PROJECT_ROOT, "ocr_runtime", "src"))

_LOCK = threading.Lock()
_ENGINE = None
_ENGINE_ERROR = ""


def _setup_sys_path():
    for p in (OCR_SITE, OCR_SRC):
        if p not in sys.path:
            sys.path.append(p)


class _Args:
    """模仿 argparse.Namespace，供 src/ocr.py 的 get_detector/get_recognizer 用。"""


class OCREngine:
    def __init__(self):
        import numpy as np  # noqa: F401  (ensure bundled numpy loads first via path order)
        from ocr import get_detector, get_recognizer  # ocr_runtime/src/ocr.py

        a = _Args()
        model_dir = os.path.join(OCR_SRC, "model")
        config_dir = os.path.join(OCR_SRC, "config")
        a.det_weights = os.path.join(model_dir, "rtmdet-s-1280x1280.onnx")
        a.det_classes = os.path.join(config_dir, "ndl.yaml")
        # 与官方 GUI main.py 相同的默认阈值
        a.det_score_threshold = 0.2
        a.det_conf_threshold = 0.25
        a.det_iou_threshold = 0.2
        a.rec_weights = os.path.join(model_dir, "parseq-ndl-32x384-tiny-10.onnx")
        a.rec_classes = os.path.join(config_dir, "NDLmoji.yaml")
        a.device = "cpu"
        self.detector = get_detector(args=a)
        self.recognizer = get_recognizer(args=a)
        self._np = np

    # ------------------------------------------------------------------
    # Night3: 垃圾检测框过滤（v3，按 tools/debug_ocr_boxes.py 的实测数据设计）
    #
    # 实测事实（竹取物語 1400x933）：
    #   - 「十四番熊」来自页面右下的**朱印**（box 30x149，satMean 98.4），
    #     不是色卡（色卡/标尺根本没被 eval_xml 输出成 LINE）；
    #   - 正文列高 500~540px 且相当集中（中位约 527），朱印高 149 只有 28%；
    #   - 米色纸底会把 satFrac 推到 0.106 —— 之前 satFrac>0.10 阈值误杀了
    #     真列「をとりつゝよろつの事につかひけり」（v2 教训）。
    # 规则（可经环境变量 KANBUN_OCR_JUNK_FILTER=0 关闭）：
    #   1) satFrac(S>120) > 0.18 —— 纯色块（彩色色卡若被框出）；
    #   2) w > 60% 图宽 —— 标尺/边框横贯整页的细长条；
    #   3) 贴边窄条：右缘 >97% 或左缘 <10% 图宽；
    #   4) 縦行高度 < 0.55×縦行中位高 且 satMean>90 —— 朱印/花押（明显偏矮
    #      且颜色浓）。纯墨迹的短行（割注等）饱和度低，不受影响。
    def _sat_stats(self, img, x, y, w, h):
        np = self._np
        crop = img[y:y + h, x:x + w]
        if crop.size == 0:
            return None
        from PIL import Image as _Image
        hsv = np.array(_Image.fromarray(crop).convert("HSV"))
        sat = hsv[:, :, 1]
        return float(sat.mean()), float((sat > 120).mean())

    def _is_junk_line(self, img, x, y, w, h, median_vh=None) -> bool:
        np = self._np
        if os.environ.get("KANBUN_OCR_JUNK_FILTER", "1") == "0":
            return False
        img_h, img_w = img.shape[:2]
        stats = self._sat_stats(img, x, y, w, h)
        if stats is None:
            return True
        s_mean, s_frac = stats
        if s_frac > 0.18:
            return True
        if w > 0.60 * img_w:
            return True
        if x > 0.97 * img_w or (x + w) < 0.10 * img_w:
            return True
        if median_vh and h < 0.55 * median_vh and s_mean > 90.0:
            return True
        return False

    # ------------------------------------------------------------------
    # Night3: 列序聚类（縦書き版式的阅读顺序）
    #
    # 官方 eval_xml(xy_cut) 的行序在多列密排页面会中段交错（Night2 竹取
    # 物语实测）。这里做确定性聚类：
    #   縦書き行（h>w）→ 按 x 重叠聚成“列”，列按右→左，列内按上→下；
    #   横書き行（w>h）→ 按 y 重叠聚成“行”，行按上→下，行内按右→左；
    #   列/行两个单元再按其包围盒质心（右→左优先）合并输出。
    # KANBUN_OCR_ORDER=cluster 启用；默认 native（保持官方顺序，便于对照）。
    def _cluster_order(self, boxes):
        np = self._np
        if not boxes:
            return []
        vert = [b for b in boxes if b["h"] >= b["w"]]
        horz = [b for b in boxes if b["h"] < b["w"]]

        def overlap_x(a, b):
            lo = max(a["x"], b["x"])
            hi = min(a["x"] + a["w"], b["x"] + b["w"])
            inter = max(0, hi - lo)
            return inter / max(1, min(a["w"], b["w"]))

        def overlap_y(a, b):
            lo = max(a["y"], b["y"])
            hi = min(a["y"] + a["h"], b["y"] + b["h"])
            inter = max(0, hi - lo)
            return inter / max(1, min(a["h"], b["h"]))

        units = []
        # 縦書き：列聚类
        for b in sorted(vert, key=lambda t: -(t["x"] + t["w"])):
            placed = False
            for u in units:
                if u["kind"] == "col" and overlap_x(u["box"], b) >= 0.4:
                    u["items"].append(b)
                    u["box"] = {
                        "x": min(u["box"]["x"], b["x"]),
                        "y": min(u["box"]["y"], b["y"]),
                        "w": max(u["box"]["x"] + u["box"]["w"], b["x"] + b["w"]) - min(u["box"]["x"], b["x"]),
                        "h": max(u["box"]["y"] + u["box"]["h"], b["y"] + b["h"]) - min(u["box"]["y"], b["y"]),
                    }
                    placed = True
                    break
            if not placed:
                units.append({"kind": "col", "box": dict(b), "items": [b]})
        # 横書き：行聚类
        for b in sorted(horz, key=lambda t: t["y"]):
            placed = False
            for u in units:
                if u["kind"] == "row" and overlap_y(u["box"], b) >= 0.4:
                    u["items"].append(b)
                    u["box"] = {
                        "x": min(u["box"]["x"], b["x"]),
                        "y": min(u["box"]["y"], b["y"]),
                        "w": max(u["box"]["x"] + u["box"]["w"], b["x"] + b["w"]) - min(u["box"]["x"], b["x"]),
                        "h": max(u["box"]["y"] + u["box"]["h"], b["y"] + b["h"]) - min(u["box"]["y"], b["y"]),
                    }
                    placed = True
                    break
            if not placed:
                units.append({"kind": "row", "box": dict(b), "items": [b]})
        # 列单元按右→左、行单元按上→下，最后把单元按质心排序输出
        for u in units:
            if u["kind"] == "col":
                u["items"] = sorted(u["items"], key=lambda t: t["y"])
            else:
                u["items"] = sorted(u["items"], key=lambda t: -(t["x"]))
        units.sort(key=lambda u: -(u["box"]["x"] + u["box"]["w"] / 2.0))
        idx = []
        for u in units:
            idx.extend(b["index"] for b in u["items"])
        return idx

    def recognize_bytes(self, data: bytes, order: str | None = None) -> dict:
        """图片字节 → OCR 文本。流程与官方 GUI main.py 的 ocr_button_result 一致。

        order: "native"（默认，eval_xml 顺序）| "cluster"（Night3 列序聚类）
        """
        np = self._np
        from ndl_parser import convert_to_xml_string3
        from reading_order.xy_cut.eval import eval_xml
        from PIL import Image

        if order is None:
            # Night3 实测：4 张样张上 cluster 全部 ≥ native（竹取物语的中段
            # 交错被修正，其余相同），故默认 cluster；KANBUN_OCR_ORDER=native 可回退。
            order = os.environ.get("KANBUN_OCR_ORDER", "cluster")

        start = time.time()
        pil_image = Image.open(io.BytesIO(data)).convert("RGB")
        img = np.array(pil_image)
        img_h, img_w = img.shape[:2]
        imgname = "upload"

        detections = self.detector.detect(img)
        classeslist = list(self.detector.classes.values())

        resultobj = [dict(), dict()]
        resultobj[0][0] = list()
        for i in range(17):
            resultobj[1][i] = []
        for det in detections:
            xmin, ymin, xmax, ymax = det["box"]
            conf = det["confidence"]
            char_count = det.get("pred_char_count", 0)
            if det["class_index"] == 0:
                resultobj[0][0].append([xmin, ymin, xmax, ymax])
            resultobj[1][det["class_index"]].append([xmin, ymin, xmax, ymax, conf, char_count])

        xmlstr = convert_to_xml_string3(img_w, img_h, imgname, classeslist, resultobj)
        xmlstr = "<OCRDATASET>" + xmlstr + "</OCRDATASET>"
        root = ET.fromstring(xmlstr)
        eval_xml(root, logger=None)

        lineimgs = []
        boxes = []
        junk_count = 0
        raw_boxes = []
        for lineobj in root.findall(".//LINE"):
            xmin = int(lineobj.get("X"))
            ymin = int(lineobj.get("Y"))
            line_w = int(lineobj.get("WIDTH"))
            line_h = int(lineobj.get("HEIGHT"))
            raw_boxes.append({"x": xmin, "y": ymin, "w": line_w, "h": line_h})
        # 縦行中位高（朱印/花押判据的分母），只统计縦書き行
        vh = sorted(b["h"] for b in raw_boxes if b["h"] >= b["w"])
        median_vh = vh[len(vh) // 2] if vh else None
        for b in raw_boxes:
            if self._is_junk_line(img, b["x"], b["y"], b["w"], b["h"], median_vh):
                junk_count += 1
                continue
            boxes.append(b)
            lineimgs.append(img[b["y"]:b["y"] + b["h"], b["x"]:b["x"] + b["w"], :])

        # 官方 GUI 的 cascade 最终都用同一个 PARSeq 模型；这里直接单模型多线程识别
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr") as ex:
            resultlines = list(ex.map(self.recognizer.read, lineimgs))

        # 剔除明显的检测废框（与官方一致的过滤模式）。
        # 注意：不做行序反转——eval_xml 的阅读顺序输出已经是右→左（实测
        # 竹取物語整页 17 行顺序正确）；官方 GUI 的反转只作用于“多页”列表，
        # 不作用于行列表，这里保持与其 full-image 路径一致。
        patterns = ["□□□", "、、、"]
        # NIGHT6 建议: 纯 ASCII/符号行（信長公記 刊本界框被读成「}」）一并剔除
        # ——行内不含假名或汉字即视为非内容行
        def _has_text(s):
            return any(("\u3040" <= c <= "\u30ff") or ("\u3400" <= c <= "\u9fff") or ("\u4e00" <= c <= "\u4dbf") for c in s)
        keep = [i for i, s in enumerate(resultlines)
                if s and not any(p in s for p in patterns) and _has_text(s)]
        resultlines = [resultlines[i] for i in keep]
        # boxes 必须与 resultlines 同步过滤（Night3 踩过：只筛了行文本没筛盒子，
        # cluster 输出的 index 越界 -> IndexError）
        boxes = [dict(boxes[i], index=j) for j, i in enumerate(keep)]

        if order == "cluster":
            idx = self._cluster_order(boxes)
            resultlines = [resultlines[i] for i in idx]

        return {
            "text": "\n".join(resultlines),
            "lines": resultlines,
            "line_count": len(resultlines),
            "junk_filtered": junk_count,
            "order": order,
            "elapsed_sec": round(time.time() - start, 2),
        }


def get_engine():
    """惰性单例。首次调用会加载两个 ONNX 模型（Celeron 上约 10~30 秒）。"""
    global _ENGINE, _ENGINE_ERROR
    with _LOCK:
        if _ENGINE is not None:
            return _ENGINE
        if _ENGINE_ERROR:
            raise RuntimeError(_ENGINE_ERROR)
        try:
            if not os.path.isdir(OCR_SRC):
                raise RuntimeError(
                    "ocr_runtime/src 不存在: %s —— 请先按 backend/ocr_engine.py 头部注释解压 app.zip" % OCR_SRC)
            _setup_sys_path()
            _ENGINE = OCREngine()
            return _ENGINE
        except Exception as e:
            _ENGINE_ERROR = repr(e)
            raise


def is_available() -> bool:
    return os.path.isdir(OCR_SRC)
