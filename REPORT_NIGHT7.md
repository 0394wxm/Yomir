# REPORT_NIGHT7.md — Night 7（2026-11-18 值班段）

按 ROADMAP.md Night 7 执行：用户纠错工作流（行別対照 + 历史翻回 + 行级缓存）。

---

## 1. 后端

- **历史记录**（backend/db.py）：requests 表迁移加两列（`ocr_hakubun` OCR 原始白文、
  `prev_request_id` 翻回链，ALTER TABLE 幂等迁移）；`save_kundoku()` 接收新字段；
  新增 `get_history(limit)` 按 id 倒序返回 requests⋈results。
- **API**：
  - `POST /api/kundoku` 请求体新增 `ocr_hakubun` / `prev_request_id`（可选）；
    响应新增 `request_id`（落库后的请求 id，前端链式引用）。
  - 新增 `GET /api/history?limit=N`（1~100，默认 20）。
- **行级缓存**（"改一行只重算一行"）：`_kundoku_line_cached` + `_kundoku_result_for`。
  按输入行拆分，缓存键 = (行文本, merge)，OrderedDict LRU 上限 500 条；
  风格修正/正字化在取值后按开关叠加。`cache=0` 可回退整段路径（Night1-3 原始行为）。
  **等价性已测**：多行输入 cache=1 与 cache=0 的 kakikudashi/kaeriten_text 完全一致
  （tests/test_api.py::test_cache_path_equivalent_to_whole_text，真实断言）。

## 2. 前端（frontend/src/App.tsx / App.css）

- **行別対照**：上传 OCR 后出现对照面板——左边原图预览，右边逐行编辑框；
  与 OCR 原行不同的行**高亮**（#fff3d6）；编辑实时写回白文（重新訓読只提交当前文本，
  后端行级缓存保证未改的行秒回）。
- **履歴（翻回上一条）**：白文卡新增按钮，`GET /api/history` 取最近 20 条；
  点一条即恢复该条的白文与訓読输出（results 里有记录时直接回显输出）。
- vite 编译验证：`GET /src/App.tsx` 200。浏览器人工确认留给用户（agent 无浏览器自动化）。

## 3. 测试（pytest 14 条全过，其中新增 3 条）

```
tests/test_api.py::test_cache_path_equivalent_to_whole_text PASSED   ← 新
tests/test_api.py::test_history_roundtrip PASSED                     ← 新
tests/test_api.py::test_history_limit_clamped PASSED                 ← 新
14 passed, 2 warnings
```

## 4. 过程中抓出并撤销的一个坏规则（诚实记录）

新测试 `test_kundoku_classic` 抓出 **Night5 Rule C（て而して→て）破坏经典句**：
「王顧左右而言他」的规范训读是「王は左右を顧みて**而して**他を言ふ」，
Rule C 把它变成「顧みて他を言う」。语料内 26/26 的证据被语料外的名句推翻——
而して 续接在文语里合法常见，语料证据不足以支撑删改。
**已撤销 Rule C**（style_fix 不再调用；函数与注释保留作证据存档），
fu→う（Rule A）保留（expected 语料 0 处ふ，且测试更新为「言う」口径并注明理由）。
连带影响：REPORT_NIGHT5.md 记录的 full_v3 数字是实测值但该规则已撤销，
后续以 full_v2 配置（avgDist 21.02）为准；full_v3 的 26 条改善不再可用。

## 5. 禁止事项自查

无 key/token 入库；测试断言真实（含抓出自己上一夜的坏规则）；只本地提交；
浏览器人工确认项已列明（行別対照渲染、履歴按钮、高亮样式），留给用户打勾。
