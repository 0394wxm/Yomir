# -*- coding: utf-8 -*-
"""day6_stage_sidecar.py — 把 PyInstaller 的 onedir 产物搬到 Tauri 的 resources 目录。

为什么需要这一步：
  tauri.conf.json 里 `bundle.resources: ["sidecar/**/*"]` 是相对 src-tauri/ 的
  glob，文件必须真的在那儿，Tauri 才会在打包时把它拷进安装目录。而 PyInstaller
  产物在项目根的 dist/kanbun-sidecar/。两者不能混（dist/ 是整个项目的构建输出，
  src-tauri/ 是壳的构建输入），用一个显式的搬运步骤把边界划清楚。

用法：
  python tools/day6_stage_sidecar.py            # 复制
  python tools/day6_stage_sidecar.py --check    # 只检查是否已就位
  python tools/day6_stage_sidecar.py --clean    # 删掉暂存目录
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "dist", "kanbun-sidecar")
DST = os.path.join(ROOT, "frontend", "src-tauri", "sidecar")


def size_of(path):
    tot = n = 0
    for dp, _, fs in os.walk(path):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(dp, f))
                n += 1
            except OSError:
                pass
    return n, tot


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""

    if arg == "--clean":
        if os.path.isdir(DST):
            shutil.rmtree(DST)
            print("已删除", DST)
        return 0

    if not os.path.isdir(SRC):
        print("找不到 PyInstaller 产物:", SRC)
        print("先运行: python -m PyInstaller --noconfirm kanbun_sidecar.spec")
        return 1

    exe_src = os.path.join(SRC, "kanbun-sidecar.exe")
    if not os.path.isfile(exe_src):
        print("产物不完整，缺 kanbun-sidecar.exe:", SRC)
        return 1

    sn, ss = size_of(SRC)

    if arg == "--check":
        if not os.path.isdir(DST):
            print("未暂存:", DST)
            return 1
        dn, ds = size_of(DST)
        ok = dn == sn and ds == ss
        print("源 %d files %.1f MB / 暂存 %d files %.1f MB -> %s"
              % (sn, ss / 1048576.0, dn, ds / 1048576.0, "一致" if ok else "不一致"))
        return 0 if ok else 1

    print("源: %s (%d files, %.1f MB)" % (SRC, sn, ss / 1048576.0))
    if os.path.isdir(DST):
        print("清掉旧暂存…")
        shutil.rmtree(DST)
    print("复制中（onedir 有 800+ 文件，D: 上约 1~3 分钟）…")
    shutil.copytree(SRC, DST)
    dn, ds = size_of(DST)
    print("完成: %s (%d files, %.1f MB)" % (DST, dn, ds / 1048576.0))
    if (dn, ds) != (sn, ss):
        print("警告: 复制后大小不一致")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
