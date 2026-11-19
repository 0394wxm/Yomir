# REPORT_DAY11.md — D11：规则挖掘 Rule D（これ→之）（2026-11-19）

任务单：白天清单第 4 项（按 Night 22 方法论：解剖 → 离线模拟 ≥3 条候选 → 真机 → 门 + pytest 锁定；
变差 >0 的一律不上线，只上线 0 变差带护栏的那一条）。

起点 `4117d1c`，分支 `ds/dayshift-text-mining`。评测集用 D10 的 1000 条。

**结果：Rule D（これ→之，白文「之」护栏）上线。1000 条 avgDist 26.090 → 25.201（-0.889），
改善 282 / 变差 0 / 精确 3，真机与离线模拟逐位一致，pytest 33 → 41 passed，既有约定全 PASS。**

---

## 1. 数据解剖（1000 条，`tools/day11_mine.py` → `eval/day11_mine.json`）

字符级 diff 的高频片段（输出有、expected 没有）：

| 片段 | 处数 |
| --- | --- |
| は | 661 |
| の | 519 |
| す | 101 |
| に | 66 |
| なる | 60 |
| これ | —（见下，作为整体替换对出现） |

替换对 top：

| got | exp | 次数 |
| --- | --- | --- |
| **これ** | **之** | **180（单字级对齐；整词口径 292 条）** |
| は | 、 | 232（方向不一致，弃） |
| を | に | 188（变差 586，弃） |
| へ | え | 90（改善 80 / 变差 0） |
| ひ | い | 65（改善 74 / 变差 0） |

**「これ→之」是唯一同时满足「高频 + 方向一致 + 0 变差」的候选。**

## 2. 关键发现：expected 里「これ」出现 0 次

`tools/day11_kore2.py` 的统计：

| 量 | 值 |
| --- | --- |
| expected 里「之」的总处数 | **522** |
| 引擎输出里「これ」的总处数 | **527** |
| expected 里「これ」的总处数 | **0** |
| 输出「これ」数 == expected「之」数的条目 | **934 / 1000（93.4%）** |

522 vs 527——几乎完全对应。这不是「日语该怎么写」的模糊问题，而是**引擎把汉文助词「之」
一律训读为假名「これ」**的系统性偏差；kanbun.info 的规范書き下し写「之」。
**「わが国語表記の揺れ」ではなく、単純な字面の統一。**

## 3. 离线模拟（同一把尺子：剥空白后编辑距离）

`tools/day11_sim.py`（eval/day11_sim.json）：

| 候选 | 改写 | avgDist | Δ | 改善/变差 | 判定 |
| --- | --- | --- | --- | --- | --- |
| D0 基线 | 0 | 26.090 | — | — | — |
| D1 全替换 | 292 | **25.201** | **-0.889** | **282 / 0** | 收益最大 |
| D2 排除副词（これい/ゆ） | 286 | 25.218 | -0.872 | 276 / 0 | — |
| D3 非句首 | 290 | 25.205 | -0.885 | 280 / 0 | — |
| D4 助词限定（をにがのはと） | 269 | 25.242 | -0.848 | 266 / 0 | — |
| D5 非标点后 | 250 | 25.443 | -0.647 | 241 / 0 | — |

`tools/day11_pick3b.py` 枚举了 6 类护栏元素的 **64 种组合**：**全部 0 变差**（因为语料内
没有一处「これ」需要保留）。

## 4. 失败的护栏尝试（如实记录）

**第一次尝试（D7/D8，语义护栏）失败**：按「これ＋見/言/思」「これ＋より/まで/から」
「これ＋ぞ/こそ/のみ」设计护栏，结果：

- 只改写 135–139 条（护栏过宽，把「これを飲す」「これを誉めて」也挡住了）
- 仍有 **1 条变差**（keiko-1，110→111）

**根因诊断**（`tools/day11_diag.py`）：keiko-1 输出里有 3 个「これ」，expected 里只有 1 个「之」（位置 188）。
逐位置测试：

| 只替换第 k 个 | 编辑距离 |
| --- | --- |
| 第 1 个（位置 31） | 111（+1） |
| 第 2 个（位置 47） | 110（持平） |
| 第 3 个（位置 189） | **108（-2）** |
| 全替换 | 109（-1） |

也就是说，这条句子里**只有第 3 个「これ」对应真正的「之」**，前两个是引擎在有歧义的句子里
额外生成的。语义护栏挡掉了一部分真「之」又留下了假「これ」，所以净效果反而变差。

**还抓到一个实现 bug**：`day11_pick2.py` 的护栏实现用过 sentinel 占位但没正确恢复，
和 `day11_final.py` 对同一条 keiko-1 给出不同结果。用 `tools/day11_check_bug.py`
逐条核对后确认 **D1 全替换在 1000 条上确实是 0 变差**——之前那个「1 条变差」是实现错误。

**这是一条重要教训：护栏的正确性必须用「逐条核对」验证，不能只看汇总数字。**

## 5. 最终护栏设计：白文「之」判据

任务书要求「0 变差**带护栏**」，而语义护栏在 keiko-1 上就是挡错了。改用**白文（输入）判据**：

> 白文里含「之」才做替换；白文里没有「之」，一个「これ」都不动。

`tools/day11_align2.py` 的交叉表验证（1000 条）：

| 白文有「之」 | 输出有「これ」 | 条目数 |
| --- | --- | --- |
| 否 | 否 | 514 |
| 是 | 否 | 194 |
| 是 | 是 | **292** |
| **否** | **是** | **0** |

- 语料内**零成本**：护栏从不触发误挡，结果与 D1 全替换完全相同（-0.889 / 0 变差）
- 语料外**真的能挡**：像「これを見よ」这种白文没有「之」的现代和文，一个「これ」都不会被改

**这满足「0 变差 + 带护栏」两个条件，且护栏依据是可验证的数据而不是猜的语义清单。**

## 6. 上线（`backend/kundoku_rules.py` + `backend/main.py`）

```python
def style_kore_to_shi(text: str, hakubun: str = "") -> str:
    if hakubun and "之" not in hakubun:   # 护栏
        return text
    return text.replace("これ", "之")

def style_fix_with_hakubun(text: str, hakubun: str) -> str:
    t = style_modern_kana(text)
    t = style_drop_wa_before_iwaku(t)
    t = style_dedup_shite_soshite_guarded(t)
    t = style_kore_to_shi(t, hakubun)
    return t
```

`backend/main.py:280` 从 `style_fix(kakikudashi)` 改为 `style_fix_with_hakubun(kakikudashi, text)`——
必须传白文才能做护栏判定。旧入口 `style_fix` **保留且行为不变**（供 pytest / 验收门 / guwenbert 脚本
按原有语义调用），Rule D 只在带白文的入口生效。

节流位置：`style` 段（NIGHT22 起就在此处），实测量级 <1ms，对 66 秒的 1000 条无影响。

## 7. 真机验证

`tools/day11_live.py`（真实 TestClient + 完整后端路径，结果 `eval/day11_results_1000.json`）：

```
engine OK 1000 / error 0 | 精确 3/1000 | avgDist 25.201
  ≤20    n= 391 avgDist  10.12  精确 3
  21-40  n= 322 avgDist  21.74  精确 0
  41-60  n= 169 avgDist  37.51  精确 0
  >60    n= 118 avgDist  66.97  精确 0
```

**与离线模拟 25.201 逐位一致**（离线 `tools/day11_final.py`/`day11_align2.py` 都是 25.201）。

对照 D10 基线 26.090：

| 分档 | 基线 | Rule D 后 | Δ |
| --- | --- | --- | --- |
| ≤20字 | 10.41 | 10.12 | -0.29 |
| 21-40字 | 22.48 | 21.74 | -0.74 |
| 41-60字 | 38.89 | **37.51** | **-1.38** |
| >60字 | 69.57 | **69.57→66.97** | **-2.60** |

收益仍然随句长增大——与 Night 22 的模式一致（长文里「之」出现更多）。

## 8. pytest 锁定（33 → 41 passed）

新增 `tests/test_rule_d_kore.py` 8 例：

| 测试 | 锁什么 |
| --- | --- |
| `test_kore_replaced_when_hakubun_has_shi` | 白文有之 → 替换生效 |
| `test_kore_kept_when_hakubun_has_no_shi` | 白文无之 → **护栏不动** |
| `test_kore_all_occurrences_replaced` | 多个これ全部替换 |
| `test_kore_no_hakubun_means_no_guard` | 空白文按纯函数处理（离线脚本用） |
| `test_style_fix_with_hakubun_orders_rules` | 四规则顺序执行互不破坏 |
| `test_style_fix_with_hakubun_guard_from_real_hakubun` | 语料外安全网 |
| `test_style_fix_unchanged_for_rule_d` | 旧入口不受影响（NIGHT22 语义保持） |
| `test_classic_sentence_still_intact` | 经典句锁定 |

`python -m pytest tests -q` → **41 passed**（原 33 + 8）。

## 9. 验收门

`python tools/accept_night.py 35`（提交前）：

```
[FAIL] repo_clean   已跟踪文件有未提交改动：2 个   ← 即将提交的改动，行为正确
[PASS] pytest       15 passed
[SKIP] eval_integrity  Night 35 未登记评测归档
[PASS] rule_regression  Rule C' 护栏正常；ふ→う/は曰く 正常；正字化幂等；合并词表 21 条
[PASS] engine_smoke  6 项全部符合约定
[PASS] perf_envelope 短句中位 10ms
```

**Rule C' 护栏、经典句「王は左右を顧みて而して他を言う」、正字化、合并词表全部未被 D11 破坏。**

## 10. 未上线的候选（0 变差以外，如实记录）

| 候选 | Δ | 变差 | 不上线原因 |
| --- | --- | --- | --- |
| は→、 | — | 245 | 方向不一致（661 处多余里有 118 处缺失） |
| を→に | — | 586 | 大面积变差 |
| 削除「は」 | -0.77 | 141 | 变差过多，殊助詞不可一律删 |
| 削除「なる」 | -0.45 | 29 | 仍需词级判断 |
| へ→え | -0.10 | 0 | 收益太小（-0.10），不值得单独加规则 |
| ひ→い | -0.08 | 0 | 同上 |
| べ→可 | -0.16 | 7 | 有变差，不符合上线条件 |

**「へ→え」「ひ→い」是 0 变差但收益 <0.2 的，按任务书「变差>0 的一律不上线」它们可以通过，
但收益太小且需要单独的口径说明，本次不合并到 Rule D——留作下次候选。**

## 11. 交付物

| 文件 | 说明 |
| --- | --- |
| `backend/kundoku_rules.py` | 新增 `style_kore_to_shi` + `style_fix_with_hakubun`（+41 行） |
| `backend/main.py` | 调用点改为带白文入口（+5/-2 行） |
| `tests/test_rule_d_kore.py` | 8 个锁定测试 |
| `eval/day11_results_1000.json` | 真机 1000 条结果 |
| `eval/day11_mine.json` / `day11_sim.json` / `day11_kore.json` / `day11_align2.json` / `day11_final.json` | 解剖与模拟证据 |
| `tools/day11_*.py` | 解剖/模拟/诊断脚本 14 个（含两个失败版本，保留作证据） |

## 12. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
set "PYTHONIOENCODING=utf-8"
python tools\day11_mine.py          :: 字符级 diff 解剖
python tools\day11_sim.py           :: D0-D5 候选模拟
python tools\day11_align2.py        :: 白文护栏交叉表
python tools\day11_live.py          :: 真机 1000 条（约 66s）
python -m pytest tests -q           :: 41 passed
python tools\accept_night.py 35     :: 验收门
```

## 13. 禁止事项自查

- expected 一字未改（`day11_live.py` 只读 golden_1000 的 expected）
- 变差 >0 的候选全部拒之门外（§10 逐条列出）；只上线 0 变差 + 白文护栏的 D1 变体
- 两个失败的护栏实现（D7/D8 语义护栏、pick2 的 sentinel bug）**保留在 tools/ 里并入档**，没删
- 未碰 `eval/ocr_gt_*`、`REPORT_NIGHT36/37/38.md`、`backend/ocr*.py`、`ocr_runtime/`、
  `eval/golden.json`、已有评测归档、Night 9/16-20、KuroNet、定价、部署
- 全程未发图、未读图、未打开任何图片文件
- 只本地提交到 `ds/dayshift-text-mining`，未推远程，未动 master
