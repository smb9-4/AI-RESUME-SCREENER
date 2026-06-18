"""
Skill gap detection engine.
Compares resume skills against JD skills using:
  - Set difference (hard gaps)
  - Frequency weighting (critical vs minor gaps)
  - Semantic soft-matching (embeddings catch synonyms)
  - Category bucketing (technical / tools / soft / domain)
"""

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SKILLS_TAXONOMY_PATH = Path(os.getenv("SKILLS_TAXONOMY", Path(__file__).parent.parent / "data" / "skills.json"))
SOFT_MATCH_THRESHOLD = float(os.getenv("SOFT_MATCH_THRESHOLD", "0.82"))  # cosine sim cutoff
EMBED_MODEL_NAME     = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

_embed_model: SentenceTransformer | None = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SkillMatch:
    skill:      str
    category:   str   # technical | tools | soft | domain
    frequency:  int   # times mentioned in JD
    priority:   str   # critical | moderate | minor


@dataclass
class SoftMatch:
    jd_skill:      str   # what the JD wants
    resume_skill:  str   # what the candidate has (close match)
    similarity:    float
    category:      str


@dataclass
class SkillGapReport:
    hard_gaps:    list[SkillMatch]   # skills in JD, absent from resume
    soft_matches: list[SoftMatch]    # semantic near-matches
    matched:      list[str]          # skills present in both
    resume_only:  list[str]          # skills on resume not in JD
    gap_score:    float              # 0–100, higher = bigger gap
    by_category:  dict[str, list[SkillMatch]]  # gaps bucketed by category


# ---------------------------------------------------------------------------
# Skills taxonomy loader
# ---------------------------------------------------------------------------

_FALLBACK_TAXONOMY: dict[str, list[str]] = {
    "technical": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "scala",
        "sql", "nosql", "machine learning", "deep learning", "nlp", "computer vision",
        "data structures", "algorithms", "system design", "rest api", "graphql",
        "microservices", "distributed systems", "linux", "bash", "git",
    ],
    "tools": [
        "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
        "jenkins", "github actions", "gitlab ci", "prometheus", "grafana",
        "elasticsearch", "kafka", "redis", "postgresql", "mongodb", "mysql",
        "spark", "airflow", "dbt", "tableau", "power bi",
        "react", "nextjs", "fastapi", "django", "flask", "spring boot",
        "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow",
    ],
    "soft": [
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "time management", "collaboration", "adaptability",
        "project management", "stakeholder management", "mentoring",
    ],
    "domain": [
        "fintech", "healthtech", "edtech", "e-commerce", "saas", "b2b", "b2c",
        "data engineering", "data science", "mlops", "devops", "backend", "frontend",
        "full stack", "mobile", "ios", "android", "cloud native", "cybersecurity",
    ],
}


def _load_taxonomy() -> dict[str, list[str]]:
    if SKILLS_TAXONOMY_PATH.exists():
        with open(SKILLS_TAXONOMY_PATH) as f:
            return json.load(f)
    return _FALLBACK_TAXONOMY


def _build_skill_to_category(taxonomy: dict[str, list[str]]) -> dict[str, str]:
    mapping = {}
    for category, skills in taxonomy.items():
        for skill in skills:
            mapping[skill.lower()] = category
    return mapping


# ---------------------------------------------------------------------------
# Skill extraction from raw text
# ---------------------------------------------------------------------------

def extract_skills(text: str, taxonomy: dict[str, list[str]] | None = None) -> list[str]:
    """
    Extract skills from raw text using taxonomy lookup.
    Returns a deduplicated list of matched skill strings.
    """
    if taxonomy is None:
        taxonomy = _load_taxonomy()

    text_lower = text.lower()
    found = []

    all_skills = [skill for skills in taxonomy.values() for skill in skills]
    # sort longest first so "machine learning" matches before "learning"
    all_skills_sorted = sorted(all_skills, key=len, reverse=True)

    for skill in all_skills_sorted:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower) and skill not in found:
            found.append(skill)

    return found


def extract_skills_with_frequency(text: str, taxonomy: dict[str, list[str]] | None = None) -> Counter:
    """
    Extract skills and count how many times each appears in the text.
    Useful for JD weighting — skills mentioned 4x are more critical.
    """
    if taxonomy is None:
        taxonomy = _load_taxonomy()

    text_lower = text.lower()
    counts: Counter = Counter()

    all_skills = [skill for skills in taxonomy.values() for skill in skills]
    all_skills_sorted = sorted(all_skills, key=len, reverse=True)

    for skill in all_skills_sorted:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        matches = re.findall(pattern, text_lower)
        if matches:
            counts[skill] += len(matches)

    return counts


# ---------------------------------------------------------------------------
# Priority labelling
# ---------------------------------------------------------------------------

def _label_priority(freq: int, total_jd_skills: int) -> str:
    if freq >= 3 or (total_jd_skills > 0 and freq / total_jd_skills > 0.15):
        return "critical"
    if freq == 2:
        return "moderate"
    return "minor"


# ---------------------------------------------------------------------------
# Soft matching via embeddings
# ---------------------------------------------------------------------------

def _find_soft_matches(
    hard_gap_skills: list[str],
    resume_skills:   list[str],
    skill_to_cat:    dict[str, str],
    threshold:       float = SOFT_MATCH_THRESHOLD,
) -> tuple[list[SoftMatch], list[str]]:
    """
    For each hard gap skill, check if any resume skill is semantically close.
    Returns (soft_matches, remaining_hard_gaps).
    """
    if not hard_gap_skills or not resume_skills:
        return [], hard_gap_skills

    model       = _get_embed_model()
    gap_vecs    = model.encode(hard_gap_skills,   convert_to_numpy=True)
    resume_vecs = model.encode(resume_skills,     convert_to_numpy=True)

    sim_matrix  = cosine_similarity(gap_vecs, resume_vecs)  # (n_gaps, n_resume)

    soft_matches:      list[SoftMatch] = []
    remaining_gaps:    list[str]       = []

    for i, gap_skill in enumerate(hard_gap_skills):
        best_idx = int(np.argmax(sim_matrix[i]))
        best_sim = float(sim_matrix[i][best_idx])

        if best_sim >= threshold:
            soft_matches.append(SoftMatch(
                jd_skill     = gap_skill,
                resume_skill = resume_skills[best_idx],
                similarity   = round(best_sim, 3),
                category     = skill_to_cat.get(gap_skill, "general"),
            ))
        else:
            remaining_gaps.append(gap_skill)

    return soft_matches, remaining_gaps


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def detect_skill_gaps(
    resume_text: str,
    jd_text:     str,
    use_embeddings: bool = True,
) -> SkillGapReport:
    """
    Full skill gap analysis between a resume and a job description.

    Args:
        resume_text:    Raw text of the resume
        jd_text:        Raw text of the job description
        use_embeddings: Whether to run semantic soft-matching (requires sentence-transformers)

    Returns:
        SkillGapReport with hard gaps, soft matches, matched skills, and gap score
    """
    taxonomy     = _load_taxonomy()
    skill_to_cat = _build_skill_to_category(taxonomy)

    resume_skills_list = extract_skills(resume_text, taxonomy)
    jd_skill_counts    = extract_skills_with_frequency(jd_text, taxonomy)

    resume_set = set(s.lower() for s in resume_skills_list)
    jd_set     = set(jd_skill_counts.keys())

    # --- Hard gaps: in JD, missing from resume ---
    raw_hard_gaps = sorted(jd_set - resume_set, key=lambda s: -jd_skill_counts[s])

    # --- Matched: present in both ---
    matched = sorted(jd_set & resume_set)

    # --- Resume-only skills: on resume, not asked for in JD ---
    resume_only = sorted(resume_set - jd_set)

    # --- Soft matching via embeddings ---
    soft_matches:  list[SoftMatch]  = []
    true_hard_gaps = raw_hard_gaps

    if use_embeddings and raw_hard_gaps and resume_skills_list:
        soft_matches, true_hard_gaps = _find_soft_matches(
            raw_hard_gaps, resume_skills_list, skill_to_cat
        )

    # --- Build SkillMatch objects with priority labels ---
    total_jd = sum(jd_skill_counts.values())
    hard_gap_objects: list[SkillMatch] = []

    for skill in true_hard_gaps:
        freq = jd_skill_counts.get(skill, 1)
        hard_gap_objects.append(SkillMatch(
            skill    = skill,
            category = skill_to_cat.get(skill, "general"),
            frequency = freq,
            priority = _label_priority(freq, total_jd),
        ))

    # sort: critical first, then by frequency
    priority_order = {"critical": 0, "moderate": 1, "minor": 2}
    hard_gap_objects.sort(key=lambda g: (priority_order[g.priority], -g.frequency))

    # --- Bucket by category ---
    by_category: dict[str, list[SkillMatch]] = {}
    for gap in hard_gap_objects:
        by_category.setdefault(gap.category, []).append(gap)

    # --- Gap score: weighted by priority ---
    weights = {"critical": 3, "moderate": 2, "minor": 1}
    weighted_gap   = sum(weights[g.priority] for g in hard_gap_objects)
    weighted_total = sum(weights[_label_priority(jd_skill_counts[s], total_jd)] for s in jd_set)
    gap_score = round((weighted_gap / weighted_total * 100) if weighted_total > 0 else 0.0, 1)

    return SkillGapReport(
        hard_gaps    = hard_gap_objects,
        soft_matches = sorted(soft_matches, key=lambda m: -m.similarity),
        matched      = matched,
        resume_only  = resume_only,
        gap_score    = gap_score,
        by_category  = by_category,
    )
