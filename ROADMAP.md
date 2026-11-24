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
状态: Night 21 已由 agent 写细并执行（REPORT_NIGHT21.md）：评测 500 条落地、长度分档统计（≤20 字 196 条是规则有效区）、合并护栏实验否决、OCR 符号行过滤；論語/漢詩 分文体因页面结构不同顺延。Night 22 已由 agent 写细并执行（REPORT_NIGHT22.md）：Rule C'（て而して→て+顧み护栏）500 条验证 107 改善/0 变差、avgDist 27.02→26.21、精确匹配 0→1，上线并三重锁定；「汉字前置删」假设被数据否决；punct 前置 42 处多余而して未动（需句法信息，后续夜）。其余为 TODO（到阶段开头再写细，不要提前写细）。Night 23 已由 agent 写细并执行（REPORT_NIGHT23.md）：論語分文体评测落地——golden_rongo 117 条（20 篇×前 6 章）、avgDist 35.55 vs 故事名言 26.21（同长度档 ≤20 更差 13.74 vs 10.32、20-40 反而更好 20.33 vs 24.71）；Night 21 §5 的 honbun02 记录修正为 yomi03。Night 29 已由 agent 写细并执行（REPORT_NIGHT29.md）：语料基线 1705 条 24.77、精确 4/1705（新增 shimen-8 有美人、yamai-3 求醫于秦）；して系全量计数 にして got 1/exp 319、而して got 319/exp 23（总体 1:1 镜像钉死）、て而して got 0（Rule C' 全量回归实证）。Night 24 已由 agent 写细并执行（REPORT_NIGHT24.md，负结果）：行首/、前置而して的 keep(8):unwanted(40) 表面同形不可分，R4c/R5a 否决（want 信号运行时不可得），仅、前置 2 处干净（-6 dist 噪声级）不上线；行首段剩余上限 ~-0.09 挂起待句法信号。Night 25 已由 agent 写细并执行（REPORT_NIGHT25.md）：发现 して系链条错位（exp にして 111 处 vs 引擎 0 产出；got 而して→exp して/にして/删除三路同形不可分）——剩余 ~-0.37 上限确认锁在句法层，表面规则收益见底；分文体类别结构相同（助词+切分主导），論語差异机制定位到 相＋动词/可からず/にして 等解析层约定。Night 26 已由 agent 写细并执行（REPORT_NIGHT26.md）：评测集扩到 1000 条（golden_1000.json，原 golden.json 字节级不动），新基线 avgDist 25.62、精确 2/1000（君子不器 新命中），与 500 条归档交集 499 条逐位一致。Night 27 已由 agent 写细并执行（REPORT_NIGHT27.md，负结果收束）：guwenbert 离线标注检验句法信号——cc/advmod 与 して系三路结果不对应，且跨语料取舍相反（night22 vs night26 的 kanji 前置分布相反），判定 kanbun.info 取舍是逐页编辑习惯；して系规则路线正式关闭（剩余 -0.37 需逐页风格适配/生成模型，产品级决策）；孟子部不存在（経部只有論語）；沉淀了 guwenbert 离线批量标注管线（night27_parse_signal.py）。Night 28/30 已由 agent 写细并执行（REPORT_NIGHT28.md / REPORT_NIGHT30.md）：Kanbun-LM 数据集思路复现落地为全站平行语料库 1705 对（kanbun_parallel.json，QC 干净，273 对跨页重复如实）；字符级热图暴露 SHINJITAI_MAP 40 个标准新字体缺口（學→学 105/樂→楽 41/德→徳 36…），模拟 -0.39（433 改善/0 变差）+ 幂等 40/40 + 官方重评 24.77→24.38 逐位一致，表 77→117 条上线；count≥1 低频对未收（如实）。Night 31 已由 agent 写细并执行（REPORT_NIGHT31.md）：新表下两套官方线重基线 500 条 26.21→25.88（116/0）、論語 117 条 35.55→34.88（43/0），皆 0 变差；night22/23/29 归档保留为历史快照，对比基准改为 night31 系列。Night 32 已由 agent 写细并执行（REPORT_NIGHT32.md）：論語全量 498 章（golden_rongo_full.json）avgDist 28.12、精确 2/498（德不孤必有鄰——Night 30 新映射直接闭环）；**Night 23 的抽样偏差修正：論語难度被高估 ~7 点，文体差距收窄到 2.2**；一次写覆盖事故（结果归档覆盖语料文件）零重抓恢复 + 修复 + 如实入档。Night 34 已由 agent 写细并执行（REPORT_NIGHT34.md，负结果）：切分错挖掘 15 个复合词候选（忠信×9/辞気×5/孟嘗君 等，排除 色仁/爾舜 型非词汇并列）引擎实测 **+0.10（5/25）净负** → 已回退、24.38 逐位恢复；与 Night 21 merge_guard 失败同机制（全局合并的长句树手术连带效应）；启用须先做「短句限定合并」产品拍板。Night 35 已由 agent 写细并执行（REPORT_NIGHT35.md，只测不改）：D3 词库泛化确证——1705 语料命中 99.5%（分档 98.8–100%），top 命中词为泛用词 → 命中率饱和、词库扩充降级；**准确率深水区（21–35）列名方向至此全部处理完**（更大评测集/分文体/して系关闭/Kanbun-LM 思路/LLM 标注管线仍门禁）。

为什么不把 100 夜全写细：Night 4 之后评测分数、模型能不能拿到、用户给不给 key，都会改后面的路。现在写细等于写废纸，到那时再按实际结果细化。

- 准确率深水区（Night 21–35）：Kanbun-LM 数据集思路复现、LLM 标注管线、更大评测集（500–1000 条）、分文体评测（史书 / 漢詩 / 駢文分开记分）。
- OCR 深水区（Night 36–50）：KuroNet 对照评测、行序模型调优、自建样张 ground truth、批量导入一本古籍。**Night 33 已提前写细本阶段开头**（REPORT_NIGHT33.md）：样张库 0/20 有 GT（实证）；GT 试点 1 页（竹取 R0000002）——内容层 OCR 可验、逐字层 agent 不可靠，**GT 来源是拍板项**（权威翻刻 or 人工抽样）；KuroNet hf-mirror 0 hit（NII 配布在 GitHub，本机抖动）——也是拍板项；GT 缺位降级方案（跨引擎一致率/结构指标）已入计划。**Night 43 已完成**（REPORT_NIGHT43.md）：页边噪音过滤（纯框几何，`backend/ocr_layout.py` 页脚带判据 + `KANBUN_OCR_LAYOUT_FILTER` 开关），GT 92 行 CER 逐位不变、零错滤、pytest 97。**Night 44 已完成**（REPORT_NIGHT44.md）：47 页全本 filter=ON/OFF 双线重跑对照——OFF 线 2056 行完整复现 Night42 基线，ON 线 1833 行（净删 223），275 个被滤框**全部**经几何校验为列末插入物（同列下方保留行 = 0/275），GT 产品流 CER 0.3053 逐位不变、被滤框触碰 GT 行 = 0；p014/p015/p044 的 69 个被滤框逐框人工读过，错滤 0；pytest 97→104。**Night 45 已完成**（REPORT_NIGHT45.md）：行序模型调优——原「头注归列」假设被独立列连续性指标**证伪**（原顺序 659 列零打断，原型反造 48 处打断/31 页变差，代码已删），改以 I5 主栏列对指标定位到真缺陷（544 对中 2 对颠倒：并列主栏被跨列头注桥接后 y 差 2px 判反）；最小修复 `reorder_main_slots`（列单元内只重排主栏框槽位）只改 p021 一页、端到端 OCR 逐行验证方向正确（「天下之無道也久矣、天将以夫子爲木鐸」），GT 92 行 CER raw 0.3568/norm 0.3053 逐位不变，`KANBUN_OCR_MAINCOL=0` 可回退；pytest 104→116。**Night 46 已完成**（REPORT_NIGHT46.md）：上部手写批注长条过滤——**推翻 Night43 的挂起理由**（「头注带落入版心内部」用的是被污染量 `miban.y=min(主栏y)`，而 p012/p017 的手写长条自己被误判为主栏，属循环论证）；改用稳健量 `body_top=median(主栏y)`（47 页实测 209-256）后，`judge_headnote_strip`（縦框 ∧ `y+100<=body_top` ∧ `h>=0.5*hmax`）纯几何分离出 **62 框/18 页**手写公文批注（夹「候」「御」「様」），零误伤、与页脚带**零重叠**、参数在平台区（offset 60-150 × h_frac 0.4-0.6 命中数不变）；两个中间方案（y 聚类护栏、宽度间隙法）**均被证伪**（前者误杀 p009 的正文列「子曰。弟子入則孝。出則弟謹」y=417，后者在 p012 把阈值降到 29.5 反而多收 2 条）；真实 OCR 6 页端到端**内容守恒 6/6**、保留行顺序反转 ≤0.1%、账目闭合（99 删行 = 39 上部 + 74 页脚 − 14 已被 junk 前置剔除）；GT 92 行 CER raw 0.3568/norm 0.3053 **逐位不变**、GT 8 页新增滤框 **0**；复用 `KANBUN_OCR_LAYOUT_FILTER` 开关，`layout_filtered.reason` 新增 `headnote_strip`；pytest 116→124。顺带查清：`miban.y` 污染对产品流**零影响**（引擎丢弃 miban、页脚判据用 y_max）、横排行单元在 47 页里**零命中**（死代码）、81 个「割注候选」里 55 个是上部手写长条的伪阳性。**Night 47 已完成**（REPORT_NIGHT47.md，只测不改）：版面过滤后的**残留噪音盘点**——当前判据（页脚 223 + 上部 62）后保留 1770 框，假名比率 <0.01 的占 **89.9%**（该版白文基本纯汉字），>0.15 的 **48 框/30 页（2.7%）**是几何漏掉的真噪音；两条修补路线**均失败**：① 纯几何（`h_rel<0.3` 短框）误删 **1064 正文短行 : 命中 45 噪音 ≈ 24:1**，因为手写書き入れ与「列末 2-3 字正文短行」框几何完全重合；② 文本判据（假名比率 >0.15）在 GT 8 页零误伤，但全本有 **p026「如丘者焉不レ如レ如クリ丘之好レ学也」**（真正文含返り点/送り仮名，r=0.29）会被误删，且 48 框里 23 框含返り点记号 → GT 零误伤是采样侥幸，**不上线**；顺带发现 `eval/night44_full/filter_on` 是 Night44 产物（不含 N46 判据）的 stale 基线问题，已评估对 N45/N46 结论无影响（只删不排、且相关工具已用 filter_off 重算）；生产代码**零改动**，pytest 124 不变。**Night 48 已完成**（REPORT_NIGHT48.md，只测不改）：**窄框（割注）判据的否证**——起因是 Night44 §7 记的 p044 两个漏滤框，实测**中心在主栏底之上 70/40px**（`dy=-70/-40.5`），根本不在页脚带；全本 47 页 `dy>0` 的保留框 = **0**，即**页脚判据无漏滤**，Night44 的「页脚边界」定性需订正为「版心内窄条」。全本窄框（`w<0.6×主栏宽`）**1118 框/40 页**，其中 **1047（94%）能配成对**（并排 + y 重合 + 两框宽+间隙≈主栏宽）→ **这是双行割注本**，「窄」是**注文的版式特征而非噪音特征**。三条几何路线全部否决：R1「窄=噪音」阈值 0.35 误删 **584 框（291 带句读）**；R2「未配对窄框=噪音」71 框里 **29 个是 C4 割注**、C5 还混有 `'者、猶報道、'` 正文；R3「未配对+贴页边」只命中 16/71、**误伤 5 个全高割注（31%）**。与 Night47 互为印证（那夜是假名比率切面、本夜是宽度+配对切面），合起来证明**版心内残留噪音无纯离线判据可分离**；生产代码零改动，新增 6 工具 + 5 证据 JSON + 6 测试，pytest 124→**130**。
- 产品深水区（Night 51–70）：账号与订阅、历史云同步、导出 EPUB / PDF、手机版、机构授权。
- 增长深水区（Night 71–100）：日本歴史学会等渠道试用、大学图书馆合作、定价实测、把 Web MVP 做到能收费的第一版。

每到一个阶段开头，先由用户（或当晚的 agent）把该阶段的第一夜写细，再开工，不要提前写细。

### Night 61 — README 刷新（日语全文，公开仓库准备）
状态: DONE（REPORT_NIGHT61.md，2026-11-21 16:09 班执行：README.md 全文日语重写为公开仓库版；数字逐条按 master 代码/归档取证，tools/verify_readme_facts.py 扩展到 GT 行数与割注右先率基线；分支状态（night62-eval10000 / night64-rulei 未合 master）如实写入 README；pytest 193、accept 61 PASS。原任务说明 2026-11-22 用户指令：**用日语写**。小件活，可与当晚主任务并做或作为当晚主任务）。
仓库已开公开库 `github.com/0394wxm/Yomir`（remote 未加、尚未推送；推送本身由用户执行）。
README.md 还停在 v0.1（Night 3 时代）：写的 pytest 14 条 / 评测 200 条，实际 **pytest 193 / golden_4000（4000 条）**。
要求（当晚 agent 按此核对，不要从记忆里抄，逐条对当前代码/归档取数）：
1. **全文用日语重写**（用户指定；技术术语如 漢文/書き下し文/返り点/訓読 照用；标题考虑体现仓库名 Yomir 与项目名 kanbun-kakikudashi 的关系）；
2. 数字与功能刷到当前：pytest 193（tests 全量口径）；评测 `eval/golden_4000.json` 4000 条、规则引擎 avgDist 13.889 / 精确 19/3998（night60 归档口径）；规则链 Rule A / C' / D（これ→之）/ E / F / G / H（假名→汉字四批 5+4+4+3 条）+ SHINJITAI_MAP 147 对（程序化核对 2026-11-22，勿凭记忆抄数字）；OCR：GT 92 行 CER raw 0.3568 / norm 0.3053（eval/ocr_gt_100.tsv）、版面过滤（ocr_layout：页脚带/头注带/割注右先 98.6%）、批量 OCR / IIIF 任意 PID 整本导入（tools/import_pid.py）；导出：EPUB（GET/POST /api/export/epub、縦書き、白文 EPUB 按钮）；現代語訳/語釈仍是无 key 占位（KANBUN_LLM_API_KEY 只读环境变量）；
3. **已知问题清单逐条复核重写**——v0.1 清单里已过时的：2.4s 离群已定位（D4=db save_kundoku 三次 fsync）、OCR 无 GT 已解决（N36 起 92 行）、guwenbert 兼容已解决（D1 加载器，离线对比 五五开~略优，未接后端=REPORT_DAY9 定性维持）、词库 209→500 条；逐条核当前实况后再写，不要照抄旧清单；
4. 环境变量表补全：KANBUN_OCR_LAYOUT_FILTER / KANBUN_OCR_WARICHU / KANBUN_OCR_MAINCOL / KANBUN_SERVE_WEB / KANBUN_SIDECAR / KANBUN_LAZY_ENGINE / KANBUN_TIMING / KANBUN_DB 等（从 backend/ 代码里 grep 实际读的变量，不要凭记忆）；
5. **公开仓库注意**：不写 `C:\Users\Wang` 等本机路径、不写任何 key/token、qkana shim 段保留（复现需要）但按公开读者视角表述；
6. pytest 全量 + `python tools/accept_night.py 61` 照常；报告 REPORT_NIGHT61.md；本地提交不推远程。

---

## 需要用户拍板的事（路线图里的门禁，汇总）

1. 产品推理 API 用哪家、key 怎么给（Night 9 门禁）。
2. 官方 qkana / guwenbert 模型文件怎么拿到（异地下载后拷入）。
3. 找谁试用 v0.1（Night 16–18 门禁）。
4. 域名 / 远程仓库 / 部署方案（Night 19 门禁）。
5. 定价三档是否按 ¥980/月锚点走（Night 20 门禁）。

没拍板的事，agent 一律跳过并写进报告，不要自己替用户定。

- 状态: CLOSED — ⑩「應→応 白文预处理」否决结案（Night 67，零代码改动）：Night 59 实证 no-op（18 行含應白文逐字节不变、error 照旧——lemma 归一到應，AUX 查键照样缺）；真正缺的是 udkundoku AUX 活用表条目，已由 ⑬ backend runtime 补丁修复（golden_4000 error 2→0）。
- 状态: CLOSED — Rule J（かな→漢字第 6 批・7 語：ごとし族按白文 若／如 分目标＋まさに→方に）与 SHINJITAI 29 組（246→275）上线（Night 68）：golden_4000 avgDist 13.716→13.684、golden_8165 14.741→14.698，改写 283 行／改善 234／变差 0；拒案 7 条（べき・べから・もし・なんぞ＋预拒复核 なかれ・ことなく・がため）0 变差门不过，如实归档。
- 状态: CLOSED — Night 68b（README 漂移修补＋验收门补登记）：正字化行 246→275 組（N68 漏项）；已知问题① 24/3998→24/4000（N68 口径，分档对 night68 归档 3 改 1 未变）；数字节表头/ブランチ統合状況 54d2410→9fca166 两处；NIGHT_ARTIFACTS[68] 补登记，accept 68 重跑 PASS（fail=0 skip=0，eval_integrity skip→实查）；verify_readme_facts.py 加 README 逐项比对段（13/13）。構成节 pytest 214→241 已在 Night 68 主提交在位（审计口径滞后，无漂移）。
- 状态: CLOSED — Night 69（第二语源阴性＋Rule K 挖词・离线成立）：8 候选全不达三条硬标准（第 1 名 Wikisource 國譯漢文大成＋漢文叢書＝去重可抓 ~700-850<1000 且混池重合 29.5%≥10%）→ 不建新集；Rule K 第三遍挖词 12 候选收 8 語（仮名遣い族 ひて→いて・へて→えて・はず→わず・へず→えず＋いやしくも→苟くも＋Xぞ族拆分翻案 なんぞ→盍ぞ/奚ぞ/曷ぞ，guard 白文 盍/奚/曷）模拟全 0 变差、组合幂等 0，离线双口径真跑 golden_4000 avgDist 13.684→13.584（改写 467/改善 290/变差 0）・golden_8165 14.698→14.632（768/402/0）；拒 はざる/とも/がため/つひに 实数归档。backend/kundoku_rules.py 不在 N69 允许清单→8 条 K 上线移交 Night 70。
- 状态: CLOSED — Night 70（Rule K backend 上线）：N69 移交的 8 条 K 规则写入 kundoku_rules.py 接 J 链尾（5 条 guard=() 无条件语义明示＝死规则陷阱显式回避、Xぞ族 3 条共享「なんぞ」白文 guard 盍/奚/曷互斥、拒案 はざる/とも/がため/つひに 注释存档不上线）；tests/test_night70_rule_k.py 19 项（全量 260 passed）；TestClient 双口径真跑与 N69 离线逐位一致——golden_4000 13.684→13.584（改写 467/改善 290/变差 0/exact 24）、golden_8165 14.698→14.632（768/402/0/30）；GT CER 结构性不变；README/verify 同步 14/14；NIGHT_ARTIFACTS[70] 登记、accept 70 终跑 PASS（fail=0 skip=0）。
- 状态: CLOSED — Night 71（整本导入＋guwenbert 全量 h2h・无口径改动夜）：样书库补齐 5 本导入（1287221 竹取物語.上 27/28＋10301438 人間萬事翁馬 19/20＋9973821 伊藤博文関係文書 6/6＋1288060 元和卯月本写本 17/19＋1033232 墨場必携新註 582/582（p450 udkanbun kaeriten IndexError 页级容错、白文保留）verify 全 PASS）；guwenbert 全量 8165 条离线跑 OK 8165/error 0/exact 20/avgDist 30.872/211.8 分钟，h2h 全量对照规则更好 3221／gwb 更好 2635／平 2309、规则 avgDist 14.632 vs gwb 30.872——规则引擎口径不变（golden_4000 13.584/golden_8165 14.632 维持）、README 数字表不动；accept 71 终跑 PASS。
- 状态: CLOSED — Night 72（Rule L かな→漢字第 8 系列＋N69/N70 拒案翻案）：9 条写入 kundoku_rules.py 接 K 链尾（つひに→終に、いずくんぞ→安んぞ／悪んぞ——守り字は旧字体「惡」、guard 新旧両形照合が本夜成文规矩、ただ→但だ、ゆえ→由、はじめ→始め、がため→為——N68/N69 拒案翻案・repl 為は exp 実在形で全字形と漢字を共有、はざるなり／はざるを→わざる…——接続拆分で N69 唯一変差行 24shihin10-4 を回避）；tests/test_night72_rule_l.py 23 项（全量 283 passed）；TestClient 双口径真跑与离线模拟逐位一致——golden_4000 13.584→13.544（改写 114/改善 110/变差 0/exact 24）、golden_8165 14.632→14.583（244/239/0/30）；拒案 とも(1 変差)／べからず(5 変差・exp 自写仮名)／がため落选字形（が為に 2 変差・為に 3 変差）実数归档；GT CER 结构性不变；README/verify 同步 15/15；NIGHT_ARTIFACTS[72] 登记、accept 72 PASS（fail=0 skip=0）。
- 状态: CLOSED — Night 73（Rule M かな→漢字第 9 系列＋禁止族 guard 分割）：8 条写入 kundoku_rules.py 接 L 链尾（なかれ→勿かれ——I 毋かれ 同構 guard 分割・莫 行は exp 莫かれ/莫し 混在＋kokyo09-5 1 変差で不収、そく→即ち——守り字新旧両形 即/卽 照合、はあるいは→或いは、ゆき→之、はそれ→其れ、何のごとし→奈何・何のごとく→奈何ぞ——J の 如/若 に対する guard 奈 分割、もし→若——裸形 repl＝exp 実在形・若し は kyugyu-2 1 変差で拒）；tests/test_night73_rule_m.py 24 项（全量 307 passed）；TestClient 双口径真跑与离线模拟逐位一致——golden_4000 13.544→13.517（改写 65/改善 55/变差 0/exact 24）、golden_8165 14.583→14.546（167/139/0/30）；拒案 9 项実数归档（陳→陣 30 変差＝exp 側自書 39 回、べき→可き 6 変差、莫かれ 1 変差 等）；GT CER 结构性不变；README/verify 同步 17/17（テスト行 pytest 計数断言を新設＝N72 移交⑥対応）；NIGHT_ARTIFACTS[73] 登记、accept 73 PASS（fail=0 skip=0）。
- 状态: DONE — Night 74（2026-11-22，分支 night74-lexicon，report-only）：词库 500 条校对审计（OK 438／存疑 43／错 19／来源不可达 0；weblio 主源，kotobank 403 不可达，白文命中 359／零命中 141）；错 19 条修复清单见 REPORT_NIGHT74.md 与 eval/night74_lexicon_audit.md Top-20，修不修词库留用户拍板；backend 一字未改，pytest 307，accept 74 PASS fail=0 skip=1（skip=eval_integrity，report-only 夜无评测归档）。
- 状态: DONE — Night 75（2026-11-22，分支 night75-lexicon-fix）：修词库 19 条错项（17 条按 N74 审计证据修改 + 舎/玷く 2 条核验后不改，diff 只动两个词库文件共 17 行）；回归 tests/test_night75_lexicon_fix.py 24 passed，死条目異端/収拾す复活，golden_4000 真跑与 night73 归档逐位一致（avgDist 13.517/exact 24/error 0）；accept 75 PASS fail=0 skip=0（pytest 331=331）。详见 REPORT_NIGHT75.md。
- 状态: DONE — Night 76（2026-11-22，分支 night76-suspect43，report-only）：存疑 43 条语料振り仮名对照（N75 舎案方法＋语料出处页 kanbun.info 振り仮名 62 页）：確認OK 22／要修正 16／仍存疑 0／语料无实例 5；要修正含读法类 10 条（牧す→ぼくす、狙→そ、冀う=こいねが、弐びす=ふたたびす、愈れる→まされる、止→や・とど、失→うしな・しっ、孰/奚/一犬吠形 等）＋释义类 6 条（乃ち/且つ/大いに/一朝一夕/崇飾す/利し 附加语无据）；N74 的「未→いまだ」提案被语料 ruby（未=いま）推翻、噫/喪ぼす evidence 互换实証修正；词库覆盖缺口新观察＝而る後/而ち/利す(りす) 无条目；backend 一字未改，pytest 331，accept 76 PASS fail=0 skip=1（skip=eval_integrity，report-only 夜无评测归档）；修不修词库留用户拍板。详见 REPORT_NIGHT76.md 与 eval/night76_suspect43.md。
- 状态: DONE — Night 77（2026-11-22，分支 night77-lexicon-fix16）：修词库 16 条（N76 存疑定案 16 条落地：读法 10＋释义 6，diff numstat 14+2 只动两个词库文件，其余 484 条一字未动，总数仍 500、README 不动）；三关全绿（test_night77_lexicon_fix16 20 passed、全量 pytest 351；词头改动冀う golden_8165 kkd 命中 1/1（shushu-3，find_in_lexicon 第 1 位命中）、弐びす 终止形 0 命中（语料只有活用形弐びせず 2/2，精确子串匹配局限如实记录、ruby 证据为准）；golden_4000 真跑与 night75 归档逐位一致 avgDist 13.517/exact 24/error 0/差异 0 行，eval/night77_results_4000.json）；accept 77 PASS fail=0 skip=0（首次 FAIL＝test_ocr_batch_progress flaky 与本夜无关，复跑全绿）；任务书与底稿 6 处差异处理如实记录 REPORT §5 留拍板（牧す meaning 未动、孰按底稿全换等）。详见 REPORT_NIGHT77.md。
- 状态: CLOSED — Night 78（Rule N かな→漢字第 10 系列＋ことな族活用形分割＋現代語副詞族）：13 条写入 kundoku_rules.py 接 M 链尾（ことな族 5 条——umbrella ことなかれ→こと莫かれ は死行 kokyo09-5（白文「嚴父莫大於配天」＝すことなかれ 行・15→16 変差）で拒＝N58/N68/N73 なかれ→莫かれ と同死因の機構境界実証、prefix keys（する/ざる/なる/う/る）は死行を避けて全 0 変差・ることなかれ 1 本で 61 行 substring 覆盖；現代語副詞族 8 条——はいよいよ/いよいよ→弥〻（守り字新旧両形 弥/彌：白文は旧字体 彌・単形 guard は 0 発火を sim が捕捉）、しばしば→屢〻、ほとんど→殆、はやや→稍く、やや→稍、たま→偶、なんぞ→胡（K 盍/奚/曷 の守り外 7 行））；tests/test_night78_rule_n.py 30 项（全量 337 passed）；TestClient 双口径真跑与离线模拟逐位一致——golden_4000 13.517→13.495（改写 55/改善 45/变差 0/exact 24）、golden_8165 14.546→14.526（97/85/0/30）；拒案 koto_full umbrella（変差 1）＋き/ぶ/く/つことなかれ（無益 Δ−0.000）＋落选字形 屢/弥/偶〻 実数归档；GT CER 结构性不变；README/verify 同步 18/18；NIGHT_ARTIFACTS[78] 登记、accept 78 PASS（fail=0 skip=0）；備選⑥なかれ→莫かれ復活条件調查（eval/night78_mokaku.md）——post-N 目標 16 行 12 改善/1 変差（kokyo09-5 のみ）、莫大 co-occurrence 判別式仮説を実測で否定。
- 状態: DONE - Night 79(2026-11-23,分支 night79-lexicon-expand):词库扩充 500→824(golden_8165 汉字复合词频次挖矿 503 候选→逐条 weblio+语料双证据入库 324/排除 179/剩余 0;N76 §3.5 缺口 而る後/而ち/利す 全收录;本体 GLOSSARY_LEXICON 500 条不动(N75/N77 size 不变式维持),合并查找在 llm 层 find_in_lexicon2;golden_4000 与 night77 归档逐位一致 13.517/24/0;tests 363=363;accept 79 PASS fail=0 skip=0)

-状態: DONE - Night 80(2026-11-23,分支 night80-lexicon-expand2 自 night79-lexicon-expand 分出):词库再扩充 824→1085(golden_8165 汉字复合词频次 3-4 区 500 候选→逐条 weblio+语料双证据入库 261/排除 239/剩余 0;本体 GLOSSARY_LEXICON 500 条不动,extra2 追加 261 条至 585,合并查找 find_in_lexicon2;golden_4000 与 night79 归档逐位一致 13.517/24/0;tests 374=374;accept 80 PASS fail=0 skip=0)

- 状態: DONE - Night 82(2026-11-23,分支 night82-lexicon-expand3 自 night80-lexicon-expand2 6fba6a7 分出):词库再扩充 1085→1301(频次 3-4 区剩余 rank500-965 466 候选→逐条 weblio+语料双证据入库 216/排除 250/剩余 0;N79 待拍板 3+8 条与 N80 Wikipedia-only 4 条一字未动;本体 GLOSSARY_LEXICON 500 条不动,extra2 追加 216 条至 801,合并查找 find_in_lexicon2;golden_4000 与 night80 归档逐位一致 13.517/24/0;tests 385=385;verify 17/17 exit 0;accept 82 PASS fail=0 skip=0)
- 状態: DONE - Night 84(2026-11-23,分支 night84-empty-got 自 master dce1ba6 分出):empty-got 249 行调查＋修(N78 §8 交班点名;根因=detect_text_type 把（）ruby 夹注内假名计入分子、括号本身排除出分母→夹注行假名占比>0.3 误判 kana 分流→kakikudashi 空串返回、引擎未调用;修法=kana 分支 ruby 尾段 fallback(_ruby_tail_kanbun:取最后「）」后剥前置送り仮名残段;尾段≤8 白文直出/>8 分段重跑、无尾段保持空串、绝不编造训读);golden_4000 与 night83 归档逐位一致 13.495/24/0;golden_8165 avgDist 14.526→13.505/exact 30/error 0、目标集 16321→7988(-8333)、改善 248/持平 1/变差 0、非目标行 0 变化;tests 422=422;verify 18/18 exit 0;accept 84 PASS fail=0 skip=0)
- 状態: DONE - Night 86(2026-11-23,分支 night86-ruleo 自 master d4738a5 分出):Rule O 挖规则(B2 方法论第七遍 mine→probe→sim 0 変差门,基线 night85 归档・行分类 engine7916/echo30/rerun218/no_tail1 复现=規則可達 8134 行;収録 3 条=はざる者→わざる者(N72 拍板待ち 2 行+N84 rerun 4 行=6 行 0 変差)・たりせ→為ら(guard 爲/爲 新旧両形,白文 爲 完了形 たり 出力 6 行)・なきか→莫し(guard 莫 3 行);組合 15 行改善 15/変差 0/幂等 bad 0;拒案=べからず族 89 行 79 改善 5 変差・べからざる 1 変差・なかれ→莫かれ post-N 17 行 kokyo09-5 1 変差(排除 guard 拍板不通)・使役族構造差・長尾 scramble patch 3 件(語彙対応でない=過拟合拒,基準初明文化);真跑=sim 逐位一致 计画外 0;golden_4000 13.495→13.491/24/0、golden_8165 13.505→13.502/30/0;tests 434=434;verify 19/19 exit 0(归档源 night78→night86 切换+Rule O 語数,N78 先例);accept 86 PASS fail=0 skip=0)
- 状態: DONE - Night 89(2026-11-24,分支 night89-lexicon-freq2 自 master 35ba6e5 分出):词库频次 2 区扩充(golden_8165 汉字复合词频次 2 区总量 3074(基线=现行 1301+N79/80/82 排除 668 形)→取前 500 全 kkd 直证逐条判定;双证据门 weblio+语料 入库 230/排除 270/剩余 0;本体 500 不动,extra2 追加 230 条至 1031,总数 1301→1531,合并查找 find_in_lexicon2;golden_4000 与 night87 归档逐位一致 13.491/24/0・golden_8165 13.502/30/0(词库不进规则引擎);tests 443=443;verify 19/19 exit 0;accept 89 PASS fail=0 skip=0)
