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

    def recognize_bytes(self, data: bytes) -> dict:
        """图片字节 → OCR 文本。流程与官方 GUI main.py 的 ocr_button_result 一致。"""
        np = self._np
        from ndl_parser import convert_to_xml_string3
        from reading_order.xy_cut.eval import eval_xml
        from PIL import Image

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
        pred_char_cnts = []
        tatelinecnt = 0
        alllinecnt = 0
        for lineobj in root.findall(".//LINE"):
            xmin = int(lineobj.get("X"))
            ymin = int(lineobj.get("Y"))
            line_w = int(lineobj.get("WIDTH"))
            line_h = int(lineobj.get("HEIGHT"))
            try:
                pcc = float(lineobj.get("PRED_CHAR_CNT"))
            except Exception:
                pcc = 100.0
            if line_h > line_w:
                tatelinecnt += 1
            alllinecnt += 1
            lineimgs.append(img[ymin:ymin + line_h, xmin:xmin + line_w, :])
            pred_char_cnts.append(pcc)

        # 官方 GUI 的 cascade 最终都用同一个 PARSeq 模型；这里直接单模型多线程识别
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr") as ex:
            resultlines = list(ex.map(self.recognizer.read, lineimgs))

        # 剔除明显的检测废框（与官方一致的过滤模式）。
        # 注意：不做行序反转——eval_xml 的阅读顺序输出已经是右→左（实测
        # 竹取物語整页 17 行顺序正确）；官方 GUI 的反转只作用于“多页”列表，
        # 不作用于行列表，这里保持与其 full-image 路径一致。
        patterns = ["□□□", "、、、"]
        resultlines = [s for s in resultlines if not any(p in s for p in patterns)]

        return {
            "text": "\n".join(resultlines),
            "lines": resultlines,
            "line_count": len(resultlines),
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
