# REPORT_NIGHT64.md — Night 64：Rule I 挖掘（Night 22 方法论，golden_4000）【2026-11-21】

任务书：Rule I 挖掘（Night 22 方法论：解剖 → 离线模拟 → 0 变差有护栏才上线 → 真机与模拟逐位一致 → 幂等）；
只动 `backend/kundoku_rules.py` + tests + 工具脚本；不碰 eval/golden*.json、OCR、前端；
pytest + `accept_night.py 64` 通过；REPORT_NIGHT64.md；当前分支本地提交，不合 master、不推远程。

本夜产线数字（先给结论）：**Rule I 6 条假名→汉字 + SHINJITAI 99 对上线，golden_4000 全量
3998 条 avgDist 13.889 → 13.719（-0.170），656 行改写、改善 514 / 变差 0 / 持平 142，
精确匹配 19 → 24（+5），幂等 PASS，GT CER 0.3568/0.3053 逐位不变，pytest 193 → 211**。
真机与离线模拟逐位一致（本项目第五次「API=离线真函数」等价）。

---

## 0. 开工检查与环境偏差（如实）

- `D:\kanbun-rulei` **不存在**（任务书给的路径）。D: 盘上只有主仓 `D:\kanbun-kakikudashi`
  和上一个任务的 clone `D:\kanbun-eval10k`（分支 night62-eval10000，停在 b370761 未提交）。
  按 kanbun-eval10k 的先例，本夜从**本地主仓 clone** 出 `D:\kanbun-rulei` 并建任务分支
  **night64-rulei**：`git log -1` = `b370761`（roadmap: Night 61 README 刷新），与主仓 master 一致。
- **开工 pytest 第一次 192 passed + 1 failed**（`test_ocr_missing_runtime_message_shape`）：
  clone 缺 `ocr_runtime\`（.gitignore 的构建产物，从 dlkotenocr-lite 的 app.zip 解压，
  主仓盘上有）→ 从主仓 `robocopy` 拷回（81 文件 / 121.4MB）→ 重跑 **193 passed**。
  证据：`eval/night64_pytest_start.txt`（前后两次都留档）。
- pytest 全量在 clone 里 9.94s～85s 量级（含 193+18 条）。

## 1. 解剖（tools/night64_mine.py，只读，输出 eval/night64_mine.json）

golden_4000 的基线 = **night60 真机归档**（D/E/F/G/H 全链 + SHINJITAI 147 对，
avgDist 13.889，`diff_rows_vs_n58=0`，是当前上线链的输出）。三个切面：

**A. 字符 delta（exp-got 汉字计数）**——新增段（toushisen 1000，全 ≤20 字）几乎全是
SHINJITAI 缺口与已拒绝字（為/若/莫）；全 4000 段的头部：
為 270（已拒）、可 186（已覆盖）、不 100 / 若 97 / 莫 85 / 勿 22 / 焉 27（已拒）、
**聴 39 / 観 32 / 舎 23 / 弁 19 / 争 21 / 慎 21 / 遅 17 / 継 12 / 蔵 13 / 寝 11 / 勧 10 / 静 10 / 巻 10 / 髪 14 / 揺 14 got=0**（=引擎写旧形，SHINJITAI 缺口）、
**蓋 24 / 毋 23**（=引擎写对应假名 けだし / なかれ，Rule E 型候选）。

**B. 假名串 delta（got ≥5 次且 exp ≤ 1/4）**——全 4000 头部：して 1947 / なりて 552 /
ひて 297 / するを 258 / へて 181 / するは 113 …（活用/句法结构差异，Night 24/25 已定性
规则层不可分，本夜不做）；**真候选：けだし 19、いずくんぞ 34、もし 40、それ 48、
することなかれ 20、うべきか 22**；のみ got 86 < exp 96（非候选）；すなわち / なほ /
ゆゑに **got = 0**（引擎已不写，无候选）。

**C. SHINJITAI 1:1 扫描**（N58 同款判据 exp 旧形 0 次 & got ≥2）：1:1 块收 7 对
（聽→聴 / 壯→壮 / 絕→絶 / 祿→禄 / 溪→渓 / 劒→剣 / 峯→峰）；
拒绝 冰→氷（exp 写旧形 2）/ 弦→絃（2）/ 亦→又（105）——与 N58 同判据。

## 2. 候选取证（tools/night64_probe.py，输出 eval/night64_probe.json）

**SHINJITAI 第二遍「计数判据」**（N58 教训：difflib 1:1 块会漏多字对齐里的对）：
对全部不在表中的汉字做「exp 全库写 0 次 && got ≥2 次」扫描 + 等长替换块逐位多数票定
目标形 → 共定型 **99 对**（73 对有票 + 26 对票为 0 的等长块漏投票字取标准新字体，
票据里 被/廃/耳/擻/於/躍/為 等杂票确认为对位噪音）。**99 对全部要求 exp 写过新形
≥1 次**（脚本核验 0 对被核掉）；程序断言「目标 ∩ 旧形键 = 无」。

**kana 候选按 exp 真实词形逐条取证**（D14 教训：词形按 expected 的真实形态）：

| 候选 | got | exp | 白文含护栏字行数 | exp 词形 |
| --- | --- | --- | --- | --- |
| けだし→蓋し | 23 | 0 | 22 | 蓋し（rongo0727-1 等） |
| いずくんぞ→焉くんぞ | 52 | 0 | 31 | 焉くんぞ（izukunei-1 等） |
| もし→如し | 46 | 0 | 22 | 如し（moshisono-1 等） |
| それ→夫れ | 72 | 0 | 45 | 夫れ（ishiwoidaki-1 等） |
| ただ→惟だ | 25 | 0 | 14 | 惟だ/惟れ（ryoyaku-3 等） |
| なかれ→毋かれ | 96 | 0 | 10 | 毋かれ/毋く/毋し（onoreshika-2 等） |

其中 いずくんぞ→焉 与 なかれ→勿 是 **D14 当年拒绝的候选**——拒绝原因是裸字替换
+ 当时的变差（5/19、1/8）；本夜按 exp 真实词形（焉くんぞ / 毋かれ）+ 白文护栏复核，
见 §3 模拟结果。补一句如实的话：那两条的变差行当时就是 exp 混写问题，本夜翻案靠的是
「词形对了 + 护栏分工」两个条件同时成立，不是数据变了。

## 3. 离线模拟（tools/night64_sim.py，基线 night60 全链 3998 条，逐条真算 Levenshtein）

| 候选 | 改写行 | Δ | 改善 / 变差 | 结论 |
| --- | --- | --- | --- | --- |
| SHINJITAI 99 对 | 545 | -0.117 | 406 / **0** | 收 |
| けだし→蓋し（白文含蓋） | 22 | -0.011 | 22 / **0** | 收 |
| いずくんぞ→焉くんぞ（白文含焉） | 31 | -0.019 | 31 / **0** | 收（D14 拒案翻案） |
| もし→如し（白文含如） | 22 | -0.003 | 13 / **0** | 收 |
| それ→夫れ（白文含夫） | 45 | -0.011 | 41 / **0** | 收（H 只 分工之后） |
| ただ→惟だ（白文含惟） | 14 | -0.004 | 14 / **0** | 收（E 唯 分工之后） |
| なかれ→毋かれ（白文含毋） | 10 | -0.005 | 10 / **0** | 收（D14 拒案翻案） |
| **组合（kana 6 条 + SHINJITAI）** | **656** | **-0.170** | **514 / 0** | **上线** |

SHINJITAI 的 0 变差有结构性保证（exp 全库无旧形 ⇒ 映射后的对齐代价只会持平或下降），
kana 六条是逐条真算出来的。**任务书「≥3 个候选」实际模拟了 7 个，全部 0 变差**——
没有一条触发「变差>0 一律不上线」的否决门，**本夜没有拒绝的候选**（拒绝的只有
§1 解剖阶段就没进候选的：结构差异假名串、のみ、零命中 kana、exp 写旧形的 3 对字）。
幂等：显式两遍法 3998/3998 坏 0。

## 4. 上线（backend/kundoku_rules.py，本夜唯一生产代码改动）

- **Rule I**（`I_KANA_TO_KANJI` 6 条 + `I_LONGER_WORDS` + `style_kana_to_kanji_i`），
  接入 `style_fix_with_hakubun`，链序在 Rule H 之后（F→G→H→I；それ 的 只/夫、
  ただ 的 唯/惟 按白文分工，互不越位）。护栏与 E/F/G/H 同构：白文无对应汉字一个都不动。
- **SHINJITAI_MAP +99 对**：147 → **246 对**（含 寳 U+5BF3 异体码位先例同款的
  荆→荊 变体归一；每对 exp 新形 ≥1 次核验过）。
- **一个测试阶段发现（如实）**：`なかれ` 的长词条目（ことなかれ/することなかれ）是
  **死条目**——它们是「なかれ」的**后缀**重叠，`tail.startswith` 前缀护栏保护不到
  （写进去也不生效）。实测行为 = なかれ 一律转换（ことなかれ→こと毋かれ），而模拟里
  10 个护栏行**全部改善 0 变差**（exp 在这些行写 毋く/毋し，な→毋 方向正确）→
  删掉死条目、注释里写明机制、测试锁定「なかれ 不在 I_LONGER_WORDS」。这与
  D14 教训「长词表必须显式更长词清单」互补：**前缀重叠才需要长词条目，后缀重叠不需要**。
- 上线代码总 diff：+1 个规则函数 +1 张表 +1 张长词表 + 99 对映射，其余一字未动。

## 5. 真机验证（tools/night64_eval_4000.py + tools/night64_compare.py）

- **真机全量 4000 条**（TestClient 完整后端链，monkeypatch save_kundoku 避 D 盘 fsync）：
  3998 OK / 2 error（toushisen135-12、toushisen043-16，仍是 N59 定性的 AUX 活用表缺應，
  规则层不可修，维持拍板 ⑬ 现状）/ **avgDist 13.719** / 精确 **24**/3998。
- 分档全部下降：≤20字 7.84→7.74、21-40字 21.742→21.476、41-60字 37.162→36.692、
  >60字 63.845→63.143。
- **确定性对照：全 4000 条 vs night60 归档不同行数 = 656，恰等于模拟改写行数**。
- **逐位对照（eval/night64_compare.txt）**：
  1. 模拟改写 656 行：真机输出 vs 模拟预测文本 逐位不符 **0**；
  2. 未触及 3342 行：真机输出 vs night60 归档 逐位不符 **0**；
  3. 改写行 dist：改善 514 / 变差 **0** / 持平 142（与模拟完全一致）；
  4. 全库 avgDist 13.889→13.719（Δ **-0.170**，与模拟 -0.170 一致）；
  5. 精确 19→24；丢失 0。
  —— **第五次「API=离线真函数」逐位等价**（N30/N57/N60/N58 之后）。
- **真机幂等**：656 改写行原样重投 API，输出与归档逐位不符 **0**。
- **精确 +5 的构成**：kokyo03-6 / kokyo04-8 / kokyo05-8（蓋し，孝経三连）、
  kokyo08-10（夫れ）、toushisen173-6（爐→炉）。如实注明：exact 口径是空白剥除后
  逐字相等（N22 以来全部口径一致），toushisen173-6 视觉上仍差一个全角空格。

## 6. 测试（tests/test_night64_rule_i.py，18 条）

护栏转换 / 无护栏跳过 / 长词跳过 / E・H 与 I 的白文分工链序 / 链幂等 / 空白文=纯函数语义 /
SHINJITAI 99 对抽查 + 幂等 + 目标∩旧键=无 / 语料外现代和文探针（それいいじゃん・
ただいま・もしもし・ことなかれ主義・けだもの 一字不动）/ 经典句不回归 /
表结构 wellformed。pytest **193 → 211 passed**。

如实记录测试阶段纠错：18 条测试首跑 3 处失败，**全部是测试期望值写错**（ひ→い 活用
不属于 Rule I、ただ 测试句抄 exp 带了 のみ、以及 ことなかれ「保护」断言暴露死条目问题），
其中第 3 处促成了 §4 的死条目发现与删除；没有改生产代码迁就测试。

## 7. GT CER 门（OCR 侧不变证据）

`tools/night49_gt_run.py --out eval/night64_gt_lines.json` + `tools/eval_ocr_gt.py`
（CER 输出显式落 eval/night64_gt_cer.json，不覆盖跟踪文件）：8 页 92 行，
**raw micro 0.3568 / norm micro 0.3053——与 N49 以来基线逐位一致**。
本夜零 OCR 代码改动，GT 门验证的是「显示层规则上线不越界」。

## 8. 验收门

提交前 `tools/accept_night.py 64`：pytest / rule_regression / engine_smoke /
perf_envelope / order_rate **PASS**，eval_integrity **skip**（NIGHT_ARTIFACTS 未登记 64
——登记 golden_3000/4000 归档属于既有拍板 ⑨/⑭，不越权），repo_clean **FAIL**
（门如实报未提交改动——与 Night 22 同款行为，提交后终跑见 ACCEPT_LOG.md 终态）。

## 9. 不作为候选 / 负结果（如实）

- 活用・句法结构差异的假名串（して 1947 / なりて 552 / ひて 297 / するを 258 /
  へて 181 / せず / みて …）：Night 24/25 已定性「逐页编辑习惯 + 语法层面差异，
  规则层不可分」，本夜维持不做。它们是剩余 dist 的大头，不是矿脉是岩层。
- のみ：exp 96 > got 86，kanbun.info 自己写 のみ，非候选。
- すなわち / なほ / ゆゑに：引擎输出 0 次（すなわち 假说被证伪——引擎写的是
  卽→即 的旧形缺口，由 SHINJITAI 批量覆盖）。
- SHINJITAI 拒绝：冰→氷 / 弦→絃 / 亦→又（exp 自身写旧形 2/2/105 次）——与 N58 同判据。
- 戾 / 襢 / 鑒 / 皋：计数判据命中但无可靠目标形（exp 无对应写法或标准形有歧义），
  不收。
- ことなかれ→莫かれ：N58 已拒（11 变差，exp 混写 莫かれ/莫し/莫き），维持拒绝。

## 10. 任务书执行偏差（全部如实）

1. **D:\kanbun-rulei 不存在**：按 kanbun-eval10k 先例 clone 主仓新建 + 分支
   night64-rulei（b370761 起）。若用户本意是别的目录，本分支整体可 cherry-pick/rebase。
2. **clone 缺 ocr_runtime**：从主仓拷回构建产物（不入库，.gitignore 管着）。
3. **SHIFT_LOG.md 未追加**：不在任务书允许路径清单内（kundoku_rules.py + tests +
   工具脚本 + 本报告），故未动；如需补记可由用户点头后追加。
4. **ROADMAP.md 未动**：N64 不是 ROADMAP 行，Night 61-63 保持原状。
5. **accept_night.py 未登记 NIGHT_ARTIFACTS[64]**：同 ⑨/⑭ 拍板边界。

## 11. 待拍板（不新增改代码类，只补观察）

- N54 ④-⑧、N55 ①-③、N57 ⑨、N58 ⑩（已否决结案）/⑬、N60 ⑭⑮ 原样保留。
- **⑯（观察，N60 ⑮ 的印证）**：本夜 Rule I 六条里五条的主战场在故事/論語长句段，
  新增段（漢詩短句）只贡献 5 行改写（けだし 1 + ただ 4）+ SHINJITAI 的一部分——
  评测集偏科再次实证：继续挖长句档需要歴代散文/赋类语料（⑮ 的扩 5000 提案）。
- **⑰（新）**：ことなかれ 88 处、うべきか 22 处等「N55/N58 已拒机制」的残余，
  是否接受「只改与 exp 词形完全一致的子集」类半护栏规则，属产品层拍板（本夜未做）。

## 12. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
cd /d D:\kanbun-rulei
set PYTHONIOENCODING=utf-8
:: 解剖 → 取证 → 模拟（全部只读 eval，输出 night64_*.json/txt）
python tools\night64_mine.py
python tools\night64_probe.py
python tools\night64_sim.py
:: 上线后：真机全量 + 逐位对照 + 幂等复投
python -X utf8 tools\night64_eval_4000.py
python -X utf8 tools\night64_compare.py
python tools\night64_exact_rows.py
:: GT 门
python -X utf8 tools\night49_gt_run.py --out eval\night64_gt_lines.json
python -X utf8 tools\eval_ocr_gt.py eval\night64_gt_lines.json eval\night64_gt_cer.json
:: 测试 + 验收门
python -m pytest tests -q
python tools\accept_night.py 64
```

## 13. 禁止事项自查

expected 一字未改（golden_4000 前缀锁测试 + 3998 行 expected 与 night60 归档逐位一致 +
验收门 eval_integrity 对 golden.json 全查）；没有为提分删规则或动评测数据；
eval/golden*.json、OCR 生产代码、前端**零改动**（改动面 = backend/kundoku_rules.py、
tests/test_night64_rule_i.py、tools/night64_*.py 共 7 个脚本、eval/night64_* 产物、本报告）；
无 key/token/凭据；本地提交在当前分支 night64-rulei，不合 master、不推远程。
