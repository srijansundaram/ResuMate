import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .skills import extract_skills

_SBERT = None


def _sbert():
    global _SBERT
    if _SBERT is None:
        from sentence_transformers import SentenceTransformer
        _SBERT = SentenceTransformer("all-MiniLM-L6-v2")
    return _SBERT


def tfidf_score(resume_text: str, jd: str) -> float:
    v = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    m = v.fit_transform([resume_text, jd])
    return float(cosine_similarity(m[0], m[1])[0][0])


def semantic_score(resume_text: str, jd: str) -> float:
    e = _sbert().encode([resume_text, jd], normalize_embeddings=True)
    return float(np.dot(e[0], e[1]))


def skill_gap(resume_skills: list[str], jd: str) -> dict:
    need = set(extract_skills(jd))
    have = set(resume_skills)
    return {
        "required": sorted(need),
        "matched": sorted(need & have),
        "missing": sorted(need - have),
        "coverage": round(len(need & have) / len(need), 2) if need else 0.0,
    }


def match(resume: dict, jd: str, use_semantic: bool = True) -> dict:
    gap = skill_gap(resume["skills"], jd)
    t = tfidf_score(resume["raw_text"], jd)
    s = semantic_score(resume["raw_text"], jd) if use_semantic else t
    # weighted blend: skills matter most
    final = 0.5 * gap["coverage"] + 0.3 * s + 0.2 * t
    return {"score": round(final * 100, 1), "tfidf": round(t, 3),
            "semantic": round(s, 3), **gap}


def rank(resumes: list[dict], jd: str) -> list[dict]:
    rows = []
    for r in resumes:
        m = match(r, jd)
        rows.append({"id": r.get("id"), "name": r.get("name"), "score": m["score"],
                     "matched": len(m["matched"]), "missing": ", ".join(m["missing"])})
    return sorted(rows, key=lambda x: x["score"], reverse=True)


def semantic_search(resumes: list[dict], query: str, top_k: int = 5) -> list[dict]:
    if not resumes:
        return []
    model = _sbert()
    docs = model.encode([r["raw_text"][:2000] for r in resumes], normalize_embeddings=True)
    q = model.encode([query], normalize_embeddings=True)[0]
    sims = docs @ q
    idx = np.argsort(-sims)[:top_k]
    return [{"name": resumes[i]["name"], "id": resumes[i].get("id"), "similarity": round(float(sims[i]), 3)} for i in idx]


def recommend_jobs(resume: dict, jobs: dict[str, str]) -> list[tuple[str, float]]:
    """jobs = {'Data Analyst': 'JD text...', ...}"""
    scored = [(title, match(resume, jd)["score"]) for title, jd in jobs.items()]
    return sorted(scored, key=lambda x: x[1], reverse=True)