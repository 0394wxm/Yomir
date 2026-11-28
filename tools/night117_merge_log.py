# -*- coding: utf-8 -*-
"""night117_merge_log.py — N117 合并夜接缝文件字节安全并集
（night114_merge_log.py 方法论克隆・assert-only・不写任何归档）。

纯字节操作（SHIFT_LOG 非纯 UTF-8・blob 内有历史 0xf3＝禁整文件 decode）。
夜序升序（机械并集会逆序＝N110/N112/N114 教训）：115<116<117。
两侧都必须是纯追加（startswith base）——否则停下报数。
接缝：追加段末尾无终止符 \\n 则补 1 个并计入字节账。
夜序检查＝心跳行锚定（裸 b"N115" 会误匹配 REPORT_NIGHT115 等文件名＝N112
坑位①）：行首「YYYY-MM-DD HH:MM」＋行内首个夜 token。N114 形式
「… HH:MM N11n …」に加え N115 行の変体形式「… HH:MM Night 115 …」／
「… HH:MM 进度：N115 …」も同一 extractor で捕捉（N117 実測：N115 群
6 行＝Night 115 开工/收工＋进度：N115 4 行・N116 群 4 行＝N116 紧随形式）。
ROADMAP 行锚 b"Night 115" / b"Night 116"（先断言 base 无此二者）；
ACCEPT_LOG 行锚 b" | 115 | " / b" | 116 | "（先断言 base 无此二者）。
canary 0 基索引（SHIFT_LOG・并集前后两形态都要实测再写数）：
  LF blob [807]=63・0xf3 在 blob offset 800＝243・CRLF 虚拟形态 [807]=243。
哨兵守恒＝夜 token 计数 merged==base＋两侧追加之和（N111…N117）。
爲 (U+7232) 字形防护＝本脚本 CJK 字面量不含 爲；merge 内容若有 爲
也原样字节保留（不 decode 不 re-encode）。
用法: python -I tools/night117_merge_log.py m1|m2
  m1 = merge night115-annotation-design（冲突预期恰 SHIFT_LOG.md；
       并集 = base＋theirs 追加（N115 群）＋ours 追加（N117 开工行）＝115<117）
  m2 = merge night116-annotation-impl（冲突预期 SHIFT_LOG/ROADMAP/ACCEPT_LOG；
       SHIFT_LOG = base＋N115 群＋theirs 追加（N116 群）＋ours 残部（N117）
         ＝115<116<117（N115 群＝ours 追加段前缀・与 632f8c3 blob−base 逐位相等断言）
       ROADMAP    = base＋ours 追加（Night 115 行）＋theirs 追加（Night 116 行）
       ACCEPT_LOG = base＋ours 追加（115 两行）＋theirs 追加（116 两行））
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

N115_TIP = "632f8c3"  # night115-annotation-design tip（SHIFT_LOG N115 群再構成源）


def sh(args):
    r = subprocess.run(args, capture_output=True)
    if r.returncode != 0:
        sys.exit("git failed: %s" % " ".join(args))
    return r.stdout


def stage(n, path):
    return sh(["git", "show", ":%d:%s" % (n, path)])


_DT = None  # line-start datetime pattern, built lazily (SHIFT_LOG only)
_ID = None  # first night token in a heartbeat line (N114 form + N115 variants)


def shift_anchors(buf):
    """[(b"N<nnn>", line_start_offset)] for every line starting with
    YYYY-MM-DD HH:MM that carries a Night token. Byte-level only."""
    global _DT, _ID
    if _DT is None:
        import re
        _DT = re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
        _ID = re.compile(rb"(?:Night |N)(11[0-9])")
    out = []
    off = 0
    for ln in buf.split(b"\n"):
        if _DT.match(ln):
            m = _ID.search(ln)
            if m:
                out.append((b"N" + m.group(1), off))
        off += len(ln) + 1
    return out


def seam_fix(segs):
    seam = 0
    fixed = []
    for s in segs:
        if s and not s.endswith(b"\n"):
            s += b"\n"
            seam += 1
            print("seam: appended \\n to segment (len before=%d)" % (len(s) - 1))
        fixed.append(s)
    return fixed, seam


def finish(path, merged, evidence, extra_lines):
    assert b"\r" not in merged, "merged contains CR -> stop"
    with open(evidence, "wb") as f:
        for ln in extra_lines:
            f.write(ln)
    with open(path, "wb") as f:
        f.write(merged)
    with open(path, "rb") as f:
        wf = f.read()
    assert wf == merged, "working-tree write mismatch"
    print("written %s len=%d (LF byte form)" % (path, len(wf)))


def canary_shift(merged):
    crlf = merged.replace(b"\n", b"\r\n")
    print("canary(LF): [800]=%d [807]=%d | CRLF virtual: [800]=%d [807]=%d"
          % (merged[800], merged[807], crlf[800], crlf[807]))
    assert merged[800] == 243 and merged[807] == 63, "canary LF failed"
    assert crlf[807] == 243, "canary CRLF virtual failed"


def sentinels(merged, base, adds, sids):
    for sid in sids:
        c_m = merged.count(sid)
        c_e = base.count(sid) + sum(a.count(sid) for a in adds)
        print("sentinel %s: merged=%d (base %d + adds %s)"
              % (sid.decode(), c_m, base.count(sid), [a.count(sid) for a in adds]))
        assert c_m == c_e, "sentinel %s conservation failed" % sid.decode()


def resolve_shift(base, ours, theirs, m115part=None, evidence=""):
    """m1: merged = base + theirs(115) + ours(117).
    m2 (m115part given): ours append = n115part + rest(117);
        merged = base + n115part + theirs(116) + rest = 115<116<117."""
    print("bytes: base=%d ours=%d theirs=%d" % (len(base), len(ours), len(theirs)))
    assert ours.startswith(base), "ours not pure append -> stop"
    assert theirs.startswith(base), "theirs not pure append -> stop"
    add_ours = ours[len(base):]
    add_theirs = theirs[len(base):]
    print("appends: ours+%d theirs+%d" % (len(add_ours), len(add_theirs)))
    an_ours = shift_anchors(add_ours)
    an_theirs = shift_anchors(add_theirs)
    ids_ours = set(i for i, _ in an_ours)
    ids_theirs = set(i for i, _ in an_theirs)
    print("anchored ids: ours=%s theirs=%s"
          % (sorted(x.decode() for x in ids_ours),
             sorted(x.decode() for x in ids_theirs)))
    if m115part is None:  # m1
        assert ids_ours == {b"N117"}, "ours ids != {N117}"
        assert ids_theirs == {b"N115"}, "theirs ids != {N115}"
        segs, seam = seam_fix([add_theirs, add_ours])
        merged = base + segs[0] + segs[1]
    else:  # m2
        assert ids_ours == {b"N115", b"N117"}, "ours ids != {N115,N117}"
        assert ids_theirs == {b"N116"}, "theirs ids != {N116}"
        assert add_ours.startswith(m115part), \
            "ours append does not start with N115 part (len %d)" % len(m115part)
        rest = add_ours[len(m115part):]
        segs, seam = seam_fix([m115part, add_theirs, rest])
        merged = base + segs[0] + segs[1] + segs[2]
    # night order positions on merged
    an_m = shift_anchors(merged)
    pos = {}
    for i, p in an_m:
        pos.setdefault(i, []).append(p)
    if m115part is None:
        assert pos[b"N115"] and pos[b"N117"] and max(pos[b"N115"]) < min(pos[b"N117"]), \
            "night order 115<117 failed"
        print("order 115<117: N115 %d-%d < N117 %d"
              % (min(pos[b"N115"]), max(pos[b"N115"]), min(pos[b"N117"])))
    else:
        assert pos[b"N115"] and pos[b"N116"] and pos[b"N117"], "missing group"
        assert max(pos[b"N115"]) < min(pos[b"N116"]), "order 115<116 failed"
        assert max(pos[b"N116"]) < min(pos[b"N117"]), "order 116<117 failed"
        print("order 115<116<117: N115 %d-%d < N116 %d-%d < N117 %d"
              % (min(pos[b"N115"]), max(pos[b"N115"]), min(pos[b"N116"]),
                 max(pos[b"N116"]), min(pos[b"N117"])))
    canary_shift(merged)
    sids = [b"N11%d" % n for n in range(1, 8)]  # N111..N117
    sentinels(merged, base, [add_theirs, add_ours], sids)
    assert len(base) + len(add_ours) + len(add_theirs) + seam == len(merged), \
        "byte account mismatch"
    print("account: base %d + ours %d + theirs %d + seam %d = merged %d"
          % (len(base), len(add_ours), len(add_theirs), seam, len(merged)))
    lines = [b"base=%d ours=%d theirs=%d\n" % (len(base), len(ours), len(theirs)),
             b"add_ours=%d add_theirs=%d seam=%d merged=%d\n"
             % (len(add_ours), len(add_theirs), seam, len(merged))]
    if m115part is not None:
        lines.append(b"n115part=%d\n" % len(m115part))
        lines.append(b"n115part repr:\n" + repr(m115part).encode("utf-8") + b"\n")
    lines.append(b"add_ours repr:\n" + repr(add_ours).encode("utf-8") + b"\n")
    lines.append(b"add_theirs repr:\n" + repr(add_theirs).encode("utf-8") + b"\n")
    finish("SHIFT_LOG.md", merged, evidence, lines)
    print("OK: SHIFT_LOG.md byte-safe union done")


def resolve_pair(path, base, ours, theirs, mine, their, evidence):
    """m2 ROADMAP/ACCEPT_LOG: merged = base + ours(115 side) + theirs(116 side)."""
    print("%s: base=%d ours=%d theirs=%d" % (path, len(base), len(ours), len(theirs)))
    assert ours.startswith(base), "%s ours not pure append -> stop" % path
    assert theirs.startswith(base), "%s theirs not pure append -> stop" % path
    add_ours = ours[len(base):]
    add_theirs = theirs[len(base):]
    print("appends: ours+%d theirs+%d" % (len(add_ours), len(add_theirs)))
    assert base.find(mine) == -1, "%s: base already has %s" % (path, mine.decode())
    assert base.find(their) == -1, "%s: base already has %s" % (path, their.decode())
    assert add_ours.find(mine) != -1, "%s: ours append lacks %s" % (path, mine.decode())
    assert add_theirs.find(their) != -1, "%s: theirs append lacks %s" % (path, their.decode())
    segs, seam = seam_fix([add_ours, add_theirs])
    merged = base + segs[0] + segs[1]
    p_mine = merged.find(mine)
    p_their = merged.find(their)
    assert p_mine >= len(base), "%s: %s not in append region" % (path, mine.decode())
    assert p_their >= len(base), "%s: %s not in append region" % (path, their.decode())
    assert p_mine < p_their, "%s: night order 115<116 failed" % path
    print("order 115<116: %s@%d < %s@%d" % (mine.decode(), p_mine, their.decode(), p_their))
    sentinels(merged, base, [add_ours, add_theirs], [mine, their])
    assert len(base) + len(add_ours) + len(add_theirs) + seam == len(merged), \
        "byte account mismatch"
    print("account: base %d + ours %d + theirs %d + seam %d = merged %d"
          % (len(base), len(add_ours), len(add_theirs), seam, len(merged)))
    lines = [b"path=%s base=%d ours=%d theirs=%d\n" % (path.encode(), len(base), len(ours), len(theirs)),
             b"add_ours=%d add_theirs=%d seam=%d merged=%d\n"
             % (len(add_ours), len(add_theirs), seam, len(merged)),
             b"add_ours repr:\n" + repr(add_ours).encode("utf-8") + b"\n",
             b"add_theirs repr:\n" + repr(add_theirs).encode("utf-8") + b"\n"]
    finish(path, merged, evidence, lines)
    print("OK: %s byte-safe union done" % path)


def main():
    mode = sys.argv[1]
    confl = sh(["git", "diff", "--name-only", "--diff-filter=U"]).decode().split()
    if mode == "m1":
        assert confl == ["SHIFT_LOG.md"], "conflicts != [SHIFT_LOG.md]: %s" % confl
        resolve_shift(stage(1, "SHIFT_LOG.md"), stage(2, "SHIFT_LOG.md"),
                      stage(3, "SHIFT_LOG.md"),
                      evidence="eval/night117_merge_m1_stages.txt")
    elif mode == "m2":
        assert sorted(confl) == ["ACCEPT_LOG.md", "ROADMAP.md", "SHIFT_LOG.md"], \
            "conflicts != 3 expected: %s" % confl
        base_s = stage(1, "SHIFT_LOG.md")
        n115_blob = sh(["git", "show", "%s:SHIFT_LOG.md" % N115_TIP])
        assert n115_blob.startswith(base_s), "N115 tip blob not base-append"
        n115part = n115_blob[len(base_s):]
        resolve_shift(base_s, stage(2, "SHIFT_LOG.md"), stage(3, "SHIFT_LOG.md"),
                      m115part=n115part, evidence="eval/night117_merge_m2_stages.txt")
        resolve_pair("ROADMAP.md", stage(1, "ROADMAP.md"), stage(2, "ROADMAP.md"),
                     stage(3, "ROADMAP.md"), b"Night 115", b"Night 116",
                     "eval/night117_merge_m2_roadmap.txt")
        resolve_pair("ACCEPT_LOG.md", stage(1, "ACCEPT_LOG.md"),
                     stage(2, "ACCEPT_LOG.md"), stage(3, "ACCEPT_LOG.md"),
                     b" | 115 | ", b" | 116 | ",
                     "eval/night117_merge_m2_acceptlog.txt")
    else:
        sys.exit("mode must be m1 or m2")


if __name__ == "__main__":
    main()
