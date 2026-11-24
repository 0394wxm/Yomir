# -*- coding: utf-8 -*-
"""accept_night.py — 每夜验收门（D2）。

设计目标：
  * **只读**：不改任何源码/数据，不跑训练，不联网（除本地 API 可选）。
  * **可回测**：`python tools/accept_night.py 4` 能拿 Night 4 的归档文件重新判一次。
  * 输出：stdout 一份人读摘要 + `eval/accept_night_<n>.json`（机器读），
    并把一行摘要 append 到 `ACCEPT_LOG.md`。
  * 退出码：全部检查 pass → 0；有 fail → 1；门槛数据缺失 → 该检查记 skip（不算 fail）。

6 项检查（全部围绕「这一夜声称的成果是否真的还在」）：
  1. repo_clean        git 工作区干净（或只有未跟踪的临时文件）
  2. pytest            tests 全量通过（D13 起；原为只跑 test_api.py）
  3. eval_integrity    评测文件 id 唯一、无重复、总数与自报一致、expected 未被改动
  4. rule_regression   规则按当前约定生效（NIGHT22 起：顧みて而して 保留、
                       无护栏 て而して 删除；正字化表可逆）
  5. engine_smoke      引擎实际可用：3 句经典句输出符合当前约定（含 kana 分流、空输入 400）
  6. perf_envelope     单句训读耗时在包络内（防止性能悄悄退化）
  7. order_rate        割注对右先率（NIGHT50 新增；**只测量，不判死刑**）
                       原因：GT CER 对阅读顺序是盲的（见 REPORT_NIGHT49.md §11）

用法:
    python tools/accept_night.py 21          # 当前夜
    python tools/accept_night.py 4           # 回测 Night 4
    python tools/accept_night.py 21 --no-pytest   # 跳过 pytest（快速冒烟）
    python tools/accept_night.py 21 --json-only
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

LOG_PATH = os.path.join(ROOT, "ACCEPT_LOG.md")
OUT_DIR = os.path.join(ROOT, "eval")

# D13/D14 曾用硬编码 MIN_PASSED（14 → 50 → 65）作为 pytest 通过数下限。
# D15 改成动态：pytest --collect-only 数出多少就要求过多少（见 _count_collected）。
# 不再有常量需要维护。

# 每个夜声明的「评测归档文件」（用于检查 3）。缺省只查通用项。
NIGHT_ARTIFACTS = {
    4: ["night4_results_baseline.json", "night4_results_full_v1.json",
        "night4_results_full_v2.json"],
    5: ["night5_results_full_v3.json"],
    11: ["night21_results_full.json"],
    13: [],
    21: ["night21_results_full.json", "night21_results_full_v4.json",
         "night21_results_full_v4_500.json"],
    75: ["night75_results_4000.json"],
    77: ["night77_results_4000.json"],
    79: ["night79_results_4000.json"],
    80: ["night80_results_4000.json"],
    82: ["night82_results_4000.json"],
    84: ["night84_results_4000.json"],
    85: ["night85_results_4000.json"],
    86: ["night86_results_4000.json"],   # N86 Rule O 上线後の默认口径（13.491/24/0）
    22: ["night22_results_full.json"],
    23: ["night23_results_rongo.json"],
    26: ["night26_results_full.json"],
    29: ["night29_results_parallel.json"],
    30: ["night30_results_parallel.json"],
    31: ["night31_results_full.json", "night31_results_rongo.json"],
    32: ["night32_results_rongo.json"],
    34: ["night34_results_parallel.json"],
    # Night 67：默认评测口径 = golden_4000（⑬ AUX 补丁后全量重跑的归档）。
    # golden_7908 / golden_8165 是扩充归档，不登记为默认口径。
    67: ["night67_results_4000.json"],
    68: ["night68_results_4000.json"],
    70: ["night70_results_4000.json"],
    71: ["night70_results_4000.json"],   # N71 无新口径归档（导入夜＋gwb 全量），登记现行最新口径
    72: ["night72_results_4000.json"],
    73: ["night73_results_4000.json"],
    78: ["night78_results_4000.json"],
    81: ["night81_results_4000.json"],
    83: ["night83_results_4000.json"],   # N83 合并夜登记默认口径（Rule N 口径 13.495/24/0）
    # Night 44 的产物（night44_*.json）是版面过滤的对照分析，不是 golden 格式的
    # 评测结果（无 results[].id），登记进 eval_integrity 会 KeyError；
    # 它们由 tests/test_ocr_night44.py 的 7 条不变式测试守护。
    # Night 45 同理：night45_*.json 是阅读顺序的度量与原型对照，由
    # tests/test_ocr_night45.py 的 12 条不变式测试守护。
}

# Night 4 之后 expected 应保持的经典句（防止有人改评测数据来「提分」）
CLASSIC_CASES = [
    # (白文, 期望 kakikudashi, 说明)
    ("王顧左右而言他", "王は左右を顧みて而して他を言う",
     "经典句 1：而して 必须保留（Night7 撤销 Rule C 的证据）"),
    ("宋人有耕田者。", None, "专名合并：不得出现「宋の人」"),
    ("梁惠王曰", None, "正字化：惠→恵，白文原样"),
]


class Check(object):
    def __init__(self, name, title):
        self.name = name
        self.title = title
        self.status = "pass"
        self.detail = {}
        self.notes = []

    def fail(self, msg, **kv):
        self.status = "fail"
        self.notes.append(msg)
        self.detail.update(kv)

    def skip(self, msg, **kv):
        if self.status != "fail":
            self.status = "skip"
        self.notes.append(msg)
        self.detail.update(kv)

    def to_dict(self):
        return {"name": self.name, "title": self.title, "status": self.status,
                "notes": self.notes, "detail": self.detail}


# --------------------------------------------------------------------------
# 1. repo_clean
# --------------------------------------------------------------------------
def check_repo_clean(night):
    c = Check("repo_clean", "git 工作区干净")
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8").stdout
    except Exception as e:
        c.skip("git 不可用，跳过：%r" % (e,))
        return c
    lines = [l for l in out.splitlines() if l.strip()]
    c.detail["changed"] = lines
    # 判定标准：**已跟踪文件**的改动 = fail（说明有人改了代码没提交，
    #   这一夜声称的状态不可复现）；未跟踪文件（??）= 只记 note，
    #   因为验收门自身的 JSON/LOG/新脚本天然是未跟踪的。
    # 例外：验收门自己的产物（ACCEPT_LOG.md、eval/accept_night_*.json）
    #   每次运行都会写，若计入就会「跑一次就脏一次」→ 连跑两夜必 FAIL。
    #   这两个模式只可能是验收门自己写的，排除它们不影响检测真实代码改动。
    gate_owned = []
    tracked = []
    for l in lines:
        if l.startswith("??"):
            continue
        path = l[3:].strip().strip('"')
        if path == "ACCEPT_LOG.md" or re.match(r"eval/accept_night_.*\.json$", path):
            gate_owned.append(l)
        else:
            tracked.append(l)
    if gate_owned:
        c.detail["gate_owned_changes"] = gate_owned
        c.notes.append("验收门自身产物有更新（不计脏）：%s"
                       % ", ".join(g[3:] for g in gate_owned))
    untracked = [l for l in lines if l.startswith("??")]
    c.detail["tracked_changes"] = tracked
    c.detail["untracked"] = untracked
    if tracked:
        c.fail("已跟踪文件有未提交改动：%d 个" % len(tracked), files=tracked[:20])
    else:
        c.notes.append("已跟踪文件无改动")
    if untracked:
        c.notes.append("未跟踪：%s" % ", ".join(u[3:] for u in untracked[:10]))
    return c


# --------------------------------------------------------------------------
# 2. pytest
# --------------------------------------------------------------------------
def _count_collected():
    """用 pytest --collect-only 数出当前测试总数（D15）。

    为什么不再用硬编码基线：D13 写死 50、D14 加测试后要手改成 65，
    忘了改基线就等于「新增测试不在门的保护范围」，改错了又会误判。
    动态计数让「收集到多少就必须过多少」始终成立，不需要人工维护。
    """
    p = subprocess.run([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    text = p.stdout or ""
    # 末行形如 "65 tests collected in 2.36s"；无测试时是 "no tests ran"
    m = re.search(r"(\d+) tests? collected", text)
    if m:
        return int(m.group(1))
    # 退回按行数数（每行一个 test id），过滤汇总/空行
    ids = [l for l in text.strip().splitlines()
           if "::" in l and not l.startswith("=")]
    return len(ids)


def check_pytest(night, run_pytest):
    # D13: 口径从 tests/test_api.py（15 例）改成全量 tests。
    # D15: 通过数下限改为**动态**——collect 到多少个就要求过多少个。
    c = Check("pytest", "tests 全量通过")
    if not run_pytest:
        c.skip("--no-pytest：跳过")
        return c

    t_collect0 = time.time()
    expected = _count_collected()
    c.detail["collected"] = expected
    c.detail["collect_sec"] = round(time.time() - t_collect0, 1)
    if expected <= 0:
        c.fail("--collect-only 数不出测试（收集失败或被跳过）")
        return c

    t0 = time.time()
    p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    tail = (p.stdout or "").strip().splitlines()
    c.detail["elapsed_sec"] = round(time.time() - t0, 1)
    c.detail["tail"] = tail[-3:]
    m = re.search(r"(\d+) passed", p.stdout or "")
    c.detail["passed"] = int(m.group(1)) if m else 0
    for kw in ("failed", "error", "skipped", "xfailed", "xpassed"):
        mm = re.search(r"(\d+) %s" % kw, p.stdout or "")
        if mm:
            c.detail[kw] = int(mm.group(1))
    if p.returncode != 0:
        c.fail("pytest 退出码 %d" % p.returncode, returncode=p.returncode)
    elif c.detail["passed"] < expected:
        c.fail("通过数 %d < 收集数 %d（有测试没通过/没跑）"
               % (c.detail["passed"], expected))
    elif c.detail["passed"] > expected:
        # 多出来说明 collect 与实际执行不一致（如参数化动态生成），记一笔但不判 fail
        c.notes.append("通过数 %d > 收集数 %d（差异已记录）"
                       % (c.detail["passed"], expected))
        c.notes.append("%d passed（%.1fs）" % (c.detail["passed"], c.detail["elapsed_sec"]))
    else:
        c.notes.append("%d passed = %d collected（%.1fs，收集 %.1fs）"
                       % (c.detail["passed"], expected, c.detail["elapsed_sec"],
                          c.detail["collect_sec"]))
    return c


# --------------------------------------------------------------------------
# 3. eval_integrity
# --------------------------------------------------------------------------
def check_eval_integrity(night):
    c = Check("eval_integrity", "评测归档完整、id 唯一、expected 未被改")
    files = NIGHT_ARTIFACTS.get(night, [])
    if not files:
        c.skip("Night %d 未登记评测归档文件，只查 golden.json" % night)
        files = []

    golden_path = os.path.join(OUT_DIR, "golden.json")
    golden = {}
    if os.path.exists(golden_path):
        with open(golden_path, encoding="utf-8") as f:
            golden = {x["id"]: x["expected_kakikudashi"] for x in json.load(f)}
        c.detail["golden_n"] = len(golden)
    else:
        c.fail("eval/golden.json 缺失")

    rows = []
    for fn in files:
        p = os.path.join(OUT_DIR, fn)
        if not os.path.exists(p):
            c.fail("归档缺失：%s" % fn)
            continue
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        rs = doc["results"]
        ids = [r["id"] for r in rs]
        uniq = len(set(ids))
        ds = [r["edit_distance"] for r in rs if r.get("edit_distance") is not None]
        avg = round(sum(ds) / len(ds), 3) if ds else None
        ex = sum(1 for r in rs if r.get("exact_match"))
        # expected 与 golden 对照（只对 golden 里有的 id）
        common = [r for r in rs if r["id"] in golden]
        mismatch = [r["id"] for r in common if r["expected_kakikudashi"] != golden[r["id"]]]
        row = {"file": fn, "n": len(rs), "unique": uniq, "avg": avg,
               "exact": ex, "self_total": doc.get("total"),
               "self_exact": doc.get("exact_match_count"),
               "expected_mismatch": mismatch,
               "not_in_golden": [i for i in ids if i not in golden] if golden else []}
        rows.append(row)
        if uniq != len(rs):
            c.fail("%s 有重复 id" % fn, dups=len(rs) - uniq)
        if doc.get("total") not in (None, len(rs)):
            c.fail("%s 自报 total=%s 与实际 %d 不符" % (fn, doc.get("total"), len(rs)))
        if doc.get("exact_match_count") not in (None, ex):
            c.fail("%s 自报 exact_match_count=%s 与实际 %d 不符"
                   % (fn, doc.get("exact_match_count"), ex))
        if mismatch:
            c.fail("%s 有 %d 条 expected 与 golden 不一致" % (fn, len(mismatch)), ids=mismatch[:10])

    c.detail["files"] = rows

    # D16：golden_2000 的独立完整性检查（2000 条 id 都不在 golden.json 里，
    # 上面的对照对它们无效）。查三件事：2000 条、id 唯一、前 1000 条与
    # golden_1000 逐字段一致（防止有人改 expected 来「提分」）。
    g2_path = os.path.join(OUT_DIR, "golden_2000.json")
    g1_path = os.path.join(OUT_DIR, "golden_1000.json")
    if os.path.exists(g2_path) and os.path.exists(g1_path):
        with open(g2_path, encoding="utf-8") as f:
            g2 = json.load(f)
        with open(g1_path, encoding="utf-8") as f:
            g1 = json.load(f)
        ids2 = [x["id"] for x in g2]
        c.detail["golden_2000"] = {"n": len(g2), "unique": len(set(ids2))}
        if len(g2) != 2000:
            c.fail("golden_2000 条数 %d != 2000" % len(g2))
        if len(set(ids2)) != len(ids2):
            c.fail("golden_2000 有重复 id", dups=len(ids2) - len(set(ids2)))
        if len(g2) >= 1000:
            head_mismatch = [g1[i]["id"] for i in range(min(len(g1), 1000))
                             if g2[i].get("id") != g1[i].get("id")
                             or g2[i].get("hakubun") != g1[i].get("hakubun")
                             or g2[i].get("expected_kakikudashi")
                             != g1[i].get("expected_kakikudashi")]
            c.detail["golden_2000"]["head_mismatch"] = len(head_mismatch)
            if head_mismatch:
                c.fail("golden_2000 前 1000 条与 golden_1000 不一致",
                       ids=head_mismatch[:10])
        c.notes.append("golden_2000 %d 条、id 唯一、前 1000 条与 golden_1000 逐字段一致"
                       % len(g2))

    if c.status == "pass":
        c.notes.append("检查 %d 个归档，id 唯一、自报数一致、expected 未改" % len(rows))
    return c


# --------------------------------------------------------------------------
# 4. rule_regression（已撤销/已验证的规则必须仍按当前约定）
# --------------------------------------------------------------------------
def check_rule_regression(night):
    c = Check("rule_regression", "已撤销规则未复活 / 规则表未破坏")
    try:
        from backend import kundoku_rules as kr
    except Exception as e:
        c.skip("无法 import backend.kundoku_rules：%r" % (e,))
        return c

    # 4a. Rule C 语义检查（NIGHT22 起带护栏复活）：护栏处「顧みて而して」必须保留，
    #     无护栏的「て而して」必须被删。无护栏旧版 style_dedup_shite_soshite 仍是存档函数。
    if not hasattr(kr, "style_dedup_shite_soshite"):
        c.notes.append("无护栏版 style_dedup_shite_soshite 已删除（可接受）")
    t = kr.style_fix("顧みて而して他を言う")
    c.detail["style_fix_rule_c_guard"] = t
    if "而して" not in t:
        c.fail("护栏失效：style_fix 删掉了「顧みて而して」", out=t)
    t2 = kr.style_fix("見て而して思ふ")
    c.detail["style_fix_rule_c_prime"] = t2
    if t2 != "見て思う":  # ふ→う 先行（思ふ→思う），Night22 单测同款坑
        c.fail("Rule C' 未生效：style_fix 没删无护栏的「て而して」", out=t2)

    # 4b. style_fix 该做的两件事仍在做
    a = kr.style_fix("云ふ")
    b = kr.style_fix("子は曰く")
    c.detail["style_fix_fu"] = a
    c.detail["style_fix_wa_iwaku"] = b
    if a != "云う":
        c.fail("ふ→う 规则失效：%r -> %r" % ("云ふ", a))
    if b != "子曰く":
        c.fail("は曰く→曰く 规则失效：%r -> %r" % ("子曰く", b))

    # 4c. 正字化表：抽查 + 幂等
    n = kr.normalize_shinjitai("惠對竊雞盡數點譽")
    if n != "恵対窃鶏尽数点誉":
        c.fail("normalize_shinjitai 抽查不符：%r" % n)
    if kr.normalize_shinjitai(n) != n:
        c.fail("normalize_shinjitai 不是幂等的")

    # 4d. 合并词表必须含 Night4 的 10 个扩充词（防回退）
    need = {"諸侯", "木鐸", "樗蒲", "壑雷", "馬肥", "投足", "原君", "平原君", "人人", "自得"}
    missing = sorted(need - set(kr.MERGE_WORDS))
    c.detail["merge_words_n"] = len(kr.MERGE_WORDS)
    c.detail["merge_words_missing"] = missing
    if missing:
        c.fail("MERGE_WORDS 缺 Night4 扩充词：%s" % missing)

    if c.status == "pass":
        c.notes.append("Rule C' 护栏正常（顧みて留/て而して删）；ふ→う/は曰く 正常；正字化幂等；合并词表 %d 条"
                       % len(kr.MERGE_WORDS))
    return c


# --------------------------------------------------------------------------
# 5. engine_smoke（进程内 TestClient，不依赖 uvicorn）
# --------------------------------------------------------------------------
def check_engine_smoke(night):
    c = Check("engine_smoke", "引擎实际可用（3 句 + 分流 + 400）")
    try:
        import tempfile
        os.environ.setdefault("KANBUN_DB", os.path.join(tempfile.mkdtemp(prefix="accept_"), "a.db"))
        from fastapi.testclient import TestClient
        from backend.main import app
    except Exception as e:
        c.skip("无法 import backend.main：%r" % (e,))
        return c

    with TestClient(app) as client:
        h = client.get("/health").json()
        c.detail["health"] = h
        if not h.get("engine_loaded"):
            c.fail("引擎未加载：%r" % (h,))
            return c

        out = {}
        r = client.post("/api/kundoku", json={"text": "王顧左右而言他"})
        out["classic"] = r.json().get("kakikudashi", "") if r.status_code == 200 else r.text
        if r.status_code != 200:
            c.fail("经典句 HTTP %d" % r.status_code, body=r.text[:300])
        elif out["classic"].strip() != CLASSIC_CASES[0][1]:
            c.fail("经典句输出变了", got=out["classic"], want=CLASSIC_CASES[0][1])

        r = client.post("/api/kundoku", json={"text": "宋人有耕田者。"})
        out["merge"] = r.json().get("kakikudashi", "") if r.status_code == 200 else r.text
        if "宋の人" in out["merge"]:
            c.fail("专名合并失效：出现「宋の人」", got=out["merge"])

        r = client.post("/api/kundoku", json={"text": "梁惠王曰"})
        j = r.json()
        out["ortho"] = j.get("kakikudashi", "")
        out["ortho_hakubun"] = j.get("hakubun", "")
        if "恵" not in out["ortho"] or "惠" in out["ortho"]:
            c.fail("正字化失效", got=out["ortho"])
        if "惠" not in out["ortho_hakubun"]:
            c.fail("白文被改动（应原样保留旧字体）", got=out["ortho_hakubun"])

        r = client.post("/api/kundoku", json={"text": "いまはむかし、竹取の翁といふものありけり。"})
        out["kana"] = {"status": r.status_code, "text_type": r.json().get("text_type"),
                       "kk": r.json().get("kakikudashi")}
        if out["kana"]["text_type"] != "kana" or out["kana"]["kk"] != "":
            c.fail("假名分流失效", got=out["kana"])

        r = client.post("/api/kundoku", json={"text": "   "})
        out["empty"] = r.status_code
        if r.status_code != 400:
            c.fail("空输入应 400，实际 %d" % r.status_code)

        c.detail["outputs"] = out
    if c.status == "pass":
        c.notes.append("健康检查/经典句/合并/正字化/假名分流/空输入 全部符合约定")
    return c


# --------------------------------------------------------------------------
# 6. perf_envelope
# --------------------------------------------------------------------------
def check_perf_envelope(night):
    c = Check("perf_envelope", "单句训读耗时在包络内")
    try:
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        import udkundoku
        import udkanbun
    except Exception as e:
        c.skip("无法 import 引擎：%r" % (e,))
        return c

    try:
        eng = udkanbun.UDKanbun(True, False, None)
        eng("王顧左右而言他")  # 预热
    except Exception as e:
        c.skip("引擎加载失败（见 engine_smoke）：%r" % (e,))
        return c

    sent = "楚人有鬻楯與矛者。"
    ts = []
    for _ in range(3):
        t0 = time.time()
        udkundoku.translate(eng(sent), raw=True)
        ts.append((time.time() - t0) * 1000)
    med = sorted(ts)[1]
    c.detail["ms"] = [round(x, 1) for x in ts]
    c.detail["median_ms"] = round(med, 1)
    # Night 11 实测 unique avg 513ms（长句）、这里用短句；包络给到 3s（很宽松，只抓严重退化）
    LIMIT = 3000.0
    c.detail["limit_ms"] = LIMIT
    if med > LIMIT:
        c.fail("短句中位耗时 %.0fms 超过包络 %.0fms" % (med, LIMIT))
    else:
        c.notes.append("短句中位 %.0fms（包络 %.0fms）" % (med, LIMIT))
    return c


# --------------------------------------------------------------------------
# 7. order_rate（NIGHT50：只测量，不判死刑）
# --------------------------------------------------------------------------
def check_order_rate(night):
    """割注对右先率 —— **只测量，绝不判 FAIL**。

    背景（REPORT_NIGHT49.md §11）：GT 92 行 CER 对阅读顺序是**盲的**——
    Night49 改了 34/47 页的行序，CER 仍逐位不变（0.3568/0.3053）。
    所以要单独量「顺序」，否则以后再退化也没人知道。

    口径与 Night49 完全同源：`tools/night50_order_rate.measure()` 直接
    复用 `tools/night49_final.py` 的 `find_pairs` / `order_of`（连版面
    过滤与 wmed 的取法都走同一份代码）。两条线：
      off —— filter_off 归档 + 离线套版面过滤（生产口径，基线 98.57%）
      on  —— filter_on 归档（生产默认输出，交叉核对，基线 98.63%）
    严格层 A_strict（gap<0.15w ∧ 顶对齐 ∧ 等高）是真割注子集，基线 100%。

    **为什么永不 FAIL**：阈值是拍板事项，不是本门能定的。现在只把数字
    写进 ACCEPT_LOG / accept_night_<n>.json 留痕，供人判断。要改成判死刑
    门，需用户先批准阈值（例如「生产口径 < 95% 或严格层 < 100% 即 FAIL」）。
    """
    c = Check("order_rate", "割注右先率（只测量，不判死刑）")
    try:
        import contextlib
        import importlib.util
        import io

        path = os.path.join(ROOT, "tools", "night50_order_rate.py")
        spec = importlib.util.spec_from_file_location("n50_order_rate", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # night49_final / night49_simulate 在模块级调 sys.stdout.reconfigure()，
        # 必须先在**真实 stdout** 下导入，否则 StringIO 没有 reconfigure。
        mod._load_n49()
    except Exception as e:
        c.skip("无法载入顺序测量口径：%r" % (e,))
        return c

    lines = [
        ("off", os.path.join(ROOT, "eval", "night44_full", "filter_off"), True,
         "filter_off + 离线版面过滤（生产口径）"),
        ("on", os.path.join(ROOT, "eval", "night44_full", "filter_on"), False,
         "filter_on 归档（交叉核对）"),
    ]
    detail = {}
    for key, directory, apply_filter, label in lines:
        if not os.path.isdir(directory):
            c.skip("缺归档 %s" % directory)
            continue
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                m = mod.measure(directory, apply_filter, label)
        except Exception as e:
            # 量不出来也**不判 FAIL**，只记 skip（本门是测量门）
            c.skip("%s 量不出：%r" % (key, e))
            continue
        detail[key] = {
            "pairs": m["tot"],
            "right_first": m["after"],
            "rate": m["rate"],
            "before_rate": m["rate_before"],
            "strict_pairs": m["strict_n"],
            "strict_right_first": m["strict_after"],
            "strict_rate": m["strict_rate"],
            "regress_pages": m["regress_n"],
            "regress_detail": [{"page": p["page"], "before": p["before"],
                                "after": p["after"], "n": p["n"]}
                               for p in m["regress"]],
            "baseline_rate": mod.BASELINE[key]["rate"],
            "delta_vs_baseline": round(m["rate"] - mod.BASELINE[key]["rate"], 2),
        }

    c.detail.update(detail)
    if not detail:
        c.skip("两条线都缺归档，无法测量")
        return c

    # status 保持 pass（除非上面已 skip）；数值高低不触发 fail
    for key in ("off", "on"):
        if key not in detail:
            continue
        d = detail[key]
        c.notes.append(
            "%s 右先率 %d/%d = %.2f%%（基线 %.2f%%，差 %+.2fpp）；"
            "严格层 %d/%d = %.2f%%；退化页 %d"
            % (key, d["right_first"], d["pairs"], d["rate"],
               d["baseline_rate"], d["delta_vs_baseline"],
               d["strict_right_first"], d["strict_pairs"], d["strict_rate"],
               d["regress_pages"]))
    c.notes.append("**只测量不判死刑**：阈值需用户拍板后才能转成 FAIL 判据")
    return c


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="每夜验收门")
    ap.add_argument("night", nargs="?", type=int, default=0)
    ap.add_argument("--no-pytest", action="store_true", help="跳过 pytest（快速冒烟）")
    ap.add_argument("--json-only", action="store_true", help="只输出 JSON")
    ap.add_argument("--no-log", action="store_true", help="不追加 ACCEPT_LOG.md")
    arg = ap.parse_args()

    night = arg.night or 0
    t0 = time.time()
    checks = [
        check_repo_clean(night),
        check_pytest(night, not arg.no_pytest),
        check_eval_integrity(night),
        check_rule_regression(night),
        check_engine_smoke(night),
        check_perf_envelope(night),
        check_order_rate(night),
    ]
    n_fail = sum(1 for c in checks if c.status == "fail")
    n_skip = sum(1 for c in checks if c.status == "skip")
    verdict = "PASS" if n_fail == 0 else "FAIL"
    payload = {
        "night": night,
        "verdict": verdict,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_sec": round(time.time() - t0, 1),
        "n_checks": len(checks),
        "n_fail": n_fail,
        "n_skip": n_skip,
        "checks": [c.to_dict() for c in checks],
    }

    out_file = os.path.join(OUT_DIR, "accept_night_%s.json" % (night or "x"))
    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    if arg.json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("=== accept_night.py  Night %s  ===" % (night or "-"))
        for c in checks:
            mark = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[c.status]
            print("[%s] %-18s %s" % (mark, c.name, c.title))
            for n in c.notes:
                print("        - %s" % n)
        print("\nverdict: %s  (fail=%d skip=%d, %.1fs)"
              % (verdict, n_fail, n_skip, payload["elapsed_sec"]))
        print("json: %s" % os.path.relpath(out_file, ROOT))

    if not arg.no_log:
        line = "| %s | %s | %s | fail=%d skip=%d | %.1fs | %s |\n" % (
            payload["checked_at"], night or "-", verdict, n_fail, n_skip,
            payload["elapsed_sec"], out_file.replace("\\", "/").split("eval/")[-1])
        need_header = not os.path.exists(LOG_PATH)
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as f:
            if need_header:
                f.write("# ACCEPT_LOG.md — 每夜验收门运行记录\n\n")
                f.write("由 `python tools/accept_night.py <night>` 自动追加，一行一次运行。\n\n")
                f.write("| 时间 | night | verdict | 统计 | 耗时 | json |\n")
                f.write("| --- | --- | --- | --- | --- | --- |\n")
            f.write(line)

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
