# REPORT_NIGHT2.md — 第 2 夜（2026-11-17 00:30 ～ 09:00 窗口）

执行者：ZCode 挂机任务（无人工介入）。上夜进度见 REPORT_NIGHT1.md，本报告只记事实。
提交信息：`night2: ocr wired, kundoku quality, frontend polish`（本地，不推远程）。

---

## 0. 结论速览

| 步骤 | 状态 | 一句话结论 |
| --- | --- | --- |
| 1. OCR 接通 | ✅ **接通** | /api/ocr 真实返回 200，竹取物语整页 17 行识别成功；图片→OCR→白文→訓読全链路 curl 实测 |
| 2. 訓読质量 | ⚠️ 有改善 | 精确匹配 **0/10 → 0/10**（没涨分），但 6/10 条的可读性可见提升；qkana 官方源重试仍被墙（~1 分钟放弃）；guwenbert 模型源被墙，未实测 |
| 3. 后端+前端打磨 | ✅ | SQLite 两表落库 35 条；vite 双栈监听（127.0.0.1:5173 已能打开）；縦書き+返り点ルビ完成（待人工浏览器确认）；CLI 编码问题根因查明并修正 |
| 4. LLM 适配层 | ✅ | backend/llm.py 只读环境变量 KANBUN_LLM_API_KEY，无 key 时 mock 返回占位；结构不变 |

---

## 1. 步骤 1 — OCR 接通（完成）

### 1.1 引擎入口

GUI（Flutter 壳）不是命令行入口。`app.zip` 解包后发现真正的推理在
`src/ocr.py`（get_detector/get_recognizer）+ `main.py` 的 `ocr_button_result`
路径：rtmdet 检测行框 → ndl_parser 转 XML → reading_order/xy_cut 排序 →
行图裁切 → PARSeq 逐行识别 → 縦書き主流时行序右→左（由 eval_xml 完成，
**不需要**再做行序反转——night2 初版加了反转反而打乱顺序，已删）。

依赖不必新装：官方 Windows 版 GUI 自带的 `D:\dlkotenocr-lite\site-packages`
里有全套 cp312 包（onnxruntime 1.23.2 / numpy 2.2.2 / pillow 12.1.1 / lxml /
yaml / tqdm / networkx），系统 Python 3.12.10 里没有冲突包，直接 sys.path
追加复用。模型从 app.zip 解压到 `ocr_runtime\src\model\`（parseq 42MB +
rtmdet 40MB），`ocr_runtime/` 已加入 .gitignore 不入库。

包装：`backend/ocr_engine.py`（NDL ndlkotenocr-lite, CC BY 4.0，只搬运推理
流程未改算法；路径可用 KANBUN_OCR_SITE / KANBUN_OCR_SRC 环境变量覆盖）。
惰性单例：首次 /api/ocr 调用时加载两个 ONNX 模型，本机 Celeron 上实测
**首次加载 43~64 秒，单张图推理 72~80 秒**；之后模型常驻，无需再加载。

### 1.2 样张（来源如实记录）

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `ocr_runtime/samples/ndl_1287221_R0000002_clean.jpg` | **NDL 数字收藏 IIIF**：`https://dl.ndl.go.jp/api/iiif/1287221/R0000002/full/1400,/0/default.jpg`（竹取物語 3 軸，dl.ndl.go.jp 本机可直连 200/1.6s）| 主样张（干净无标注）|
| `10301438_0017.jpg` 等 3 张 + demo 图 | ndl-lab/ndlkotenocr-lite 仓库 `resource/`（raw.githubusercontent 被墙，经 `api.github.com` contents API base64 下载；jsdelivr 对部分文件 301）| 对照（自带蓝色检测框标注）|

样张识别结果（真实输出，未修一字）：
```
十四番熊
いまはむかしたけとりのおきなといふ
ものありけり野山にましりてたけ
をとりつゝよろつの事につかひけり
名をはさるきのみやつことなんいひ
ける其竹の中にもとひかる竹なん
一すちありけりあやしかりてよりて
見るにつゝの中ひかりたりそれをみ
れは三すんはかりなる人いとうつくしう
てゐたりおきないふやうわれ朝こと夕
ことに見るたけの中におはするにて
しりぬ子になり給ふへき人なめり
とて手にうち入て家へもちてきぬ
めの女にあつけてやしなはすうつ
くしき事かきりなしいとおさなけ
れははこに入てやしなふ竹とりのお
きな竹とるに此子を見つけてのちに
```
判断（只记事实）：开头「いまはむかし…」名句段行序、行内文字基本正确；
第 1 行「十四番熊」是图片下方的**色卡校准条**被误读；中段有几处列序交错
（如「きな竹とるに此子を見つけてのちに」应为下一段开头）。识别是«可用初稿»，
符合“用户可在白文编辑区手改”的定位。准确率数字无法给——无 ground truth 对照。

### 1.3 全链路 curl 实测

`POST /api/ocr`（clean 样张，200，115s 含首次模型加载）：
```json
{"hakubun": "十四番熊\nいまはむかしたけとりのおきなといふ\nものありけり野山にましりてたけ\n…（§1.2 全文）",
 "status": "ok", "line_count": 17, "elapsed_sec": 72.1,
 "note": "NDL 古典籍 OCR-Lite（ndl-lab/ndlkotenocr-lite, CC BY 4.0）。白文可修改，请以原文为准。", ...}
```

接着把 OCR 返回的 hakubun 原样 `POST /api/kundoku`（200）：
```
kaeriten_text: '十四番熊\nいまはむかしたけとりのおきなといふ\nものありけり二野山一にましりてたけ\n…'
kakikudashi:   '十四番熊\nいまはむかし…野の山をものありけりにましりてたけ\n…'
modern: '待接入 LLM（占位）'   glossary: []
```
诚实说明：竹取物語是**假名文学**，UD-Kundoku 是汉文引擎，对假名白文插助词
的结果语言学上不成立（输出可见乱插的「の/は/を」）；链路机制全部打通、
字段结构不变，语义质量要有意义需输入漢文白文（例如用户手工改成漢文，或
未来加「假名→漢文判断」的前置分流）。

前端：上传成功后 OCR 文本自动填入白文编辑区并提示可修改（App.tsx 已更新）。

## 2. 步骤 2 — 訓読质量

### 2.1 基线确认

后端加 `POST /api/kundoku?merge=0` 开关后重跑 10 条：
`eval/night2_results_baseline.json` 的输出与 REPORT_NIGHT1.md 记录的
Night1 输出**逐条一致**（楚の人は楯矛ともを… / 項の王軍の壁垓下 / 張僧は繇す…），
基线未漂移。**精确匹配 0/10。**

### 2.2 后处理规则（backend/kundoku_rules.py）

针对 night1 点名的「专名切分错」做了**词元级合并**（在 reorder/translate
之前对 UD 树做手术，不是对最终字符串做正则）：

- 白名单（2~3 字专名，手工维护）：楚人/宋人/狙公/項王/垓下/張僧繇/梁惠王/荊宣王/昭奚恤/江乙/群臣
- 仅当首词元为名词性（xpos 以 n, 开头）才合并
- 合并后重编号，并绕过 udkanbun 的特殊 `__setattr__`（见 §2.3）

结果（`eval/night2_results_merge.json`）：**精确匹配 0/10 → 0/10**，
但 6/10 条可读性可见提升：

| id | Night1（基线） | Night2（合并后） | expected |
| --- | --- | --- | --- |
| mujun-1 | 楚の人は楯矛ともを鬻ぐ者有り。 | 楚人楯矛ともを鬻ぐ者有り。 | 楚人に楯と矛とを鬻ぐ者有り。 |
| shimen-1 | 項の王軍の壁垓下。 | 項王軍壁垓下。 | 項王の軍、垓下に壁す。 |
| garyo-1 | 張僧は繇す、呉は中の人なり。 | 張僧繇、呉は中の人なり。 | 張僧繇は、呉中の人なり。 |
| shushu-1 | 宋の人は田を耕す者有り。 | 宋人田を耕す者有り。 | 宋人に田を耕す者有り。 |
| gojippo-1 | 梁の惠王は曰く、 | 梁惠王曰く、 | 梁の恵王曰く、 |

没涨分的残差（如实记录，规则解决不了的）：
- 助词选择（に/は）、体言止め（項王の軍、垓下に**壁す**）的动词条目缺失、
  「祠る者」类名词化——都在解析/词条层面，字符串或树手术修不动；
- 旧字体/新字体（惠→恵、對→対、竊→窃、雞→鶏）：expected 用新字体，
  引擎输出旧字体。可做输出正字化规则，今晚未做（留下一步）。

### 2.3 实现中踩的坑（修复，值得记录）

udkanbun 的 `UDPipeEntry.__setattr__` 对 `head`/`id` 赋值有特殊语义：
`head` 传 int 会被解释成“相对 id 偏移”，传 token 对象直接
`TypeError: unsupported operand type(s) for +: 'int' and 'UDPipeEntry'`；
`id` 赋值会触发列表元素交换。第一版合并规则直接 `other.head = head_tok`
导致 7/10 条 500（后端日志留档）。修法：用 `object.__setattr__` 绕过。

### 2.4 qkana 官方源重试（限时 ~1 分钟，未通过）

`curl --retry 3` 直连 `https://clrd.ninjal.ac.jp/unidic_archive/2203/UniDic-202203_60b_qkana.zip`
→ 3 次全部 TLS 重置（exit 35），与 night1 判断一致。**继续用 shim，未耗 1 小时。**

### 2.5 guwenbert（只试不强求 → 未实测）

`udkanbun/supar.py` 显示 guwenbert 模式要从
`https://raw.githubusercontent.com/KoichiYasuoka/UD-Kanbun/master/udkanbun/supar-kanbun/`
下载 `guwenbert-base.supar`（~400MB 级）。本机 `raw.githubusercontent.com` 被墙；
jsdelivr CDN 对 GitHub 文件有 20MB 上限放不下；api.github.com contents API 上限 1MB。
另需安装 supar+torch（~2GB）。**结论：模型不可达，未实测**，记入下一步建议
（在有网络的机器上把 .supar 文件拷过来即可试）。

## 3. 步骤 3 — 后端 + 前端打磨

- **SQLite**（backend/db.py）：requests(id, hakubun, created_at) + results(id, request_id, kaeriten_text, kakikudashi, created_at)，无多余字段。每次訓読成功落库，失败不影响 API。实测：今晚累计 **requests=35, results=35**（含评测 20 次）。
- **vite 双栈监听**：vite.config.ts `server.host: true` → Local + Network 双栈，`http://127.0.0.1:5173/` 实测 200（night1 只监听 [::1]）。
- **縦書き + ルビ**（frontend/src/App.tsx / App.css）：①返り点付き原文与②書き下し文改为 `writing-mode: vertical-rl` 縦書き；返り点ルビ化用**raw 版合字**（后端新增 `kaeriten_text_raw` 字段，保留 ㆑㆒㆓ 等合字）解析成 `<ruby>字<rt>点</rt></ruby>`——合字无歧义，不会把白文里的普通汉字「一/上/中」误当返り点；③現代語訳/④語釈按 mock 返回渲染，空时显示占位。**人工浏览器确认留给用户**（本环境无浏览器自动化），vite 已成功 HMR 编译新 App.tsx（200）。
- **CLI 编码问题（night1 结论修正）**：根因不是“控制台 GBK 显示问题”，而是**内联在 shell 命令行里的日文被转成了 `?`**（`echo 不入虎穴不得虎子 | python …` 的 echo 输入本身就是 8 个 `?`，引擎输出自然是 `?`）。修正验证：
  - `type tools\cli_test_input.txt | python -X utf8 tools\udkundoku_cli.py` → 正确输出两行训读；
  - 官方 `python -m udkundoku.cli -j` 在 UTF-8 文件输入 + chcp 65001 下**也能正常工作**——night1 记录的 Danku TypeError 未能复现（当时输入已被转成 `?`，行为不可比）。长句无标点合法触发 seg=True 路径时输出为逐字断行（质量差但不崩）。
  - `tools/udkundoku_cli.py` 保留：stdin 字节流 utf-8→gbk 逐级尝试解码，固定 Danku=False，避免 seg 分支。

## 4. 步骤 4 — LLM 适配层（只搭架子）

`backend/llm.py`：
- 只读环境变量：`KANBUN_LLM_API_KEY`（必需）/ `KANBUN_LLM_BASE_URL` / `KANBUN_LLM_MODEL`。代码里没有任何 key 值，也没有从 ZCode 抓 token 的逻辑。
- 无 key → 离线 mock：modern 返回 `"待接入 LLM（占位）"`，glossary 返回 `[]`，字段结构不变。
- 有 key 时的真实调用路径已写好但 TODO 注明未启用（OpenAI 兼容 /chat/completions，提示词已备好）。
- 实测（全链路那一次）：`modern: '待接入 LLM（占位）'`，`glossary: []` ✓。
- 需要用户拍板：产品推理用哪家 API、key 通过什么方式给（建议环境变量注入，不进 git）。

## 5. 做到哪 / 卡在哪 / 下一步建议

**本夜无未解决卡点。** 所有步骤都有结论，OCR 承诺兑现。

下一步候选（按建议优先级）：
1. **官方 qkana 拿到后替换 shim**（URL 与缓存路径见 REPORT_NIGHT1 §2.1；解压覆盖 `unidic2ud\download\qkana\` 即生效），重跑 eval 看涨多少。
2. **guwenbert-base.supar** 在有网络的机器下载后放进 `site-packages\udkanbun\supar-kanbun\`，装 supar+torch 后 `udkundoku.load(BERT="guwenbert-base")` 对比——对切分/解析质量的预期提升最大。
3. **输出正字化规则**（惠→恵、對→対、竊→窃、雞→鶏…旧→新字体映射表）——低成本，可能直接帮 gojippo-1 类条目涨分。
4. **OCR 行序/列序**：竹取物语中段列序交错，可调 reading_order 参数或加列聚类后处理；色卡等非文字区可按位置过滤。
5. **假名白文分流**：OCR 出来的若是假名文学文本，訓読管线不适用——加文本类型判断，假名文本直接给现代语标注或转写建议。
6. 現代語訳/語釈 等用户给 key 后在 llm.py 里启用 TODO 段落即可。

需要用户拍板的事：
- 产品推理 API 用哪家、key 注入方式（环境变量名已定：KANBUN_LLM_API_KEY）。
- 是否在别的网络环境下载官方 qkana / guwenbert 模型并拷贝到本机。
- 域名/远程仓库仍按禁令未动。

## 6. 禁止事项遵守情况

- 本地 git 提交，未建远程、未推远程、未部署、未买域名。
- 代码/报告/git 历史无任何 API key/token；llm.py 只写环境变量名。
- 未编造：OCR 无 ground truth 就不给准确率数字；评测 0/10 原样记录；qkana/guwenbert 未实测如实标注。
- 縦書き/ルビ未做浏览器人工确认前，报告不写“通过”。
- 报告写完即停，不做第 3 夜。

## 7. 产出物清单（相对 night1 新增/修改）

```
backend/ocr_engine.py      NDL OCR-Lite 进程内包装（新增）
backend/kundoku_rules.py   专名合并规则（新增）
backend/db.py              SQLite 两表（新增）
backend/llm.py             LLM 适配层 + mock（新增）
backend/main.py            接通 OCR/DB/LLM/merge 开关，kaeriten_text_raw 字段
frontend/src/App.tsx       OCR 回填白文、縦書き、返り点ルビ、③④渲染 mock 结果
frontend/src/App.css       縦書き样式
frontend/vite.config.ts    host:true 双栈监听
tools/udkundoku_cli.py     Windows 管道安全 CLI 包装（新增）
tools/fetch_github_file.py api.github.com base64 下载器（新增）
tools/test_ocr.py          OCR 独立测试（新增）
tools/run_eval.py          支持 --no-merge / 输出文件名参数
eval/night2_results_baseline.json / night2_results_merge.json
kanbun.db                  SQLite 数据文件（不入库）
ocr_runtime/               不入库（模型+样张，见 .gitignore）
REPORT_NIGHT2.md           本报告
```
