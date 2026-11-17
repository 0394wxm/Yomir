# REPORT_NIGHT11.md — Night 11（2026-11-18 值班段）

按 ROADMAP.md Night 11 执行：性能与稳定性。

---

## 1. 连续 20 次 /api/kundoku（tools/night11_perf.py，真实耗时 ms）

```
unique#01 2091 ms   ← 引擎首请求预热（Night3 起已知）
unique#02 347 ms … unique#10 6 ms
cached#01 494 ms … cached#10 8 ms
unique: avg 513 ms (min 5 max 2091)
cached: avg 526 ms (min 3 max 2412)
```

- **内存**：后端进程 WorkingSet 首测 140.5MB → 20 连调后 143.1MB（+2.6MB，稳定无泄漏迹象）。
- 行级缓存命中时单次最低 **3~9ms**（整段路径的等价性由 pytest 保证）；
  未命中路径 350~900ms/句（Celeron + udkundoku）。
- 如实记录：cached 组里出现 2412ms 的离群值（长句二次命中却慢）——已复算仍存在，
  原因未定位（怀疑 uvicorn 线程池调度/DB 落库抖动），列为下一夜观察项。

## 2. OCR 批量端点（POST /api/ocr/batch，串行不并行）

实测 2 张（竹取 R2 16 行 + 伊藤文書 R3 23 行）：
```
batch_code:200 total 126.1s
  ndl_1287221_R0000002.jpg  ok 16 行 42.81s
  ndl_9973821_R0000003.jpg  ok 23 行 54.53s
```
- 按顺序出结果、不并行压 CPU ✓；单张分相耗时（加载 49.8s / 检测 ~20.8s / 识别 ~2.2s每行）
  见 REPORT_NIGHT6.md §3。
- curl 注意：`-F` 的本地路径必须正斜杠且真实存在（error 26 踩坑记录）。

## 3. 前端构建

- `npm run build`：**通过（8.44s）**，产物 **229KB**（vite 7 + React 19，未压缩资源全量）。
- `npx tsc --noEmit` 零错误（Night10 验证过，本夜 build 再次通过）。

## 4. 下一步建议

1. cached 2412ms 离群值定位（加计时日志分辨 kaeriten/translate/DB 各段）；
2. OCR 批量端点加轮询/进度（前端等待 2 分钟以上的体验问题）；
3. dist 229KB 已够小，无需再分包。

## 5. 禁止事项自查

真实计时原样记录（含离群值）；无 key/token；只本地提交。
