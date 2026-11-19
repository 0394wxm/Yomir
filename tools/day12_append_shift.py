# -*- coding: utf-8 -*-
"""day12_append_shift.py — 把白天班（D2/D4/D10/D11/D12）总结追加进 SHIFT_LOG.md。

为什么要脚本：SHIFT_LOG.md 早期的夜班条目在旧会话里写坏了编码
（含 0xf3 等非法 UTF-8 字节），任何「读全文 → 重写」的操作都会失败或损坏历史。
所以这里只用二进制追加（'ab'），旧字节一个不动。

用法：python tools\\day12_append_shift.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")
MARK = "白天班 D2/D4/D10/D11/D12"

SECTION = u"""

# —— 2026-11-19 15:15 ～ 18:20（白天班，`ds/dayshift-text-mining`，起点 4117d1c）——

注：本段由 `tools/day12_append_shift.py` 以二进制追加写入，未触碰上方任何历史字节。

- 2026-11-19 15:15 | D2 验收门 | `tools/accept_night.py` 六项检查（repo_clean/pytest/eval_integrity/rule_regression/engine_smoke/perf_envelope），JSON + exit 0/1 + 追加 ACCEPT_LOG.md | 抓到**自指 bug**：门自己写 ACCEPT_LOG.md 和 eval/accept_night_*.json，连跑两次第二次必 FAIL → 白名单这两个模式（计入 gate_owned_changes 不算脏）；注入脏文件 selftest 5/5 证明没放过真脏

- 2026-11-19 15:20 | D4 离群值 DONE | 20 连调 + 分段计时（KANBUN_TIMING=1）：cached 中位 400.8ms，db 468.5ms；ablation A 495.3 → B 0.6ms；db 内部 connect 11.4 / pragma 25.3 / **commit 262.4** / **close 158.1**；D: 446.0ms vs C: 13.6ms（32.8×）；裸 fsync 70.8 vs 1.8（39.3×） | 结论：所谓「cached 2.4s」97–100% 是 `save_kundoku` 的三次 fsync，缓存只省 8ms 引擎时间；**本次未复现 2.4s（max 0.81s），如实记录**；只定位不重构，5 个候选方案仍等拍板

- 2026-11-19 17:18 | D10 评测扩 1000 DONE | `eval/golden_1000.json` = 500 基础条（**逐字节不动**）+ 500 新增（`golden_rongo_full` 362 + `kanbun_parallel` 138），按 hakubun 去重、id 加 p-/c- 前缀；规则引擎 26.09 / exact 3/1000 / 0 错，guwenbert 离线 25.27 / exact 5（Δ -0.822，但慢 50×） | 爬虫日产太低（50 页仅 11 条新增，多数已在库）→ 改用仓内 kanbun.info 语料；**事故已入档**：误跑既有 `tools/run_eval_1000.py`（输出硬编码）覆盖 `eval/night26_results_full.json`，当场 `git checkout --` 恢复，之后所有脚本改独立输出路径

- 2026-11-19 18:03 | D11 Rule D DONE（本班最大产出） | 解剖 1000 条：expected 里「之」522 处/「これ」**0 处**，输出「これ」527 处——引擎把汉文「之」系统性训读成假名「これ」；模拟 6 候选，仅 これ→之 满足高频+方向一致+0 变差（D1 全替换 -0.889，**282 改善 / 0 变差**）；上线 `style_kore_to_shi` + `style_fix_with_hakubun`，旧 `style_fix` 保留不动 | 两次失败如实入档：①**语义护栏全错**（挡 135 条、keiko-1 仍 +1；逐位置诊断发现真正对应的是第 3 个「これ」，护栏挡掉真「之」留下假「これ」）②**pick2 sentinel 实现 bug** 造出假变差（逐条核对确认 D1 确实 0 变差）。改用**白文判据护栏**（白文含「之」才替换）：交叉表白文无「之」&输出有「これ」= **0 条**，语料内零成本等价于全替换，语料外真能挡。真机 1000 条 avgDist **25.201**，与离线**逐位一致**，pytest 33→41

- 2026-11-19 18:19 | D12 死代码 + 测试 DONE | ①`window.__KANBUN_API_BASE__` 先查后删（Rust 侧 0 注入，与 REPORT_DAY6 §7.2 一致；功能性读取只有 App.tsx 一处）②`@app.on_event("startup")` → `@asynccontextmanager` lifespan（**必须在 app = FastAPI(...) 之前定义**，否则 NameError）③`tests/test_lifespan_migration.py` 9 例 | 取证 `tools/day12_warn_check.py`（子进程各导一次）：**当前 0 条 / HEAD 版 2 条** DeprecationWarning；pytest **41 → 50 passed**；`npx tsc --noEmit` 干净、`npx vite build` 成功（30 modules 7.79s）。教训：前端测试第一版被**自己写的注释**绊倒 → 测试锁代码不锁文字

- 2026-11-19 18:20 | 白天班收尾 | **五项全部完成并提交**，7 个提交（8c20507 → 06a65c4），每项都有 REPORT_DAY*.md 与可复现脚本；验收门 **Night 22 PASS 6/6 / Night 35 PASS 5/6+1 skip**（提交后跑）；树干净（只剩 13 个 Night36 未跟踪文件，全程未 add）；未推远程、未动 master | 转待命：等下一个信号。待拍板 5 项见 REPORT_DAY12 §10 与下方汇总

## 白天班数字汇总

| 指标 | 起点 4117d1c | 终点 06a65c4 | Δ |
| --- | --- | --- | --- |
| pytest | 33 passed | **50 passed** | +17 |
| DeprecationWarning | 2 | **0** | -2 |
| 评测集 | 500 条 | **1000 条** | +500 |
| 规则引擎 avgDist（1000 条） | 26.090 | **25.201** | **-0.889** |
| 验收门 22 / 35 | — | **6/6 PASS / 5/6+1 skip** | — |

## 待拍板（5 项）

1. `accept_night.py` 的 pytest 只跑 `tests/test_api.py`（15 例），全量是 50 例——要不要改口径
2. `frontend/src-tauri/{sidecar,target}/_internal/` 是旧拷贝（含旧 on_event 与旧 dist JS），未跟踪；是否清理/重建
3. D12 顺带把 `VITE_API_BASE` 的尾部斜杠也归一化了（原来只有 injected 分支做）——要不要回退成绝对零行为变化
4. 「へ→え」「ひ→い」0 变差但 Δ<0.2，收益太小未合入，留作下次
5. guwenbert 好 0.822 但慢 50×（55min vs 66s），是否值得混合/蒸馏
"""


def main():
    with open(PATH, "rb") as f:
        head = f.read()
    if MARK.encode("utf-8") in head:
        print("已存在白天班段落，跳过（避免重复追加）")
        return
    before = len(head)
    with open(PATH, "ab") as f:
        f.write(SECTION.encode("utf-8"))
    after = os.path.getsize(PATH)
    print("appended: %d -> %d bytes (+%d)" % (before, after, after - before))
    print("旧字节前缀一致: %s" % (open(PATH, "rb").read(before) == head))


if __name__ == "__main__":
    main()
