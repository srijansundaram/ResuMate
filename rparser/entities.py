import re
import spacy

try:
    # swap in your custom-trained model here: spacy.load("models/resume_ner")
    NLP = spacy.load("en_core_web_sm")
except OSError:
    NLP = None

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(\+?\d[\d\s\-().]{8,}\d)")
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-%]+", re.I)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+", re.I)
DEGREE = re.compile(
    r"\b(b\.?\s?tech|b\.?\s?e\b|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|b\.?\s?c\.?a|m\.?\s?c\.?a|mba|b\.?\s?com|m\.?\s?com|"
    r"ph\.?d|bachelor[s]?(?: of [\w ]+)?|master[s]?(?: of [\w ]+)?|diploma|b\.?\s?a\b|m\.?\s?a\b|"
    r"12th|10th|hsc|ssc)\b", re.I)
GPA = re.compile(r"(?:cgpa|gpa)\s*[:\-]?\s*(\d(?:\.\d{1,2})?)|(\d(?:\.\d{1,2})?)\s*/\s*(?:10|4)\b", re.I)
YEAR = re.compile(r"\b(19|20)\d{2}\b")


def extract_name(text: str) -> str | None:
    for line in text.splitlines()[:6]:
        line = line.strip()
        words = line.split()
        if 2 <= len(words) <= 4 and all(w.replace(".", "").replace("-", "").isalpha() for w in words):
            return line.title()
    if NLP:
        for ent in NLP(text[:500]).ents:
            if ent.label_ == "PERSON":
                return ent.text
    return None


def extract_phone(text: str) -> str | None:
    for m in PHONE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 10 <= len(digits) <= 13:
            return m.group().strip()
    return None


def extract_location(text: str) -> str | None:
    if not NLP:
        return None
    for ent in NLP(text[:600]).ents:
        if ent.label_ == "GPE":
            return ent.text
    return None


def extract_education(section_text: str) -> list[dict]:
    out = []
    for line in section_text.splitlines():
        d = DEGREE.search(line)
        if d:
            years = [m.group() for m in YEAR.finditer(line)]
            g = GPA.search(line)
            out.append({
                "degree": d.group().strip(),
                "line": line.strip(),
                "year": years[-1] if years else None,
                "gpa": (g.group(1) or g.group(2)) if g else None,
            })
    return out


def extract_certifications(section_text: str) -> list[str]:
    return [l.strip("•-* \t") for l in section_text.splitlines() if len(l.strip()) > 4][:15]


def extract_entities(text: str, sections: dict) -> dict:
    email = EMAIL.search(text)
    li = LINKEDIN.search(text)
    gh = GITHUB.search(text)
    return {
        "name": extract_name(text),
        "email": email.group() if email else None,
        "phone": extract_phone(text),
        "linkedin": li.group() if li else None,
        "github": gh.group() if gh else None,
        "location": extract_location(sections.get("header", text)),
        "education": extract_education(sections.get("education", text)),
        "certifications": extract_certifications(sections.get("certifications", "")),
    }