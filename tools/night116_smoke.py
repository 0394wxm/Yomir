# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from backend.main import RUBY_SPAN_RE, has_ruby_annotation, strip_annotation

lines = []
doc = json.load(io.open("eval/night111_results_8165.json", encoding="utf-8"))
rows = {r["id"]: r for r in doc["results"]}
lines.append("helpers import OK, RUBY_SPAN_RE=%s" % RUBY_SPAN_RE.pattern)

# 残渣 2 行：剥前注记 span 数、剥后注记 span 数、幂等
for rid in ("rikutou59-2", "soji07-6"):
    hb = rows[rid]["hakubun"]
    st = strip_annotation(hb)
    lines.append("%s: has=%s spans_before=%d spans_after=%d idem=%s" % (
        rid, has_ruby_annotation(hb), len(RUBY_SPAN_RE.findall(hb)),
        len(RUBY_SPAN_RE.findall(st)), strip_annotation(st) == st))

# rongo 编号 6 行须假 + dangling/空括号保留
rongo_ids = ["rongo1125-1", "rongo1125b-1", "rongo1125c-1", "rongo1125d-1", "rongo1125e-1", "rongo1125f-1"]
lines.append("rongo 6 行 has_ruby_annotation 全假: %s" % [has_ruby_annotation(rows[i]["hakubun"]) for i in rongo_ids])
dang = [i for i, r in rows.items() if "）" in r["hakubun"] and "（" not in r["hakubun"]]
lines.append("dangling ） %d 行 identity: %s" % (len(dang), all(strip_annotation(rows[i]["hakubun"]) == rows[i]["hakubun"] for i in dang)))

# 全 8165 行 identity/幂等/剥后无括号 快算
n_ident = n_idem = n_clean = n_f1 = 0
for r in doc["results"]:
    s = r["hakubun"] or ""
    if not has_ruby_annotation(s):
        if strip_annotation(s) == s: n_ident += 1
    if strip_annotation(strip_annotation(s)) == strip_annotation(s): n_idem += 1
    if has_ruby_annotation(s):
        n_f1 += 1
        st = strip_annotation(s)
        if "（" not in st and "）" not in st: n_clean += 1
lines.append("8165: identity %d/%d idem %d/8165 f1 %d clean_after %d/%d" % (n_ident, 8165-n_f1, n_idem, n_f1, n_clean, n_f1))

# sonshi09-38 剥后仍 kana
from backend.main import detect_text_type
st = strip_annotation(rows["sonshi09-38"]["hakubun"])
lines.append("sonshi09-38 strip 后 detect=%s (须 kana)" % detect_text_type(st))

io.open("eval/night116_smoke.txt", "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("SMOKE_OK")
