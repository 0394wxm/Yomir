# -*- coding: utf-8 -*-
"""night82_log.py — N82 helper: append one timestamped line to SHIFT_LOG.md.

Binary-append in UTF-8; existing bytes are never rewritten (N74/N80 precedent).
Absolute path (N66 lesson: relative path lands in the wrong directory).
Text is expected to be ASCII (N72 lesson).
Usage: python tools/night82_log.py <text...>
"""
import sys
import time

LOGPATH = r"D:\kanbun-rulel\SHIFT_LOG.md"


def main():
    text = " ".join(sys.argv[1:])
    ts = time.strftime("%Y-%m-%dT%H:%M")
    line = "[%s N82] %s\n" % (ts, text)
    with open(LOGPATH, "ab") as f:
        f.write(line.encode("utf-8"))
    print(line.rstrip())


if __name__ == "__main__":
    main()
