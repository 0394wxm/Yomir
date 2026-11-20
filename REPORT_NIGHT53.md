# REPORT_NIGHT53

## 0. 一句话结论

Night 52「导出 EPUB」的自然闭环：**`POST /api/export/epub`**——客户端持有的文本
（批量 OCR 白文、纠错后未训读的白文）直接导出 EPUB，不要求落库；前端导出区加
第五个按钮「**白文 EPUB**」。新增 5 条测试（导出共 16 条），**全套 157 passed**；
`tsc --noEmit` 零错误、`npm run build` 通过。

## 1. 定位与范围

产品深水区「导出 EPUB / PDF」在 N52 落地了**已落库训读结果**的导出（GET ?ids=），
但产品的核心工作流是「批量 OCR → 行级纠错（N7）→ 训读」——纠错后的白文在用户
点训读**之前**也应该是可带走的资产（「批量导入一本古籍」路线的前半段交付物）。
本夜补 POST 半边，不新开方向：

- 章节模型与 N52 同一个 `build_epub`（`kakikudashi` 为空 = 纯白文章节，不渲染
  空训读段——构建器小改一处）；
- 校验：chapters 非空、≤500、每章白文/書き下し文至少一项非空（否则 400）；
- `title` 缺省回退 `DEFAULT_TITLE`；确定性语义与 N52 一致（POST 文本无落库时间
  → `created_at=None` → `dcterms:modified` 走 1980 下限，同输入同字节）；
- 响应复用新抽的 `_epub_response(data, prefix)`，文件名前缀 `kanbun_hakubun_`
  区分原始导出（前端 `a.download` 自行命名，前缀只影响直连 curl 场景）。

## 2. 改动清单

| 文件 | 内容 |
| --- | --- |
| `backend/epub_export.py` | `_chapter_xhtml`：`kakikudashi` 为空时跳过训读段（1 处条件） |
| `backend/main.py` | `ExportChapter`/`ExportRequest` 模型 + `POST /api/export/epub` + `_epub_response` 助手（GET/POST 共用）|
| `frontend/src/App.tsx` | `saveBlob` 助手 + `downloadEpubRaw()` + 「白文 EPUB」按钮（`disabled={!hakubun.trim()}`）|
| `tests/test_export_epub.py` | +5 条：POST roundtrip（转义+纯白文章节无训读段）/ 空章 400 / 超 500 章 400 / title 回退 / POST 确定性 |
| `REPORT_NIGHT53.md` / `tools/night53_append_shift.py` / `SHIFT_LOG.md` | 报告与夜志 |

## 3. 验证（全部离线）

- `python -m pytest tests/test_export_epub.py -q` = **16 passed**（11 + 5）；
- 全套 `python -m pytest tests -q` = **157 passed**（18.44s）；
- `npx tsc --noEmit` 零错误；`npm run build` 通过；
- GET 路径行为不变（16 条测试同时覆盖 GET 11 条原断言）。

## 4. 已知限制（如实）

1. 真实阅读器人工验证仍缺（N52 REPORT §5.1 同款——结构级已尽，待用户点按钮人眼确认）；
2. POST 章节上限 500 是本夜拍的保守值（防误用/内存），不是产品需求——要改等用户发话；
3. 前端「白文 EPUB」把当前白文编辑框整体作为**单章**导出（多页书稿还不分章）——
   批量结果按页分章需要 job 级结果结构留在前端，属后续夜，不在本夜拍的范围。

## 5. 待拍板（编号 = 下一班的下单清单）

1. N52 §6 三条原样：PDF 引擎 / EPUB 带不带 現代語訳 / N50 ①③ + N49 §16 ③④；
2. 新增 ④：批量 OCR 结果要不要按「页=章」分章导出（本夜是整本单章）？
3. 新增 ⑤：POST 章节 500 上限合适吗？

## 6. 禁止事项自查

未发图 / 未改 eval 基线 / 未重跑全本 OCR / 未碰 N9、16-20 / 未动 order_rate 与
night50_* / 心跳二进制追加前缀断言不变 / 本地提交不推远程 ✓
