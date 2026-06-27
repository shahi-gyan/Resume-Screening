"""
parser.py — Extract text and structured info from PDF/DOCX resumes.
"""
import re
import io
import fitz  # PyMuPDF
from docx import Document


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from a PDF file (bytes)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract raw text from a DOCX file (bytes)."""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to correct extractor based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ── Structured field extraction ────────────────────────────────────────────────

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)

SECTION_HEADERS = {
    "skills": re.compile(
        r"(skills?|technical skills?|core competencies|technologies)", re.I
    ),
    "education": re.compile(r"(education|academic|qualification)", re.I),
    "experience": re.compile(r"(experience|employment|work history|career)", re.I),
    "projects": re.compile(r"(projects?|portfolio)", re.I),
    "summary": re.compile(r"(summary|objective|profile|about)", re.I),
}

# Common tech skills to scan for
SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin",
    "swift", "r", "sql", "html", "css", "bash", "scala", "php", "ruby",
    "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "machine learning", "deep learning", "nlp", "computer vision", "data analysis",
    "rest api", "graphql", "microservices", "agile", "scrum",
]


def extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else ""


def extract_linkedin(text: str) -> str:
    match = LINKEDIN_RE.search(text)
    return match.group(0) if match else ""


def extract_name(text: str) -> str:
    """Heuristic: first non-empty line that looks like a name."""
    for line in text.splitlines():
        line = line.strip()
        if line and len(line.split()) in (2, 3) and line.replace(" ", "").isalpha():
            return line
    return ""


def extract_skills_from_text(text: str) -> list[str]:
    """Return list of detected skill keywords present in the text."""
    lower = text.lower()
    return [skill for skill in SKILL_KEYWORDS if skill in lower]


def extract_section(text: str, section: str) -> str:
    """
    Pull the text block that belongs to a section (e.g. 'skills', 'education').
    Returns everything between that section header and the next one.
    """
    lines = text.splitlines()
    header_re = SECTION_HEADERS.get(section)
    if not header_re:
        return ""

    # Find all section boundaries
    boundaries = []
    for i, line in enumerate(lines):
        for sec, pattern in SECTION_HEADERS.items():
            if pattern.search(line):
                boundaries.append((i, sec))
                break

    start_idx = None
    end_idx = len(lines)

    for i, (line_no, sec) in enumerate(boundaries):
        if sec == section:
            start_idx = line_no + 1
            if i + 1 < len(boundaries):
                end_idx = boundaries[i + 1][0]
            break

    if start_idx is None:
        return ""
    return "\n".join(lines[start_idx:end_idx]).strip()


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Full parse of a resume. Returns a structured dict with all fields.
    """
    text = extract_text(file_bytes, filename)
    return {
        "filename": filename,
        "raw_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_linkedin(text),
        "skills": extract_skills_from_text(text),
        "skills_section": extract_section(text, "skills"),
        "education_section": extract_section(text, "education"),
        "experience_section": extract_section(text, "experience"),
        "projects_section": extract_section(text, "projects"),
        "summary_section": extract_section(text, "summary"),
    }
