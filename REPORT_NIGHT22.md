# REPORT_NIGHT22.md — Night 22：「而して」去留判别与 Rule C'（带护栏复活）（2026-11-18 夜）

按 ROADMAP.md 授权（准确率深水区 Night 21–35，阶段第一夜 Night 21 已写细；本夜由当晚 agent
按同一授权写细）+ REPORT_DAY9.md §5.3 的指认（「当前最大的收益点不在换解析器，而在
『而して』的处理策略」）定为：**「而して」去留判别——数据解剖 → 候选规则离线模拟 → 有证据才上线**。

起点：`git log -1` = `ecf4413`；`pytest tests/test_api.py -q` = 15 passed。
本夜产线数字（先给结论）：**avgDist 27.02 → 26.21（-0.81），改善 107 / 变差 0 / 持平 393，
精确匹配 0/500 → 1/500**，经典句与全部既有约定无一破坏，pytest 33 passed，验收门 5/6 PASS
（repo_clean 待提交后终跑）。

---

## 1. 数据解剖（500 条，eval/night21_results_full.json，上线前生产线输出）

工具：`tools/night22_sodashite_scan.py`、`tools/night22_rule_sim.py`（本夜新写）。
四象限（输出含而して? × expected 含而して?）：

| expected 含 | expected 不含 | 合计 |
| --- | --- | --- |
| 输出含 | 8（引擎做对的） | 151（多余） |
| 输出不含 | 0 | 341 |

「expected 想要而引擎没给」为 **0 条**——引擎在而して上只有「多做」没有「漏做」。

**输出层前置字符分布**（256 处 而して，规则真正能看到的信号）：

| 前置字符 | 处数 | 其中 expected 需要 |
| --- | --- | --- |
| kana（て而して 为主） | 191 | **0** |
| punct（句首/分句首） | 50 | 8（keep 类全在这） |
| kanji | 13 | 0 |
| BOS | 2 | 1（gyofu-5「而鷸啄其肉」） |

白文层粗分类（首个而的前一字符）会严重误导：keep 类 8/8 在标点后、delete 类 81% 在汉字后，
但经典句「王顧左右而言他」（て前置、expected 保留而して）**不在 500 条归档里**（scan §5 无输出），
只有 pytest/验收门锁着它。**判别必须在输出层上下文做，护栏必须显式存在。**

## 2. 候选规则离线模拟（同一把尺子：剥空白后编辑距离，`tools/night22_rule_sim.py`）

| 规则 | 改写条数 | avgDist | delta | 改善/变差 | 备注 |
| --- | --- | --- | --- | --- | --- |
| R0 全删（上限参照） | 159（含 8 条 keep） | 26.13 | -0.89 | 134/17 | 8 条 keep 全变差 +2~3；语料外必坏经典句 |
| **R1 汉字前置删+护栏** | 13 | 27.04 | **+0.01** | 1/5 | **假设被否决**：kanji 前置仅 13 处且多在已坏句里，删了不涨反跌 |
| R2 汉字前置删无护栏 | 13 | 27.04 | +0.01 | 1/5 | 同上 |
| **R3 て而して→て + 顧み护栏** | 110（keep 0 条） | **26.21** | **-0.81** | **107/0** | **上线候选** |

R1 的否决是本夜最有价值的负结果：DAY9 §5.3 原设想「按词性区分接续助词与副詞」，但表面层面
kanji 前置的 13 处里删 而して 是 1 改善 5 变差——**那 13 处的编辑距离坏点不在而して上**。
不先模拟就上线就是倒退。真正的大头是 191 处 kana 前置（其中 て而して 形态占比最高：
して 73 / りて 44 / みて 15 / びて 7…），全部多余。

## 3. 上线决策：R3 = Rule C'（Night 5 Rule C 的带护栏复活）

历史链条：Night 5 Rule C（て而して→て，200 条 26/26 方向一致）→ Night 7 撤销（唯一反例
「顧みて而して他を言う」，pytest test_kundoku_classic 抓出）→ **Night 22：500 条上
191 处 て而して 逐条核对无一需要它（107 改善/0 变差），反例仍然只有经典句一个 → 加显式护栏复活**。

实现（`backend/kundoku_rules.py`）：

```python
def style_dedup_shite_soshite_guarded(text):        # Rule C'
    return re.sub(r"(?<!顧み)て而して", "て", text)
```

- 接入 `style_fix`（ふ→う → は曰く → Rule C'）；
- 无护栏旧函数 `style_dedup_shite_soshite` 原样存档（注释标注「已撤销，不要启用」）；
- 护栏 = て 的前 2 字是「顧み」时保留——覆盖经典句；语料内足迹审计：500 条输出里
  「顧みて而して」0 处（护栏在语料内零成本），语料外保护经典句；
- 范围刻意只到「て而して」：に/は/より 等 kana 前置 8 处、punct 前置 42 处、BOS 1 处
  一律不动（R3 与 R0 的 -0.08 差距即此，剩余空间需要词级判断，本夜不做）。

## 4. 真机验证（不是只靠模拟）

- **500 条真机复跑**（起 uvicorn :8000 → `tools/run_eval.py night22_results_full.json`）：
  avgDist 26.21，改善 107 / 变差 0 / 持平 393，**与离线模拟逐项一致**（对照表
  `tools/night22_compare.py` 输出）。分档：≤20 字 -0.41（27/0）、20-40 -0.88（33/0）、
  >40 -1.30（47/0）——长句档仍是大头。
- **精确匹配 0/500 → 1/500**：`kantanayu-3`「直匍匐而歸耳。」→「直に匍匐して帰るのみ。」
  （此前 v4/guwenbert 的唯一精确命中是另一条 kiyu-4；规则引擎自己是第一次有精确命中）。
- **pytest 33 passed**（原 25 + 本夜 `tests/test_sodashite_guard.py` 8 例）：
  て而して删 / して而して删 / 顧みて而して留 / に前置留 / 句首留 / ふ→う共存 / 同句混合 /
  孤立而して不变。既有 test_kundoku_classic 原样通过。
- **验收门**（`tools/accept_night.py 22`，本夜把 4a 语义更新为「护栏处留 + 无护栏处删」双断言、
  归档登记 night22_results_full.json）：pytest/eval_integrity/rule_regression/engine_smoke/
  perf_envelope 全 PASS，repo_clean 在提交前 FAIL（门如实报未提交改动——行为正确），
  提交后终跑见 ACCEPT_LOG.md。
- 门更新过程中自抓到一个错误：4a 期望串写成「見てと思ふ」漏算 ふ→う（应为「見て思う」），
  与本夜单测首跑同一个坑，两处都已改正并留注释。

## 5. 与 guwenbert 路线的对照（DAY9 数字，不动）

DAY9 的结论「guwenbert 不接后端」（-1.06 / 100 倍延迟）保持不变；本夜用一条显示层规则拿到
-0.81，相当于换解析器收益（-1.06）的 76%，而成本是 0 延迟、1 行正则 + 1 个护栏。
DAY9 §5.3 说「这需要词性/句法信息，正好是 guwenbert 能提供的」——本夜证明**先到这一步
不需要**：输出层前置字符这个表面信号已经把 191/191 分对了（护栏保护唯一已知反例）。

## 6. 局限与风险（如实）

1. **护栏是词级的单点**：只保护「顧み」。语料外若有其它「Xみて而して」构造（含むて/恨みて等）
   的规范训读保留而して，会被本规则误删。语料内（500 条）0 反例；发现即把该词加进护栏
   （改一处正则）。
2. **punct 前置的 42 处多余而して未动**（8 处需要的也在这类里，表面信号分不开），
   剩余上限约 -0.08~-0.3；要吃掉需要句法信息，留给后续夜。
3. 编辑距离改善≠用户可读性必然提升（删掉的多余而して绝大多数确实是 kanbun.info 不写的，
   但个别句可能另有别的错处）。107 条改善里 dist 下降 ≥7 的有 8 条（kyusu-1 +17、
   iaritake-1 +11、kamotorite-1 +11 等）。
4. 行级缓存（Night 7）按白文缓存引擎结果、style_fix 在其后每次执行——缓存不受影响，
   已由真机评测（走缓存路径）验证。

## 7. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night22_sodashite_scan.py    :: 数据解剖 → eval/night22_sodashite_scan.json
python -I tools\night22_rule_sim.py          :: R0/R1/R2/R3 离线模拟
python -m pytest tests -q                    :: 33 passed
:: 起后端：python -X utf8 -m uvicorn backend.main:app --port 8000
python -X utf8 -I tools\run_eval.py night22_results_full.json   :: 真机 500 条
python -I tools\night22_compare.py           :: 上线前后对比 + 护栏足迹
python tools\accept_night.py 22              :: 验收门
```

## 8. 禁止事项自查

expected 未改一字（验收门 eval_integrity 对 night22 归档做了逐条 expected 比对 + golden 全查）；
没有为提分删规则——规则上线走的是「解剖→模拟→真机复跑→门+pytest 锁定」全链路，R1 负结果如实
入档；经典句/护栏由 pytest 3 处 + 验收门 4a 双断言 + 引擎冒烟三重锁定；无 key/token；只本地提交。
