# REPORT_DAY2.md — 白天 D2：每夜验收门 `tools/accept_night.py`（2026-11-18）

任务单：白天清单第 2 项（D2 验收门补做）。
起点：`git log -1` = `89c20de day9: full_v4 ...`。

**结果：验收门建成，Night 21 PASS、Night 4 回测 PASS，注入 5 种故障 5/5 全部被抓到。**

---

## 1. 交付物

| 文件 | 作用 |
| --- | --- |
| `tools/accept_night.py` | 验收门本体，6 项检查，JSON + exit 0/1 + 追加 `ACCEPT_LOG.md` |
| `tools/accept_selftest.py` | 自检：往临时副本里注入故障，确认验收门会 FAIL |
| `ACCEPT_LOG.md` | 运行记录（验收门自己追加） |
| `eval/accept_night_<n>.json` | 每次运行的机器可读结果 |

## 2. 6 项检查的设计与判定标准

| # | 检查名 | 判定什么 | 为什么这么判（防止什么） |
| --- | --- | --- | --- |
| 1 | `repo_clean` | **已跟踪文件**无未提交改动 | 防止「报告说改了、代码没提交」→ 状态不可复现。未跟踪文件（验收门自己的 JSON/LOG）只记 note 不判失败 |
| 2 | `pytest` | `tests/test_api.py` 全过且 ≥14 条 | 防止功能和回归断言被悄悄破坏；14 是 Night 7 以来的基线 |
| 3 | `eval_integrity` | 归档存在、id 唯一、自报 total/exact 与实际一致、**expected 与 golden 逐条一致** | 防止「改答案提分」和「结果文件手工编辑」 |
| 4 | `rule_regression` | Rule C 仍处撤销状态、ふ→う/は曰く 仍在生效、正字化幂等、Night4 的 10 个合并词还在 | 防止迟到的合并把 Night 7 撤销的规则又带回来（这个项目已经发生过一次） |
| 5 | `engine_smoke` | 进程内 TestClient 跑 6 个真实请求：健康检查、经典句精确串、专名合并、正字化+白文原样、假名分流、空输入 400 | 防止「pytest 绿了但引擎其实没加载」这类事故 |
| 6 | `perf_envelope` | 短句训读中位耗时 < 3000ms | 防止性能悄悄退化（包络刻意很宽，只抓数量级退化） |

设计取舍（如实写）：

- **检查 4 和 5 有重叠但都保留**：检查 4 只看规则函数的纯函数行为（快、不依赖引擎），
  检查 5 走完整 HTTP 栈（慢、能抓「规则对了但接错地方」）。在自检里可以看到，破坏 Rule C 时
  两项同时 fail——这是预期行为，不是误报。
- **`perf_envelope` 的 3000ms 很松**：本机实测短句中位 11–13ms，包络是它的 230 倍。
  故意放松，因为 Celeron 机器上偶发 GC/杀毒抖动会到几百毫秒；这个检查只该拦「退化两个数量级」。
- **不做**「跑完 500 条评测」这类检查：太慢（32 分钟），验收门要能在 1 分钟内跑完。

## 3. Night 21 实测（PASS）

```
[PASS] repo_clean        已跟踪文件无改动；未跟踪：ACCEPT_LOG.md / eval/accept_night_21.json / tools/accept_night.py
[PASS] pytest            14 passed（17.8s）
[PASS] eval_integrity    检查 3 个归档（night21_results_full / _v4 / _v4_500），id 唯一、自报数一致、expected 未改
[PASS] rule_regression   Rule C 仍撤销；ふ→う/は曰く 正常；正字化幂等；合并词表 21 条
[PASS] engine_smoke      健康检查/经典句/合并/正字化/假名分流/空输入 全部符合约定
[PASS] perf_envelope     短句中位 11ms（包络 3000ms）

verdict: PASS  (fail=0 skip=0, 38.2s)
```

exit code 0。

## 4. Night 4 回测（PASS）

```
[PASS] repo_clean        已跟踪文件无改动
[PASS] pytest            14 passed（18.7s）
[PASS] eval_integrity    检查 3 个归档（baseline / full_v1 / full_v2），id 唯一、自报数一致、expected 未改
[PASS] rule_regression   Rule C 仍撤销；ふ→う/は曰く 正常；正字化幂等；合并词表 21 条
[PASS] engine_smoke      6 项全部符合约定
[PASS] perf_envelope     短句中位 13ms

verdict: PASS  (fail=0 skip=0, 41.1s)
```

**回测说明（必须写清楚）**：Night 4 的归档本身还在、expected 没被改、那 3 个归档的 id 唯一性也都过；
但**规则相关项检查的是「今天」的代码**，不是 Night 4 当天的代码——Night 4 之后 Night 5 加了 Rule C、
Night 7 又撤销了它，`MERGE_WORDS` 也从 20 条变成 21 条。所以 Night 4 回测的 PASS 含义是
「Night 4 的产出到今天仍然完整、且当前代码没违反当时的约定」，**不是**「Night 4 当天代码的回归测试」。

这一点是刻意的设计：验收门是**当前状态体检**，不是历史快照回放。要真做历史回放得 checkout 旧 commit，
那会改工作区，跟「只读」冲突。

## 5. 自检：故障注入 5/5 全部抓到（`tools/accept_selftest.py`）

| 注入的故障 | verdict | 抓到它的检查项 |
| --- | --- | --- |
| 把 Rule C 塞回 `style_fix` | FAIL | `rule_regression` + `engine_smoke` |
| 改一条 `expected` 使其等于引擎输出 | FAIL | `eval_integrity` |
| 清空 `MERGE_WORDS` | FAIL | `rule_regression` + `engine_smoke` |
| 归档里复制一条制造重复 id | FAIL | `eval_integrity` |
| 已跟踪文件改动未提交 | FAIL | `repo_clean` |

自检在临时目录里做，不碰仓库本体；跑完 `5/5 个故障被正确抓到`，退出码 0。

## 6. 一处如实记录的返工

第一次跑 Night 21 是 **FAIL**（`ACCEPT_LOG.md` 里保留了这条记录，没有删）：

```
| 2026-11-18T15:58:15 | 21 | FAIL | fail=1 skip=0 | 35.4s | accept_night_21.json |
```

原因：`repo_clean` 那时把**未跟踪的 `tools/accept_night.py` 自己**也算成「工作区不干净」——
自指错误（验收门是新文件，它一出生就未跟踪，于是永远 FAIL）。

修法：判定标准改成「**已跟踪文件**有改动才算脏，未跟踪只记 note」。理由：验收门自己的
JSON/LOG 天然未跟踪；而「未提交的代码改动」才是真正要让验收门拦下的风险。
修完重跑 → PASS；自检里「已跟踪文件脏」still 能抓到（5/5），说明修改没把检测能力改没。

## 7. 用法

```
python tools/accept_night.py 21               # 完整跑（约 40s）
python tools/accept_night.py 4                # 回测其它夜
python tools/accept_night.py 21 --no-pytest   # 跳过 pytest（约 20s，快速冒烟）
python tools/accept_night.py 21 --json-only   # 只输出 JSON（给 CI/脚本用）
python tools/accept_selftest.py               # 自检（约 2 分钟）
```

退出码：`0` 全过；`1` 有 fail。`skip` 不算失败（比如某个夜没登记评测归档、或引擎 import 失败时，
会记 skip 并在 notes 里写原因，而不是假报 pass）。

## 8. 未覆盖的部分（如实）

1. **不检查报告内容**：`REPORT_NIGHTn.md` 里的数字与归档文件是否对得上，仍要人工核对。
   技术上可做（解析报告里的 avgDist 与 JSON 比对），但每个夜的报告格式不统一，先不做。
2. **不检查前端**：`tsc --noEmit`、`npm run build` 没进验收门（需要 node，且慢）。
3. **`perf_envelope` 只测短句**：长句（>60 字）实测 137ms，如果将来退化到 10s 这个检查抓不到。
4. **历史夜回放能力缺失**：见 §4，需要 checkout 旧 commit，与只读冲突。

## 9. 验收

- `python tools/accept_night.py 21` → PASS，exit 0。
- `python tools/accept_night.py 4` → PASS，exit 0。
- `python tools/accept_selftest.py` → 5/5，exit 0。
- `pytest tests/test_api.py -q` → 14 passed（验收门内部也跑了一遍）。
- 未改任何源码/评测数据；未推远程；无 key/token。

## 10. 禁止事项自查

未改 expected（改完还会被自己的检查 3 抓到）；第一次 FAIL 的记录保留在 ACCEPT_LOG.md 未删；
自检是真实注入故障而非空跑；「回测 PASS」的含义在 §4 明确写了它不是历史回放；只本地提交。
