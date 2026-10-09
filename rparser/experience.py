import re
from datetime import datetime
from dateutil import parser as dparser

MON = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
DATE = rf"(?:(?:{MON})[a-z]*\.?,?\s*\d{{4}}|\d{{1,2}}/\d{{4}}|\d{{4}})"
RANGE = re.compile(
    rf"({DATE})\s*(?:-|–|—|to)\s*({DATE}|present|current|now|till date|ongoing)", re.I)


def _to_date(s: str) -> datetime:
    s = s.strip().lower().replace(".", "").replace(",", "")
    if s in ("present", "current", "now", "till date", "ongoing"):
        return datetime.now()
    return dparser.parse(s, default=datetime(2000, 1, 1))


def extract_experience(text: str) -> list[dict]:
    lines = text.splitlines()
    jobs = []
    for i, line in enumerate(lines):
        m = RANGE.search(line)
        if not m:
            y = re.search(r"\s(20\d{2})\s*$", line)
            if y and not line.lstrip().startswith(("•", "-", "–")) and len(line) < 90:
                head = line[:y.start()].strip(" |,-–—")
                jobs.append({"title_company": head, "start": f"{y.group(1)}-01",
                             "end": f"{y.group(1)}-12", "months": 11})
            continue
        try:
            start, end = _to_date(m.group(1)), _to_date(m.group(2))
        except (ValueError, OverflowError):
            continue
        if end < start:
            continue
        # title/company: the line itself minus the date, else the previous line
        head = RANGE.sub("", line).strip(" |,-–—()")
        if len(head) < 3 and i > 0:
            head = lines[i - 1].strip()
        jobs.append({
            "title_company": head,
            "start": start.strftime("%Y-%m"),
            "end": end.strftime("%Y-%m"),
            "months": (end.year - start.year) * 12 + end.month - start.month,
        })
    return jobs


def total_years(jobs: list[dict]) -> float:
    """Merge overlapping ranges so overlaps aren't double counted."""
    spans = sorted((datetime.strptime(j["start"], "%Y-%m"), datetime.strptime(j["end"], "%Y-%m")) for j in jobs)
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    months = sum((e.year - s.year) * 12 + e.month - s.month for s, e in merged)
    return round(months / 12, 1)


def career_flags(jobs: list[dict]) -> dict:
    spans = sorted((datetime.strptime(j["start"], "%Y-%m"), datetime.strptime(j["end"], "%Y-%m")) for j in jobs)
    gaps = []
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        gap = (s2.year - e1.year) * 12 + s2.month - e1.month
        if gap > 6:
            gaps.append({"from": e1.strftime("%Y-%m"), "to": s2.strftime("%Y-%m"), "months": gap})
    avg = sum(j["months"] for j in jobs) / len(jobs) if jobs else 0
    return {
        "gaps": gaps,
        "job_hopping": len(jobs) >= 3 and avg < 12,
        "avg_tenure_months": round(avg, 1),
    }