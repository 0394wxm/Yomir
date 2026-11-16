# -*- coding: utf-8 -*-
r"""
try_guwenbert.py — 下载 guwenbert-base.supar 并对比 BERT 模式訓読（NIGHT3）。

背景：udkanbun 的 BERT 模式（udkundoku.load(BERT="guwenbert-base")）走
SuPar 依存句法器，对切分/解析质量预期有最大提升。模型文件在：

    https://raw.githubusercontent.com/KoichiYasuoka/UD-Kanbun/master/udkanbun/supar-kanbun/guwenbert-base.supar
    （~400MB 级；raw.githubusercontent.com 本机被墙，jsdelivr 有 20MB 上限放不下）

使用：在 **网络可达 GitHub** 的环境跑：
    python -X utf8 tools/try_guwenbert.py            # 下载+对比
    python -X utf8 tools/try_guwenbert.py --download-only

前置依赖（模型就位后还需要）：
    python -m pip install supar -i https://pypi.tuna.tsinghua.edu.cn/simple
    （supar 依赖 torch，CPU 版 wheel 约数百 MB）

行为：
1. 读 site-packages\udkanbun\supar-kanbun\filesize.txt 里 guwenbert-base.supar 的期望字节数
2. 按 URL 候选顺序下载（可用 GITHUB_MIRROR 环境变量加镜像前缀）
3. 大小对上后放到位，再调 udkundoku.load(BERT="guwenbert-base")
4. 对三句经典例句分别用 默认模式 / guwenbert 模式 各跑一遍输出，供人工对比
"""
import os
import shutil
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

RAW = "https://raw.githubusercontent.com/KoichiYasuoka/UD-Kanbun/master/udkanbun/supar-kanbun/"
MODEL = "guwenbert-base.supar"
import site

SITE = os.environ.get("KANBUN_PYTHON_SITE", r"D:\Python312\Lib\site-packages")
SUPAR_DIR = os.path.join(SITE, "udkanbun", "supar-kanbun")
TARGET = os.path.join(SUPAR_DIR, MODEL)
SENTENCES = ["王顧左右而言他", "不入虎穴不得虎子", "欲治其國者先齊其家"]


def expected_size():
    fs = os.path.join(SUPAR_DIR, "filesize.txt")
    if not os.path.isfile(fs):
        print("[size] filesize.txt 不存在（udkanbun 包应自带）:", fs)
        return None
    with open(fs, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2 and parts[0] == MODEL:
                return int(parts[1])
    print("[size] filesize.txt 里没有", MODEL)
    return None


def download():
    mirror = os.environ.get("GITHUB_MIRROR", "").rstrip("/")
    base = (mirror + "/" + RAW) if mirror else RAW
    exp = expected_size()
    if exp and os.path.isfile(TARGET) and os.path.getsize(TARGET) == exp:
        print("[download] 已存在且大小匹配:", TARGET)
        return True
    print("[download] chunked: %s<MODEL>.1 .2 ... expected_total=%s" % (base, exp), flush=True)
    # 官方仓库把模型切成 80MB 分片（.1 .2 .3...），udkanbun.download 也是这么拼的。
    # 每片带断点续传 + 3 次重试；总预算 30 分钟（GUWENBERT_BUDGET_MIN 可调）。
    import time as _t

    budget = float(os.environ.get("GUWENBERT_BUDGET_MIN", "30")) * 60
    deadline = _t.time() + budget
    tmp = TARGET + ".part"
    mode = "ab"
    got = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    i = 1
    while exp is None or got < exp:
        if _t.time() > deadline:
            print("[download] 超过 %.0f 分钟预算，停止（.part 保留，可续传）" % (budget / 60), flush=True)
            return False
        chunk_url = "%s%s.%d" % (base, MODEL, i)
        ok = False
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(chunk_url)
                if os.path.exists(chunk_tmp := tmp + ".chunk%d" % i):
                    req.add_header("Range", "bytes=%d-" % os.path.getsize(chunk_tmp))
                with urllib.request.urlopen(req, timeout=60) as r, open(chunk_tmp, "ab") as f:
                    while True:
                        data = r.read(1 << 20)
                        if not data:
                            break
                        f.write(data)
                size = os.path.getsize(chunk_tmp)
                # 分片大小: 官方每片 80MB（最后一片除外）；读到 0 字节说明越界
                if size == 0:
                    break
                with open(chunk_tmp, "rb") as f:
                    shutil.copyfileobj(f, open(tmp, mode and "ab"), 1 << 20)
                got += size
                os.remove(chunk_tmp)
                print("[download] chunk %d done, total %.1f MB / %s"
                      % (i, got / 1e6, ("%.1f MB" % (exp / 1e6)) if exp else "?"), flush=True)
                ok = True
                break
            except Exception as e:
                print("[download] chunk %d attempt %d failed: %r" % (i, attempt, e), flush=True)
                if _t.time() > deadline:
                    break
        if not ok:
            print("[download] chunk %d 重试耗尽，停止" % i, flush=True)
            return False
        i += 1
        mode = "ab"
    if exp and got != exp:
        print("[download] 大小不符 expected=%d got=%d，保留 .part 供续传检查" % (exp, got))
        return False
    os.replace(tmp, TARGET)
    print("[download] saved:", TARGET, flush=True)
    return True


def compare():
    import udkundoku

    print("=== 默认模式（UDPipe）===", flush=True)
    base = udkundoku.load(MeCab=True, Danku=False)
    for s in SENTENCES:
        print(s, "->", udkundoku.translate(base(s), raw=True).count("# text = ") and
              "\n".join(l[9:] for l in udkundoku.translate(base(s), raw=True).split("\n") if l.startswith("# text = ")), flush=True)
    print("=== guwenbert-base（SuPar）===", flush=True)
    # torch 2.6+ 默认 weights_only=True，supar 的 checkpoint 是完整 pickle
    # （含 supar.utils.config.Config）。来源可信：KoichiYasuoka 官方仓库，
    # 且字节数与包内 filesize.txt 逐一核对——这里局部关闭该开关，不改第三方库。
    import torch

    _orig_load = torch.load

    def _trusted_load(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return _orig_load(*args, **kwargs)

    torch.load = _trusted_load
    # udkundoku.load() 不暴露 BERT 参数；BERT 模式在 udkanbun.load() 上（Night3 实测）
    import udkanbun

    bert = udkanbun.load(MeCab=True, Danku=False, BERT="guwenbert-base")
    for s in SENTENCES:
        t0 = time.time()
        raw = udkundoku.translate(bert(s), raw=True)
        out = "\n".join(l[9:] for l in raw.split("\n") if l.startswith("# text = "))
        print(s, "->", out, "(%.1fs)" % (time.time() - t0), flush=True)


def main():
    os.makedirs(SUPAR_DIR, exist_ok=True)
    if not download():
        return 1
    if "--download-only" in sys.argv:
        return 0
    try:
        import supar  # noqa: F401
    except ImportError:
        print("[compare] 缺 supar/torch：先 python -m pip install supar -i https://pypi.tuna.tsinghua.edu.cn/simple 再跑对比。")
        return 0
    compare()
    return 0


if __name__ == "__main__":
    sys.exit(main())
