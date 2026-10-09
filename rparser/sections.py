import re

HEADINGS = {
    "education": r"education|academic|qualification|academics",
    "experience": r"experience|employment|work history|professional background|internship",
    "skills": r"(?:technical\s+)?skills?|technologies|core competencies|expertise|tech stack",
    "interests": r"areas? of interest|interests|hobbies",
    "projects": r"projects?|personal projects|academic projects",
    "certifications": r"certifications?|certificates?|courses|licenses",
    "summary": r"summary|objective|profile|about me",
    "achievements": r"achievements?|awards?|honou?rs",
    "languages": r"languages?",
}


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        clean = line.strip().strip(":-_ ").lower()
        matched = None
        if 0 < len(clean) <= 40:
            for name, pat in HEADINGS.items():
                if re.fullmatch(rf"(?:{pat})(?:\s+(?:summary|overview|proficiency))?(?:\s*(?:&|and)\s*\w+)?", clean):
                    matched = name
                    break
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "".join(v).strip()}