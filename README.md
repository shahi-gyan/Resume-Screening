# 🎯 RecruitAI — AI-Powered Resume Screening System

An end-to-end ML-based recruitment assistant that parses resumes, extracts skills, matches candidates to job descriptions, and ranks them via a Streamlit dashboard.

---

## 📁 Project Structure

```
resume-screening/
├── app/
│   ├── main.py          ← Streamlit dashboard (entry point)
│   ├── parser.py        ← PDF/DOCX text extraction & field parsing
│   ├── matcher.py       ← TF-IDF matching, skill scoring, ranking
│   └── database.py      ← SQLite persistence via SQLAlchemy
├── data/
│   ├── sample_resumes/  ← Put your test PDFs/DOCXs here
│   └── job_descriptions.json
├── models/              ← (future: saved vectorizer pickles)
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app/main.py
```

The app opens at `http://localhost:8501`.

---

## 🚀 Usage Flow

1. **Upload Resumes** → Upload PDF or DOCX files on the "Upload Resumes" page.
2. **Add Jobs** → Go to "Manage Jobs" → click "Seed All 5 Sample JDs" or add your own.
3. **Run Screening** → Go to "Results & Rankings", select a job, click "Run Screening Now".
4. **View Results** → See ranked candidates, fit scores, charts, and a radar comparison.
5. **Candidate Detail** → Inspect any individual candidate's profile, skills, and scores.

---

## 🧠 How Scoring Works

| Component | Weight | Method |
|---|---|---|
| TF-IDF Similarity | 50% | Cosine similarity between resume and JD |
| Skill Overlap | 35% | % of JD-required skills found in resume |
| Experience Heuristic | 15% | Years-of-experience pattern detection |

**Composite Fit Score = 0.50 × TF-IDF + 0.35 × Skill + 0.15 × Experience**

---

## 📦 Tech Stack

- **Python 3.10+**
- **Streamlit** — dashboard UI
- **Scikit-learn** — TF-IDF vectorizer + cosine similarity
- **PyMuPDF (fitz)** — PDF text extraction
- **python-docx** — DOCX text extraction
- **NLTK** — stopword removal
- **SQLAlchemy + SQLite** — lightweight persistence
- **Plotly** — interactive charts

---

## 🔮 Possible Extensions

- Swap TF-IDF for sentence-transformers (BERT embeddings) for better semantic matching
- Add DOCX/PDF export of screening reports
- Integrate PostgreSQL for production deployment
- Add an email notification module for top candidates
- Build a REST API using FastAPI on top of the matching logic
