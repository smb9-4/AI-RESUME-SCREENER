import argparse
import json
import re
from pathlib import Path
from typing import TypedDict

import pdfplumber
import spacy

from jd_loader import SUPPORTED_ROLES, resolve_jd

nlp = spacy.load("en_core_web_sm")

_SKILLS_PATH = Path(__file__).parent / "skills_list.json"
with _SKILLS_PATH.open(encoding="utf-8") as f:
    _SKILLS_LIST: list[str] = json.load(f)

_SKILLS_SET = {skill.lower() for skill in _SKILLS_LIST}
_MULTI_WORD_SKILLS = sorted(
    (skill for skill in _SKILLS_SET if " " in skill),
    key=len,
    reverse=True,
)


class SkillExtractionResult(TypedDict):
    resume_skills: list[str]
    jd_skills: list[str]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _extract_candidates(doc: spacy.tokens.Doc) -> set[str]:
    candidates: set[str] = set()

    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and not token.is_stop:
            candidates.add(_normalize(token.lemma_))

    for chunk in doc.noun_chunks:
        candidates.add(_normalize(chunk.text))

    return candidates


def _extract_skills_from_text(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    doc = nlp(text)
    candidates = _extract_candidates(doc)
    normalized_text = _normalize(text)
    matched: set[str] = set()

    for candidate in candidates:
        if candidate in _SKILLS_SET:
            matched.add(candidate)

    for skill in _MULTI_WORD_SKILLS:
        if skill in normalized_text:
            matched.add(skill)

    for skill in _SKILLS_SET:
        if " " not in skill and re.search(rf"\b{re.escape(skill)}\b", normalized_text):
            matched.add(skill)

    multi_word = {skill for skill in matched if " " in skill}
    filtered: set[str] = set()
    for skill in matched:
        if " " in skill:
            filtered.add(skill)
            continue
        if not any(skill in phrase for phrase in multi_word):
            filtered.add(skill)

    return sorted(filtered)


def extract_skills(resume_text: str, jd_text: str) -> SkillExtractionResult:
    return {
        "resume_skills": _extract_skills_from_text(resume_text),
        "jd_skills": _extract_skills_from_text(jd_text),
    }


def _extract_text_from_pdf(pdf_path: Path) -> str:
    pages_text: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text.strip())
    return "\n\n".join(t for t in pages_text if t)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "AI Role 1: NLP keyword & skill extraction.\n"
            "Reads a resume PDF and a Kaggle JD, extracts skills as individual terms."
        )
    )
    parser.add_argument("--resume-pdf", type=str, required=True, help="Path to resume PDF.")
    parser.add_argument(
        "--jd-id",
        type=str,
        help=(
            "JD id from the Kaggle dataset (e.g. software_engineer_0001). "
            "If omitted, the first JD in the dataset is used."
        ),
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=SUPPORTED_ROLES,
        help="When --jd-id is omitted, pick the first JD for this role.",
    )
    parser.add_argument(
        "--jds-path",
        type=str,
        help="Optional path to normalized JD JSON (default: data/jds/jds.json).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    resume_path = Path(args.resume_pdf)
    if not resume_path.is_file():
        raise SystemExit(f"Resume PDF not found: {resume_path}")

    resume_text = _extract_text_from_pdf(resume_path)
    if not resume_text:
        raise SystemExit("No text could be extracted from the resume PDF.")

    jds_path = Path(args.jds_path) if args.jds_path else None
    try:
        jd = resolve_jd(jd_id=args.jd_id, role=args.role, jds_path=jds_path)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    jd_text = jd["description"]
    if not jd_text:
        raise SystemExit(f"Job description text is empty for JD id: {jd['id']}")

    result = extract_skills(resume_text, jd_text)
    print(result)


if __name__ == "__main__":
    main()
