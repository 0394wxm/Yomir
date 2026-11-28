# -*- coding: utf-8 -*-
"""night114_merge_log.py — N114 合并夜 SHIFT_LOG.md 字节安全并集
（night112_merge_log.py 方法论克隆・assert-only・不写任何归档）。

纯字节操作（SHIFT_LOG 非纯 UTF-8・blob 内有历史 0xf3＝禁整文件 decode）：
  并集 = base(stage1) ＋ theirs(stage3) 追加（N113 群）＋ ours(stage2) 追加（N114 行）
  ——夜序 113<114 升序（机械并集 ours+theirs 会把 N114 行放在 N113 群之前＝逆序，
  N112 坑位②同款・直接按夜号升序构造并断言位置）。
  两侧都必须是纯追加（startswith base）——否则停下报数。
  接缝：theirs/ours 末尾无终止符 \\n 则补 1 个接缝 \\n 并计入字节账。
  夜序检查＝心跳行锚定「YYYY-MM-DD HH:MM N11n」模式目视段行
  （裸 b"N113"/b"N114" 会误匹配 REPORT_NIGHT113 等文件名＝N112 坑位①）。
  canary 0 基索引实测（并集前后・两形态都要实测再写数）：
    LF blob [807]=63・0xf3 在 blob offset 800＝243・CRLF 虚拟形态 [807]=243。
  爲 (U+7232) 字形防护＝本脚本 CJK 字面量不含 爲——merge 内容里若有 爲
  也原样字节保留（不 decode 不 re-encode）。
用法: python -I tools/night114_merge_log.py
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")


def stage(n):
    r = subprocess.run(["git", "show", ":%d:SHIFT_LOG.md" % n],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit("stage %d 取出失败" % n)
    return r.stdout


base = stage(1)     # merge-base ed5b2db 版
ours = stage(2)     # master 侧（含 N114 开工心跳 a73989e）
theirs = stage(3)   # night113-inventory tip fa71e23 版

print("bytes: base=%d ours=%d theirs=%d" % (len(base), len(ours), len(theirs)))
assert ours.startswith(base), "ours 非 base 纯追加（有删改）→ 停下报数"
assert theirs.startswith(base), "theirs 非 base 纯追加（有删改）→ 停下报数"

add_ours = ours[len(base):]
add_theirs = theirs[len(base):]
print("追加: ours+%d theirs+%d" % (len(add_ours), len(add_theirs)))

# 夜序检查（心跳行锚定・目视段行）：裸 b"N114" 哨兵会误匹配 REPORT_NIGHT114 等
# 文件名（N112 坑位①）——锚定「日期 HH:MM N11n」行首模式。
import re as _re
_pat = _re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2} (N11\d)")
ids_ours = set(_m.group(1) for _m in _pat.finditer(add_ours))
ids_theirs = set(_m.group(1) for _m in _pat.finditer(add_theirs))
print("心跳行锚定: ours=%s theirs=%s" % (sorted(ids_ours), sorted(ids_theirs)))
assert ids_ours == {b"N114"}, "ours 追加段心跳行 %s != {N114}" % sorted(ids_ours)
assert ids_theirs == {b"N113"}, "theirs 追加段心跳行 %s != {N113}" % sorted(ids_theirs)

seam_nl = 0
if add_theirs and not add_theirs.endswith(b"\n"):
    add_theirs += b"\n"
    seam_nl += 1
    print("接缝补 \\n（theirs 末尾无终止符）＋1")
if add_ours and not add_ours.endswith(b"\n"):
    add_ours += b"\n"
    seam_nl += 1
    print("接缝补 \\n（ours 末尾无终止符）＋1")
if not seam_nl:
    print("接缝 0（两侧追加段都以 \\n 终止）")

# 并集前 canary 实测（0 基・LF blob・两侧 base 段同一 blob）
print("canary(并集前 LF): ours[800]=%s ours[807]=%s theirs[800]=%s theirs[807]=%s"
      % (ours[800], ours[807], theirs[800], theirs[807]))

# 夜序 113<114＝并集按夜号升序：base＋theirs 追加（N113 群）＋ours 追加（N114 行）。
# ours 原始字节中的 base 部分＝merged 前段（追加段都在 base 末尾＝夜序重排不改 base 字节）。
merged = base + add_theirs + add_ours
assert merged[:len(base)] == base, "base 段被改动→ 停下报数"

# 夜序位置断言（并集内目视段行＝N113 群必须整体在 N114 行之前）
_pos113 = [m.start() for m in _pat.finditer(merged) if m.group(1) == b"N113"]
_pos114 = [m.start() for m in _pat.finditer(merged) if m.group(1) == b"N114"]
assert _pos113 and _pos114 and max(_pos113) < min(_pos114), \
    "夜序不成立：N113 位置 %s N114 位置 %s" % (_pos113, _pos114)
print("夜序 113<114：N113 群 offset %d-%d < N114 offset %d"
      % (min(_pos113), max(_pos113), min(_pos114)))

# canary（并集後・LF blob 与 CRLF 虚拟形态两值实测）
assert b"\r" not in merged, "merged 含 CR（非预期）→ 停下报数"
crlf = merged.replace(b"\n", b"\r\n")   # 虚拟 CRLF 形态（autocrlf 检出时的形态）
print("canary(并集後 LF blob): [800]=%s [807]=%s | CRLF 虚拟形态: [800]=%s [807]=%s"
      % (merged[800], merged[807], crlf[800], crlf[807]))
assert merged[800] == 243 and merged[807] == 63, "canary LF 断言失败（0xf3@800=243/[807]=63）"
assert crlf[807] == 243, "canary CRLF 虚拟形态断言失败 [807]=243"

# 哨兵守恒（并集完整性：两侧心跳行全部保留＝base+两侧追加的和）
for sid in (b"N111", b"N112", b"N113", b"N114"):
    c_merged = merged.count(sid)
    c_expect = base.count(sid) + add_theirs.count(sid) + add_ours.count(sid)
    print("哨兵 %s: merged=%d（base %d＋theirs %d＋ours %d）"
          % (sid.decode(), c_merged, base.count(sid),
             add_theirs.count(sid), add_ours.count(sid)))
    assert c_merged == c_expect, "哨兵 %s 守恒失败" % sid.decode()

print("字节账: base %d ＋ theirs 追加 %d ＋ ours 追加 %d ＋ 接缝 %d ＝ merged %d"
      % (len(base), len(theirs) - len(base), len(ours) - len(base), seam_nl, len(merged)))

# 证据落盘（console CJK mojibake 规避・N113 坑位④）：两侧追加段 repr + 并集摘要
with open("eval/night114_merge_stages.txt", "wb") as f:
    f.write(b"base=%d ours=%d theirs=%d\n" % (len(base), len(ours), len(theirs)))
    f.write(b"add_ours=%d add_theirs=%d seam=%d merged=%d\n"
            % (len(add_ours), len(add_theirs), seam_nl, len(merged)))
    f.write(b"add_ours repr:\n" + repr(add_ours).encode("utf-8") + b"\n")
    f.write(b"add_theirs repr:\n" + repr(add_theirs).encode("utf-8") + b"\n")

with open("SHIFT_LOG.md", "wb") as f:
    f.write(merged)
# 工作区文件（已写=LF 原字节形态）实测
with open("SHIFT_LOG.md", "rb") as f:
    wf = f.read()
print("工作区文件长度=%d [807]=%s（LF 原字节形态写入）"
      % (len(wf), wf[807] if len(wf) > 807 else None))
print("OK: 字节安全并集已写回 SHIFT_LOG.md（夜序 113<114）")
