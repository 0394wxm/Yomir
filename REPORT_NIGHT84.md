# REPORT_NIGHT84 — empty-got 249 行调查＋修（AutoClaw，night84-empty-got 单会话）

## 0. 结果一句话

N78 §8 交班点名的「空 got 249 行」根因＝**我方管线** `detect_text_type` 把（…）ruby 夹注内假名计入分子、括号本身排除出分母，夹注行假名占比 >0.3 被误判为假名文学文本、kana 分流直接返回空 `kakikudashi`（引擎从未被调用）——N78 的「udkanbun エンジンが空文字列を返す（パーサ系）」定性不成立。修法＝kana 分支 ruby 尾段 fallback（≤8 字白文直出／>8 字分段重跑、无尾段保持空串）：golden_8165 avgDist **14.526→13.505**、目标集 16321→7988（−8333）、改善 248／持平 1／**变差 0**、非目标行逐位一致；golden_4000 与 N83 归档逐位一致 13.495/24/0。accept 84 **PASS fail=0 skip=0**。

## 1. 开工核对与隔离

- master `dce1ba6` 分出 `night84-empty-got`；开工 pytest **415 passed**（20.93s）；已跟踪文件零改动 ✓
- 只动允许清单内文件：backend/main.py、tests/test_night84_empty_got.py、tools/night84_collect.py／night84_eval_4000.py／night84_eval_8165.py、tools/accept_night.py（仅 NIGHT_ARTIFACTS 加 84 一条）、README.md（仅テスト行 415→422）、ROADMAP.md（末尾一行）、SHIFT_LOG.md、ACCEPT_LOG.md（accept 自動追加分）、eval/night84_*（empty_lines／results_4000／results_8165／accept_night_84）、REPORT_NIGHT84.md ✓
- site-packages 一字未动（udkanbun/udkundoku 库本身不改，修法只做我方侧 fallback）✓；禁 OCR、禁 guwenbert、网络使用 0 ✓；golden expected 一字未改（accept eval_integrity 実查）✓

## 2. 复现＋定性（先数，再猜）

- **实测条数：249 行**（`night83_results_8165.json`＝N83 链尾 TestClient 全量真跑归档内 `udkundoku_kakikudashi==""`，与 N78 交班计数完全一致；`tools/night84_collect.py` 実数化，证据归档 `eval/night84_empty_lines.json`）。
- 分层 ①genre：rikutou 65／utsuryo 40／shiba 38／shiki 31／toushisen 23／soji 22／goshi 10／sanryaku 8／roushi 5／nekowoma・sonshi・ichiyorai・itteiji・kenkon・kotoge・ryuryu 各 1——集中度与 N78 交班一致。
- 分层 ②内容：249 行全部**单行**（\n=0）、白文平均 **472.4 字**（语料平均 29.1）、全部含标点（、5222／。3600）。**249/249 含全角（…）ruby 夹注＋夹注内假名**；语料含（）257 行中 249 空串、含假名 252 行中 249 空串——相关性近完备，但（）不是充分条件（rikutou59-2／soji07-6 等 8 行假名占比 ≤0.3 幸存）。
- 分层 ③裸库对照：`ENGINE(line) → entry.kaeriten() → udkundoku.translate(entry, raw=True)` 对空串样本（toushisen006-10／toushisen007-2／stripped 变体）**全部输出非空 `# text`**——空串不出在库、出在我方管线（预处理／分流层）。
- 分层 ④最小复现：`detect_text_type('不知何王殿知（し）らず何王（なにおう）の殿（でん）ぞ遺構絶壁下')`＝`"kana"`（夹注内假名计入分子、（）在标点排除表里＝分母不含）→ endpoint kana 分支 `kakikudashi=""` 直接返回。**触发条件＝kana 分流命中**；249/249 行全部命中（collect 実数化）。新旧字体并查（悪/惡・為/爲・与/與・弥/彌・即/卽）：空串行中 爲 102／爲+為 177 行出现，但它们只是夹注行的普通成分，**不是触发字**——触发的是 ruby 夹注结构本身。

## 3. 根因

backend/main.py `detect_text_type`（NIGHT3 分流，N84 未改其判定）：

```python
chars = [c for c in text if not c.isspace() and c not in "、。，．・「」『』（）！？―ー"]
# （）被排除出分母；但 （こん） 等夹注内的假名全部计入分子 kana
return "kana" if (kana / len(chars)) > threshold else "kanbun"
```

kanbun.info 系页面的白文行是「漢文＋（ruby 読み）」交织形（[汉文段][（読み）][尾段汉文]），夹注内假名密度高 → 假名占比极易 >30% → 被判 "kana" → kana 分支为竹取物語等真·假名文学设计、返回 `kakikudashi=""`＋note。语料结构证据：249 行的 expected 全部对应**尾段无夹注汉文**的書き下し文（逐一核对，见 eval/night84_empty_lines.json 的 ruby_tail 字段）。

## 4. 修法（A：已修）

backend/main.py kana 分支 fallback（新 `_ruby_tail_kanbun`＋分支改造；_RUBY_TAIL_ECHO_MAX=8）：

1. ruby 证据：文本含（…）且至少一个夹注内含假名（rongo1125 系「1）」编号只有闭括号，不触发）；
2. 截取最后一个「）」之后的文本、剥掉前置假名/标点残段（上一段読み的送り仮名）；
3. 剩余为**无假名纯汉文**才触发；尾段 ≤8 字（一句以内）→ **白文直出**（任务书点名 fallback；无返り点、note 如实标注）；>8 字 → **分段重跑**：只对尾段走 `_kundoku_result_for`（merge/style 与常规路径一致，输出真实训読＋返り点）；
4. 引擎对尾段返空（249 行实测未出现）→ 退回白文直出兜底；
5. 无尾段（真·假名文本）→ 保持原行为（kakikudashi=""、原 note）。

绝不编造训读（直出＝原样白文、重跑＝真实引擎输出）；幂等 ✓（行级缓存＋确定性）；text_type 保持 "kana"、note 含 "N84" 标注。

## 5. 试过的方法（含放弃项）

| 方法 | 结果 | 处置 |
| --- | --- | --- |
| 剥夹注后整行入引擎重跑 | 多段重読み、输出远长于 expected、长文行距离大增 | 放弃（无一行变差门） |
| 纯引擎尾段重跑（无长度阈值） | 242 改善／**3 变差**（toushisen006-10 8→10、211-1 9→11、384-2 11→12；短句插助词不稳定；ortho 后仍 2 变差） | 不满足硬门 → 保留为 >8 字分支 |
| 纯白文直出（全行 echo） | 248 改善／0 变差，但长文行改善小（avgDist 只到 13.713）且丢真实训読 | 保留为 ≤8 字分支 |
| **混合：≤8 echo／>8 重跑** | 248 改善／0 变差＋长文行真实训読 | **采用**（阈值 8/10/12 全验证 0 变差，取最小 8 恰覆盖全部 3 个变差证据行） |

## 6. 验证（④）

- 回归测试 `tests/test_night84_empty_got.py` **7 个**：单元（尾段截取／判定阈值不动／ruby 证据）＋TestClient 最小复现（echo 分支、重跑分支、真·假名行为不变、幂等、无夹注不受影响）。pytest 全量 **422 passed**（415+7，13.50s）。
- golden_4000 全量真跑（`tools/night84_eval_4000.py`，86s）：与 night83_results_4000.json **逐位一致 13.495／24／0**、输出差异 0 行、变差 0 行（空串目标行 0——golden_4000 与 249 行零交集，修法对默认口径无影响）。归档 `eval/night84_results_4000.json`。
- golden_8165 全量真跑（`tools/night84_eval_8165.py`，~3 分钟）：**avgDist 14.526→13.505**／exact **30**（不变）／error **0**；目标集 16321→**7988**（−8333）；**改善 248**（echo 30 行 296→161＋重跑 218 行 16012→7814）／**持平 1**（sonshi09-38：）后全假名无尾段，保持空串）／**变差 0**；非目标行输出变化 **0**。归档 `eval/night84_results_8165.json`（扩充归档，不登记默认口径）。
- `tools/verify_readme_facts.py` **18/18 exit 0**（评测数字未变，仅テスト行 415→422 同步）。

## 7. 验收（⑤）

- NIGHT_ARTIFACTS 照例加 `84: ["night84_results_4000.json"]`；`accept_night.py 84` **PASS fail=0 skip=0**（30.0s，主提交后首跑即 PASS；repo_clean／pytest 422／eval_integrity／rule_regression／engine_smoke（kana 分流约定句不受影响）／perf_envelope／order_rate 七门全绿）。
- 本地分支两提交（主 `9fbb5b0`＋wrap-up），**未合 master、未推远程**。

## 8. 移交

1. N78 §8 的「udkanbun エンジンが特定白文で空文字列を返す（パーサ系の調査候補）」定性由本夜修正：引擎无恙，是我方 kana 分流的口径问题。N78 的 249 计数与实测一致。
2. 含（）但假名占比 ≤0.3 的行（rikutou59-2／soji07-6 等 8 行）在 kanbun 分支仍带夹注残渣出力（got 内残留（そう）等）——本夜不动（动则破坏逐位一致）；若要让夹注行全面走「剥夹注」管线，属另一个拍板（需改 detect_text_type 口径＋全量回归）。
3. sonshi09-38 一行无尾段保持空串——若后续语料证实其 expected 有对应尾段，可再议截取规则。
4. ≤8 字尾段的 30 行 kakikudashi 是新字体化汉文骨架而非训読（note 已如实标注）——升级需规则/词库层配合，本夜范围外。

## 9. 禁止事项自查

- golden 数据 expected 一字未改 ✓（accept eval_integrity 実查）；site-packages 一行未动 ✓；udkanbun/udkundoku 库不改、只做我方 fallback ✓
- 允许清单内文件のみ ✓；缓存目录（.night72_deps 等）保持 untracked、精确 add 12 文件 ✓
- SHIFT_LOG 纯追加（python 'ab'、绝对路径、UTF-8 无 BOM、byte807=243 写前后断言）✓；无 OCR／guwenbert／网络 ✓
- 规则引擎层（backend/kundoku_rules.py）一字未改——修法只在 backend/main.py 分流层 ✓；词库 1301 条不动 ✓
