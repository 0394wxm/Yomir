# -*- coding: utf-8 -*-
"""night74_log.py — N74 helper: append one timestamped line to SHIFT_LOG.md.

Binary-append in UTF-8; existing bytes (incl. historical mixed-encoding
content) are never rewritten. Text is expected to be ASCII (N72's CJK argv
came out as mojibake on this host; N73's ASCII lines are clean).
Usage (repo root): python tools/night74_log.py <text...>
"""
import sys
import time


def main():
    text = " ".join(sys.argv[1:])
    ts = time.strftime("%Y-%m-%dT%H:%M")
    line = "[%s N74] %s\n" % (ts, text)
    with open("SHIFT_LOG.md", "ab") as f:
        f.write(line.encode("utf-8"))
    print(line.rstrip())


if __name__ == "__main__":
    main()
