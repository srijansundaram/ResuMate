from langdetect import detect
from .extract_text import extract_text
from .sections import split_sections
from .entities import extract_entities
from .skills import extract_skills, categorize
from .experience import extract_experience, total_years, career_flags
from .classify import classify_domain, classify_seniority
from .ats import ats_check
from .extras import candidate_summary, interview_questions, salary_estimate, fake_skill_check


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    text, layout = extract_text(file_bytes, filename)
    sections = split_sections(text)
    ents = extract_entities(text, sections)
    skills = extract_skills(text)
    jobs = extract_experience(sections.get("experience", ""))
    years = total_years(jobs) if jobs else 0.0

    try:
        lang = detect(text[:1000])
    except Exception:
        lang = "unknown"

    r = {
        **ents,
        "language": lang,
        "skills": skills,
        "skill_categories": categorize(skills),
        "experience": jobs,
        "total_years": years,
        "career": career_flags(jobs),
        "projects": [l.strip() for l in sections.get("projects", "").splitlines() if l.strip()][:10],
        "domain": classify_domain(skills),
        "seniority": classify_seniority(years),
        "unverified_skills": fake_skill_check(skills, sections),
        "ats": ats_check(text, sections, ents, layout),
        "layout": layout,
        "raw_text": text,
    }
    r["summary"] = candidate_summary(r)
    r["interview_questions"] = interview_questions(r)
    r["salary"] = salary_estimate(r)
    return r