# -*- coding: utf-8 -*-
"""night75_log.py — N75 helper: append one timestamped line to SHIFT_LOG.md.

Binary-append in UTF-8; existing bytes (incl. historical mixed-encoding
content) are never rewritten. Text is expected to be ASCII (CJK argv came
out as mojibake on this host in N72; N74 kept ASCII lines clean).
Usage (repo root): python tools/night75_log.py <text...>
"""
import sys
import time


def main():
    text = " ".join(sys.argv[1:])
    ts = time.strftime("%Y-%m-%dT%H:%M")
    line = "[%s N75] %s\n" % (ts, text)
    with open("SHIFT_LOG.md", "ab") as f:
        f.write(line.encode("utf-8"))
    try:
        print(line.rstrip())
    except UnicodeEncodeError:  # cp1252 控制台打不了 CJK，落盘已成功
        print("logged (%d chars, console-ascii only)" % len(line))


if __name__ == "__main__":
    main()
