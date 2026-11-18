# -*- coding: utf-8 -*-
"""accept_selftest.py — 验证验收门真的会 FAIL（不是永远 PASS 的摆设）。

做法：在临时副本里注入 4 种故障，逐项跑 accept_night，断言 verdict=FAIL 且是对应检查项 fail。
不改仓库本体（复制到 tempdir 后跑）。

python tools/accept_selftest.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def copy_light(dst):
    """只复制验收门需要的部分（不复制 node_modules / ocr_runtime / .git 的大件）。"""
    for item in ["backend", "tools", "tests", "eval", "start_backend.bat"]:
        src = os.path.join(ROOT, item)
        if not os.path.exists(src):
            continue
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dst, item),
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, os.path.join(dst, item))
    # 空 git 仓库，让 repo_clean 能跑（改动会被算作 tracked）
    subprocess.run(["git", "init", "-q"], cwd=dst, capture_output=True)


def run(dst, night, *extra):
    p = subprocess.run([sys.executable, os.path.join("tools", "accept_night.py"), str(night),
                        "--no-pytest", "--json-only", "--no-log", *extra],
                       cwd=dst, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        d = json.loads(p.stdout[p.stdout.index("{"):])
    except Exception:
        print("!! 无法解析 JSON，stdout 尾部：\n%s\n%s" % (p.stdout[-800:], p.stderr[-800:]))
        return None
    return d


def case(name, mutate, expect_check):
    dst = tempfile.mkdtemp(prefix="accept_selftest_")
    try:
        copy_light(dst)
        mutate(dst)
        d = run(dst, 21)
        if d is None:
            print("[ERR ] %-22s 无法运行" % name)
            return False
        bad = [c["name"] for c in d["checks"] if c["status"] == "fail"]
        ok = (d["verdict"] == "FAIL" and expect_check in bad)
        print("[%s] %-22s verdict=%s  fail项=%s" % ("OK  " if ok else "MISS", name, d["verdict"], bad))
        return ok
    finally:
        shutil.rmtree(dst, ignore_errors=True)


def mut_break_rule_c(dst):
    """把已撤销的 Rule C 塞回 style_fix。"""
    p = os.path.join(dst, "backend", "kundoku_rules.py")
    s = open(p, encoding="utf-8").read()
    s = s.replace("    t = style_modern_kana(text)\n",
                  "    t = style_dedup_shite_soshite(text)\n    t = style_modern_kana(t)\n")
    open(p, "w", encoding="utf-8").write(s)


def mut_tamper_expected(dst):
    """改一条 expected（模拟「改答案提分」）。"""
    p = os.path.join(dst, "eval", "night21_results_full.json")
    d = json.load(open(p, encoding="utf-8"))
    d["results"][0]["expected_kakikudashi"] = d["results"][0]["udkundoku_kakikudashi"]
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def mut_break_merge(dst):
    """清空合并词表。"""
    p = os.path.join(dst, "backend", "kundoku_rules.py")
    s = open(p, encoding="utf-8").read()
    i = s.index("MERGE_WORDS = [")
    j = s.index("]", i)
    s = s[:i] + "MERGE_WORDS = []" + s[j + 1:]
    open(p, "w", encoding="utf-8").write(s)


def mut_bad_archive(dst):
    """复制一条 id，制造重复。"""
    p = os.path.join(dst, "eval", "night21_results_full_v4.json")
    d = json.load(open(p, encoding="utf-8"))
    d["results"][1] = dict(d["results"][0])
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def mut_dirty_tracked(dst):
    """已跟踪文件改动未提交。"""
    p = os.path.join(dst, "backend", "main.py")
    subprocess.run(["git", "add", "-A"], cwd=dst, capture_output=True)
    subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "init"],
                   cwd=dst, capture_output=True)
    open(p, "a", encoding="utf-8").write("\n# dirty\n")


def main():
    print("验收门自检：注入故障，确认会 FAIL\n")
    results = [
        case("Rule C 复活", mut_break_rule_c, "rule_regression"),
        case("改 expected", mut_tamper_expected, "eval_integrity"),
        case("清空合并词表", mut_break_merge, "rule_regression"),
        case("归档重复 id", mut_bad_archive, "eval_integrity"),
        case("已跟踪文件脏", mut_dirty_tracked, "repo_clean"),
    ]
    print("\n%d/%d 个故障被正确抓到" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
