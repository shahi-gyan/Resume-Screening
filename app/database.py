"""
database.py — Lightweight SQLite persistence for candidates and scores.
"""
import json
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./resume_screening.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ── ORM Models ─────────────────────────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"

    id         = Column(Integer, primary_key=True, index=True)
    filename   = Column(String, unique=True, index=True)
    name       = Column(String, default="")
    email      = Column(String, default="")
    phone      = Column(String, default="")
    linkedin   = Column(String, default="")
    skills_json = Column(Text, default="[]")       # JSON list
    raw_text   = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def skills(self) -> list[str]:
        return json.loads(self.skills_json or "[]")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, unique=True, index=True)
    description = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Score(Base):
    __tablename__ = "scores"

    id               = Column(Integer, primary_key=True, index=True)
    candidate_id     = Column(Integer, index=True)
    job_id           = Column(Integer, index=True)
    tfidf_score      = Column(Float, default=0.0)
    skill_score      = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    fit_score        = Column(Float, default=0.0)
    matched_skills   = Column(Text, default="[]")
    scored_at        = Column(DateTime, default=datetime.utcnow)


# ── Helpers ────────────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upsert_candidate(db, parsed: dict) -> Candidate:
    existing = db.query(Candidate).filter_by(filename=parsed["filename"]).first()
    if existing:
        existing.name       = parsed.get("name", "")
        existing.email      = parsed.get("email", "")
        existing.phone      = parsed.get("phone", "")
        existing.linkedin   = parsed.get("linkedin", "")
        existing.skills_json = json.dumps(parsed.get("skills", []))
        existing.raw_text   = parsed.get("raw_text", "")
        db.commit()
        return existing
    candidate = Candidate(
        filename    = parsed["filename"],
        name        = parsed.get("name", ""),
        email       = parsed.get("email", ""),
        phone       = parsed.get("phone", ""),
        linkedin    = parsed.get("linkedin", ""),
        skills_json = json.dumps(parsed.get("skills", [])),
        raw_text    = parsed.get("raw_text", ""),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def upsert_job(db, title: str, description: str) -> JobDescription:
    existing = db.query(JobDescription).filter_by(title=title).first()
    if existing:
        existing.description = description
        db.commit()
        return existing
    job = JobDescription(title=title, description=description)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def save_scores(db, candidate: Candidate, job: JobDescription, result: dict):
    existing = (
        db.query(Score)
        .filter_by(candidate_id=candidate.id, job_id=job.id)
        .first()
    )
    if existing:
        for field in ("tfidf_score", "skill_score", "experience_score", "fit_score"):
            setattr(existing, field, result[field])
        existing.matched_skills = json.dumps(result.get("matched_skills", []))
        db.commit()
        return
    score = Score(
        candidate_id     = candidate.id,
        job_id           = job.id,
        tfidf_score      = result["tfidf_score"],
        skill_score      = result["skill_score"],
        experience_score = result["experience_score"],
        fit_score        = result["fit_score"],
        matched_skills   = json.dumps(result.get("matched_skills", [])),
    )
    db.add(score)
    db.commit()
