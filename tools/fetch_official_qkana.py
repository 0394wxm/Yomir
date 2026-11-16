# -*- coding: utf-8 -*-
r"""
fetch_official_qkana.py — 下载官方 UniDic qkana 词典并替换本地 shim（NIGHT3）。

背景：import udkundoku 需要 unidic2ud/download/qkana/ 这个 MeCab 词典目录。
本机当前是 unidic_lite 冒充的 shim（tools/make_qkana_shim.py）。官方词典在：

    https://clrd.ninjal.ac.jp/unidic_archive/2203/UniDic-202203_60b_qkana.zip

本机直连 TLS 会被重置（Night1/Night2 各试过，curl exit 35）——本脚本供
**网络可达 NINJAL 的环境**（VPN / 境外机 / 手机热点）使用：

    python -X utf8 tools/fetch_official_qkana.py            # 下载+解压+替换
    python -X utf8 tools/fetch_official_qkana.py --download-only  # 只下载

行为：
1. 断点续传下载 zip 到 D:\kanbun-kakikudashi\ocr_runtime\qkana_official.zip
2. zipfile 校验 + 解压到临时目录
3. 校验 dicrc 存在（UniDic 词典根特征）
4. 把现有 qkana 目录备份为 qkana_shim_backup_<时间戳>，再放官方版
5. 重启后端后生效（unidic2ud 只检查目录存在，无需重装包）
"""
import os
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://clrd.ninjal.ac.jp/unidic_archive/2203/UniDic-202203_60b_qkana.zip"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(PROJECT_ROOT, "ocr_runtime", "qkana_official.zip")
QKANA_DIR = os.path.join(os.environ.get("KANBUN_PYTHON_SITE", r"D:\Python312\Lib\site-packages"),
                         "unidic2ud", "download", "qkana")


def download():
    os.makedirs(os.path.dirname(ZIP_PATH), exist_ok=True)
    part = ZIP_PATH + ".part"
    resume_from = os.path.getsize(part) if os.path.exists(part) else 0
    req = urllib.request.Request(URL)
    if resume_from:
        req.add_header("Range", "bytes=%d-" % resume_from)
    print("[download] %s (resume from %d bytes)" % (URL, resume_from), flush=True)
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(part, "ab") as f:
            total = r.headers.get("Content-Length")
            print("[download] content-length header:", total, flush=True)
            n = 0
            t0 = time.time()
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                n += len(chunk)
                if n % (50 << 20) < (1 << 20):
                    speed = n / max(1e-6, time.time() - t0) / 1e6
                    print("[download] %d MB (%.1f MB/s)" % ((resume_from + n) >> 20, speed), flush=True)
    except Exception as e:
        print("[download] FAILED: %r" % (e,), flush=True)
        print("[download] 本机网络到 clrd.ninjal.ac.jp 不可达时属预期；请在可达环境重跑本脚本。", flush=True)
        return False
    os.replace(part, ZIP_PATH)
    print("[download] saved:", ZIP_PATH, os.path.getsize(ZIP_PATH), "bytes", flush=True)
    return True


def install():
    with zipfile.ZipFile(ZIP_PATH) as z:
        bad = z.testzip()
        if bad:
            print("[install] zip corrupt at:", bad)
            return False
        tmp = tempfile.mkdtemp(prefix="qkana_extract_")
        z.extractall(tmp)
    # UniDic zip 解开是单层目录（含 dicrc）或直接文件两种版式，找 dicrc
    src = tmp
    if not os.path.isfile(os.path.join(src, "dicrc")):
        for name in os.listdir(tmp):
            p = os.path.join(tmp, name)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "dicrc")):
                src = p
                break
    if not os.path.isfile(os.path.join(src, "dicrc")):
        print("[install] 解压后找不到 dicrc，版式与预期不符，未做替换:", tmp)
        return False
    if os.path.isdir(QKANA_DIR):
        backup = QKANA_DIR + "_shim_backup_" + time.strftime("%Y%m%d_%H%M%S")
        os.rename(QKANA_DIR, backup)
        print("[install] shim backed up ->", backup, flush=True)
    os.rename(src, QKANA_DIR)
    shutil.rmtree(tmp, ignore_errors=True)
    print("[install] official qkana installed ->", QKANA_DIR, flush=True)
    print("[install] 重启 uvicorn 后生效（import udkundoku 会自动用官方词典）。", flush=True)
    return True


def main():
    ok = download()
    if not ok:
        return 1
    if "--download-only" in sys.argv:
        return 0
    return 0 if install() else 1


if __name__ == "__main__":
    sys.exit(main())
