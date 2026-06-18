"""
Quick test — run from project root:
    python test_llm.py
"""

from llm import analyze_section

SAMPLE_BULLETS = [
    "Responsible for working on the backend team",
    "Developed REST APIs using FastAPI that reduced response latency by 40%",
    "Helped with database stuff",
    "Led migration of monolith to microservices, cutting deployment time from 2h to 12min",
    "Worked on frontend features using React",
    "Automated CI/CD pipeline with GitHub Actions, eliminating 6h/week of manual testing",
]

SAMPLE_JD = """
We are looking for a Software Engineer with experience in Python, REST APIs,
microservices, and cloud infrastructure (AWS/GCP). The candidate should be
comfortable with CI/CD pipelines, Docker, and working in an agile team.
Strong communication skills required.
"""

if __name__ == "__main__":
    print("Running per-bullet LLM feedback...\n")
    result = analyze_section(SAMPLE_BULLETS, SAMPLE_JD, section="experience")

    print(f"Section : {result.section}")
    print(f"Avg score: {result.avg_score}/10\n")
    print("-" * 70)

    for fb in result.bullets:
        tag = lambda v: "✓" if v else "✗"
        print(f"Bullet   : {fb.bullet}")
        print(f"Score    : {fb.score}/10  |  Action verb {tag(fb.action_verb)}  |  Measurable {tag(fb.measurable)}  |  JD relevant {tag(fb.jd_relevant)}")
        print(f"Tip      : {fb.suggestion}")
        print(f"Improved : {fb.improved}")
        print("-" * 70)
