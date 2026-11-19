# REPORT_DAY2.md — 白天 D2：验收门复验（2026-11-19）

任务单：白天清单第 1 项（D2 验收门：写 `tools/accept_night.py`，6 项检查，JSON + exit 0/1，追加 `ACCEPT_LOG.md`，先跑 22 号回测再跑 35 号）。

起点：`git log -1` = `4117d1c night35: accept gate PASS (5/6 + 1 skip)`，`pytest tests -q` = **33 passed**。
工作分支：`ds/dayshift-text-mining`（全程只本地提交，未动 master）。

**结果：验收门已存在（上一班建成），本班做的是复验 + 修掉一个真 bug。最终 22 号 PASS 6/6、35 号 PASS 5/6+1 skip，自检 5/5。**

---

## 1. 现状核对：验收门本来就在

`tools/accept_night.py` 已由上一班（commit 见 REPORT_DAY2 旧版）交付，6 项检查齐全：

| # | 检查名 | 判定内容 |
| --- | --- | --- |
| 1 | `repo_clean` | 已跟踪文件无未提交改动（未跟踪只记 note） |
| 2 | `pytest` | `tests/test_api.py` 全过且 ≥14 条 |
| 3 | `eval_integrity` | 归档存在、id 唯一、自报数一致、expected 与 golden 逐条一致 |
| 4 | `rule_regression` | Rule C' 护栏、ふ→う、は曰く、正字化幂等、合并词表 21 条 |
| 5 | `engine_smoke` | 6 个真实 HTTP 请求（健康/经典句/合并/正字化/假名分流/空输入 400） |
| 6 | `perf_envelope` | 短句中位 < 3000ms |

所以本班的任务实际是**复验它还能不能用**，不是重写。

## 2. 第一次跑：22 PASS，35 FAIL（抓到真 bug）

`python tools/accept_night.py 22` → PASS（fail=0 skip=0，21.4s）。

紧接着 `python tools/accept_night.py 35` → **FAIL**：

```
[FAIL] repo_clean   已跟踪文件有未提交改动：2 个
        M ACCEPT_LOG.md
        M eval/accept_night_22.json
```

### 根因

**验收门自指**。`ACCEPT_LOG.md` 和 `eval/accept_night_*.json` 都是**受 git 跟踪**的文件，
而验收门每次运行都要写这两个东西。于是：

```
跑 22 号 → 验收门写 ACCEPT_LOG.md + accept_night_22.json（工作区变脏）
跑 35 号 → repo_clean 看到上一轮自己写的文件 → 判脏 → FAIL
```

上一班没暴露这个问题，因为每次跑完立刻 `git add` + commit，脏状态被清掉了。
本班按任务书「先跑 22 再跑 35」连跑两夜，bug 就现形了。

这是**上一班 D2 遗留的缺陷**，`REPORT_DAY2.md` §6 记录了当时修过一版自指错误
（未跟踪文件不算脏），但没覆盖「验收门自己写的是**已跟踪**文件」这种情况。

### 修法

`check_repo_clean` 增加一份「验收门自有产物」白名单，只排除两个精确模式：

- `ACCEPT_LOG.md`
- `eval/accept_night_*.json`

其余已跟踪改动照旧判 fail。排除项记入 `detail.gate_owned_changes` 并在 notes 里明示
「验收门自身产物有更新（不计脏）」，不是静默忽略。

改动 `tools/accept_night.py:99-122`，提交 `8c20507`。

### 为什么不放宽整个 repo_clean

如果把「已跟踪文件脏」整个降级成 note，验收门就抓不到「改了代码没提交」这个最核心的风险。
只白名单两个模式，爆炸半径最小。

## 3. 修复后复验

### 3.1 自检 5/5（确认没把检测能力改没）

`python tools/accept_selftest.py`：

```
[OK  ] Rule C 复活              verdict=FAIL  fail项=['rule_regression', 'engine_smoke']
[OK  ] 改 expected             verdict=FAIL  fail项=['eval_integrity']
[OK  ] 清空合并词表                 verdict=FAIL  fail项=['rule_regression', 'engine_smoke']
[OK  ] 归档重复 id                verdict=FAIL  fail项=['eval_integrity']
[OK  ] 已跟踪文件脏                 verdict=FAIL  fail项=['repo_clean']

5/5 个故障被正确抓到
```

「已跟踪文件脏」注入的是 `backend/main.py`（不在白名单里），仍被正确抓到。

### 3.2 Night 22 回测（PASS）

```
[PASS] repo_clean        验收门自身产物有更新（不计脏）：ACCEPT_LOG.md, eval/accept_night_22.json, eval/accept_night_35.json
                         已跟踪文件无改动
[PASS] pytest            15 passed（9.9s）
[PASS] eval_integrity    检查 1 个归档，id 唯一、自报数一致、expected 未改
[PASS] rule_regression   Rule C' 护栏正常；ふ→う/は曰く 正常；正字化幂等；合并词表 21 条
[PASS] engine_smoke      健康检查/经典句/合并/正字化/假名分流/空输入 全部符合约定
[PASS] perf_envelope     短句中位 11ms（包络 3000ms）

verdict: PASS  (fail=0 skip=0, 21.9s)
```

### 3.3 Night 35 回测（PASS，1 skip）

```
[PASS] repo_clean        已跟踪文件无改动
[PASS] pytest            15 passed（9.7s）
[SKIP] eval_integrity    Night 35 未登记评测归档文件，只查 golden.json
[PASS] rule_regression   Rule C' 护栏正常；ふ→う/は曰く 正常；正字化幂等；合并词表 21 条
[PASS] engine_smoke      6 项全部符合约定
[PASS] perf_envelope     短句中位 6ms（包络 3000ms）

verdict: PASS  (fail=0 skip=1, 20.6s)
```

`eval_integrity` 是 SKIP 不是 FAIL：`NIGHT_ARTIFACTS` 里没有 35 号的条目。
Night 35 的产物是 `eval/night35_glossary_coverage.json`（词库覆盖率统计，不是评测归档格式），
所以没有登记。**如实记录：这一项对 35 号没有检查力**，不是「过了」。

## 4. 关于 35 号回测的说明

和上一班 §4 一样的限制：验收门检查的是**今天**的代码，不是 Night 35 当天的代码。
35 号的 PASS 含义是「35 号声称的成果（词库命中率饱和的结论）没有被后续改动推翻，
且当前代码符合所有既有约定」。

35 号本身是「只测不改」的负结果夜（词库泛化确证 1705 语料命中 99.5%），
它的产物是统计 JSON，不是评测归档，所以 `eval_integrity` 对它是 skip 是合理的。

## 5. 交付物

| 文件 | 变化 |
| --- | --- |
| `tools/accept_night.py` | `check_repo_clean` 增加验收门自有产物白名单（1 处逻辑，+18/-2 行） |
| `ACCEPT_LOG.md` | 验收门自动追加 5 行运行记录 |
| `eval/accept_night_22.json`、`eval/accept_night_35.json` | 验收门自动写 |
| `REPORT_DAY2.md` | 本文件（覆盖旧版，旧版内容已在 git 历史里） |

## 6. 运行记录（ACCEPT_LOG.md 本次新增）

| 时间 | night | verdict | 统计 | 耗时 |
| --- | --- | --- | --- | --- |
| 2026-11-19T15:11:52 | 35 | FAIL | fail=1 skip=1 | 21.6s | ← 修复前，自指 bug |
| 2026-11-19T15:16:06 | 35 | FAIL | fail=1 skip=1 | 24.4s | ← 修复后但 accept_night.py 本身未提交 |
| 2026-11-19T15:18:19 | 22 | PASS | fail=0 skip=0 | 21.9s |
| 2026-11-19T15:19:22 | 35 | PASS | fail=0 skip=1 | 20.6s |

**中间那次 FAIL 没有删**：它记录的是「改了工具但还没提交」这个真实状态，
验收门判它脏是对的——这正是 repo_clean 该抓的东西。

## 7. 未覆盖的部分（沿用上一班，无变化）

1. 不检查 `REPORT_NIGHTn.md` 里的数字与归档是否对得上。
2. 不检查前端（`tsc --noEmit` / `npm run build`）。
3. `perf_envelope` 只测短句，长句退化抓不到。
4. 不做历史夜代码回放（要 checkout 旧 commit，与只读冲突）。

## 8. 禁止事项自查

- 未改 `expected`（改完会被自己的 `eval_integrity` 抓到，自检里验证过）。
- 未碰 `eval/ocr_gt_*`、`REPORT_NIGHT36/37/38.md`、`backend/ocr*.py`、`ocr_runtime/`、
  `eval/golden.json`、已有评测归档。
- 未编造通过：中间两次 FAIL 都保留在 `ACCEPT_LOG.md` 里，没删。
- 只本地提交到 `ds/dayshift-text-mining`，未推远程，未动 master。
- 工作区里的 Night36 未跟踪文件（`tools/night36_*.py`、`eval/ocr_samples/gt36*`）一个没 add。
