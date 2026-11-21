# REPORT_NIGHT68

## 0. 一句话结论

Rule J（かな→漢字第 6 批）收录 **7 条**（ごとし族 6 条按白文 若/如 分目标＋まさに→方に）＋
**SHINJITAI 29 对**（246→275），组合 **283 行改写／改善 234／变差 0**／幂等坏 0，模拟与真机逐位一致；
拒 7 条（べき・べから・もし・なんぞ＋预拒复核 なかれ・ことなく・がため），全部 0 变差门不过，如实归档。
golden_4000 avgDist **13.716→13.684**／exact 24／error 0；golden_8165 avgDist **14.741→14.698**／exact 30／error 0。
GT CER raw **0.3568**／norm **0.3053** 逐位不变。pytest **219→241**。guwenbert 本夜未跑（原因见 §7）。

## 1. 开工核对

- HEAD = `3805a1b`（= origin/master，ahead 0）✓；tracked 零改动；pytest **219 passed**（13.2s）✓
- SHIFT_LOG 开工心跳已补写（本夜首行），byte807=**243** ✓
- 方法论输入：REPORT_NIGHT64.md（Rule I 全流程）＋ REPORT_DAY14.md 拒案表（331 行附近）；
  なかれ→毋（I）・いずくんぞ→焉くんぞ（I）・また→亦た（F）已上线不再列

## 2. Rule J：挖词（②）→ 模拟门（③）→ 上线（④）

### 2.1 基线与工具

- 挖词基线 = `eval/night67_results_8165.json`（8165 条 0 error，与 HEAD 引擎状态完全一致——
  **②复用归档不重跑**，等价且省两次全量；与 3805a1b 引擎等价性由 results/golden 同序断言保证）
- `tools/night68_mine.py`（→ `eval/night68_mine.json/.txt`）：四切面字符/假名 delta
  （shibu02 1310 行／[4000:7908) 3908／paren 257／全库）
- `tools/night68_probe.py`（→ `eval/night68_probe.json/.txt`）：逐词取证
- `tools/night68_sim.py`（→ `eval/night68_sim.json/.txt`＋`night68_combo_changed_rows.json`）：
  离线模拟 0 变差裁决

### 2.2 候选清单（J1-J11＋预拒 R1-R3＋SHINJITAI 29，全文见 eval/night68_candidates.txt）

B 切面假名 delta 真信号：**のごとし（全 80）／がため（71）**；隐蔽词第二轮扫描发现
**まさに got 23 / exp 同形 0**（kanbun.info 白文把「將(まさに)」写作「方」——23 行白文全含方）
与 **なんぞ got 24 / exp 同形 0**（exp 目标 奚ぞ/奚んぞ/盍ぞ/曷ぞ/何ぞ 混）。

### 2.3 模拟门裁决（全 8165，逐行证据见 eval/night68_sim.txt）

**收录 7 条（全 0 变差）**：

| 规则 | 护栏 | 改写 | Δ | 改善/变差/持平 |
|---|---|---|---|---|
| まさに→方に | 白文含方 | 23 | −0.004 | 22/0/1 |
| ごとし→若し | 白文含若 | 49 | −0.011 | 47/0/2 |
| ごとく→若く | 白文含若 | 42 | −0.006 | 32/0/6 |
| ごとき→若く | 白文含若 | 17 | −0.004 | 16/0/1 |
| ごとし→如し | 白文含如 | 5 | −0.000 | 4/0/1 |
| ごとく→如く | 白文含如 | 6 | −0.001 | 6/0/0 |
| ごとき→如き | 白文含如 | 3 | −0.000 | 3/0/0 |

**SHINJITAI 29 对**：改写 158 行／改善 123／**变差 0**（−0.018）。

**组合**：configA(如先) 283 行/−0.042/234 改善/0 变差；**configB(若先) 283 行/−0.043/234 改善/0 变差/幂等坏 0**
——选 **configB**（Δ 略优，且若枝是本夜主矿脉；両有行两序皆 0 变差，取 Δ 优者）。

### 2.4 上线实现（backend/kundoku_rules.py）

- `J_KANA_TO_KANJI`（7 条）＝模拟 configB 顺序逐位一致：まさに→方に → 若枝×3 → 如枝×3
  （组合 sim 的实际顺序 = others(まさに) + jos + nyos，実装与之一致）
- `J_LONGER_WORDS`：仅 まさに。**ことごとく/ことごとし/ことごとき 是 kana 的前缀重叠**
  （kana 是更长词的后缀）——tail.startswith 前缀护栏保护不到，写进去就是死条目；
  N64 なかれ 教训在本次实测复现，**不登记**（当前语料 got 侧 ことごと* = 0 次，
  night68_probe.py 核验，无评分风险；后缀护栏机制列移交项 §8）
- `style_kana_to_kanji_j`（E-I 同构：护栏＋长词掩码）＋ `style_fix_with_hakubun` 链尾接 J（I 之后）
- `SHINJITAI_MAP` +29 对（Night 68 注释：来源/判据/票噪修正 2 对/拒绝清单）
- 拒案 4 条写入代码注释，与 eval/night68_sim.txt 逐行证据互为索引

## 3. SHINJITAI 29 对（第二遍计数判据）

判据 = exp 全库写旧形 0 次 & got ≥2 次 & 等长块多数票（第二遍计数）& exp 新形 ≥1 次；
主力来自 8165 全量（擊/歡/虛/壘/筭/徃/吳…，N64 的 4000 挖不到的子部长句段旧形）。

- **票噪修正 2 对（行级证据裁决，拒票记档）**：區→区（montai13-10 got 區區/exp 区区 直接对位，
  多数票错取「別」）；鬭→闘（mokkei-1・toushisen192-2 exp 闘 直接对位，多数票错取「養」）
- 结构性 0 变差保证与 N64 相同（exp 旧形全库 0 次 ⇒ 映射只会持平或下降），仍逐行真算验证
- 拒绝：霸→覇（exp 自写旧形 1 次）、陳→陣（exp 写陳 39 次，非同字）、冰→氷/弦→絃/亦→又/烟→煙/遲→遅
  （exp 自身写旧形）——与 N58/N64 同判据

## 4. 实跑（⑤ TestClient 完整后端链 + monkeypatch save_kundoku + 确定性对照）

### 4.1 golden_4000（tools/night68_eval_4000.py → eval/night68_results_4000.json/.txt）

- **avgDist 13.684**（N67 13.716，Δ −0.032）／exact **24**（不变）／error **0**（不变）
- 确定性对照 vs night67_results_4000.json：改写 **97 行 = 模拟预测 97**（双向 0：预测有实跑无 0、
  实跑有预测无 0）／**改善 79 / 变差 0 / 持平 18**；error→恢复 0、仍 error 0

### 4.2 golden_8165（tools/night68_eval_8165.py → eval/night68_results_8165.json/.txt）

- **avgDist 14.698**（N67 14.741，Δ −0.043，与模拟一字不差）／exact **30**（不变）／error **0**（不变）
- 确定性对照 vs night67_results_8165.json：改写 **283 行 = 模拟预测 283**（双向 0）／
  **改善 234 / 变差 0 / 持平 49**（＝模拟 234/0/49 逐位一致）；error→恢复 0、仍 error 0
- ⑯ **偏科分档**：shibu02 长句段（avgDist 31.956，全库最肥）改写 119／**改善 106**／变差 0／持平 13；
  漢詩短句段（漢詩×≤20字）改写 76／**改善 53**／变差 0／持平 23——长句段与短句段双主战场，
  本夜与 N64「主力在长句段」不同：ごとし族在漢詩段（若枝）与 shibu02（子部长句）两头收

### 4.3 GT CER 门（night49_gt_run.py --out eval/night68_gt_lines.json + eval_ocr_gt.py）

- **raw micro 0.3568 / norm micro 0.3053** —— 与 N64 §7 冻结值逐位不变 ✓
  （输出落 eval/night68_gt_cer.json，未覆盖冻结归档）

## 5. 拒案表（0 变差硬门，模拟门逐行证据）

| 候选 | 改写 | 改善/变差 | 拒因（一句话） | 变差样例 |
|---|---|---|---|---|
| べき→可き | 103 | 86/**6** | exp 自写假名 べき 行被搅动 | sanennosho-7「相狎るべき有り」5→6 |
| べから→可から | 158 | 145/**5** | exp 自写 べからず/べからざる 假名行被搅动 | shushu-4「得べからずして」11→12 |
| もし→若し | 55 | 34/**1** | kyugyu-2 的 exp 若し 在句尾，与 got 位置漂移 | kyugyu-2 67→68 |
| なんぞ→何ぞ | 18 | 14/**2** | exp 有 奚んぞ/曷んぞ 三字形，なんぞ3字→何ぞ2字反加距 | rongo0302-1（奚んぞ）、kouji-2（曷んぞ） |

**D14/N58 拒案表按真实词形重测（预拒复核，全部 0 变差门不过——拒案维持）**：

| 候选 | 改写 | 改善/变差 | 拒因 |
|---|---|---|---|
| なかれ→莫かれ | 84 | 67/**1** | exp 词形混写（莫し49/莫かれ21/莫き11/莫く6），kokyo09-5 exp 写「莫し」15→16 |
| ことなく→莫き | 19 | 12/**2** | exp 直接证据 0；toushisen065-8 exp 写「莫かれ」、roushi32-2 段落不写莫 |
| がため→が為に | 92 | 63/**2** | 80/92 行 exp 不写 為に（混写 為す48/為に12/為る6/為り6）；rongo0518-1・mitabitsu-1 |

**D14 复查结论**：なかれ→毋かれ（Rule I）、いずくんぞ→焉くんぞ（Rule I）、また→亦た（Rule F）
均已上线，不再列；**ごとし→如し（D14 当年拒：裸如 0 改写）本夜按真实词形复核翻案收录**——
改用「若」目标后 ごとし族成建制改善（若枝 108 行改写），是 D14 拒案表中唯一翻案。

## 6. README / verify / ROADMAP 同步（⑥）

- README.md：テスト行 219→**241 passed**；規則エンジン行 **13.716→13.684**／24/4000（N68 口径、
  `eval/night68_results_4000.json`）；ルールチェーン行追加 **Rule J（第 6 系列・7 語）**描述；
  另两处陈旧数字行同步（「テスト（214 条）」→241、「tests/ pytest 214 条」→241——N67 未及的数字行）
- tools/verify_readme_facts.py：Rule 计数行加 J（E/F/G/H/I/J = 5/4/4/3/6/**7**）；归档源行
  `night67_results_4000.json`→`night68_results_4000.json`——任务书写「仅 Rule J 计数行」，此处为
  verify 与 README 对得上的**最小必要同步**（N64→N67 源切换同款先例），如实声明此偏差；跑通 ✓
- ROADMAP.md：末尾追加 Rule J/SHINJITAI 上线一行（CLOSED 状态）

## 7. 验证汇总

- tests/test_night68_rule_j.py **22 passed**：每条规则正例＋无护栏反例（両無行保 exact）＋
  ことごと* 死条目实测锁定（後缀重叠＝前缀护栏不可达，N64 なかれ 教训复现并记录）＋
  両有行 configB 行为锁定＋I/J 分工链序＋链幂等＋SHINJITAI 29 对抽查/冲突性/幂等＋
  语料外现代和文探针（まさにその通り/ことごとく/それいいじゃん 一字不动）＋经典句不回归
- 全量 pytest **241 passed**（219＋22，12.8s）
- **guwenbert 本夜未跑**，原因：Rule J 无独立新增段（影响面＝ごとし系散布段＋SHINJITAI 行，
  已由 golden_8165 全量双对照逐位覆盖）；45 分钟预算线优先保障实跑与验收
- 组合幂等：模拟幂等坏 0；真机 diff 集合与模拟逐位一致（双向 0）——幂等在真机复现

## 8. 移交

1. **後缀护栏机制（新拍板项）**：ことごとく/ことごとし/ことごとき 是ごとく/ごとし/ごとき的前缀重叠，
   现有「更长词前缀掩码」机制不可达（死条目）。当前 got 侧 0 次无风险；将来语料若出现
   ことごと* 需先拍板「后缀护栏」机制再收录（本夜已实测并记录，不批量猜）
2. **なんぞ→奚んぞ/曷んぞ 按白文拆目标**：本夜単一目标 何ぞ 2 变差被拒；exp 词形 奚んぞ/曷んぞ
   与白文奚/曷一一对应，拆成两条护栏独立规则后有望 0 变差——下夜 Rule 候选（附
   eval/night68_sim.txt 逐行证据）
3. **べき/べから 结构性 gap**：exp 自写假名（相狎るべき/得べからずして）在 6/5 行真实存在，
   引擎按汉字化目标永远追不上——非规则问题，是 exp 侧混写（假名行/汉字行并存），
   除非按行判别（风险高），不建议再试单条 kana→漢字
4. もし→若し 位置漂移 1 变差（kyugyu-2 句尾）：若将来引入「词序感知」机制可重测（远期）

## 9. 禁止事项自查

- golden 数据 expected 一字未改 ✓；site-packages 一行未动 ✓
- 只动了允许清单内文件：backend/kundoku_rules.py、tests/test_night68_rule_j.py、
  tools/night68_mine/probe/sim/eval_4000/eval_8165.py、eval/night68_*（mine/probe/sim/candidates/
  combo/results_4000/results_8165/gt_lines/gt_cer）、README.md、tools/verify_readme_facts.py、
  ROADMAP.md、SHIFT_LOG.md、ACCEPT_LOG.md、eval/accept_night_68.json、REPORT_NIGHT68.md ✓
- 不进 D:\kanbun-eval10k / D:\kanbun-rulei ✓；550 保护性 untracked 零触碰 ✓
- SHIFT_LOG byte807=243（两次心跳后复查）✓；本地 master 两提交，**未推远程** ✓
- SHINJITAI 扩充逐对列出（29 对全量＋判据＋票噪修正 2 对＋拒票记档），无批量猜 ✓
