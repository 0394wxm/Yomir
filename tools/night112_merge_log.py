# -*- coding: utf-8 -*-
"""night112_merge_log.py — N112 合并夜 SHIFT_LOG.md 字节安全并集（N110 方法论克隆・assert-only）。

纯字节操作（SHIFT_LOG 非纯 UTF-8・byte 有历史 0xf3＝禁整文件 decode）：
  并集 = ours(stage2) 全部字节 ＋ theirs(stage3) 相对 merge-base(stage1) 的追加字节。
  两侧都必须是纯追加（startswith base）——否则停下报数。
  接缝：ours 末尾无 \\n 则补 1 个接缝 \\n 并计数；theirs 末尾无终止符 \\n 则补 1 个并计数。
  夜序检查＝目视实际段行（并集里 111 段在 112 段之前＝seam 顺序）。
  canary 0 基索引实测：并集内容 LF blob [807]＝63 ＋ 工作区（CRLF 混合检出）[807]＝243。
  爲 (U+7232) 字形防护＝本脚本 CJK 字面量只含 SHIFT_LOG 哨兵串（N111/N112），
  不含 爲——merge 内容里若有 爲 也原样字节保留（不 decode 不 re-encode）。
用法: python -I tools/night112_merge_log.py
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


base = stage(1)     # merge-base 5633eca 版
ours = stage(2)     # master 侧（含 N112 开工心跳 5bc8718）
theirs = stage(3)   # night111-followmap-impl tip e1e0344 版

print("bytes: base=%d ours=%d theirs=%d" % (len(base), len(ours), len(theirs)))
assert ours.startswith(base), "ours 非 base 纯追加（有删改）→ 停下报数"
assert theirs.startswith(base), "theirs 非 base 纯追加（有删改）→ 停下报数"

add_ours = ours[len(base):]
add_theirs = theirs[len(base):]
print("追加: ours+%d theirs+%d" % (len(add_ours), len(add_theirs)))

# 夜序检查（目视段行・111<112）：心跳行锚定＝「2026-11-28 HH:MM N11n」模式
# （裸 b"N111"/b"N112" 会误匹配 REPORT_NIGHT111 等文件名＝本夜实测坑位）
import re as _re
_pat = _re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2} (N11\d)")
ids_ours = set(_m.group(1) for _m in _pat.finditer(add_ours))
ids_theirs = set(_m.group(1) for _m in _pat.finditer(add_theirs))
print("心跳行锚定: ours=%s theirs=%s" % (sorted(ids_ours), sorted(ids_theirs)))
assert ids_ours == {b"N112"}, "ours 追加段心跳行 %s != {N112}" % sorted(ids_ours)
assert ids_theirs == {b"N111"}, "theirs 追加段心跳行 %s != {N111}" % sorted(ids_theirs)
seam_nl = 0
if add_theirs and not add_theirs.endswith(b"\n"):
    add_theirs += b"\n"
    seam_nl += 1
    print("接缝补 \\n（theirs 末尾无终止符）＋1")
if add_ours and not add_ours.endswith(b"\n"):
    add_ours += b"\n"
    seam_nl += 1
    print("接缝补 \\n（ours 末尾无终止符）＋1")
# 夜序 111<112＝并集顺序按夜号升序排列：base＋theirs 追加（N111 群 12:03–12:55）
# ＋ours 追加（N112 行 13:37）。ours 原始字节中的 base 部分＝merged 前段（ours=
# base+add_ours、追加段与 theirs 追加段都在 base 末尾＝夜序重排不改 base 字节）。
merged = base + add_theirs + add_ours

# 夜序位置断言（并集内目视段行＝N111 群必须整体在 N112 行之前）
_pos111 = [m.start() for m in _pat.finditer(merged) if m.group(1) == b"N111"]
_pos112 = [m.start() for m in _pat.finditer(merged) if m.group(1) == b"N112"]
assert _pos111 and _pos112 and max(_pos111) < min(_pos112), \
    "夜序不成立：N111 位置 %s N112 位置 %s" % (_pos111, _pos112)
print("夜序 111<112：N111 群 offset %d-%d < N112 offset %d"
      % (min(_pos111), max(_pos111), min(_pos112)))

# canary 0 基索引实测（并集前后・先实测再写数）
c_ours = ours[807] if len(ours) > 807 else None
c_theirs = theirs[807] if len(theirs) > 807 else None
c_merged = merged[807] if len(merged) > 807 else None
print("canary(0-based): ours[807]=%s theirs[807]=%s merged(LF blob)[807]=%s"
      % (c_ours, c_theirs, c_merged))
print("merged 长度=%d（base %d＋ours 追加 %d＋theirs 追加 %d＋接缝 %d）"
      % (len(merged), len(base), len(ours) - len(base), len(theirs) - len(base), seam_nl))

# N111/N112 哨兵行数（并集完整性：两侧心跳行全部在）
n111 = merged.count(b"N111")
n112 = merged.count(b"N112")
print("哨兵行数: N111=%d N112=%d（并集＝两侧行全部保留）" % (n111, n112))
assert n112 >= 1, "N112 心跳行丢失"

with open("SHIFT_LOG.md", "wb") as f:
    f.write(merged)
# 工作区文件（已写=LF 原字节形态）实测 [807]
with open("SHIFT_LOG.md", "rb") as f:
    wf = f.read()
print("工作区文件长度=%d [807]=%s" % (len(wf), wf[807] if len(wf) > 807 else None))
print("OK: 字节安全并集已写回 SHIFT_LOG.md")
