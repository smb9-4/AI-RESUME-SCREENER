import argparse
import json
from pathlib import Path
from typing import Optional, TypedDict

import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from jd_loader import SUPPORTED_ROLES, JobDescription, load_jds


class SemanticMatchResult(TypedDict):
    jd_id: str
    role: str
    title: str
    company: str
    location: str
    similarity_score: float


class SemanticAnalysisResult(TypedDict):
    dataset_size: int
    matches: list[SemanticMatchResult]


def extract_text_from_pdf(pdf_path: Path) -> str:
    pages_text: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text.strip())
    return "\n\n".join(t for t in pages_text if t)


def load_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name)


def compute_similarity(
    resume_text: str, jd_text: str, model: Optional[SentenceTransformer] = None
) -> float:
    if model is None:
        model = load_model()

    resume_vec = model.encode(resume_text, convert_to_numpy=True)
    jd_vec = model.encode(jd_text, convert_to_numpy=True)

    score = cosine_similarity([resume_vec], [jd_vec])[0][0]
    return float(score * 100.0)


def analyze_resume_against_jds(
    resume_text: str,
    job_descriptions: list[JobDescription],
    *,
    model: Optional[SentenceTransformer] = None,
    top_n: int = 10,
) -> SemanticAnalysisResult:
    if model is None:
        model = load_model()

    resume_vec = model.encode(resume_text, convert_to_numpy=True)
    matches: list[SemanticMatchResult] = []

    for jd in job_descriptions:
        jd_vec = model.encode(jd["description"], convert_to_numpy=True)
        score = cosine_similarity([resume_vec], [jd_vec])[0][0]
        matches.append(
            {
                "jd_id": jd["id"],
                "role": jd["role"],
                "title": jd["title"],
                "company": jd["company"],
                "location": jd["location"],
                "similarity_score": round(float(score * 100.0), 2),
            }
        )

    matches.sort(key=lambda item: item["similarity_score"], reverse=True)
    return {
        "dataset_size": len(job_descriptions),
        "matches": matches[:top_n],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute semantic similarity between a resume PDF and Kaggle job "
            "descriptions using sentence-transformers and cosine similarity."
        )
    )
    parser.add_argument(
        "--resume-path",
        type=str,
        required=True,
        help="Path to the resume PDF file.",
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=SUPPORTED_ROLES,
        help="Optional role filter (data_analyst, data_scientist, software_engineer).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top matching JDs to return (default: 10).",
    )
    parser.add_argument(
        "--jds-path",
        type=str,
        help="Optional path to normalized JD JSON (default: data/jds/jds.json).",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="all-MiniLM-L6-v2",
        help="SentenceTransformer model name (default: all-MiniLM-L6-v2).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    resume_path = Path(args.resume_path)
    if not resume_path.is_file():
        raise SystemExit(f"Resume PDF not found: {resume_path}")

    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text:
        raise SystemExit("No text could be extracted from the resume PDF.")

    roles = [args.role] if args.role else None
    jds_path = Path(args.jds_path) if args.jds_path else None
    job_descriptions = load_jds(roles=roles, jds_path=jds_path)

    model = load_model(args.model_name)
    result = analyze_resume_against_jds(
        resume_text,
        job_descriptions,
        model=model,
        top_n=args.top,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
