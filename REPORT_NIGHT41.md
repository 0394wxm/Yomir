# REPORT_NIGHT41.md — Night 41（2026-11-20 凌晨段）

按 ROADMAP「OCR 深水区」主题「批量导入一本古籍」执行：**論語序説等（NDL 11892692）
R3–R5 三页端到端导入**（批量 OCR 产品流 → 白文 → 训读 → 汇总文档），
并顺手修了一个集成缺口 + main.py 的 seg 健壮性。

---

## 1. 新增

- `tools/import_book.py`：整本导入脚本（batch20 样张 → engine.recognize_bytes 产品流 →
  `_kundoku_result_for(merge+ortho, 行级缓存)` → eval/import_rongo/book.md 逐页汇编）。
  插图页（0 行）优雅跳过。实测：OCR 121s（3 页）+ 训读 2.8s（41 行，行级缓存命中后
  单页 0.2-0.3s）。
- 产出 `eval/import_rongo/book.md`：3 页 白文 + 書き下し文 汇编。

## 2. 顺手修的两个问题

1. **词典修没进引擎（集成缺口）**：Night 38 的 B 类护栏词典只接在 main.py 的 3 个 API 端点，
   直接调 `engine.recognize_bytes` 的调用方（批量导入/离线脚本）拿不到修正——book.md 第一版
   仍是「見嬉戯/陳組豆」。修复：引擎行级后处理统一收口 `postprocess_line`（兼容码位 +
   词典），端点层的二次调用幂等无害。
2. **`_kundoku_line_timed`/`seg` 假调用方崩溃**：`seg["engine"] += ...` 假定调用方预置键，
   离线调用 KeyError。改 `seg.get(k, 0) + …`（对 API 既有调用行为不变）。

## 3. 实测（92 行 GT，产品流=引擎+全套后处理，norm 口径）

| 指标 | N40 末（词典未进引擎） | N41（统一后处理） | Δ |
| --- | --- | --- | --- |
| CER micro (norm) | 0.3216 | **0.3053** | −0.0163 |
| CER macro (norm) | 0.2528 | **0.2242** | −0.0286 |
| 論語 R5 | 0.0859 | **0.0508** | 词典命中 |
| 信長上 表紙 | 0.0556 | **0.0000** | 同上 |
| 逐行不变差 | — | **变差 0 / 改善 15** | ✓（vs N40 末） |

产品流累计（N40 基线 0.3842 → 0.3053，**−21%**）；对 Night36 bench 流起点 0.3919 累计 −22%。

**训读质量（如实）**：書き下し文可用但粗糙——OCR 白文的句读缺失/专名误字让 kundoku
出现「史が世の家を記す」类错切与「暗に求む」（暗=聯 的 OCR 误字被照读）——这是已知
avgDist≈21 的质量域，导入管线本身不提升训读质量；Night 38 词典已在白文层吃掉专名子集。

## 4. 门禁

- pytest：**89 passed**（无新增测试；main.py seg 改动由既有 89 个测试覆盖）。
- accept_night 22：提交后重跑 PASS。

## 5. 下一步建议

- 导入脚本目前吃 batch20 样张；接 IIIF 整页清单（自动下全本）即可成「任意 PID 整本导入」，
  配合前端批量端点可做产品功能（留下一夜，需用户拍板交互形态）。
- 训读质量的主要瓶颈已回到白文句读/专名——B 类词典继续扩词条需更多 GT 页（拍板：GT 第二轮）。

## 6. 禁止事项自查

只新增 tools/import_book.py、eval/import_rongo/book.md、eval/night40_engine_post41.json、
eval/night41_cer.json、本报告；backend/ocr_engine.py 后处理收口 2 行；backend/main.py seg
健壮性 5 处 get() 化；未改 expected；未推远程；未碰 Night 9、Night 16–20。
