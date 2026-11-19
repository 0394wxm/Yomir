# REPORT_NIGHT39.md — Night 39（2026-11-20 凌晨段）

按 ROADMAP「OCR 深水区」自定范围：**输出侧两条小修**（同字串垃圾行过滤 + CJK 兼容码位归一），
都是 Night 6 遗留建议与 Night 37 实证的收口。不动检测/行序/recognizer。

---

## 1. 改动

1. **同字串垃圾行过滤** `backend/ocr_postfix.is_junk_repeat_line`：整行同一汉字重复 ≥3 次
   （781193 界框被读成「一一一一」串）→ 剔除。Night 6 的 `_has_text` 挡不住它（一/十 都是汉字），
   这是 Night 6 报告 §3「垃圾过滤」系列的第三形态收口。单字行/两字行不拦（合法内容）。
2. **CJK 兼容码位归一** `backend.ocr_postfix.normalize_compat_ideographs`：U+F900–U+FA6B
   （NEC/IBM 选字）逐字 NFKC → 正则等价。实测 OCR 输出含 U+FA42（旣形）、U+FA5B（者形）
   ——Night 37 C 类证据。只动 FA 区，不做全串 NFKC。
3. 接线：`backend/ocr_engine.py` 过滤链加同字串规则 + 行级归一；`ocr_postfix.postprocess_line`
   供评测脚本共用同一实现。boxes 与 resultlines 同步过滤机制沿用（Night3 的坑已防）。

## 2. 实测（92 行 GT，norm 口径）

| 指标 | Night38 后 | Night39 后 | Δ |
| --- | --- | --- | --- |
| CER micro (norm) | 0.3242 | **0.3233** | −0.0009 |
| 論語 R5 | 0.0547 | **0.0508** | FA 者形命中 1 处 |
| 逐行不变差 | — | **变差 0 / 改善 1** | ✓ |
| 垃圾行剔除 | — | 1 行（纯「一」串） | 781193 页 |

**如实说明**：CER 增量很小。本修法的价值在下游正确性——FA 兼容码位若不归一，
kundoku/检索/导出里的「者」会以不可检索的兼容码位存在；同字串过滤对 781193 这类
碎框页只清掉 1 行**纯**「一」串，该页其余垃圾是混合字符形态，仍需列还原才能根治（见 §4）。

## 3. 门禁

- pytest：**87 passed**（83 + 本夜 4 个新测试）。
- accept_night 22：提交后重跑 PASS。

## 4. 下一步建议（留给下一夜）

- **E_结构（23.5%）根治项**：碎框列还原进管线（night36_xcols 的 x 聚类思路前移到识别前
  合并裁剪，或识别后列级拼接），781193 页 CER 0.938 → 预计显著下降；动检测/行序，
  需独立一夜 + 19 张样张全回归。
- **A_标点（12.4%）**：OCR 输出剥离圈点句读的**可选参数**（默认关——是否默认开属产品拍板）。
- **GT 第二轮**：墨場必携序正文（行書）与竹取草仮名需人工专家读；1288060/伊藤文書同理。

## 5. 禁止事项自查

只新增 tests/test_ocr_night39.py、tools/night39_apply.py、eval/night36_ocr_lines_n39.json、
eval/night39_cer.json、本报告；backend/ocr_engine.py 仅过滤链 2 处 + import 3 行；
backend/ocr_postfix.py 新增 2 函数；未改 expected；未推远程；未碰 Night 9、Night 16–20。
