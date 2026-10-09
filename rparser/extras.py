import re
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def anonymize(text: str, ents: dict) -> str:
    out = text
    for key, token in (("name", "[NAME]"), ("email", "[EMAIL]"), ("phone", "[PHONE]"),
                       ("linkedin", "[LINKEDIN]"), ("github", "[GITHUB]")):
        if ents.get(key):
            out = out.replace(ents[key], token)
    out = re.sub(r"\b(he|she|his|her|him|mr|mrs|ms)\b\.?", "[X]", out, flags=re.I)
    out = re.sub(r"(?i)(date of birth|dob|age|gender|marital status)\s*[:\-].*", "", out)
    return out


def candidate_summary(r: dict) -> str:
    top = ", ".join(r["skills"][:5]) or "various skills"
    edu = r["education"][0]["degree"].upper() if r["education"] else "a relevant degree"
    return (f"{r['seniority']} {r['domain']} candidate with {r['total_years']} years of experience. "
            f"Holds {edu}. Key strengths: {top}. "
            f"ATS readiness: {r['ats']['ats_score']}/100.")


QUESTION_BANK = {
    "Python": "Explain the difference between a list, tuple and set, and when you'd use each.",
    "SQL": "How would you find the second-highest salary per department?",
    "Machine Learning": "How do you detect and handle overfitting?",
    "NLP": "Compare TF-IDF, Word2Vec and transformer embeddings.",
    "Docker": "What's the difference between an image and a container?",
    "React": "Explain the virtual DOM and when useEffect runs.",
    "AWS": "How would you design a highly available web app on AWS?",
    "Git": "How do you resolve a merge conflict? Rebase vs merge?",
    "Deep Learning": "Explain backpropagation and the vanishing gradient problem.",
    "REST API": "How would you design pagination and error handling for a REST API?",
}


def interview_questions(r: dict, n: int = 6) -> list[str]:
    qs = [QUESTION_BANK[s] for s in r["skills"] if s in QUESTION_BANK][:n]
    qs.append("Walk me through the most challenging project on your resume.")
    if r["career"]["job_hopping"]:
        qs.append("I notice short tenures. What drove those moves?")
    for g in r["career"]["gaps"][:1]:
        qs.append(f"There's a {g['months']}-month gap ({g['from']} to {g['to']}). What were you doing?")
    return qs


def salary_estimate(r: dict, base_by_level=None) -> dict:
    """Rough heuristic in INR LPA. Calibrate with real data (e.g. a Kaggle salary dataset) for credibility."""
    base = base_by_level or {"Fresher": 4, "Junior": 7, "Mid-level": 14, "Senior": 26}
    b = base[r["seniority"]]
    hot = {"Machine Learning", "Deep Learning", "NLP", "AWS", "Kubernetes", "Spark"}
    premium = 1 + 0.04 * len(hot & set(r["skills"]))
    lo, hi = b * premium * 0.85, b * premium * 1.25
    return {"min_lpa": round(lo, 1), "max_lpa": round(hi, 1), "note": "heuristic estimate"}


def fake_skill_check(skills: list[str], sections: dict) -> list[str]:
    """Skills claimed in the Skills section but never evidenced in experience/projects."""
    from .skills import extract_skills
    evidence = extract_skills(sections.get("experience", "") + "\n" + sections.get("projects", ""))
    claimed = extract_skills(sections.get("skills", ""))
    return sorted(set(claimed) - set(evidence))


def github_enrich(url_or_user: str) -> dict:
    user = url_or_user.rstrip("/").split("/")[-1]
    try:
        repos = requests.get(f"https://api.github.com/users/{user}/repos?per_page=100", timeout=10).json()
        if not isinstance(repos, list):
            return {"error": "user not found or rate limited"}
        langs: dict[str, int] = {}
        for r in repos:
            if r.get("language"):
                langs[r["language"]] = langs.get(r["language"], 0) + 1
        return {"repos": len(repos), "stars": sum(r["stargazers_count"] for r in repos),
                "languages": dict(sorted(langs.items(), key=lambda x: -x[1])),
                "top_repos": [r["name"] for r in sorted(repos, key=lambda r: -r["stargazers_count"])[:5]]}
    except requests.RequestException as e:
        return {"error": str(e)}


def find_duplicates(resumes: list[dict], threshold: float = 0.85) -> list[tuple]:
    if len(resumes) < 2:
        return []
    m = TfidfVectorizer(stop_words="english").fit_transform([r["raw_text"] for r in resumes])
    sim = cosine_similarity(m)
    return [(resumes[i]["name"], resumes[j]["name"], round(float(sim[i][j]), 2))
            for i in range(len(resumes)) for j in range(i + 1, len(resumes)) if sim[i][j] >= threshold]