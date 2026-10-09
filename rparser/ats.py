import re
from spellchecker import SpellChecker

ACTION_VERBS = {
    "worked on": "developed / built", "responsible for": "led / managed / owned",
    "helped": "supported / enabled", "assisted": "collaborated on", "did": "executed",
    "made": "created / designed", "duties included": "delivered", "involved in": "contributed to",
}
STRONG = {"developed", "built", "designed", "led", "implemented", "optimized", "created", "deployed",
          "automated", "improved", "reduced", "increased", "managed", "analyzed", "launched", "engineered"}
REQUIRED_SECTIONS = ["experience", "education", "skills"]
_SPELL = SpellChecker()


def ats_check(text: str, sections: dict, ents: dict, layout: dict) -> dict:
    score, issues, tips = 0, [], []
    words = text.split()

    # sections (30)
    present = [s for s in REQUIRED_SECTIONS if s in sections]
    score += 10 * len(present)
    for s in set(REQUIRED_SECTIONS) - set(present):
        issues.append(f"Missing section: {s.title()}")
    if "projects" not in sections:
        tips.append("Add a Projects section to show practical work.")

    # contact (15)
    for k, pts in (("email", 5), ("phone", 5), ("linkedin", 5)):
        if ents.get(k):
            score += pts
        else:
            issues.append(f"Missing contact detail: {k}")

    # length (15)
    if 300 <= len(words) <= 900:
        score += 15
    else:
        issues.append(f"Resume length is {len(words)} words (ideal 300-900).")
    if layout["pages"] > 2:
        issues.append("More than 2 pages; trim it down.")

    # bullets (20)
    bullets = [l.strip("•-*– \t") for l in text.splitlines() if l.strip().startswith(("•", "-", "*", "–"))]
    weak = []
    for b in bullets:
        for phrase, better in ACTION_VERBS.items():
            if phrase in b.lower():
                weak.append({"bullet": b[:90], "replace": phrase, "with": better})
    starts_strong = sum(1 for b in bullets if b.split() and b.split()[0].lower().rstrip("ed") + "ed" in STRONG
                        or (b.split() and b.split()[0].lower() in STRONG))
    ratio = starts_strong / len(bullets) if bullets else 0
    score += int(20 * min(1, ratio + 0.3)) if bullets else 0
    if not bullets:
        issues.append("No bullet points found; use bullets for achievements.")
    if weak:
        issues.append(f"{len(weak)} weak/vague bullets found.")

    # quantified impact (10)
    nums = sum(bool(re.search(r"\d+\s*(%|x|\+|users|ms|k\b)", b)) for b in bullets)
    score += min(10, nums * 2)
    if nums < 3:
        tips.append("Quantify impact (e.g. 'reduced latency by 30%').")

    # ATS-hostile layout (10)
    if layout["tables"] or layout["images"]:
        issues.append(f"Tables/images detected ({layout['tables']} tables, {layout['images']} images): ATS may misread.")
    else:
        score += 10

    # spelling
    tokens = [w.strip(".,;:()") for w in re.findall(r"[A-Za-z]{4,}", text)]
    unknown = [w for w in _SPELL.unknown([t.lower() for t in tokens])][:40]

    return {"ats_score": min(score, 100), "issues": issues, "tips": tips,
            "weak_bullets": weak[:10], "possible_typos": unknown[:15]}