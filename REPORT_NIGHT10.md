# REPORT_NIGHT10.md — Night 10（2026-11-18 值班段）

按 ROADMAP.md Night 10 执行：前端打磨第二轮（导出 + 响应式 + 打印）。

---

## 1. 导出三件套（frontend/src/App.tsx）

- **一键复制**：`resultAsText()` 把四样输出整理成「【返り点付き原文】/【書き下し文】/
  【現代語訳】/【語釈】＋免责行」的纯文本，`navigator.clipboard` 写入。
- **下载 txt**：Blob + `<a download>`，文件名 `kundoku_<时间戳>.txt`。
- **打印**：`window.print()` + 新增 `@media print` 样式——隐藏输入区/按钮/免责行，
  只打印输出区，縦書き（vertical-rl）在打印中保留。
- 按钮均为 ghost 样式，result 为空时禁用。

## 2. 窄屏响应式（App.css @media max-width:900px）

- `.layout` 两栏 → 单列（输入区上、输出区下）；
- `.entries`（两入口）、`.outputs`（四栏）、`.linecompare`（原图+行编辑）全部单列化；
- 原图预览限高 260px。不做 App，纯 CSS。

## 3. 排版打磨

- 导出行置于「输出」标题下（三按钮）；
- 打印样式中 `.vertical` 放开高度限制（120mm 上限）避免打印截断。

## 4. 验证

- vite dev 编译：`GET /src/App.tsx` 200；
- **类型检查**：`npx tsc --noEmit` 零错误（Night7-10 的 TSX 改动全部通过）；
- 浏览器人工确认清单（agent 无浏览器自动化，留给用户打勾）：
  - [ ] 窄窗口（<900px）下四栏改上下排列
  - [ ] 「一键复制」后粘贴内容含四样输出
  - [ ] 「下载 txt」落盘可读
  - [ ] 打印预览只见输出区且縦書き未截断
  - [ ] 行別対照的改动行高亮（Night7）

## 5. 禁止事项自查

无 key/token；只本地提交；无编造（人工确认项如实留给用户）。
