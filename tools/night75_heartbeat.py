# -*- coding: utf-8 -*-
"""night75_heartbeat.py — N75 hourly heartbeat.

Sleeps `hours` times for 3600s each, appending one ASCII line to SHIFT_LOG.md
via binary UTF-8 append (never rewrites existing bytes).
Usage (repo root): python tools/night75_heartbeat.py [hours]
"""
import sys
import time


def main():
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    for i in range(hours):
        time.sleep(3600)
        ts = time.strftime("%Y-%m-%dT%H:%M")
        line = "[%s N75] heartbeat alive (%d/%d)\n" % (ts, i + 1, hours)
        with open("SHIFT_LOG.md", "ab") as f:
            f.write(line.encode("utf-8"))


if __name__ == "__main__":
    main()
