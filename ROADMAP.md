# ROADMAP.md — 漢文→書き下し文 App 总路线图（Night 3 ～ Night 100）

用法：每晚 23:00 新卡生效后，在 ZCode 里打开 D:\kanbun-kakikudashi，贴一句话就行：
「按 ROADMAP.md 做下一个未完成的夜，09:00 前写 REPORT_NIGHTn.md 并本地提交后停下。」
不用每晚等新任务文件。本文件就是任务队列，agent 每晚自己找下一个 TODO（状态不是 DONE 的最靠前的夜），
做完把状态改成 DONE（附提交号）再停。

本机是孤立沙盒：只在本机做，本地 git 提交，不新建远程仓库、不推远程。不要把任何 API key、token 写进代码或报告。

每晚通用规则：每条命令前先 `set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%`；
pip 走清华镜像，npm 走项目级 .npmrc；不要删 qkana shim（tools/make_qkana_shim.py）；
不要改 expected 去凑输出；不要编造"通过"；09:00 前必须写报告收尾。

---

## 已完成

- 状态: DONE — Night 1（2026-11-16/17，提交 946470f）：Web 骨架、UD-Kundoku 三句全对、后端 :8000 / 前端 :5173、评测 10 条 0/10、OCR GUI 验证。卡点：qkana 词典 NINJAL TLS 被重置，用 unidic_lite shim 解决。
- 状态: DONE — Night 2（2026-11-17，提交 4d6513a）：OCR 接通（NDL IIIF 竹取物語 17 行）、專名合并规则（精确匹配仍 0/10，6/10 可读性提升）、SQLite 落库、vite 双栈、縦書き + 返り点ルビ、LLM 适配层只读环境变量。
- 状态: DONE — Night 3（2026-11-17，提交 b1e1c85，REPORT_NIGHT3.md）：正字化 22 对 + 评测扩到 50 条（0/50 精确，28/50 编辑距离改善、0 变差）、OCR 列序聚类（默认 cluster）与非文字区过滤 v3（朱印过滤）、假名白文分流（text_type）、pytest 11 条 + README 重写、官方 qkana / guwenbert 替换脚本。附带成果：guwenbert-base.supar 463.5MB 已下载到位（模型可加载，supar 1.1.4 predict 有 bug 未跑成对比，见 REPORT_NIGHT3.md §5.2）。

---

## 下一夜队列（每夜一个文件大小的活，做完改状态）

### Night 4 — 评测扩到 200 条 + 错误分类
状态: DONE（提交见 git log；REPORT_NIGHT4.md）。200 条就位（golden.json）；归一化口径基线 0/200 avgDist 22.14；分类：助词错 92% / 切分错 90% / 旧字体 12% / 专名 0.5%（多标签）；规则 A（ふ→う + は曰く→曰く，语料验证 0 冲突）+ 规则 B（复合词典 +10）→ full_v2 avgDist 21.02，vs 基线改善 124 / 变差 6；精确匹配仍 0/200；toranoi-1 等 6 条变差已记录。

### Night 5 — 訓読质量第二轮（模型路线）
状态: DONE（REPORT_NIGHT5.md）。guwenbert：模型已下载+可加载，但 PyPI supar 全系（1.1.2/1.1.4）predict 管线与 git-2022 checkpoint 不兼容（feats 空 IndexError，1.1.0 wheel 还有打包 bug），按 1.5h 预算止损——下一夜走「训练同代 git supar」或「手写带 bert transform 加载器」两路线之一；qkana：Range 续传被服务器支持但 body 再次停滞（26MB 粒度），仍需可达网络；规则第二轮：Rule C「て而して→て」（26/26 方向一致）落地，full_v3 26 改善/0 变差，avgDist 21.02→20.48（vs 基线累计 130 改善/6 变差）；精确匹配仍 0/200；再読文字/活用表按证据不做（解析层）。

### Night 6 — OCR 批量 + 样张库
状态: DONE（REPORT_NIGHT6.md）。20 张样张库建成（8 本书：竹取/絵本/論語序説/伊藤文書/墨場必携/信長公記上下/1288060，manifest 全记 URL）；20/20 跑通；耗时拆解：加载 49.8s 一次性、检测 ~20.8s/张恒定、识别 ~2.2s/行 线性（50 行→105s）；新垃圾形态「}」（刊本界框行）与 0 行插图页已记录并给了建议。

### Night 7 — 用户纠错工作流
状态: DONE（REPORT_NIGHT7.md）。行別対照面板（原图预览+逐行编辑+改动高亮）；SQLite 历史记录（ocr_hakubun/prev_request_id 列 + /api/history 翻回）；行级缓存（改一行只重算一行，cache=0 可回退整段路径，等价性已测）；**撤销 Night5 Rule C**（test_kundoku_classic 抓出其破坏「顧みて而して他を言う」规范训读——报告 §4 记录全过程）；pytest 14/14。

### Night 8 — 現代語訳 / 語釈的提示词与词库（无 key 也能做）
状态: DONE（REPORT_NIGHT8.md）。提示词模板两条正式化（MODERN/GLOSSARY）；文语词库 209 条（backend/glossary_lexicon.py，来源=agent 整理、未人工校对，声明两处）；glossary 无 key 时先查词库（source:lexicon）；端到端实测矛盾句命中「鬻ぐ」；10 条评测句命中率 100%（含功能词命中——如实注明选词策略待优化）；pytest 14/14。

### Night 9 — LLM 适配层启用准备（有门禁）
状态: DONE（REPORT_NIGHT9.md）——**门禁未过，跳过**（用户未提供 key / 未选供应商）；报告写明恢复后 3 步操作清单。
- 门禁：只有用户给了产品推理 API 的 key / 选了哪家，才能做这夜；没给就跳过这夜，直接做 Night 10，并在报告里写"门禁未过，跳过"。
- 给了就做：按 KANBUN_LLM_API_KEY 等环境变量接通真实调用，10 条评测句跑一次現代語訳 / 語釈，人工核对质量，记 token 成本（按官方价折算）。
- 产出：REPORT_NIGHT9.md，本地提交。

### Night 10 — 前端打磨第二轮
状态: DONE（REPORT_NIGHT10.md）。导出三件套（复制/txt 下载/打印+@media print 样式）；窄屏 ≤900px 单列响应式；tsc --noEmit 零错误；浏览器人工确认清单 5 项留待用户。

### Night 11 — 性能与稳定性
状态: DONE（REPORT_NIGHT11.md）。20 连调：unique avg 513ms / cached 最低 3ms、内存 140.5→143.1MB 稳定（2412ms 离群值如实记录）；OCR 批量端点 /api/ocr/batch 上线并实测 2 张 126.1s；npm run build 通过 dist 229KB。

### Night 12 — Web MVP v0.1 封版
状态: DONE（REPORT_NIGHT12.md，提交 243b468，本地 tag v0.1）。一键脚本 ×3（start_backend/start_frontend/eval_all）；README v0.1 重写；已知问题 8 条按严重程度排（含精确 0/200、再読文字上限、OCR 盲区、guwenbert 未接入等）。

### Night 13–15 — 桌面壳（Tauri 2）
状态: Night 13 DONE-范围限定（REPORT_NIGHT13.md §3 更新：Rust 1.100.0 via rsproxy、MSVC 14.44、WebView2 157 全装；cargo build --release 完成，**exe 7.4MB**（目标 10-50MB 达标）；「本地能跑起来」限定为 devUrl 模式——需前后端同时开着，Night 14 sidecar 顺延）。Night 14 **DONE**（白天 D6 完成，提交 899894b：sidecar 随壳打包 493.4MB、断网訓読+OCR 实测通过——断网审计 12/12、e2e 6/6，见 REPORT_DAY6.md；无独立 REPORT_NIGHT14.md，去向登记在 REPORT_DAY8.md）。Night 15 **延期（TODO）**：壳已验证（cargo build --release 成功）、只缺 NSIS 封装——① tauri CLI 传参报错 unexpected argument ';'、② 需联网下载 NSIS 插件而本机是孤立沙盒；恢复需能联网的机器 + 用户拍板（REPORT_DAY6.md §7.1/§9、REPORT_DAY8.md §2）。
- Night 13：Tauri 2 脚手架套现有 Web，本地能跑起来，体积记下来（目标 10–50MB，对照 Electron ~150MB）。
- Night 14：桌面版离线：后端随壳启动、OCR 模型随壳打包、断网能跑訓読（現代語訳无 key 时仍占位）。
- Night 15：桌面版安装包打出来，在本机装一次实测，记安装步骤与问题。
- 每夜产出对应 REPORT_NIGHTn.md，本地提交。

### Night 16–18 — 找真用户验证（门禁：用户拍板找谁试，没拍板就跳过）
状态: TODO（门禁）——2026-11-18 D8 盘点：门禁未拍板，跳过，逐夜去向见 REPORT_DAY8.md §3；拍板后按下面三夜顺序做。
- Night 16：写一份给初级研究者的试用说明（5 分钟能看懂怎么用），准备 10 句史料样例。
- Night 17：把 v0.1 的试用反馈表做出来（哪里看不懂、哪里训错了、愿不愿意付费），先自己走一遍流程。
- Night 18：按反馈修最痛的 3 个问题，不要一次修 10 个。
- 每夜产出对应报告，本地提交。这三夜要不要做、找谁试，由用户拍板，没拍板就跳过。

### Night 19–20 — 上线准备（全是门禁）
状态: TODO（门禁）——2026-11-18 D8 盘点：门禁未拍板，跳过，逐夜去向见 REPORT_DAY8.md §4。
- Night 19：域名 + 远程仓库 + 部署方案三选一写进报告，只写方案不执行，等用户拍板。
- Night 20：定价页草稿（按 ¥980/月锚点写三档：免费试用 / 月付 / 机构授权），只写文案不接支付。
- 每夜产出对应报告，本地提交。

### Night 21–100 — 后备队列（只列方向，不写细任务）
状态: Night 21 已由 agent 写细并执行（REPORT_NIGHT21.md）：评测 500 条落地、长度分档统计（≤20 字 196 条是规则有效区）、合并护栏实验否决、OCR 符号行过滤；論語/漢詩 分文体因页面结构不同顺延。Night 22 已由 agent 写细并执行（REPORT_NIGHT22.md）：Rule C'（て而して→て+顧み护栏）500 条验证 107 改善/0 变差、avgDist 27.02→26.21、精确匹配 0→1，上线并三重锁定；「汉字前置删」假设被数据否决；punct 前置 42 处多余而して未动（需句法信息，后续夜）。其余为 TODO（到阶段开头再写细，不要提前写细）。Night 23 已由 agent 写细并执行（REPORT_NIGHT23.md）：論語分文体评测落地——golden_rongo 117 条（20 篇×前 6 章）、avgDist 35.55 vs 故事名言 26.21（同长度档 ≤20 更差 13.74 vs 10.32、20-40 反而更好 20.33 vs 24.71）；Night 21 §5 的 honbun02 记录修正为 yomi03。

为什么不把 100 夜全写细：Night 4 之后评测分数、模型能不能拿到、用户给不给 key，都会改后面的路。现在写细等于写废纸，到那时再按实际结果细化。

- 准确率深水区（Night 21–35）：Kanbun-LM 数据集思路复现、LLM 标注管线、更大评测集（500–1000 条）、分文体评测（史书 / 漢詩 / 駢文分开记分）。
- OCR 深水区（Night 36–50）：KuroNet 对照评测、行序模型调优、自建样张 ground truth、批量导入一本古籍。
- 产品深水区（Night 51–70）：账号与订阅、历史云同步、导出 EPUB / PDF、手机版、机构授权。
- 增长深水区（Night 71–100）：日本歴史学会等渠道试用、大学图书馆合作、定价实测、把 Web MVP 做到能收费的第一版。

每到一个阶段开头，先由用户（或当晚的 agent）把该阶段的第一夜写细，再开工，不要提前写细。

---

## 需要用户拍板的事（路线图里的门禁，汇总）

1. 产品推理 API 用哪家、key 怎么给（Night 9 门禁）。
2. 官方 qkana / guwenbert 模型文件怎么拿到（异地下载后拷入）。
3. 找谁试用 v0.1（Night 16–18 门禁）。
4. 域名 / 远程仓库 / 部署方案（Night 19 门禁）。
5. 定价三档是否按 ¥980/月锚点走（Night 20 门禁）。

没拍板的事，agent 一律跳过并写进报告，不要自己替用户定。
