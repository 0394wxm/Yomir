# REPORT_NIGHT52

## 0. 一句话结论

按 ROADMAP 推演到「产品深水区（Night 51–70）」唯一无门禁、可离线验证的夜——
**导出 EPUB** 落地：`backend/epub_export.py`（纯标准库、逐字节确定性、縦書き CSS）+
`GET /api/export/epub` + 前端「EPUB 出力」按钮；**新增 11 条测试全过，全套 141→152 passed**；
`npx tsc --noEmit` 零错误、`npm run build` 通过。**PDF 不在本夜**（理由见 §2，需拍板/联网环境）。

## 1. 夜的定位（队列推演）

任务书：做完 Night 51 后按 ROADMAP 做下一个未完成的夜，只做**无门禁、可离线验证**的。

逐项过队列：
- Night 15（NSIS 封装）：要联网下载 NSIS 插件 + 用户拍板 → **跳过**；
- Night 16–20：全是门禁（红线明确不碰）→ **跳过**；
- Night 21–50：全部 DONE（accept gate 51 PASS 后 51 也闭环）；
- Night 51–70 产品深水区：账号与订阅 / 历史云同步 / 机构授权 / 手机版 —— 要么用户拍板
  要么要联网账号体系；**「导出 EPUB / PDF」是唯一纯离线可做可验的**。ROADMAP 规定
  「到阶段开头由当晚 agent 把第一夜写细」——本夜即按此把导出功能写细并执行。

## 2. 范围决定：EPUB 本夜做，PDF 明确不做（写明理由）

- **EPUB**：本质是 zip + XML，纯标准库可做；縦書き用 EPUB3 标准的 CSS
  `writing-mode: vertical-rl`（日文电子书通用做法），无需任何字体嵌入或组版引擎。
- **PDF**：CJK 縦書き PDF 要逐字正确的组版 + 嵌入日文字体，本机离线没有可用的
  排版引擎（reportlab 等对縦書き/ルビ支持残缺）；强行做就是装样子的坏 PDF。
  **如果用户要 PDF，需要拍板选引擎（或允许联网装 weasyprint/pagedjs），留待拍板。**

## 3. 实现

### 3.1 `backend/epub_export.py`（新文件，~180 行）

- **纯标准库**：`zipfile` + `xml.sax.saxutils.escape`，全内存 `BytesIO`，不落临时文件，零新依赖。
- **EPUB 3 最小合法结构**：`mimetype`（第一个条目、`ZIP_STORED`、逐字节
  `application/epub+zip`）→ `META-INF/container.xml` → `OEBPS/content.opf`
  （uuid5 identifier / dc:title / dc:language ja / `dcterms:modified` / nav 标记 /
  manifest+spine）→ `OEBPS/nav.xhtml`（toc）→ `OEBPS/text/chapter-NN.xhtml`
  （原文白文 / 返り点付き / 書き下し文 三段）+ `style.css`。
- **逐字节确定性**：UUID 用 `uuid5(NAMESPACE_URL, "kanbun-epub:" + 内容)` 派生；
  zip 时间戳与 `dcterms:modified` 从条目 `created_at` 派生（最大值；解析不了或缺失
  回退 1980-01-01）。同输入 → 同字节串，产物可 diff、测试可做逐字节断言。
- **转义**：正文全部经 `escape()`（OCR 噪音里的 `< > &` 不会破坏 XHTML——有专测）。
- **无路径穿越面**：zip 条目名全是常量/编号派生，用户输入不进文件名。
- 縦書き CSS + 回退：阅读器不支持 `writing-mode` 时自动横排，内容仍可读。

### 3.2 `backend/db.py`：`get_requests_by_ids(ids)`

与 `get_history` 同一投影（LEFT JOIN results），`WHERE id IN (...) ORDER BY id ASC`。
找不到的 id 不在返回里，调用方据此报 404。

### 3.3 `backend/main.py`：`GET /api/export/epub`

- `ids=1,2,3` → 指定 id 升序导出；有不存在的 id → **404**（列出到处）；
  `ids=abc` → **400**；
- `ids` 缺省 → 最近 `limit`（1–100，默认 20）条，与 `/api/history` 同源，导出按 id 升序；
- 条目缺 `kakikudashi`（无结果请求）跳过；全跳完 → 404；
- 返回 `application/epub+zip` + `Content-Disposition: attachment; filename="kanbun_YYYYMMDD.epub"`
  （纯 ASCII 文件名，避免 Content-Disposition 编码坑）。

### 3.4 前端 `App.tsx`：导出区第四个按钮

「EPUB 出力」放在 复制 / 下载 txt / 打印 之列（NIGHT10 导出三件套 → 四件套）；
`disabled={!result?.request_id}`（结果没落库就不可导），`fetch → blob → a.download`，
失败走现有 `setErrMsg` 通道。下载函数风格与 `downloadTxt` 逐行对齐。

## 4. 验证（全部离线）

### 4.1 新增 `tests/test_export_epub.py` 11 条（先跑 10 过 1 挂 → 修测试命名空间 → 11/11）

| 测试 | 断言要点 |
| --- | --- |
| mimetype_first_entry_stored_exact | 第一条目、ZIP_STORED、内容逐字节 |
| zip_layout_and_all_xml_wellformed | 条目布局；每个 xhtml/xml/opf 都 well-formed |
| opf_metadata_manifest_spine | uuid5 identifier、dcterms:modified=created_at 派生、nav properties、manifest 全条目 |
| nav_and_chapter_content | toc 链接与章一致；内容断言；`學<而> & ` 转义成实体且 raw 不出现 |
| determinism_byte_identical_and_uuid_sensitive | 同输入逐字节相同；改一字 → 字节不同且 UUID 不同 |
| empty_rows_still_builds | 空 rows 也能构建 |
| created_at_missing_falls_back | 坏时间戳回退 1980-01-01T00:00:00Z |
| export_endpoint_roundtrip | save_kundoku → GET ?ids=N → 200 + 头 + zip 结构 + 内容 |
| export_endpoint_default_limit_and_order | 缺省 limit=1 取最新条、章数=1 |
| export_endpoint_missing_id_404_and_bad_ids_400 | 404 / 400 语义 |
| export_endpoint_skips_resultless_requests | 孤儿 request（无 results 行）被跳过 |

修过的一处是**测试自身**的命名空间写法：`<nav>` 是 XHTML 元素，epub 命名空间只在
`epub:type` *属性*上（`find(".//{epub}nav")` 永远 None）——生产代码没改。

### 4.2 全套

- `python -m pytest tests -q` = **152 passed**（14.72s；141 + 11）；
- `npx tsc --noEmit` 零错误；`npm run build` 通过；
- `git status --porcelain --untracked-files=no` = 恰好 3 个预期源文件（backend/db.py、
  backend/main.py、frontend/src/App.tsx）——`frontend/dist` 不被跟踪，build 不弄脏工作区。

## 5. 已知限制（如实）

1. **没有真实阅读器人工验证**：本机孤立沙盒（IAB 不能传文件），EPUB 的验证止于
   结构级——EPUB3 规范要点（mimetype 位置/压缩、container→opf→spine 引用链、
   XHTML well-formed、nav 标记）逐条断言过，但 Apple Books / Kindle 实开效果
   （縦書き渲染、字体）**未经人眼**。用户下次在桌面版/浏览器里点一次「EPUB 出力」
   即可人工确认。
2. **現代語訳/語釈未进 EPUB**：modern 是无 key 占位文本，进书稿只会污染；EPUB
   承载的是 白文→書き下し文 的对读。要进的话等 Night 9 门禁（LLM key）落地后随内容一起进。
3. dcterms:modified 用派生值（确定性优先）——阅读器只要求合法 xsd dateTime，不影响打开。

## 6. 待拍板（编号 = 下一班的下单清单）

1. **PDF 导出引擎**（本夜明确没做）：要吗？要的话允许联网装 weasyprint/pagedjs，
   还是先只留 EPUB？（REPORT §2）
2. EPUB 要不要带 現代語訳/語釈 段（等 Night 9 有 key 后才有意义）？
3. N50 待拍板①③（order_rate 阈值 / night50_* 证据入库）、Night49 §16 ③④ —— 原样保留。

## 7. 禁止事项自查

- 未发图、未改 `eval/ocr_gt_100.tsv` / `golden*` / expected ✓
- 未重跑 47 页全本 OCR ✓；未碰 Night 9、16–20 ✓
- 未自定 order_rate 阈值、未动 night50_* 文件 ✓
- 心跳 2 行（23:19 开工 / 00:45 N52 中点）二进制追加、前缀断言不变 ✓
- 本地提交不推远程 ✓

## 8. 本次改动清单

| 文件 | 性质 |
| --- | --- |
| `backend/epub_export.py` | 新增：EPUB 3 构建器（纯标准库、确定性） |
| `backend/db.py` | 新增 `get_requests_by_ids` |
| `backend/main.py` | 新增 `GET /api/export/epub` |
| `frontend/src/App.tsx` | 「EPUB 出力」按钮 + `downloadEpub()` |
| `tests/test_export_epub.py` | 新增 11 条测试 |
| `REPORT_NIGHT52.md` | 本报告 |
| `tools/night52_append_shift.py` | SHIFT_LOG 二进制追加脚本 |
| `SHIFT_LOG.md` | N52 块 + 心跳 ×3 |
