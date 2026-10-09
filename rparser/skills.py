import re

# canonical -> (category, aliases). EXTEND THIS: more skills = better results.
SKILL_DB = {
    "Python": ("Programming", ["python3", "py"]),
    "Java": ("Programming", ["core java", "java se"]),
    "JavaScript": ("Programming", ["js", "javascript", "java script", "ecmascript", "es6"]),
    "TypeScript": ("Programming", ["ts"]),
    "C++": ("Programming", ["cpp"]),
    "C#": ("Programming", ["csharp", "c sharp"]),
    "R": ("Programming", ["r programming"]),
    "SQL": ("Database", ["mysql", "postgresql", "postgres", "sqlite", "t-sql", "pl/sql"]),
    "MongoDB": ("Database", ["mongo"]),
    "Redis": ("Database", []),
    "HTML": ("Web", ["html5"]),
    "CSS": ("Web", ["css3"]),
    "React": ("Web", ["reactjs", "react.js"]),
    "Angular": ("Web", ["angularjs"]),
    "Node.js": ("Web", ["nodejs", "node js"]),
    "Django": ("Web", []),
    "Flask": ("Web", []),
    "FastAPI": ("Web", []),
    "REST API": ("Web", ["rest", "restful", "rest apis"]),
    "Machine Learning": ("Data Science", ["ml"]),
    "Deep Learning": ("Data Science", ["dl"]),
    "NLP": ("Data Science", ["natural language processing"]),
    "Computer Vision": ("Data Science", ["cv", "opencv"]),
    "TensorFlow": ("Data Science", ["tf"]),
    "PyTorch": ("Data Science", ["torch"]),
    "scikit-learn": ("Data Science", ["sklearn", "scikit learn"]),
    "Pandas": ("Data Science", []),
    "NumPy": ("Data Science", ["numpy"]),
    "Data Visualization": ("Data Science", ["matplotlib", "seaborn", "plotly", "tableau", "power bi"]),
    "Spark": ("Data Engineering", ["pyspark", "apache spark"]),
    "Hadoop": ("Data Engineering", []),
    "Kafka": ("Data Engineering", ["apache kafka"]),
    "Airflow": ("Data Engineering", ["apache airflow"]),
    "AWS": ("Cloud/DevOps", ["amazon web services", "ec2", "s3"]),
    "Azure": ("Cloud/DevOps", ["microsoft azure"]),
    "GCP": ("Cloud/DevOps", ["google cloud"]),
    "Docker": ("Cloud/DevOps", ["containers"]),
    "Kubernetes": ("Cloud/DevOps", ["k8s"]),
    "CI/CD": ("Cloud/DevOps", ["jenkins", "github actions", "gitlab ci"]),
    "Terraform": ("Cloud/DevOps", []),
    "Linux": ("Cloud/DevOps", ["ubuntu", "bash", "shell scripting"]),
    "Git": ("Tools", ["github", "gitlab", "version control"]),
    "Excel": ("Tools", ["ms excel", "microsoft excel"]),
    "Jira": ("Tools", []),
    "Communication": ("Soft Skills", ["communication skills"]),
    "Leadership": ("Soft Skills", ["team lead", "team leadership"]),
    "Teamwork": ("Soft Skills", ["team player", "collaboration"]),
    "Problem Solving": ("Soft Skills", ["problem-solving"]),
}

# alias (lowercase) -> canonical
_ALIAS = {}
for canon, (_, aliases) in SKILL_DB.items():
    _ALIAS[canon.lower()] = canon
    for a in aliases:
        _ALIAS[a.lower()] = canon

# Longest first so "machine learning" wins over "ml"
_PATTERN = re.compile(
    r"(?<![\w+#.])(" + "|".join(re.escape(a) for a in sorted(_ALIAS, key=len, reverse=True)) + r")(?![\w+#])",
    re.I,
)


def extract_skills(text: str) -> list[str]:
    found = {_ALIAS[m.group(1).lower()] for m in _PATTERN.finditer(text)}
    return sorted(found)


def categorize(skills: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in skills:
        out.setdefault(SKILL_DB[s][0], []).append(s)
    return out


def normalize(skill: str) -> str:
    return _ALIAS.get(skill.lower().strip(), skill)