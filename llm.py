"""
Per-bullet LLM feedback engine.
Supports Groq (free tier) and Ollama (local, offline).
"""

import os
import json
import re
import httpx
from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class LLMProvider(str, Enum):
    GROQ   = "groq"
    OLLAMA = "ollama"


PROVIDER      = LLMProvider(os.getenv("LLM_PROVIDER", "groq"))
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL",   "llama3-8b-8192")   # free tier
OLLAMA_URL    = os.getenv("OLLAMA_URL",   "http://localhost:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class BulletFeedback:
    bullet:         str    # original bullet text
    score:          int    # 1–10
    action_verb:    bool   # starts with a strong action verb?
    measurable:     bool   # contains a quantifiable outcome?
    jd_relevant:    bool   # relevant to the job description?
    suggestion:     str    # one-line improvement suggestion
    improved:       str    # rewritten bullet


@dataclass
class SectionFeedback:
    section:   str                  # e.g. "experience"
    bullets:   list[BulletFeedback]
    avg_score: float


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a professional resume coach and ATS expert.
Evaluate each resume bullet point and return ONLY a JSON array — no preamble, no markdown fences.

Each element must follow this exact schema:
{
  "bullet": "<original bullet>",
  "score": <int 1-10>,
  "action_verb": <true|false>,
  "measurable": <true|false>,
  "jd_relevant": <true|false>,
  "suggestion": "<one-line actionable tip>",
  "improved": "<rewritten bullet>"
}

Scoring rubric:
  10 = strong action verb + quantified outcome + directly relevant to JD
  7–9 = two of three criteria met
  4–6 = one criterion met
  1–3 = generic, passive, or irrelevant

Keep "suggestion" under 20 words.
Keep "improved" under 25 words.
Return ONLY the JSON array."""


def _build_user_message(bullets: list[str], jd_text: str) -> str:
    bullets_block = "\n".join(f"- {b}" for b in bullets)
    return (
        f"Job description (first 600 chars):\n{jd_text[:600]}\n\n"
        f"Resume bullets to evaluate:\n{bullets_block}"
    )


# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

def _call_groq(messages: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set. "
            "Get a free key at https://console.groq.com and set it in your .env"
        )
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model":       GROQ_MODEL,
            "messages":    messages,
            "temperature": 0.2,
            "max_tokens":  1800,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_ollama(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model":    OLLAMA_MODEL,
            "messages": messages,
            "stream":   False,
            "options":  {"temperature": 0.2},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call_llm(messages: list[dict]) -> str:
    if PROVIDER == LLMProvider.GROQ:
        return _call_groq(messages)
    return _call_ollama(messages)


# ---------------------------------------------------------------------------
# JSON parsing (handles edge cases like stray markdown fences)
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str) -> list[dict]:
    # strip markdown code fences if the model adds them anyway
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # try extracting the first [...] block
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse LLM response as JSON:\n{raw[:300]}")
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array from LLM.")
    return data


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def analyze_bullets(
    bullets:  list[str],
    jd_text:  str,
    section:  str = "experience",
) -> SectionFeedback:
    """
    Score and give feedback on a list of resume bullet points.

    Args:
        bullets:  List of bullet strings (stripped, no leading '-')
        jd_text:  Full job description text for relevance scoring
        section:  Section name (for labelling, e.g. 'experience')

    Returns:
        SectionFeedback with per-bullet scores and suggestions
    """
    if not bullets:
        return SectionFeedback(section=section, bullets=[], avg_score=0.0)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": _build_user_message(bullets, jd_text)},
    ]

    raw  = _call_llm(messages)
    data = _parse_json_response(raw)

    # align response list with input bullets (LLM may skip or reorder)
    bullet_map = {item.get("bullet", "").strip(): item for item in data}

    feedbacks = []
    for original in bullets:
        item = bullet_map.get(original.strip()) or (data[len(feedbacks)] if len(feedbacks) < len(data) else {})
        feedbacks.append(BulletFeedback(
            bullet      = original,
            score       = int(item.get("score",       5)),
            action_verb = bool(item.get("action_verb", False)),
            measurable  = bool(item.get("measurable",  False)),
            jd_relevant = bool(item.get("jd_relevant", False)),
            suggestion  = item.get("suggestion", ""),
            improved    = item.get("improved",   ""),
        ))

    avg = round(sum(f.score for f in feedbacks) / len(feedbacks), 1)
    return SectionFeedback(section=section, bullets=feedbacks, avg_score=avg)


# ---------------------------------------------------------------------------
# Batch helper — splits large sections into chunks of 10 to stay under limits
# ---------------------------------------------------------------------------

def analyze_section(
    bullets:    list[str],
    jd_text:    str,
    section:    str = "experience",
    chunk_size: int = 10,
) -> SectionFeedback:
    """
    Same as analyze_bullets but handles large sections safely by chunking.
    """
    all_feedbacks: list[BulletFeedback] = []

    for i in range(0, len(bullets), chunk_size):
        chunk  = bullets[i : i + chunk_size]
        result = analyze_bullets(chunk, jd_text, section)
        all_feedbacks.extend(result.bullets)

    avg = round(sum(f.score for f in all_feedbacks) / len(all_feedbacks), 1) if all_feedbacks else 0.0
    return SectionFeedback(section=section, bullets=all_feedbacks, avg_score=avg)
