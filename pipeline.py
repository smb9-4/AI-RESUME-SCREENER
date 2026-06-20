from nlp_extractor import extract_skills
from semantic_match import compute_similarity
from skill_gap import detect_skill_gaps
from llm import analyze_section


def analyze_resume(resume_text, jd_text):

    skills = extract_skills(resume_text, jd_text)

    similarity_score = compute_similarity(
        resume_text,
        jd_text
    )

    gap_report = detect_skill_gaps(
        resume_text,
        jd_text
    )

    feedback = analyze_section(
        resume_text.split("\n"),
        jd_text
    )

    return {
        "score": similarity_score,
        "skills": skills,
        "gap_report": gap_report,
        "feedback": feedback
    }