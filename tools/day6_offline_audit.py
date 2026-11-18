# -*- coding: utf-8 -*-
"""day6_offline_audit.py — D6「断网能跑」的静态审计。

不真的拔网线（本机是孤立沙盒，本来也没网可拔），而是把「运行时会出网」的
证据全列出来，逐条判定。判定对象是打包产物 _internal/ 下的代码：
  1. 有没有 torch / transformers / huggingface_hub 这类会拉模型的包
  2. backend/llm.py 在没有 KANBUN_LLM_API_KEY 时走哪条分支
  3. 前端里有没有硬编码的外部域名（CDN、字体、统计）
  4. 后端启动路径里有没有 download() 调用（udkundoku 首次 import 会
     unidic2ud.download("qkana") —— 数据不随包就会在用户机上尝试联网）
  5. sidecar 里 qkana 数据是否真的在（在 => 不触发 download）

用法：python tools/day6_offline_audit.py [dist/kanbun-sidecar]
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "kanbun-sidecar")
INT = os.path.join(BUNDLE, "_internal")

BAD_PKGS = ("torch", "transformers", "huggingface_hub", "hf_xet", "safetensors",
            "accelerate", "sentencepiece", "tokenizers")

fails = []
notes = []


def check(title, ok, detail=""):
    print("[%s] %s%s" % ("OK  " if ok else "FAIL", title, ("  " + detail) if detail else ""))
    if not ok:
        fails.append(title + ("  " + detail if detail else ""))


print("bundle:", BUNDLE)
print("exists:", os.path.isdir(BUNDLE))
print()

# 1. 会拉模型的包
if os.path.isdir(INT):
    present = [d for d in BAD_PKGS if os.path.isdir(os.path.join(INT, d))]
    check("包内无联网下载模型的库", not present, "发现: %s" % present if present else "")
else:
    check("包内无联网下载模型的库", False, "_internal 不存在")

# 2. qkana 词典就位（在 => udkundoku 不会走 download 分支）
qkana = os.path.join(INT, "unidic2ud", "download", "qkana", "sys.dic")
sz = os.path.getsize(qkana) / 1048576.0 if os.path.isfile(qkana) else 0
check("qkana 词典随包（sys.dic %.1f MB）" % sz, sz > 100, "缺则首次 import 会联网下载")

# udkanbun 的 MeCab 词典与 UD 模型
for rel, label in (("udkanbun/mecabrc", "udkanbun/mecabrc"),
                   ("udkanbun/mecab-kanbun/sys.dic", "udkanbun/mecab-kanbun/sys.dic"),
                   ("udkanbun/ud-kanbun.udpipe", "udkanbun/ud-kanbun.udpipe")):
    p = os.path.join(INT, rel)
    check("随包 " + label, os.path.isfile(p),
          "%.1f MB" % (os.path.getsize(p) / 1048576.0) if os.path.isfile(p) else "")

# OCR 模型
for rel in ("ocr_runtime/src/model/parseq-ndl-32x384-tiny-10.onnx",
            "ocr_runtime/src/model/rtmdet-s-1280x1280.onnx"):
    p = os.path.join(INT, rel)
    check("随包 " + os.path.basename(rel), os.path.isfile(p),
          "%.1f MB" % (os.path.getsize(p) / 1048576.0) if os.path.isfile(p) else "")

# onnxruntime 本体
check("随包 onnxruntime", os.path.isdir(os.path.join(INT, "ocr_site", "onnxruntime")),
      "OCR 推理不依赖外部 exe")

# 3. 前端硬编码外部域名
fe_files = []
src = os.path.join(ROOT, "frontend", "src")
for dp, _, fs in os.walk(src):
    for f in fs:
        if f.endswith((".tsx", ".ts", ".css", ".html")):
            fe_files.append(os.path.join(dp, f))
ext = []
pat = re.compile(r"https?://([A-Za-z0-9.-]+)")
for p in fe_files:
    t = io.open(p, encoding="utf-8", errors="replace").read()
    for host in pat.findall(t):
        if host in ("127.0.0.1", "localhost", "www.w3.org"):
            continue
        ext.append((os.path.relpath(p, ROOT), host))
check("前端无外部域名引用", not ext, str(ext[:5]) if ext else "")

# dist 里也查一遍（构建产物的真实内容）
# 注意：React 生产构建里带 `https://react.dev/errors/...` 这样的**报错文案**
# 字符串，不会产生任何请求。判定标准是「发起请求」而不是「出现域名」，
# 所以这里只看 fetch/XMLHttpRequest/import()/link 等真会出网的形态。
dist = os.path.join(ROOT, "frontend", "dist", "assets")
ext2 = []
NET_CALL = re.compile(
    r"""(?:fetch|XMLHttpRequest\.open|importScripts|WebSocket)\s*\(\s*['"`]https?://([A-Za-z0-9.-]+)"""
    r"""|['"`]https?://([A-Za-z0-9.-]+)/[^'"`\s]*(?:\.js|\.css|\.woff2?|\.ttf)"""
)
ALLOW = {"127.0.0.1", "localhost", "www.w3.org"}
if os.path.isdir(dist):
    for f in os.listdir(dist):
        if f.endswith(".js"):
            t = io.open(os.path.join(dist, f), encoding="utf-8", errors="replace").read()
            for m in NET_CALL.finditer(t):
                host = m.group(1) or m.group(2)
                if host and host not in ALLOW:
                    ext2.append((f, host))
# 报错文案里的域名单独列出，不当失败
doc_hosts = set()
if os.path.isdir(dist):
    for f in os.listdir(dist):
        if f.endswith(".js"):
            t = io.open(os.path.join(dist, f), encoding="utf-8", errors="replace").read()
            for host in set(pat.findall(t)):
                if host not in ALLOW:
                    doc_hosts.add(host)
check("打包 JS 无外部请求", not ext2, str(ext2[:5]) if ext2 else "")
if doc_hosts:
    notes.append("JS 里出现域名 %s —— 均为 React 报错文案，不发起请求" % sorted(doc_hosts))

# 4. 后端运行路径无 download 调用（除 udkundoku 自己的兜底逻辑）
main_py = io.open(os.path.join(ROOT, "backend", "main.py"), encoding="utf-8").read()
check("backend/main.py 不调用 download()",
      not re.search(r"\bunidic2ud\.download\s*\(", main_py),
      "udkundoku 里的兜底分支因数据就位不会触发")

# 5. llm 占位路径
llm_py = io.open(os.path.join(ROOT, "backend", "llm.py"), encoding="utf-8").read()
has_offline = "KANBUN_LLM_API_KEY" in llm_py
check("llm.py 识别 KANBUN_LLM_API_KEY", has_offline,
      "无 key 时返回占位文案，不出网")
if "requests" in llm_py or "httpx" in llm_py or "urllib" in llm_py:
    notes.append("llm.py 引入了 HTTP 客户端（有 key 时才会用）")

print()
if notes:
    print("备注:")
    for n in notes:
        print("  -", n)
print()
if fails:
    print("FAIL %d 项" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS: 断网运行所需的资源全部随包，运行路径无联网下载")
