from rparser.skills import extract_skills, normalize
from rparser.experience import extract_experience, total_years
from rparser.entities import EMAIL, extract_phone
from rparser.classify import classify_seniority


def test_skill_normalization():
    assert normalize("JS") == "JavaScript"
    assert "JavaScript" in extract_skills("Worked with java script and ReactJS")


def test_experience_overlap():
    jobs = extract_experience("Dev, Jan 2020 - Dec 2021\nIntern, Jun 2021 - Dec 2021")
    assert total_years(jobs) == 1.9  # overlap not double counted


def test_contact():
    assert EMAIL.search("mail me at a.b@x.com").group() == "a.b@x.com"
    assert extract_phone("Call +91 98765 43210") is not None


def test_seniority():
    assert classify_seniority(0.5) == "Fresher"
    assert classify_seniority(8) == "Senior"