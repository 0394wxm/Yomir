# REPORT_NIGHT61.md — Night 61：README 全文日语重写（公开仓库准备）

日期: 2026-11-21 16:09 班（Night 61，小件活单做）
分支: `master`（在 d3da2b3 上直接做。README/工具属 master 文档面，无代码改动）
任务书: ROADMAP.md §Night 61 + 用户指令（**用日语写**；数字逐条对当前 master 的代码/归档取数，
不从记忆里抄；62/64 在分支上没合 master，README 里如实写分支状态，别把分支数字写成 master 的）。

---

## 1. 结论摘要

- **README.md 从 v0.1（Night 3 时代）全文日语重写为公开仓库版**：标题体现仓库名 Yomir 与
  项目名 kanbun-kakikudashi 的关系；新增「数字」表（全部实测）、未统合分支状态节、
  环境变量全量表（6 → 16 个）、API 一览、出典·クレジット、開発ログ；qkana shim 节保留并按
  公开读者视角改写。
- **数字全部程序化取证**，`tools/verify_readme_facts.py` 扩展为 README「数字」节的一一对照
  工具（新增 OCR GT 行数与割注右先率基线两项）；SHINJITAI_MAP 按脚本核实为 **147 对**
  （不是旧记忆里的 121）。
- pytest 全量 **193 passed**；`python tools/accept_night.py 61` **PASS**（提交后终跑，N60 惯例）；
  本地提交，**未推远程**（推送由用户执行）。
- 生产代码零改动。唯一源码树变更 = `tools/verify_readme_facts.py`（只读核对脚本扩展）。

## 2. 数字取证清单（README 每个数字的来源）

| README 里的数字 | 值 | 来源（本班实际核对） |
| --- | --- | --- |
| pytest | 193 passed | 实跑 `pytest tests -q`（eval/night61_pytest_start.txt；accept 门内复跑一致） |
| golden_4000 | 4000 組 / 白文ユニーク 3975 | `eval/golden_4000_stats.json`（verify 脚本打印） |
| 规则引擎 | avgDist **13.889** / exact **19/3998**（total 4000，error 2） | `eval/night60_results_4000.json` summary（total=4000, n=3998, exact=19, avg=13.889） |
| 正字化口径注 | ≤20字 n=3041 avg 7.84 exact 19；21-40字 avg 21.742 exact 0；漢詩 6.99／詩経 5.167／故事 21.096／論語 26.87 | 同上 `by_bucket` / `by_genre` |
| Rule A/C'/D/E/F/G/H | 链序与语义 | `backend/kundoku_rules.py`：`style_modern_kana`/`style_drop_wa_before_iwaku`（A）、`style_dedup_shite_soshite_guarded`（C'）、`style_kore_to_shi`（D）、`style_kana_to_kanji[_f/g/h]`（E/F/G/H），总入口 `style_fix_with_hakubun` |
| E/F/G/H = 5+4+4+3 = 16 語 | 5/4/4/3 | verify 脚本（`len(E/F/G/H_KANA_TO_KANJI)`） |
| SHINJITAI_MAP | **147 組** | verify 脚本（`len(SHINJITAI_MAP)`） |
| MERGE_WORDS | 21 語 | verify 脚本 |
| OCR GT | 92 行 | `eval/ocr_gt_100.tsv`（93 行 = GT 92 + 表头 1；verify 脚本打印） |
| CER raw 0.3568 / norm 0.3053 | 逐位基线 | `REPORT_NIGHT49.md`（「与 Night44/46 基线逐位相同」；accept 门 rule_regression 亦守护） |
| 割注右先率基线 | off 98.57% / on 98.63% / 厳密 296 対 100% | `eval/night50_order_rate.json` → `baseline`（verify 脚本打印） |
| OCR 1 行 1〜3 秒 | CPU | `backend/ocr_engine.py` D7 注释（「一行约 1~3 秒」） |
| 版面过滤构件 | ゴミ行/頁脚帯/上部書き入れ長条/主欄並列枠/割注対右先 | `backend/ocr_engine.py`（junk filter、`judge_layout`、`judge_headnote_strip`、`reorder_main_slots`、`reorder_warichu_slots`）+ `backend/ocr_layout.py` |
| 語釈辞書 | 500 語・未人力校正 | `backend/glossary_lexicon.py`（`GLOSSARY_LEXICON=500`；extra 291 語 D3 209→500 并入；245 行未校正声明） |
| 环境变量 16 个 | 全量 | `grep getenv/environ backend/*.py` 实际读取清单（KANBUN_DB/LLM_API_KEY/LLM_BASE_URL/LLM_MODEL/KANA_RATIO/TIMING/LAZY_ENGINE/SERVE_WEB/SIDECAR/OCR_SITE/OCR_SRC/OCR_ORDER/OCR_JUNK_FILTER/OCR_LAYOUT_FILTER/OCR_MAINCOL/OCR_WARICHU） |
| API 一览 | 9 端点 | `backend/main.py` @app 路由表（/health、/api/kundoku、/api/history、/api/ocr、/api/ocr/batch[+/async+job_id+cancel]、/api/export/epub GET+POST） |
| EPUB | EPUB3・vertical-rl 縦書き・決定論 UUID・2 按钮 | `backend/epub_export.py`（_CSS writing-mode、N53 白文章节）+ `frontend/src/App.tsx`（EPUB 出力 L614 / 白文 EPUB L615） |
| VITE_API_BASE | 既定空 → vite proxy 127.0.0.1:8000 | `frontend/src/App.tsx:14` + `frontend/vite.config.ts:12` |
| OCR 出典 | ndl-lab/ndlkotenocr-lite（CC BY 4.0） | `backend/ocr_engine.py` 头注 |
| 信長公記 51/51 | 実績 | master commit `d3da2b3`（N63 主提交）自述 |
| qkana shim | 280MB 公式辞書・レジューム | `tools/make_qkana_shim.py` 头注 + `tools/fetch_official_qkana.py` 存在 |

**分支数字**（README「未統合の作業ブランチ」节，均不冒充 master）：

| 分支 | 数字 | 来源 |
| --- | --- | --- |
| `night62-eval10000` | golden_7908（4000+3908）、avgDist **13.241**／exact **25**（n=7905、error 3）、guwenbert 追加分 3907 条 **12.466**（规则 12.577；対决 1366/1390/1151）、全站 2696 页 6000/10000 不可达实证 | eval10k clone（HEAD `7f24446`）`eval/night62_results_7908.json` summary、`eval/night62_h2h.txt`、`eval/night62_guwenbert_new3908.json`、`REPORT_NIGHT62.md` |
| `night64-rulei` | Rule I 6 語（白文ガード付き）+ SHINJITAI 99 組（147→246）、avgDist 13.889→**13.719**、exact 19→**24**、pytest 193→**211**、GT CER bit 不变 | rulei clone（HEAD `6c2d69a`）commit message 自述（逐项可数） |

## 3. v0.1 已知问题 8 条 → 新 README 7 条的逐条处置

| v0.1 条目 | 处置 |
| --- | --- |
| 1. 訓読精确匹配 0/200 | 更新为 19/3998 + 分档/文体实数（≤20字 7.84、21字超 0；漢詩 6.99/詩経 5.167 vs 故事 21.096/論語 26.87，night60 master 口径）；删去未经本班复核的旧例词（祠る者/壁す） |
| 2. 再読文字只有「未」 | 维持（master kundoku_rules 无再読处理；N64 的 Rule I 是かな→漢字，不涉再読） |
| 3. OCR 无 GT | 已解决（N36 起 GT 92 行）→ 改写为现状描述：印刷物中心、草書/草仮名/散字页苦手（N36：3 冊超出人工 GT 可读范围） |
| 4. 假名分流 >30% | 维持（`KANBUN_KANA_RATIO` 既定 0.3，main.py:123 实测） |
| 5. 語釈词库 209 条 | 更新为 500 条（未人工校对声明仍在） |
| 6. cached 2.4s 离群「原因未定位」 | 已定位（D4：db save_kundoku fsync、慢盘 14〜47×）→ 改写为「已定位・环境依存・KANBUN_DB 移设可缓和」 |
| 7. guwenbert 不兼容未接入 | 加载已解决（D1 加载器）、未接后端（REPORT_DAY9 定性维持）；N60 离线对比 h2h 291/373/335（略优）如实入册 |
| 8. 瀏覽器確認清單（N10）未打勾 | **公开 README 不载**（内部工作流项，非产品行为）；该项对用户仍挂起 |

另：v0.1 列的「刊本界框被识别为 } 符号行」已在 Night 6 由 `_has_text`/junk 系过滤解决
（ocr_engine.py NIGHT6/N39/N40/N41 注释），新 README 不再列为问题，只作为过滤器构件写进能力表。

## 4. 公开仓库红线自查

- 全文无本机绝对路径（D:\… / C:\Users\Wang 均未出现；OCR 展开命令用
  `<ndlkotenocr-lite を展開した場所>` 占位）。
- 无 key/token（KANBUN_LLM_API_KEY 只作为变量名出现）。
- qkana shim 节保留（复现必需），改写为公开读者视角：触发条件（clrd.ninjal.ac.jp 不可达）、
  生成/重建/官方替换三条命令、「取官方前不要删 shim」警告。
- 简体专用字残留扫描：0（数/速/物为日文同形字误报）。
- 分支数字全部标注「未統合・master 数字には未反映」，未混入口径。

## 5. verify_readme_facts.py 扩展

原版打印 5 项（SHINJITAI/MERGE/E/F/G/H/night60/golden_4000）。本班追加：
`ocr_gt_100.tsv` 行数（GT 92＋表头 1）与 `eval/night50_order_rate.json` 基线
（off 98.57 / on 98.63 / strict 100.0）。只读性质不变；运行输出与 README「数字」表逐行对应。

## 6. 本班发现的事实勘误（未改，留拍板）

1. ROADMAP §Night 61 写「remote 未加、尚未推送」——实际 `origin` 已指向
   `github.com/0394wxm/Yomir.git`，master ahead 2。README 未引用该行；ROADMAP 其他内容未动。
2. `SHIFT_LOG.md` 含非法 UTF-8 字节（0xF3 @807，历史某次追加混入非 UTF-8 编码）。
   本班按 UTF-8 二进制续写追加一行（旧字节原样保留）。
3. `backend/llm.py:12` 注释仍写「209 条词库」（实际 500）——代码注释 stale，非本夜范围未动。

## 7. 验收

- `python -m pytest tests -q` → **193 passed**（9.47s；eval/night61_pytest_start.txt）。
- `python tools/accept_night.py 61` → **PASS**（提交后终跑；repo_clean 按 N60 惯例在干净树上运行）。
- 本地提交两个：主提交（README/verify 脚本/ROADMAP/SHIFT_LOG/本报告）+ wrap-up
  （ACCEPT_LOG.md + eval/accept_night_61.json）。**未推远程**。

## 8. 待拍板（移交用户）

1. **LICENSE 文件不存在**：公开仓库是否加、用什么许可（MIT/CC 选择是用户决策）。
2. **推送时机与 ROADMAP 勘误**：origin 已配置且 ahead 2；ROADMAP「remote 未加」行是否更新、
   何时推送（推送本身由用户执行）。
3. **SHIFT_LOG.md 混编码字节**是否清洗（0xF3 @807）。
4. **README 公开表述 kanbun.info 数据出处**的妥当性（授权/法务角度，用户判断）。

## 9. 禁止事项自查

- 未改 expected、未改评测数据、未动 backend/ 生产代码、未动 golden/GT。
- 未从记忆抄数字：SHINJITAI 147 用脚本核；E/F/G/H、GT 行数、顺序率基线全走归档/代码；
  分支数字取自 clone 的归档与 commit message，未引第二手转述。
- 按路径 add（README.md / tools/verify_readme_facts.py / ROADMAP.md / SHIFT_LOG.md /
  REPORT_NIGHT61.md + wrap-up 的 ACCEPT_LOG.md / eval/accept_night_61.json）；
  临时探针脚本已清理，仅留 eval/night61_pytest_start.txt 作 pytest 证据（未跟踪，按惯例）。
- 未推远程。
