# -*- coding: utf-8 -*-
"""day4_raw_io.py — 裸文件写入/fsync 在 D: 与 C: 临时目录的对比 + 分段打点。

不做 SQLite，只测：write(4KB) / flush / os.fsync，各 10 次。
区分「磁盘本身慢」与「SQLite 的同步策略」。
"""
import os
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ms():
    return time.perf_counter() * 1000.0


def bench(path, n=10):
    w = f = s = 0.0
    for i in range(n):
        t0 = ms()
        fh = open(path, "wb")
        fh.write(b"x" * 4096)
        t1 = ms()
        fh.flush()
        t2 = ms()
        os.fsync(fh.fileno())
        t3 = ms()
        fh.close()
        w += t1 - t0
        f += t2 - t1
        s += t3 - t2
    return w / n, f / n, s / n


def main():
    cands = [
        ("D: 项目目录", os.path.join(ROOT, "d4_io_probe.bin")),
        ("D: 根目录", "D:\\d4_io_probe.bin"),
        ("C: %TEMP%", os.path.join(tempfile.gettempdir(), "d4_io_probe.bin")),
    ]
    print("%-14s %10s %10s %10s" % ("位置", "write", "flush", "fsync"))
    for label, p in cands:
        try:
            w, f, s = bench(p)
            print("%-14s %8.1fms %8.1fms %8.1fms  (%s)" % (label, w, f, s, p))
        except OSError as e:
            print("%-14s 失败：%s" % (label, e))
        finally:
            try:
                os.remove(p)
            except OSError:
                pass


if __name__ == "__main__":
    main()
