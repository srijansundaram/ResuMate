import json
from pathlib import Path
from rparser.pipeline import parse_resume

out = []
for f in sorted(p for p in Path("resumes").iterdir() if p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}):
    r = parse_resume(f.read_bytes(), f.name)
    out.append({"file": str(f), "name": r["name"], "email": r["email"], "skills": r["skills"]})
Path("gold.json").write_text(json.dumps(out, indent=2))
print(f"Wrote gold.json with {len(out)} resumes")