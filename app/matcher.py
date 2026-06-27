"""
matcher.py — TF-IDF based resume ↔ job-description matching and scoring.
"""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

# Download once
try:
    from nltk.corpus import stopwords
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords", quiet=True)
    nltk.download("punkt", quiet=True)

from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))


# ── Text cleaning ──────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Lowercase, remove punctuation, strip stopwords."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)


# ── Core scoring ───────────────────────────────────────────────────────────────

def compute_tfidf_score(resume_text: str, jd_text: str) -> float:
    """TF-IDF cosine similarity between resume and job description (0–1)."""
    corpus = [clean_text(resume_text), clean_text(jd_text)]
    if not any(corpus):
        return 0.0
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(float(score), 4)


def compute_skill_overlap_score(resume_skills: list[str], jd_text: str) -> float:
    """
    Fraction of required skills (detected in the JD) that the resume has.
    Returns 0–1.
    """
    from parser import SKILL_KEYWORDS
    jd_lower = jd_text.lower()
    required = [s for s in SKILL_KEYWORDS if s in jd_lower]
    if not required:
        return 0.0
    matched = [s for s in required if s in resume_skills]
    return round(len(matched) / len(required), 4)


def compute_experience_score(resume_text: str) -> float:
    """
    Heuristic: scan for years-of-experience patterns.
    Returns a 0–1 score (capped at 10 years → 1.0).
    """
    patterns = [
        r"(\d+)\+?\s*years?\s*(?:of\s+)?experience",
        r"(\d+)\+?\s*yrs?\s*(?:of\s+)?experience",
    ]
    years = []
    for p in patterns:
        for m in re.findall(p, resume_text, re.I):
            try:
                years.append(int(m))
            except ValueError:
                pass
    if not years:
        return 0.3  # neutral default if undetectable
    return min(max(years) / 10.0, 1.0)


def score_candidate(resume: dict, jd: dict) -> dict:
    """
    Produce a composite fit score for one resume against one job description.

    Weights:
        TF-IDF similarity   50 %
        Skill overlap       35 %
        Experience          15 %
    """
    tfidf = compute_tfidf_score(resume["raw_text"], jd["description"])
    skill = compute_skill_overlap_score(resume["skills"], jd["description"])
    exp   = compute_experience_score(resume["raw_text"])

    composite = round(0.50 * tfidf + 0.35 * skill + 0.15 * exp, 4)

    return {
        "candidate_name": resume.get("name") or resume["filename"],
        "filename": resume["filename"],
        "email": resume.get("email", ""),
        "job_title": jd["title"],
        "tfidf_score": tfidf,
        "skill_score": skill,
        "experience_score": exp,
        "fit_score": composite,
        "matched_skills": [
            s for s in resume["skills"] if s in jd["description"].lower()
        ],
    }


def rank_candidates(resumes: list[dict], jd: dict) -> list[dict]:
    """Score and rank all resumes for a given job description."""
    results = [score_candidate(r, jd) for r in resumes]
    results.sort(key=lambda x: x["fit_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results
