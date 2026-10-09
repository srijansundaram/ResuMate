from .skills import SKILL_DB

DOMAIN_RULES = {
    "Data Science / ML": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow",
                          "PyTorch", "scikit-learn", "Pandas", "NumPy", "Data Visualization"],
    "Web Development": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Angular", "Node.js",
                        "Django", "Flask", "FastAPI", "REST API"],
    "DevOps / Cloud": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Terraform", "Linux"],
    "Data Engineering": ["Spark", "Hadoop", "Kafka", "Airflow", "SQL"],
}


def classify_domain(skills: list[str]) -> str:
    scores = {d: sum(s in skills for s in kws) for d, kws in DOMAIN_RULES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General / Other"


def classify_seniority(years: float) -> str:
    if years < 1:
        return "Fresher"
    if years < 3:
        return "Junior"
    if years < 6:
        return "Mid-level"
    return "Senior"