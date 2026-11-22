# -*- coding: utf-8 -*-
"""night80_log.py — N80 helper: append one timestamped line to SHIFT_LOG.md.

Binary-append in UTF-8; existing bytes are never rewritten (N74 precedent).
Text is expected to be ASCII (N72 lesson).
Usage (repo root): python tools/night80_log.py <text...>
"""
import sys
import time


def main():
    text = " ".join(sys.argv[1:])
    ts = time.strftime("%Y-%m-%dT%H:%M")
    line = "[%s N80] %s\n" % (ts, text)
    with open("SHIFT_LOG.md", "ab") as f:
        f.write(line.encode("utf-8"))
    print(line.rstrip())


if __name__ == "__main__":
    main()
