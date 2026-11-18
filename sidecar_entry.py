# -*- coding: utf-8 -*-
"""sidecar_entry.py — D6: 桌面壳随附的后端进程入口（PyInstaller 打包目标）。

与 `python -m uvicorn backend.main:app` 的区别：
1. **不依赖 cwd**：被打成 exe 后 cwd 是任意的，`.spec` 里用 --add-data 把
   backend/ 与 udkundoku/unidic2ud 的数据目录塞进 `_MEIPASS`，这里负责把它们
   挂到 sys.path 与 unidic2ud 期望的位置。
2. **端口可协商**：桌面上 8000 可能被别的进程占着。这里从 8000 起找第一个
   空闲端口，找到后既传给 uvicorn，也通过 stdout 打印 `KANBUN_PORT=<n>`，
   Rust 侧读这一行就知道该把窗口指向哪里。
3. **不弹控制台**：release 下 Rust 端用 windows_subsystem=windows 启动，
   这里的 stdout 只在父进程管道里存在。
4. **只监听 127.0.0.1**：不要暴露到局域网。

退出信号：uvicorn 自己会处理 SIGTERM/CTRL_BREAK；Rust 侧在窗口关闭时
先尝试 graceful 关，超时再 kill（见 main.rs）。
"""
import os
import socket
import sys


def _free_port(start=8000, tries=40):
    for p in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
            except OSError:
                continue
            return p
    raise RuntimeError("8000-%d 全部被占用" % (start + tries - 1))


def _resource_root():
    """PyInstaller onefile/onedir 下资源解压目录；源码运行时是项目根。"""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _bootstrap_paths():
    root = _resource_root()
    # backend 包所在目录
    for cand in (root, os.path.join(root, "app")):
        if os.path.isdir(os.path.join(cand, "backend")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            break

    # unidic2ud 的数据目录：包本身随 exe 一起解压，路径已正确，无需搬运。
    # MeCab 词典由 unidic2ud 自己按包内相对路径寻找（见 unidic2ud/mecab.py）。
    # 这里只把 OCR 的 site-packages 指到随包目录，避免依赖开发机的 D:\dlkotenocr-lite。
    ocr_site = os.path.join(root, "ocr_site")
    if os.path.isdir(ocr_site) and "KANBUN_OCR_SITE" not in os.environ:
        os.environ["KANBUN_OCR_SITE"] = ocr_site
    ocr_src = os.path.join(root, "ocr_runtime", "src")
    if os.path.isdir(ocr_src) and "KANBUN_OCR_SRC" not in os.environ:
        os.environ["KANBUN_OCR_SRC"] = ocr_src


def main():
    _bootstrap_paths()

    port = _free_port()
    # 父进程（Rust）读这一行决定窗口 URL。必须先于 uvicorn 启动打印并 flush，
    # 否则窗口会先指向一个还没起来的端口。
    sys.stdout.write("KANBUN_PORT=%d\n" % port)
    sys.stdout.flush()

    os.environ.setdefault("KANBUN_SIDECAR", "1")

    import uvicorn
    from backend.main import app

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info", access_log=False)


if __name__ == "__main__":
    main()
