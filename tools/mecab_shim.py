# -*- coding: utf-8 -*-
"""mecab_shim.py — 共享的 mecab-kanbun tagger（避免各脚本重复拼 Windows 转义路径）。"""
import os
import sys

from MeCab import Tagger

import udkanbun

PKG = os.path.dirname(os.path.abspath(udkanbun.__file__))
_R = os.path.join(PKG, "mecabrc").replace("\\", "\\\\")
_D = os.path.join(PKG, "mecab-kanbun").replace("\\", "\\\\")

tagger = Tagger("-r " + _R + " -d " + _D)
