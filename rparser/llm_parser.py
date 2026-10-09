import json
import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROMPT = """Extract resume data. Return ONLY valid JSON with keys:
name, email, phone, location, skills (list), education (list of {degree, institution, year}),
experience (list of {title, company, start, end}), total_years_experience (number).

RESUME:
"""
MODEL = "openrouter/free"


def llm_parse(text: str) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY first")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": MODEL,
              "messages": [{"role": "user", "content": PROMPT + text[:8000]}]},
        timeout=90)
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    raw = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", raw, re.S)  # free models often wrap JSON in extra text
    return json.loads(m.group())

def compare(spacy_result: dict, llm_result: dict) -> dict:
    a = {s.lower() for s in spacy_result["skills"]}
    b = {s.lower() for s in llm_result.get("skills", [])}
    inter = a & b
    p = len(inter) / len(a) if a else 0
    r = len(inter) / len(b) if b else 0
    return {
        "skills_agreement_f1": round(2 * p * r / (p + r), 2) if p + r else 0,
        "only_rule_based": sorted(a - b), "only_llm": sorted(b - a),
        "name_match": (spacy_result.get("name") or "").lower() == (llm_result.get("name") or "").lower(),
        "email_match": spacy_result.get("email") == llm_result.get("email"),
        "years": {"rule_based": spacy_result["total_years"], "llm": llm_result.get("total_years_experience")},
    }