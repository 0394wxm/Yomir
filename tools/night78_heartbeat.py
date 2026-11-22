# -*- coding: utf-8 -*-
"""night78_heartbeat.py — SHIFT_LOG.md 心跳（Night 78 专用）。

只做二进制末尾追加（open 'ab'），不读改写全文件，保证历史混编码字节
（含 0xF3@807）原样不动。用法:
  python tools/night78_heartbeat.py "消息"
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "SHIFT_LOG.md"


def main() -> None:
    msg = " ".join(sys.argv[1:]).strip() or "(empty)"
    before = LOG.stat().st_size
    line = "[%s N78] %s\n" % (datetime.now().isoformat(timespec="minutes"), msg)
    with open(LOG, "ab") as f:
        f.write(line.encode("utf-8"))
    after = LOG.stat().st_size
    print("appended %d bytes (size %d -> %d), prefix untouched" % (len(line.encode("utf-8")), before, after))


if __name__ == "__main__":
    main()
