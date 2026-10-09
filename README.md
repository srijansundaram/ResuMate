# 📄 Resume Parser & Analyzer

An NLP-based resume parsing system with a recruiter/candidate dashboard, resume-to-job matching, ATS scoring, and LLM comparison. Built with Python, spaCy, scikit-learn, Sentence-BERT, Streamlit and FastAPI.

---

## ✨ Features

### Core Parsing
- Multi-format input: PDF, DOCX, TXT, PNG/JPG (OCR via Tesseract)
- Extracts name, email, phone, LinkedIn, GitHub, location
- Extracts education (degree, year, GPA), experience, skills, projects, certifications
- Automatic section segmentation (Education, Experience, Skills, etc.)

### Advanced NLP
- Skill normalization and taxonomy (e.g. "JS" → JavaScript) with categories
- Total experience calculation with overlap handling and "Present" support
- Domain classification (Data Science, Web, DevOps, Data Engineering)
- Seniority prediction (Fresher / Junior / Mid-level / Senior)
- Custom spaCy NER training script
- Language detection

### Resume–Job Matching
- Match score using TF-IDF + Sentence-BERT embeddings + skill coverage
- Skill gap analysis (matched vs missing skills)
- Rank multiple resumes against a job description
- Semantic search across all resumes
- Job recommendation for a candidate

### Quality & Feedback
- ATS score (0–100) with issues and tips
- Weak bullet detection with action-verb suggestions
- Spell check, length check, table/image layout warnings

### Unique Add-ons
- LLM-based parsing vs rule-based comparison (agreement F1)
- Duplicate / plagiarism detection
- Blind screening mode (hides name, contact, gender cues)
- GitHub profile enrichment
- Career gap and job-hopping detection
- Unverified skill detection (listed but never evidenced)
- Salary range estimation (heuristic)
- Auto-generated candidate summary
- Interview question generator

### Dashboard (Streamlit)
- **Recruiter view:** bulk upload, filters, search, shortlist/reject, comparison, Excel export, leaderboard, analytics
- **Candidate view:** ATS score, skill radar, career timeline, job match, suggestions
- **Analytics:** top skills, word cloud, experience histogram, education/domain pies, skill co-occurrence network, location chart

### Engineering
- FastAPI REST API with Swagger docs
- SQLite storage
- Unit tests (pytest)
- Evaluation script (precision, recall, F1)
- Docker support

---

## 🧰 Tech Stack

| Area | Tools |
|---|---|
| Language | Python 3.10+ |
| NLP | spaCy, Sentence-Transformers, scikit-learn, RapidFuzz, langdetect |
| Extraction | pdfplumber, python-docx, Tesseract OCR, pdf2image |
| Dashboard | Streamlit, Plotly, Matplotlib, NetworkX, WordCloud |
| API | FastAPI, Uvicorn |
| Database | SQLite |
| LLM | Anthropic API (optional) |
| Testing | pytest |

---

## 📁 Project Structure

```
resume_nlp/
├── app.py                  # Streamlit dashboard
├── api.py                  # FastAPI REST API
├── train_ner.py            # Custom spaCy NER training
├── evaluate.py             # Precision / recall / F1
├── requirements.txt
├── Dockerfile
├── tests/
│   └── test_parser.py
└── rparser/
    ├── extract_text.py     # PDF/DOCX/TXT/image + OCR
    ├── skills.py           # Skill taxonomy + normalization
    ├── sections.py         # Section segmentation
    ├── entities.py         # Name, contact, education, certs
    ├── experience.py       # Dates, total years, gaps
    ├── classify.py         # Domain + seniority
    ├── matcher.py          # JD match, gap, rank, semantic search
    ├── ats.py              # ATS / quality checker
    ├── extras.py           # Anonymize, summary, questions, salary, GitHub
    ├── llm_parser.py       # LLM parsing + comparison
    ├── db.py               # SQLite storage
    └── pipeline.py         # End-to-end pipeline
```

---

## ⚙️ Installation (Windows)

### 1. Prerequisites
- Python 3.10 or newer
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (installed to `C:\Program Files\Tesseract-OCR`)
- [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) (extracted, with `Library\bin` on PATH)

Verify both:
```bash
tesseract --version
pdftoppm -h
```

### 2. Python environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Optional: LLM comparison
```bash
setx ANTHROPIC_API_KEY "your_api_key_here"
```
Restart the terminal afterwards.

> **Linux/macOS:** `sudo apt install tesseract-ocr poppler-utils`, then follow the same Python steps with `source venv/bin/activate`.

---

## 🚀 Usage

### Run the dashboard
```bash
streamlit run app.py
```
Open http://localhost:8501

### Run the API
```bash
uvicorn api:app --reload
```
Swagger docs: http://localhost:8000/docs

| Endpoint | Method | Description |
|---|---|---|
| `/parse` | POST | Upload a resume, get structured JSON (`?save=true` to store) |
| `/match` | POST | Upload a resume + job description, get match score |
| `/candidates` | GET | List stored candidates |

### Use as a library
```python
from rparser.pipeline import parse_resume

with open("sample.pdf", "rb") as f:
    result = parse_resume(f.read(), "sample.pdf")

print(result["name"], result["skills"], result["ats"]["ats_score"])
```

### Run tests
```bash
pytest
```

### Evaluate accuracy
Create `gold.json`:
```json
[{"file": "resumes/a.pdf", "skills": ["Python", "SQL"], "email": "a@b.com"}]
```
Then:
```bash
python evaluate.py gold.json
```

### Train a custom NER model
1. Annotate resumes (Doccano / Label Studio) or use a Kaggle resume NER dataset
2. Add data to `TRAIN_DATA` in `train_ner.py`
3. Run `python train_ner.py`
4. In `rparser/entities.py`, change `spacy.load("en_core_web_sm")` to `spacy.load("models/resume_ner")`

### Docker
```bash
docker build -t resume-parser .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key resume-parser
```

---

## 🧠 How It Works

```
Resume file
   │
   ▼
Text extraction (pdfplumber / python-docx / OCR)
   │
   ▼
Section segmentation ──► Entity extraction (regex + spaCy)
   │                         │
   ▼                         ▼
Skill extraction        Experience parsing
   │                         │
   └────────► Classification (domain, seniority) ◄──┘
                     │
                     ▼
      ATS check · Summary · Questions · Salary
                     │
                     ▼
            SQLite ──► Dashboard / API
```

**Match score formula:** `0.5 × skill coverage + 0.3 × semantic similarity + 0.2 × TF-IDF similarity`

---

## 📊 Evaluation

| Method | Skills F1 | Email Acc. | Notes |
|---|---|---|---|
| Rule-based (regex + taxonomy) | _fill in_ | _fill in_ | Fast, no API needed |
| Custom spaCy NER | _fill in_ | _fill in_ | Needs training data |
| LLM parser | _fill in_ | _fill in_ | Highest accuracy, needs API |

Fill this table using `evaluate.py` on your own labeled resumes.

---

## ⚠️ Limitations
- Name, education and experience extraction are heuristic and may fail on unusual layouts (multi-column, heavy graphics)
- The skill taxonomy is limited to the skills in `skills.py`; extend it for better coverage
- Salary estimate and unverified-skill flags are rough heuristics, not facts
- OCR quality depends on scan quality
- The role switch in the dashboard is not real authentication
- Dashboard data is stored locally in `resumes.db`

---

## 🔮 Future Work
- Real authentication and role-based access
- Larger skill taxonomy (ESCO / O*NET)
- Multilingual parsing (Hindi, French) with multilingual models
- Fine-tuned BERT NER on a larger annotated dataset
- PostgreSQL support and cloud deployment
- Calibrated salary model trained on real data

---

## 🔒 Privacy Note
Resumes contain personal data. Use blind screening mode for unbiased review, and do not upload real candidate data to public deployments without consent.

---

## 👤 Author
**Srijan Sundaram** 

## 📜 License
MIT