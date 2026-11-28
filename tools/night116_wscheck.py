import json, sys, io
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from backend.main import strip_annotation, has_ruby_annotation
doc = json.load(io.open("eval/night111_results_8165.json", encoding="utf-8"))
bad = []
for r in doc["results"]:
    s = r["hakubun"] or ""
    if has_ruby_annotation(s):
        st = strip_annotation(s)
        if st != st.strip():
            bad.append((r["id"], repr(st[:20]), repr(st[-20:])))
io.open("eval/night116_wscheck.txt", "w", encoding="utf-8", newline="\n").write(
    "rows_with_edge_ws=%d %s\n" % (len(bad), bad[:5]))
print("EDGE_WS_ROWS", len(bad))
