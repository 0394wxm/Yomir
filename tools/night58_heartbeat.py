# -*- coding: utf-8 -*-
"""night58_heartbeat.py — SHIFT_LOG.md 心跳行二进制追加（N58）。

用法: python -I tools/night58_heartbeat.py "N58 <消息>"
"""
import datetime
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "SHIFT_LOG.md")


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "heartbeat"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = u"| %s | %s |\n" % (now, msg)
    with io.open(PATH, "ab") as f:
        f.write(line.encode("utf-8"))
    print("appended: %s" % line.strip())


if __name__ == "__main__":
    main()
