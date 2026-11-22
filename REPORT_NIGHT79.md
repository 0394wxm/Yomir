# REPORT_NIGHT79.md — Night 79：词库扩充 500 → 824（golden_8165 频次挖矿＋双证据门）

- 日期：2026-11-23 深夜～凌晨（周末卡，09:00 到期）
- 分支：`night79-lexicon-expand`（自 `night77-lexicon-fix16` 分出——词库链，基点 HEAD=fff5266）
- 工作目录：`D:\kanbun-rulel`（与 N71 所在的 `D:\kanbun-kakikudashi` 零接触；本夜禁 OCR/guwenbert，CPU 零占用——全部增量为 weblio/kanbun.info 的网络等待）
- 性质：**词库数据夜**。`backend/glossary_lexicon.py` 与 `glossary_lexicon_extra.py` 一字未改（本体 500 条不动），新增 `glossary_lexicon_extra2.py` 324 条，接入走 llm 层（见 §1.4）。

## 0. 开工核验

- `git checkout -b night79-lexicon-expand night77-lexicon-fix16`；HEAD=fff5266 ✓（N77 wrap-up 提交）
- pytest 全套首跑：**351 passed / 37.27s** ✓；已跟踪文件零改动 ✓（untracked 仅 `.night72_deps/` 与 `eval/night74_dict_cache/`，N72/N74 先例的本地缓存）
- 先读 REPORT_NIGHT74.md §1（词库结构与 find_in_lexicon 用法）、REPORT_NIGHT76.md §3.5（覆盖缺口三条）✓

## 1. 方法

### 1.1 频次挖矿（tools/night79_freq.py → eval/night79_candidates.json）

- golden_8165（8165 行）的白文＋書き下し文里抽汉字连续 run（2–8 字），文書頻度（行内去重）排序；既有 500 条词形完全一致者除外；纯假名功能词天然不会出现在汉字 run 里。
- 实测：distinct run 34999 个，非既有且频次 ≥1 的 34960 个；频次 ≥5 的 513 个——候选清单取频次降序前 500（rank500 边界频次=5）。
- N76 §3.5 覆盖缺口三条（而る後／而ち／利す）是かな混じり形、run 抽取取不到，按任务书置前：**而る後 9 行 13 次／而ち 5 行 9 次／利す 11 行 16 次**（tools/night79_gap_check.py 全行清单 eval/night79_gap_lines.txt；N76 的「19 例／8 例」口径为出现次数，行数口径如上）。

### 1.2 逐条双证据门（全部 503 候选逐条判定，无抽查）

每条必须**同时**满足两条证据才入库（缺一条进排除清单）：

1. **辞書**：`www.weblio.jp/content/<word>` 聚合页（tools/night79_weblio.py，GET 间隔 0.7s，缓存 eval/night79_dict_cache/——未跟踪目录，N74 先例）。読み＋释义有据；404／无条目／仅机器生成区块（ウィキペディア小見出し辞書・例文辞書）如实记录。kotobank 403／goo 超时为站点级不可达（N74 实测），本夜未用。
2. **语料**：golden_8165 实例行（候选文件自带 id＋書き下し文样本）；疑难读法另用 **kanbun.info 出处页振り仮名**（N76 方法，tools/night79_ruby.py，缓存 eval/night79_ruby_cache/）。

判定底稿 eval/night79_decisions_*.json（10 个文件、503 条全量），装配器 tools/night79_build.py 机械校验「include 必须双证据非空」。

### 1.3 ruby 深查定案的读法（语料作者 ruby 优先）

| 词 | 大辞泉等读法 | 语料 ruby（直证页数） | 采纳 |
|---|---|---|---|
| 所以 | ゆえん | ゆえん（×2 页） | ゆえん（一致） |
| 奈何 | いかん | いかん（×3 页） | いかん（一致） |
| 敵人 | てきにん（《てきじん》とも） | てきじん（×2 页） | てきじん・てきにん |
| 不可 | ふか | ふか（×2 页） | ふか（一致——訓読は「かなわ」系という予想に反し、ruby でふか 直证） |
| 左右 | さゆう | さ＋ゆう（×3 页） | さゆう（一致） |
| 父母 | ふぼ／ちちはは | ふぼ（×3 页） | ふぼ・ちちはは |
| 一人 | いちにん | いちにん（×3 页） | いちにん |
| 人間 | じんかん／ひとま | 人=ひと・間=ひそ（yotonotsu） | ひとま・じんかん |
| 三月 | さんがつ | **さんげつ**（×3 页，语の直 ruby） | さんげつ（N75 牧す→ぼくす 先例：语料 ruby 优先，差一拍如实注记） |
| 嗟乎 | （Wiktionary）ああ | ああ（enjaku-3 語の直 ruby） | ああ |

### 1.4 接入方式（与既有 size 不变式的相容）

tests/test_night75/77 有 `assert len(GLOSSARY_LEXICON) == 500`（不可改文件）。dry-run 实证：若 extend/rebind 本体列表，该断言按 import 顺序破或抖动；若 extra2 词条标 `function`，则被 1 字内容词（後・而・何）先占位置、**在自己的语料行上永远命不中（死条目化，而る後 实测复现）**。故定案：

- **本体 500 条不动**；`glossary_lexicon_extra2.py` 自带合并查找器 `find_in_lexicon2()`（算法与 `find_in_lexicon` 逐行同款：内容词先→功能词后、同组内长词优先、已覆盖位置不重复命中；词条源=本体＋extra2）。
- `backend/llm.py` 仅两处改动：`from backend.glossary_lexicon_extra2 import find_in_lexicon2`（import 一行）＋ `glossary()` 两处调用 `find_in_lexicon` → `find_in_lexicon2`（任务书「import＋列表一行」的 test-safe 等价实现——「列表合并」被既有 500 断言物理禁止，如实记录）。
- 接续系 7 条（而る後／而ち／奈何／何如／如何／以為／嗚呼）在 extra2 里归 modifier 组（as_dicts 展开为 kind=content）而非 function——规避死条目化；本体 209 条的 function 分组语义不动。

## 2. 工具与产物

| 文件 | 内容 |
|---|---|
| tools/night79_freq.py | ② 频次挖矿（503 候选，缺口三条置前） |
| tools/night79_weblio.py / _weblio2.py | weblio 聚合页抓取器（候选批量＋任意补查，0.7s 限速，断点续跑） |
| tools/night79_digest.py | 人读 compact digest（面包屑→机器例文区切片） |
| tools/night79_ruby.py | kanbun.info 出处页 ruby 按词抽取（N76 方法） |
| tools/night79_gap_check.py | N76 缺口三条全行清单 |
| tools/night79_build.py | 判定→extra2 装配器（双证据机械校验） |
| tools/night79_reclassify.py | 接续系 7 条 cat 修正（function→modifier，死条目化回避） |
| tools/night79_eval_4000.py | golden_4000 全量真跑回归（对照 night77 归档逐位） |
| tools/night79_log.py / _roadmap_append.py | SHIFT_LOG 追加器／ROADMAP 末行追加器 |
| **eval/night79_candidates.json** | 候选清单（503 条＋语料样本＋统计） |
| **eval/night79_decisions_*.json** ×10 | 逐条判定底稿（503 条全量，双证据字段） |
| **eval/night79_excluded.json** | 排除清单 179 条＋理由 |
| **backend/glossary_lexicon_extra2.py** | 新词库 324 条（extra.py 同格式＋find_in_lexicon2） |
| eval/night79_results_4000.json | golden_4000 全量归档（与 night77 逐位一致） |
| eval/night79_dict_cache/・night79_ruby_cache/ | 抓取缓存（未跟踪目录，N74 先例） |

## 3. 结论：入库 324／排除 179／剩余 0（候选 503 全判定）

- **总数 500 → 824**（本体 209＋extra 291＋extra2 324）。分组：固有名詞 31／名詞 267／動詞 2（利す・愁殺）／形容副詞 24／機能語 0（见 §1.4）。
- **N76 §3.5 覆盖缺口三条全部收录**：利す（りす，文語活用形辞書条目＋11 行语料）／而る後（しかるのち）／而ち（すなわち）。
- **排除 179 条**（eval/night79_excluded.json 全清单＋理由）三大类：
  - **weblio 404／条目なし**（约 130 条）：X曰・X問呼称部（子曰・太公曰・孔子曰…）、「者有り／道有れば／所有らず」構文断片、白文成句（爲之奈何・凡用兵之法…）、稀有人名書名（相如・季氏・軍讖・沙場・洞庭…）；
  - **読み取り違い／sense-mismatch**（12 条重点案例）：所有（ruby 所=ところ＋有=あ，構文）／昔者（dict=老人，语料=むかし 文頭語）／凡戰（dict=つまらない試合，语料=凡そ戦は）／大学（dict=university，语料=儒教経典）／相当（dict=そうとう，语料=あいたる）／諸有（dict=仏語，语料=諸＋有り）／越人（dict=越智越人 日本氏族，语料=呉越の越）／子之（dict=燕の宰相 人名，语料=子＋之 指示詞）／東流（dict=博多の流組織，语料=東に流る）／相見・相去・相拒・相望（dict 条目なし或読み別，语料=相＋動詞 構文）／終日（dict=ひもすがら，语料=しゅうじつ 系，読法確定できず）；
  - **機械生成区块のみ**（車騎・心無・名無・一車・花開・得難等）。
- **方法注记（待拍板 2 项）**：
  1. **「同語彙条目」路子**：而る後／而ち／何如 的语形自体 weblio 404，辞書证据采「同語彙の辞書条目」（而る後←実用日本語表現辞典 然る後【しかるのち】＋大辞泉「而」難読欄 而後(しかるのち)；而ち←大辞泉 すなわち【▽即ち／▽則ち／×乃ち】；何如←大辞泉 いかん【如＝何／奈＝何】）＋语料 ruby 直证。404 ありのまま記録于判定底稿。此路子是 N74「疑难词形补抓基础形」先例的延伸，若用户不认，删除这 3 条即回 821。
  2. **ウィキペディア条目の採録**：昭王／秦王／景公／恵王／司馬法／鮑叔／玉関／十万 等 8 条用 Wikipedia（或 Wiktionary）页当辞書证据（読み＋释义有据，皆是专名/数词）。不认则同上减 8 条。
- 语料内部新事实（供后续夜参考）：而=なんじ（吴越春秋）之外，又见 嗟乎=ああ（语の直 ruby）、聞道=きくならく（歴史民俗用語辞典条目＋语料 7 行）、読み取り違えの実例 12 类（§3 排除清单）——词库修 词条目化 的素材。

## 4. 验收（wrap-up 提交时补数）

- pytest 全套：开工 351 passed；N79 新增 tests/test_night79_lexicon_expand.py **12 条**（格式/总数 824/双证据全量断言/排除不在文件/N76 缺口/find_in_lexicon2 真语料命中/本体 matcher 不可见 extra2/llm.glossary 离线命中/规则引擎零变化）；全套复跑 **363 passed** ✓
- golden_4000 全量真跑（tools/night79_eval_4000.py，154s）：**engine OK 4000／error 0／exact 24／avgDist 13.517，与 night77 归档输出不一致 0 行** → eval/night79_results_4000.json 归档 ✓（词库不进规则引擎的位级实证）
- README 三处「文語 500 語」→「824 語」＋extra2 文件名同步；ROADMAP 末尾一行 ✓
- `python tools/accept_night.py 79`（主提交 1d68033 之后跑）：**PASS（fail=0 skip=0，57.0s）**
  - 七门全过：repo_clean（untracked 仅缓存目录＋运行日志，N72/N74 先例）／pytest **363 passed = 363 collected**／eval_integrity（night79_results_4000.json 4000 条、id 唯一、expected 一致）／rule_regression／engine_smoke／perf_envelope／order_rate（off 98.57% on 98.63%，基线差 +0.00pp）
  - 首跑一次 FAIL 是 cmd 分隔符坑（`;` 未被解释成命令分隔符，python 收到多余参数退出 2）——非验收门失败，重跑即 PASS，过程在 eval/accept79_run.txt

## 5. 交付与提交

- 分支两提交（主提交＋wrap-up），**不合 master、不推远程**。
- 主提交：词库 extra2（324 条）＋llm.py 接入＋测试 12 条＋工具 11 个＋判定底稿/候选/排除清单/digest/ruby 日志＋golden_4000 归档＋SHIFT_LOG 全程心跳＋ROADMAP 末行＋README 三处计数＋本报告 §0-3/§5。
- wrap-up 提交：ACCEPT_LOG.md＋eval/accept_night_79.json＋REPORT §4 数字＋SHIFT_LOG 收尾行。
- 交付顺序（任务书）：Night 79 完成，全部验收通过。
  - 开工：HEAD = fff5266 ✓；pytest 351 passed ✓；目录 D:\kanbun-rulel、分支 night79-lexicon-expand，与 N71 零接触 ✓
  - 扩库：新入库 **324** 条（目标 500，证据门通过 324／排除 179／剩余 0）；而る後／而ち／利す(りす)：**全收录（3 条）**；总数 500→**824** ✓
  - 验证：回归测试 **363** passed；golden_4000 与 night77 逐位一致（13.517／24／error 0）✓
  - 验收：accept 79 PASS（fail=0 skip=0，pytest 363=363）；分支两提交，未合 master、未推远程 ✓
  - 注：目标 500 未满（324）——任务书耐力规则「质量门是绝对的，300 条全证据好过 500 条凑数」适用；候选清单频次 ≥5 的 513 个中 503 个全判定，排除 179 条的四大理由见 §3，全部归档可复现。
