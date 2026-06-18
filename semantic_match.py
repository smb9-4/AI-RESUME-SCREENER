import argparse
from pathlib import Path
from typing import Optional

import pdfplumber
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_pdf(pdf_path: Path) -> str:
    pages_text: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text.strip())
    return "\n\n".join(t for t in pages_text if t)


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace").strip()


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute semantic similarity between a resume PDF and a job "
            "description text using sentence-transformers and cosine similarity."
        )
    )
    parser.add_argument(
        "--resume-path",
        type=str,
        required=True,
        help="Path to the resume PDF file.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--jd-text",
        type=str,
        help="Job description text (passed directly on the command line).",
    )
    group.add_argument(
        "--jd-file",
        type=str,
        help="Path to a text file containing the job description.",
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

    if args.jd_text is not None:
        jd_text = args.jd_text.strip()
    else:
        jd_file_path = Path(args.jd_file)
        if not jd_file_path.is_file():
            raise SystemExit(f"JD text file not found: {jd_file_path}")
        jd_text = read_text_file(jd_file_path)

    if not jd_text:
        raise SystemExit("Job description text is empty.")

    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text:
        raise SystemExit("No text could be extracted from the resume PDF.")

    model = load_model(args.model_name)
    similarity_score = compute_similarity(resume_text, jd_text, model)

    print(f"Cosine similarity score (0-100): {similarity_score:.2f}")


if __name__ == "__main__":
    main()

