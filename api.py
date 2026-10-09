from fastapi import FastAPI, UploadFile, File, Form
from rparser.pipeline import parse_resume
from rparser import matcher, db

app = FastAPI(title="Resume Parser API", version="1.0")


@app.post("/parse")
async def parse(file: UploadFile = File(...), save: bool = False):
    r = parse_resume(await file.read(), file.filename)
    if save:
        r["id"] = db.save(file.filename, r)
    return {k: v for k, v in r.items() if k != "raw_text"}


@app.post("/match")
async def match(file: UploadFile = File(...), jd: str = Form(...)):
    r = parse_resume(await file.read(), file.filename)
    return matcher.match(r, jd)


@app.get("/candidates")
def candidates():
    return [{k: v for k, v in c.items() if k != "raw_text"} for c in db.all_candidates()]