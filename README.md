# 📄 ResuMate: Resume Parser & Analyzer

An NLP-based resume parsing system with a recruiter/candidate dashboard, job matching, ATS scoring, PDF reports and an LLM comparison. Built with Python, spaCy, scikit-learn, Sentence-BERT, Streamlit and FastAPI.

**Live demo:** _add link after deployment_ · **Author:** [Srijan Sundaram](https://github.com/srijansundaram)


---

## ✨ Features

### Parsing
- Input formats: PDF, DOCX, TXT, PNG/JPG (OCR via Tesseract for scans and images)
- OCR preprocessing: contrast normalization plus an inverted pass for white-on-dark text
- Extracts name, email, phone, LinkedIn, GitHub, location
- Education (degree, year, GPA), experience, skills, projects, certifications
- Section segmentation that tolerates varied headings ("Skills Summary", "Tech Stack", ...)
- Name detection that handles multi-column layouts

### NLP
- Skill taxonomy with alias normalization ("JS" → JavaScript) and categories
- Experience calculation with merged overlaps and "Present" support
- Career gap and job-hopping detection
- Domain classification and seniority prediction
- Language detection

### Matching
- Match score = 0.5 × skill coverage + 0.3 × Sentence-BERT similarity + 0.2 × TF-IDF similarity
- Skill gap analysis (matched vs missing)
- Rank all candidates against a job description
- Semantic search across resumes ("ML engineer with NLP experience")

### Quality feedback
- ATS score (0 to 100) with issues and tips
- Weak-bullet detection with action-verb suggestions
- Spell check, length check, table/image layout warnings

### Add-ons
- LLM parser vs rule-based comparison (OpenRouter free models)
- Duplicate resume detection
- Blind screening mode (hides name, contact and gender cues)
- Unverified-skill flags (listed but never evidenced)
- Salary band estimate (heuristic), auto summary, interview question generator
- GitHub profile enrichment
- **PDF report download** in both recruiter and candidate views

### Dashboard (Streamlit)
- **Recruiter:** bulk upload, filters, search, resume preview, shortlist/reject/delete, comparison, Excel export, match leaderboard, analytics
- **Candidate:** ATS score, skill radar, career timeline, job match, suggestions, report download
- **Analytics:** top skills, word cloud, experience histogram, education and domain pies, skill co-occurrence network

### Engineering
- FastAPI REST API with Swagger docs
- SQLite storage (cleared on each server start)
- pytest unit tests, evaluation script, Docker support

---

## 🧰 Tech Stack

| Area | Tools |
|---|---|
| NLP | spaCy, Sentence-Transformers, scikit-learn, langdetect, pyspellchecker |
| Extraction | pdfplumber, python-docx, Tesseract OCR, pdf2image, Pillow |
| Dashboard | Streamlit, Plotly, Matplotlib, NetworkX, WordCloud |
| Reports | fpdf2 |
| API | FastAPI, Uvicorn |
| LLM | OpenRouter (free models) |
| Storage | SQLite |

---

## 📁 Project Structure

```
ResuMate/
├── app.py              # Streamlit dashboard
├── api.py              # FastAPI REST API
├── evaluate.py         # P/R/F1 evaluation, split by text PDF vs OCR image
├── make_gold.py        # drafts gold.json for hand correction
├── train_ner.py        # experimental spaCy NER training (not used by the app)
├── requirements.txt · packages.txt · Dockerfile · .env.example
├── tests/test_parser.py
└── rparser/
    ├── extract_text.py  skills.py     sections.py   entities.py
    ├── experience.py    classify.py   matcher.py    ats.py
    ├── extras.py        llm_parser.py report.py     db.py
    └── pipeline.py
```

---

## ⚙️ Installation (Windows)

**Prerequisites**
- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) on PATH (only needed for scanned PDFs and images)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Optional: LLM comparison.** Get a free key at https://openrouter.ai/keys, copy `.env.example` to `.env`, and set:
```
OPENROUTER_API_KEY=your_key
```

> **Linux/macOS:** `sudo apt install tesseract-ocr poppler-utils`, then the same Python steps.
>
> **Windows Smart App Control:** if you see "Application Control policy has blocked this file", run `Get-ChildItem -Path .venv -Recurse | Unblock-File`.

---

## 🚀 Usage

**Dashboard**
```powershell
python -m streamlit run app.py
```
Open http://localhost:8501

**API**
```powershell
python -m uvicorn api:app --reload
```
Swagger docs at http://localhost:8000/docs

| Endpoint | Method | Description |
|---|---|---|
| `/parse` | POST | Upload a resume, get structured JSON (`?save=true` to store) |
| `/match` | POST | Upload a resume plus a job description, get the match score |
| `/candidates` | GET | List stored candidates |

**As a library**
```python
from rparser.pipeline import parse_resume
r = parse_resume(open("sample.pdf", "rb").read(), "sample.pdf")
print(r["name"], r["skills"], r["ats"]["ats_score"])
```

**Tests**
```powershell
python -m pytest
```

**Docker**
```powershell
docker build -t resumate .
docker run -p 8501:8501 resumate
```

---

## 🧠 How It Works

```
Resume file (PDF / DOCX / TXT / image)
   ▼
Text extraction (pdfplumber / python-docx / OCR with preprocessing)
   ▼
Section segmentation ─► Entity extraction (regex + spaCy)
   ▼                           ▼
Skill extraction         Experience parsing
   └──────► Domain + seniority classification ◄──────┘
                         ▼
        ATS check · summary · questions · salary
                         ▼
              SQLite ─► Dashboard / API / PDF report
```

---

## 📊 Evaluation

A small development-set evaluation on **8 hand-labelled resumes** (4 text PDFs, 4 scanned images). Skills are scored against the project's skill taxonomy, so the results describe behaviour on this set, not general accuracy. The labelled resumes contain personal data and are not published in this repo. To reproduce with your own files, run `python make_gold.py`, correct the draft by hand, then run `python evaluate.py gold.json`.

| Input | N | Precision | Recall | F1 | Name | Email |
|---|---|---|---|---|---|---|
| Text PDF | 4 | 0.99 | 1.00 | 0.99 | 4/4 | 4/4 |
| Scanned/JPG (OCR) | 4 | 1.00 | 0.93 | 0.96 | 4/4 | 3/4 |
| **Overall** | 8 | 0.99 | 0.99 | 0.99 | 8/8 | 7/8 |

**Observations**
- Text PDFs are near-perfect. OCR images score slightly lower because of misreads.
- Contrast normalization and an inverted OCR pass were needed to read white-on-dark layouts.
- Multi-column layouts needed a wider name-search window and a filter that rejects headings and skill lines.
- Remaining skill errors: a soft skill ("Communication") matched inside a sentence rather than a skills list, and "Leadership" was missed because of an OCR misread.
- The one email miss is an OCR error on a template resume with a placeholder address.
- The text PDFs were also used while tuning the parser, so their scores are optimistic. The OCR row is the more honest estimate.

---

## ⚠️ Limitations
- Name, education and experience extraction are heuristic and can fail on graphic-heavy layouts.
- Project or academic work with date ranges can be counted as experience.
- Skill coverage is limited to the taxonomy in `skills.py`, so skills outside it are ignored.
- Soft skills can be matched from running sentences, not only from skills lists.
- OCR quality depends on image quality. Phone photos and low-resolution scans can fail.
- Salary estimates and unverified-skill flags are rough heuristics, not facts.
- The Recruiter/Candidate switch is a UI toggle, not authentication.
- LLM results vary by model because the free auto-router picks whichever model is available, and free tiers are rate-limited.
- The public demo shares one database across visitors, so do not upload real candidate data.

---

## 🔮 Future Work
- Train a domain classifier and a custom NER model (`train_ner.py` is a starting point)
- Expand the taxonomy with ESCO or O*NET
- Restrict soft-skill matching to the Skills section
- Real authentication and role-based access
- Multilingual parsing with multilingual spaCy and SBERT models
- Calibrate salary estimates on real data
- Evaluate on a larger labelled set, including the LLM parser

---

## 🔒 Privacy
Resumes contain personal data. Use blind screening for unbiased review, keep real resumes and labels out of the repo and public deployments, and never commit `.env`.

## 📜 License
MIT. See [LICENSE](LICENSE).