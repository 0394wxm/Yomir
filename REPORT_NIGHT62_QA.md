# REPORT_NIGHT62_QA.md — Night 62 QA 会话独立审计报告

**角色**：本会话原受同一份 Night 62 任务书（golden_4000 + 6000 新对 → golden_10000），开工探针（b370761 + pytest 193 passed in 9.83s）通过后发现**另一会话在同一分支（night62-eval10000）并行执行同一任务**（12:11 clone、12:18 起 probe→inventory→reservoir→scrape_10k，用户已在该会话拍板「方案A：扩到约束内上限、不设目标截断、按实数命名」）。本会话抓取启动后立即停止、**零文件写入**；经用户拍板本会话转 **QA 独立审计**角色（2026-11-21 12:52，SHIFT_LOG 有心跳记录）。

主会话管线（抓取→建库→评测→guwenbert）全部由对方执行；本报告所有数字均为 **QA 侧独立复算**，与主会话产物的比对逐项给出。

---

## 1. 时间线（机器时钟 2026-11-21，N58 起时钟被回拨已知）

| 时刻 | 事件（QA 侧视角） |
|---|---|
| 12:10:36 | QA 会话开工探针：git log -1 = b370761 ✓、pytest 193 passed（9.83s）✓ |
| 12:11:20 | 主会话 clone 主仓 → D:\kanbun-eval10k、建分支 night62-eval10000（reflog 实证） |
| 12:12-12:20 | QA 侧误判目录为待建、worktree add 留下空分支 eval10k（已删，主仓零残留） |
| 12:18 | 主会话 probe_site.py 落盘（QA 侧 12:20 执行过一次该脚本，输出同名覆盖，内容等价） |
| 12:24 | QA 侧独立枚举：1154 fresh 页（keibu 137 残章、koji 488、syubu 283、shibu01 9、shibu02 208、syubu02 29） |
| 12:31 | 主会话 inventory：1280 fresh 页（含 QA 未发现的 /history/ 栏 27 页——后证 0 对） |
| 12:37-12:38 | 双方独立得出同结论：全抓 ~3100-4100 < 6000；主会话启动 scrape_10k |
| 12:46 | QA 侧发现撞车、停止自己的抓取器（未写任何文件）；用户拍板转 QA |
| 12:55 | QA 心跳入 SHIFT_LOG.md（二进制追加、旧字节前缀校验） |
| 13:09-14:23 | 主会话抓取 1279/1280 页 → **3836 对**（ok 3579 + paren 257） |
| 14:23 | **golden_7908.json** 建库（4000 + 3908） |
| 14:27 | **night62_results_7908.json** 规则全量评测 |
| 15:15 | **night62_guwenbert_new3908.json** + night62_h2h.txt 落盘 |

QA 侧清理：自研的 night62_enumerate.py / night62_scrape_all.py 两个冗余工具已移出仓库（Temp 存档），避免污染主会话提交。

## 2. 审计结论（QA 独立复算）

### P1 抓取完成度 ✓
- inventory fresh 1280 页，done 1279；唯一未抓 = `sitemap/sitemap.html`（索引页，0 对，无影响）
- 3836 对 = ok 3579 + paren 257（paren=白文含（），N57 起约定拒绝、本夜只标记未启用——**257 对的去留是新拍板项**）
- 按栏目：syubu 2213 / shibu02 1310 / syubu02 248 / shibu01 53 / koji 6 / keibu 6

### P2 golden_7908 完整性 全过 ✓
- 前 4000 条与 golden_4000 **逐条相等且顺序一致** ✓（expected 一字不改的硬保证）
- id 全唯一（7908）✓；白文唯一性 = base 内部重复 25 原样保留 + **新增段零重复** ✓
- 新增段 3908 条 expected/hakubun 非空 ✓、source_url 全在 ✓、**paren 白文 0 条** ✓
- stats 交叉核对一致；skipped = dup_hakubun 1974 + dup_id 1（见 §4 机制）

### P3 规则引擎确定性 全过 ✓
- **前 4000 条 vs night60_results_4000 归档 diff=0 缺行=0** ✓（QA 独立复算，非引用主会话数字）
- **前 3000 条 vs night58_results_3000 归档 diff=0** ✓
- 全量 7908：OK 7905 / error 3 | **avgDist 13.241** | 精确 25/7905（与主会话 summary 一致 ✓）
- 分档（复算）：≤20字 6326 行 7.926 / 21-40字 903 行 22.735 / 41-60字 383 行 38.154 / >60字 293 行 66.171（单调 ✓）
- **error 3 条 = 應,v,助動詞,必要 KeyError 三连**：toushisen135-12（N57 已知）+ toushisen043-16（N60 发现）+ **zasshi-2「應知故鄉事」（王維雑詩，本夜新增）**——N59 拍板⑬（AUX 活用表补條目）的「非孤例」论据升至 **3 例实证**

### P4 guwenbert / h2h —— **bug 由 QA 抓到、主会话已修复重跑（闭环）**
- guwenbert 数据文件本身完好：QA 复算 3907 OK / 1 error（同款 zasshi-2 應 KeyError，kundoku 翻译层共享）| **avgDist 12.466** | 精确 3
- **QA 于 15:15 抓到**：`tools/night62_h2h.py` 第 39 行 `gmap = {r["id"]: r for r in rdoc["results"]}` 用错源（应为 `gdoc`），当时 night62_h2h.txt 显示「gwb avgDist 12.577=规则、全平局 3907」为假象（规则数字复制）；经用户转达
- **主会话在提交 7da8fbb（15:22）前已修 + 重跑**：提交版第 39 行 = `gdoc["results"]`，提交版 h2h.txt 数字与 QA 独立复算**逐字节一致**：双方可比 3907 | 规则更好 **1366** | gwb 更好 **1390** | 持平 **1151**；规则 avg 12.577 / 精确 6 vs gwb avg 12.466 / 精确 **3**
- 结论不变量：gwb 仅略优 0.111（0.9%），与 N57/N60「同量级、不接后端」定性一致；**本段规则精确 6 > gwb 3**（首次反超）
- QA 验证过的对决形态：规则赢 三略/尉繚子 长兵书段（sanryaku01-7、utsuryo06-6 等），gwb 赢 六韜/三略 另一批长句（rikutou02-4、sanryaku02-4 等）

### P5 交付状态（最终核验 15:41）
- tests/test_golden_7908.py（3 测试，比 N60 模板多 paren 混入断言）→ **pytest 196 passed**（提交信息 + accept 62 门内实测）
- **accept 62：15:19:12 FAIL（fail=1 skip=2，提交前 repo_clean 被未跟踪文件绊，N60 同款舞步）→ 提交后 15:38:38 重跑 PASS（fail=0 skip=1）** ✓
- 提交序列：7da8fbb（数据+工具+SHIFT_LOG 含 QA 心跳）→ c716e41（REPORT_NIGHT62.md 187 行 + wrap-up）；提交信息明确记录 QA 协调与拍板 ⑯⑰
- QA 注意：`tools/night62_koji_check.py / night62_sample_pages.py / night62_sitemap_inventory.py` 三个探针脚本**未随 wrap-up 提交**（遗漏，建议下一班补或留 untracked 拍板）

## 3. 现场抽查（expected 完整性，重抓 kanbun.info 原页复配）

- **早期抽查**（抓取中段）：38/38 行 MATCH（6 页，覆盖 syubu/toushisen・shibu02/呉子）
- **建库后抽查**：9/9 条 MATCH（覆盖 koji・shibu01 史記・shibu02・syubu 唐詩選・syubu02 詩品）
- 合计 **47/47 与现站逐字节一致**——「expected 一字不改」从页面到 golden 全链路验证 ✓

## 4. 6000 目标缺口的机制级结论（QA 侧独立确认）

主会话盘点即给出 projected_pairs≈3079 < 6000；QA 侧独立枚举+诊断补齐机制解释：

1. **全站唯一文本对存量见底**：3836（抓取）+ 330（N57/N60 缓冲残留，QA 复算 127+203、两池零交集）− 1（跨池重复）= **3908 新对 → golden_7908**，缺口 2092 对
2. **koji/keibu 的 501+136 个「fresh 页」是跨 URL 同文本**：論語章节页↔論語出典故事页互为镜像（QA 实证 4 例：rongo0106→okonaiteyo-1、rongo0108→onoreshika-1、rongo0113→kyoreichi-1、rongo0218→ookukuki-1），白文级去重正确拒绝 1974 行——**这是语料源天花板，不是管线缺陷**（主会话抓取器解析被 47/47 现场抽查验证忠实）
3. **paren 白文 257 对**未启用（N57 约定），启用可再回收 ~257 对——留拍板
4. /history/ 栏 27 页实测 0 对（纯栏目壳）；sitemap/文件名页非内容

## 5. 新增段价值（回应 N60 拍板⑮ 偏科警告）

- 新增 3908 条构成：syubu 2518（**全部 ≤20字**）+ **shibu02 1142（老子+武経七書：21-40字 344 / 41-60字 135 / >60字 124）** + syubu02 225（楚辞/詩品）+ shibu01 22（史記）+ koji 1
- **shibu02 贡献 259 行 >40字 长句**——golden_2000 以来首次实质性长句档增量；>60字 档全库 293 行（此前 168 行）
- ≤20字 占比从上一批的 100% 降至 84.1%；最长白文 186 字（montai 李衛公問対）
- 新增段规则 avgDist 12.577、精确 6（全量 13.241 被短句构成摊薄，同 N60 构成效应注意事项，方向相反——本夜是**稀释改善**）

## 6. QA 移交清单（给主会话/用户）

1. ~~修 night62_h2h.py:39 并重跑 h2h~~ **✅ 已闭环**（用户转达 → 主会话修复重跑 → 提交 7da8fbb，提交版数字与 QA 复算逐字节一致）
2. ~~`?? 0` 0 字节重定向残留~~ **✅ 已由 QA 删除**（15:17，repo_clean 门不再被它绊）
3. ~~SHIFT_LOG.md QA 心跳入库~~ **✅ 已随 7da8fbb 入库**（提交信息注明 "QA-session shift log line included"）
4. **paren 257 对是否启用 = 新拍板项**（启用则 golden 可再 +257，需重跑建库/评测/guwenbert；N57 起约定维持未启用）
5. **應 KeyError 升至 3 例**（zasshi-2 新增）——拍板⑬（AUX 补條目）证据加强
6. accept 62 首跑 15:19:12 FAIL（fail=1 skip=2，提交前 repo_clean 被未跟踪文件绊，N60 同款舞步）——提交 7da8fbb 后待重跑；剩 3 个未跟踪工具脚本（koji_check/sample_pages/sitemap_inventory）需随 wrap-up 入库

## 7. QA 收尾状态

- QA 侧产物：本报告 + SHIFT_LOG 心跳 ×2（12:55 开工条、收尾条）+ Temp 存档（自研枚举/抓取工具、审计脚本、审计输出 n62_audit.txt/json）
- QA 侧全程未触碰：规则/后端代码（零 diff）、主会话数据文件（只读审计）、golden 数据
- 唯一写操作：SHIFT_LOG.md 二进制追加（旧字节前缀校验通过）、删除 0 字节 `?? 0` 垃圾文件
- 提交：本报告 + SHIFT_LOG 收尾心跳按路径提交到 night62-eval10000（不合 master、不推远程）
