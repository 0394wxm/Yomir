# -*- coding: utf-8 -*-
"""
udkundoku_cli.py — Windows 管道安全的 udkundoku 命令行包装（Night 2）。

背景（见 REPORT_NIGHT1.md §2.6）：
- `python -m udkundoku.cli` 在 GBK 控制台下输出变成 ????（编码问题）；
- chcp 65001 下又会触发 cli.py 的 Danku 分支，SegShenShen/SegUDKanbun 在
  udpipe.process 上崩 TypeError。

本包装的做法：
1. stdin 字节流先试 UTF-8、失败再试 GBK 解码，输出统一 UTF-8；
2. 不复刻 cli.py 的 seg 判定（那是触发 Danku 崩溃的源头），固定
   load(MeCab=True, Danku=False)，自己按句号/顿号分句；
3. 输出与 `udkundoku -j` 等价（只打 # text 行）。

用法: echo 不入虎穴不得虎子 | python -X utf8 tools/udkundoku_cli.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def read_stdin_text() -> str:
    raw = sys.stdin.buffer.read()
    for enc in ("utf-8", "gbk", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def main():
    import udkundoku

    lzh = udkundoku.load(MeCab=True, Danku=False)
    text = read_stdin_text()
    for line in text.replace("\r", "").split("\n"):
        s = line.strip()
        if not s:
            continue
        # 与 udkanbun 一致：句号/顿号处断句后再整段送入
        for t in udkundoku.translate(lzh(s), raw=True).split("\n"):
            if t.startswith("# text = "):
                print(t[9:])


if __name__ == "__main__":
    main()
