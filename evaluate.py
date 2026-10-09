import json
import sys
from rparser.pipeline import parse_resume

# gold.json: [{"file": "resumes/a.pdf", "skills": ["Python", "SQL"], "email": "a@b.com"}, ...]
gold = json.load(open(sys.argv[1]))
tp = fp = fn = 0
email_ok = 0
for g in gold:
    pred = parse_resume(open(g["file"], "rb").read(), g["file"])
    P, G = {s.lower() for s in pred["skills"]}, {s.lower() for s in g["skills"]}
    tp += len(P & G); fp += len(P - G); fn += len(G - P)
    email_ok += pred["email"] == g.get("email")

p = tp / (tp + fp) if tp + fp else 0
r = tp / (tp + fn) if tp + fn else 0
print(f"Skills  P={p:.2f}  R={r:.2f}  F1={2*p*r/(p+r) if p+r else 0:.2f}")
print(f"Email accuracy = {email_ok/len(gold):.2f}")