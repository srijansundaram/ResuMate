import json
import sys
from rparser.pipeline import parse_resume
from rparser.skills import normalize

gold = json.load(open(sys.argv[1]))
norm = lambda items: {normalize(s).lower() for s in items}
groups = {}

for g in gold:
    r = parse_resume(open(g["file"], "rb").read(), g["file"])
    P, G = norm(r["skills"]), norm(g["skills"])
    key = "Scanned/JPG (OCR)" if g["file"].lower().endswith((".jpg", ".jpeg", ".png")) else "Text PDF"
    for k in (key, "Overall"):
        s = groups.setdefault(k, dict(tp=0, fp=0, fn=0, name=0, email=0, n=0))
        s["tp"] += len(P & G); s["fp"] += len(P - G); s["fn"] += len(G - P)
        s["name"] += (r["name"] or "").lower() == (g["name"] or "").lower()
        s["email"] += (r["email"] or "").lower() == (g["email"] or "").lower()
        s["n"] += 1
    print(f"{g['file']}\n   extra={sorted(P - G)}  missed={sorted(G - P)}"
          f"  name={r['name']!r}  email={r['email']!r}")

print()
for k, s in groups.items():
    p = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else 0
    rc = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else 0
    f1 = 2 * p * rc / (p + rc) if p + rc else 0
    print(f"{k:18} N={s['n']}  P={p:.2f} R={rc:.2f} F1={f1:.2f}  "
          f"Name={s['name']}/{s['n']}  Email={s['email']}/{s['n']}")