# REPORT_NIGHT1.md — 第 1 夜（2026-11-16 23:00 ～ 11-17 09:00 窗口）

执行者：ZCode 挂机任务（无人工介入）
目标：Web MVP 骨架——两个入口汇到同一条訓読管线，输出四样（返り点付き原文 / 書き下し文 / 現代語訳 / 語釈）。
本报告只记录实际跑过的命令和真实输出，未实测的地方如实标注。

---

## 0. 结论速览

| 步骤 | 状态 | 说明 |
| --- | --- | --- |
| 1. UD-Kundoku 跑通 | ✅ 完成 | 卡点已定位并解决（qkana shim 方案），三句经典例句训读正确 |
| 2. FastAPI 后端 | ✅ 完成 | /health、/api/kundoku、/api/ocr 占位全部 curl 实测 |
| 3. NDL OCR-Lite | ⚠️ 部分完成 | 程序是用户当晚 22:00 已下载解压好的（D:\dlkotenocr-lite，285MB）；GUI 启动验证通过（有截图）；无くずし字样张，识别准确率未实测；未接入 API |
| 4. 前端单页 | ✅ 完成 | vite 起服、页面四块布局、经 vite 代理调通 /api/kundoku；浏览器人工截图留给用户（本环境无浏览器自动化工具） |
| 5. 评测集 | ✅ 完成 | eval/golden.json 10 条成对样本；10 条全部实测，**0/10 全对**（原始输出如实记录） |
| git 本地提交 | ✅ | night1: web skeleton, udkundoku baseline, ocr stub |

四样输出中：①② 由本地 UD-Kundoku 引擎真实产出；③④ 今晚按要求为占位（“待接入 LLM”），未接任何 key。

---

## 1. 环境事实（与任务书假设的差异）

- Python 3.12.10 在 **D:\Python312**，Node v26.13.1 在 **D:\nodejs**，git 2.56.1 在 **D:\Git\cmd**——都不在系统 PATH（ZCode 的 shell 只拿到系统 PATH）。本报告所有命令均先 `set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%`。
- 磁盘：D: 剩 7.6GB、C: 剩 21.9GB、E: 剩 58GB。项目在 D:\kanbun-kakikudashi（纯 ASCII 路径）。
- pip 清华镜像、npm 走项目级 .npmrc（registry.npmmirror.com）。

## 2. 步骤 1 — UD-Kundoku 卡点定位与解决（核心）

### 2.1 卡点根因（不是 UDPipe 模型，是 UniDic qkana 词典）

用户实测（22:29）的现象是 `udkundoku.load()` 卡 0%。实际链路是：

1. `import udkundoku` 时执行（site-packages\udkundoku\udkundoku.py 第 6-14 行）：
   `unidic2ud.dictlist()` 里没有 `"qkana"` → 调 `unidic2ud.download("qkana","unidic")`。
2. 下载目标（unidic2ud/unidic2ud.py 第 15 行）：
   - **URL**: `https://clrd.ninjal.ac.jp/unidic_archive/2203/UniDic-202203_60b_qkana.zip`
   - **缓存路径**: `D:\Python312\Lib\site-packages\unidic2ud\download\`（zip 解压成 `download\qkana\` 目录）
3. `clrd.ninjal.ac.jp`（202.245.100.169）TLS 握手 0.67 秒内被重置：
   ```
   curl: (35) schannel: next InitializeSecurityContext failed: SEC_E_ILLEGAL_MESSAGE
   ```
   TCP 80 通但强制 301 跳 https；关 SNI 直连 IP 也被 RST。Python urllib 对这种 RST 表现为无限挂起——就是“0% 5 分钟不动”的来源。
   另：`import udkundoku` 本身就会触发下载（不是 load() 才触发），所以 `python -c "import udkundoku"` 也会卡死。
4. 注意：UDPipe 部分**不是**卡点——`udkanbun` 包自带 `ud-kanbun.udpipe`（17MB）+ `mecab-kanbun` 词典，`unidic2ud` 自带 `japanese-modern.udpipe`（10MB），全部离线可用。

### 2.2 找官方镜像的尝试（都失败了，记录备查）

- Wayback Machine（web.archive.org）：本机直连超时（TLS 不通），且 CDX 查询确认该 zip 从未被归档。
- Hugging Face：无 qkana 模型/数据集。
- GitHub 搜仓库/发行版：无任何含 UniDic qkana 的仓库；KoichiYasuoka/UniDic2UD 无 Release 资产。
- PyPI（清华镜像）：无 qkana 相关包；udkundoku 各版本 sdist（0.2.0～2.3.0）都不带词典。
- 公共代理：api.allorigins.win 返回 520，corsproxy.io 要求 API key。
- 阿里云 Debian 镜像有完整 UniDic（unidic-mecab_2.3.0+dfsg-6_all.deb，799MB；3.1.1 版 993MB）——是备选材料，最终没用上。

### 2.3 采用的解法：unidic_lite 冒充 qkana（shim）

原理：`unidic2ud` 只要发现 `download\qkana\` 是一个含 dicrc 的 MeCab 词典目录就不再联网；`udkundoku` 只在活用表兜底查询时用它的 MeCab 输出，且只按**标准 UniDic 29 列**的列号取值（s[0]=表層\t品詞1、s[4]=活用型、s[6]=語彙素読み、s[7]=語彙素、s[12]=発音形基本形）。

做法（`tools/make_qkana_shim.py`，可复现）：
1. 把已装好的 `unidic_lite`（= unidic-cwj-2.1.1 compact，PyPI 清华镜像可装）的词典目录整体复制到
   `D:\Python312\Lib\site-packages\unidic2ud\download\qkana\`；
2. 写入自定义 dicrc，把 unidic_lite 内部特征号映射成 UniDic 标准逗号分隔 29 列输出；
3. `import udkundoku` 从此离线完成。

诚实声明：**这不是官方 qkana**（qkana 是假名见出し，shim 是汉字见出し的 cwj 精简版）。对三句实测和 10 条评测里的常用文语动词够用；个别词的送り仮名可能与官方 qkana 不同。以后拿到官方 UniDic-202203_60b_qkana.zip（比如在网络能直连 NINJAL 的环境下载），解压覆盖 `download\qkana\` 即可无缝替换。

### 2.4 三句实测（tools/test_udkundoku.py 原始输出）

```
[import] udkundoku imported in 1.7s
[load] pipeline ready in 8.2s
==============================
[input] 王顧左右而言他
[kaeriten] 王顧㆓左右㆒而言㆑他
[kundoku -j] 王は左右を顧みて而して他を言ふ
==============================
[input] 不入虎穴不得虎子
[kaeriten] 不㆑入㆓虎穴㆒不㆑得㆓虎子㆒
[kundoku -j] 虎の穴に入らずして虎の子を得ず
==============================
[input] 欲治其國者先齊其家
[kaeriten] 欲㆑治㆓其國㆒者先齊㆓其家㆒
[kundoku -j] 其の國を治めんと欲する者は先に其の家を齊す
```

对照常识逐句判断：
- 「王顧左右而言他」→「王は左右を顧みて而して他を言ふ」：**符合**（《孟子·梁惠王下》标准训读）。
- 「不入虎穴不得虎子」→「虎の穴に入らずして虎の子を得ず」：**符合**（后汉书班超传常用训读）。
- 「欲治其國者先齊其家」→「其の國を治めんと欲する者は先に其の家を齊す」：**符合**（大学标准训读）。

返り点符号说明：udkanbun 输出用 Unicode 合字（㆒㆓㆔㆕=一二三四、㆑=レ、㆖㆗㆘=上中下、㆙㆚㆛㆜=甲乙丙丁、㆝㆞㆟=天地人）。后端已把它们转成通用写法（王顧二左右一而言レ他）。

### 2.5 已知上限（原样转述 udkundoku 项目文档，未逐条验证）

- 再読文字目前只对应了「未」；應・當・須・蓋・宜・將等未对应。
- 骈文和诗（对仗/押韵结构）也难。
- 本晚 10 条评测（见第 6 节）的实际表现印证了上限：复杂句、专名切分错的不少。

### 2.6 CLI 附带发现（不影响产品，记录备查）

`echo 不入虎穴不得虎子 | python -m udkundoku.cli -j` 在 Windows 管道下有两个问题：
- GBK 代码页（默认）：能出结果但控制台显示为 `????????`（编码显示问题）；
- chcp 65001 + PYTHONIOENCODING=utf-8：触发 cli.py 的 Danku 分支，报
  `TypeError: in method 'Pipeline_process', argument 2 of type 'std::string const &'`。
产品走 HTTP API 路径（已验证），CLI 问题留待以后单独处理。

## 3. 步骤 2 — FastAPI 后端（实测输出）

启动：`python -m uvicorn backend.main:app --port 8000 --host 127.0.0.1`（项目根目录）。
启动时 lifespan 加载引擎（首次 8.2s，之后常驻）。

`GET /health`：
```json
{"ok":true,"engine_loaded":true}
```

`POST /api/kundoku`，body `{"text":"王顧左右而言他"}`：
```json
{"hakubun":"王顧左右而言他","kaeriten_text":"王顧二左右一而言レ他\n","kakikudashi":"王は左右を顧みて而して他を言ふ","modern":"","glossary":[],"disclaimer":"AI 初稿，仅供参考，请以原文和专业判断为准。","engine":"udkundoku","error":""}
```
5 个必备字段（hakubun / kaeriten_text / kakikudashi / modern / glossary）全部存在；modern、glossary 按要求留空 + 代码内 TODO。

`POST /api/kundoku`，空文本 → 400：`{"detail":"text 为空，请先输入白文"}`

`POST /api/ocr`（占位），上传任意文件 →
```json
{"hakubun":"","status":"not_implemented_yet","note":"OCR agent 尚未接入（NDL 古典籍 OCR-Lite）。今晚请先粘贴文本或手动输入白文。"}
```
没有假装能识别；上传内容读掉即弃，不落盘。

经 vite 代理的同链路验证：`POST http://[::1]:5173/api/kundoku` body `{"text":"不入虎穴不得虎子"}` →
```json
{"hakubun":"不入虎穴不得虎子","kaeriten_text":"不レ入二虎穴一不レ得二虎子一\n","kakikudashi":"虎の穴に入らずして虎の子を得ず",...}
```

依赖补充：`python-multipart`（UploadFile 必需）经清华镜像补装，已写进 backend/requirements.txt。

SQLite：任务允许“只建表不写业务”——今晚没建，留作下一步建议（见第 7 节），避免发明没被要求的范围。

## 4. 步骤 3 — NDL 古典籍 OCR-Lite

- **下载状态**：发现用户当晚 22:00 已自行下载并解压到 `D:\dlkotenocr-lite`（285MB，纯 ASCII 路径）。本夜未重复下载。路径含中文/全角会启动失败这点沿用任务书提醒，记录在案。
- **包结构**：Flutter GUI 壳 + 内嵌 Python 3.12（serious_python）。OCR 模型内嵌于 `data\flutter_assets\app\app.zip`：
  - `src/model/parseq-ndl-32x384-tiny-10.onnx`（42.4MB，くずし字识别）
  - `src/model/rtmdet-s-1280x1280.onnx`（40.2MB，行/文本框检测）
  免额外下载模型。
- **GUI 启动验证**：`Start-Process D:\dlkotenocr-lite\ndlkotenocr_lite_gui.exe` → 进程 8712 存活，窗口标题 `ndlkotenocr-lite-gui`，界面完整（日文 UI、画像ファイルを処理する / OCR / Crop&OCR / 出力先選択）。截图：`docs/night1_ocr_gui_screenshot.png`。验证后已关闭进程。
- **识别准确率**：手头无くずし字样张 → **未实测，不编造**。`POST /api/ocr` 保持占位。
- 备选对照（只记录不实现）：CODH KuroNet / みを（miwo），免费服务、需登录 IIIF，适合对照不适合嵌产品。

## 5. 步骤 4 — 前端单页

- 技术栈：Vite 7.3.8 + React 19 + TypeScript 5.9，手写脚手架（不用 create-vite 交互向导），依赖装自 npmmirror（项目级 .npmrc）。npm install 首跑因 esbuild postinstall 子进程找不到 `node` 失败——带 `D:\nodejs` 进 PATH 重跑成功。
- 启动：`npm run dev` → `VITE v7.3.8 ready in 8911 ms`，监听 **[::1]:5173**（IPv6 localhost；`http://localhost:5173/` 可访问，`127.0.0.1:5173` 不通）。
- 页面一屏四块（backend/frontend/src/App.tsx）：
  - 左上输入区：入口 A 粘贴文本框 + 入口 B 上传图片按钮（上传后显示“OCR agent 尚未接入…今晚请先粘贴文本或手动输入白文”，不假装识别）；
  - 左下白文编辑区：可编辑，“重新訓読”按钮触发 `POST /api/kundoku`；
  - 右侧输出区四栏：①返り点付き原文 ②書き下し文 ③現代語訳（显示“待接入 LLM（占位）”）④語釈（同）；
  - 每栏下方一行小字“AI 初稿，仅供参考，请以原文和专业判断为准。”
- 联调验证（文字记录）：`GET http://[::1]:5173/` 返回 vite 转换后的 index.html（title「漢文 → 書き下し文」、root 挂载点、main.tsx 模块加载正常）；`POST http://[::1]:5173/api/kundoku` 经代理返回完整 5 字段 JSON（见第 3 节）。
- **浏览器人工验证留给用户**：本环境没有浏览器自动化工具（无 node_repl/CDP），截图未做。打开 http://localhost:5173/ 即可看到四块布局；后端须已启动。

## 6. 步骤 5 — 评测集与 10 条实测

- `eval/golden.json`：10 条“白文 + 書き下し文”成对样本，来自 Web漢文大系（kanbun.info）故事名言页（矛盾/韓非子、蛇足/史記、朝三暮四/列子、塞翁が馬/淮南子、四面楚歌/史記、虎の威を借る/戦国策、画竜点睛、守株/韓非子、五十歩百歩/孟子、鶏口牛後/戦国策），每条记 id / source_url / hakubun / expected_kakikudashi。构建脚本 `tools/build_golden.py`（ruby 注音剥离，不改写 expected）。
- 实测（`tools/run_eval.py` → POST /api/kundoku，**原始输出不改写**）：
  - **完全一致 0 / 10**。详细逐条对比在 `eval/night1_results.json`。
  - 典型差距（节选，前 4 条）：
    ```
    mujun-1 expected: 楚人に楯と矛とを鬻ぐ者有り。
            got     : 楚の人は楯矛ともを鬻ぐ者有り。
    dasoku-1 expected: 楚に祠る者有り。
            got     : 楚は祠者有り。
    saio-1  expected: 塞上に近きの人に、術を善くする者有り。
            got     : 近く上の人を塞ぐ、/善術有る者。   ← 切分错误
    shimen-1 expected: 項王の軍、垓下に壁す。
            got     : 項の王軍の壁垓下。               ← 壁す未识别
    ```
  - 简单句（王顧左右而言他 等 3 句）正确、长难句/专名多的句子明显不稳——与 udkundoku 已知上限一致。
- 今晚不跑完评分脚本、不做准确率优化（第 2 夜的活）。

## 7. 卡在哪 / 下一步建议（只列事实与建议，不替用户拍板）

**本夜无未解决卡点**，所有要求的验证点都有结论。留给下一夜的候选（按建议优先级）：

1. **替换官方 qkana 词典**：在网络能直连 NINJAL 的环境（VPN / 境外机 / 手机热点）下载
   `https://clrd.ninjal.ac.jp/unidic_archive/2203/UniDic-202203_60b_qkana.zip`，解压覆盖
   `D:\Python312\Lib\site-packages\unidic2ud\download\qkana\`（目录名不变即生效）。重跑 eval 看准确率变化。
2. **訓読质量**：评测 0/10 的主因是切分与文语活用。可试 udkanbun 的 `guwenbert-base/large`（BERT 模式，需另下模型）或对高频错误句做后处理规则。
3. **SQLite 建表**（任务允许但今晚未做）：requests / results 两表即可。
4. **OCR 接入**：dlkotenocr-lite 的 GUI 是 Flutter 壳，命令行/管道入口要扒 `app.zip` 里的 main.py；或直接 pip 装 ndlkotenocr（若官方提供 CLI 版）。接入后更新 POST /api/ocr。
5. **現代語訳・語釈**：等用户提供产品推理 API key 后接 LLM；代码里已留 TODO 位。
6. **前端打磨**：縦書き表示（writing-mode: vertical-rl）、返り点ルビ化、浏览器截图补档。

**需要用户拍板的事**：
- 是否找网络条件好的环境下载官方 qkana（约 100MB 级，需要能访问 clrd.ninjal.ac.jp）。
- 产品推理 API 用哪家、key 怎么给（务必不要让 ZCode 的 token 出现在项目里）。
- 是否要建远程仓库/买域名——今晚按禁止事项完全没碰。

## 8. 禁止事项遵守情况

- 未部署、未买域名、未建远程仓库、未推远程（git 仅本地）。
- 代码、报告、git 历史中无任何 API key / token（現代語訳・語釈为空占位 + TODO）。
- 未编造结果：OCR 识别未实测就明说未实测；评测 0/10 原样记录；CLI 问题原样记录。
- 未把占位功能写成已实现：/api/ocr 响应体、前端上传入口均明示未接通。
- 报告写完即停，不开始第 2 夜的工作。

## 9. 产出物清单

```
backend/main.py, __init__.py, requirements.txt     FastAPI 后端（8000）
frontend/                                          Vite+React+TS 单页（5173，[::1]）
eval/golden.json                                   10 条评测集
eval/night1_results.json                           10 条实测原始结果（0/10）
tools/make_qkana_shim.py                           qkana shim 生成（可复现）
tools/test_udkundoku.py                            三句实测脚本
tools/build_golden.py                              评测集构建脚本
tools/run_eval.py                                  评测执行脚本
tools/probe_unidic_lite.py                         词典列格式探针
docs/night1_ocr_gui_screenshot.png                 OCR GUI 启动截图
REPORT_NIGHT1.md                                   本报告
test_ud.py                                         用户 22:29 的原始卡点复现脚本（保留原样）
```
