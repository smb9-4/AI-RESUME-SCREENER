"""
Quick test — run from project root:
    python test_skill_gap.py
"""

from skill_gap import detect_skill_gaps

SAMPLE_RESUME = """
Skills: Python, FastAPI, PostgreSQL, Docker, Git, REST APIs, Pandas, NumPy, Linux
Experience:
- Built data pipelines using Python and Pandas for ETL processing
- Deployed containerised services with Docker on AWS EC2
- Designed REST APIs using FastAPI with PostgreSQL backend
- Collaborated in an agile team with strong communication and teamwork
"""

SAMPLE_JD = """
We are looking for a Backend Engineer with:
- Strong proficiency in Python and Go
- Experience with Kubernetes and Docker for container orchestration
- Knowledge of Kafka and Redis for distributed systems
- Hands-on experience with AWS (ECS, Lambda, S3)
- Familiarity with GraphQL and REST APIs
- Proficiency in PostgreSQL and MongoDB
- Experience with CI/CD using GitHub Actions or Jenkins
- Good communication and stakeholder management skills
- Microservices architecture experience required
- Bonus: experience with Terraform or Ansible for infrastructure as code
"""

if __name__ == "__main__":
    print("Running skill gap analysis...\n")
    report = detect_skill_gaps(SAMPLE_RESUME, SAMPLE_JD, use_embeddings=True)

    # --- Summary ---
    print(f"Gap score    : {report.gap_score}/100  (higher = bigger gap)")
    print(f"Hard gaps    : {len(report.hard_gaps)}")
    print(f"Soft matches : {len(report.soft_matches)}")
    print(f"Matched      : {len(report.matched)}")
    print(f"Resume-only  : {len(report.resume_only)}")

    # --- Hard gaps by category ---
    print("\n── Hard gaps by category ──────────────────────────")
    for category, gaps in report.by_category.items():
        print(f"\n  [{category.upper()}]")
        for g in gaps:
            bar = "█" * g.frequency + "░" * max(0, 5 - g.frequency)
            print(f"    {g.priority.upper():8}  {bar}  {g.skill}  (JD mentions: {g.frequency}x)")

    # --- Soft matches ---
    if report.soft_matches:
        print("\n── Soft matches (you have something close) ────────")
        for m in report.soft_matches:
            print(f"  JD wants '{m.jd_skill}'  →  you have '{m.resume_skill}'  (sim: {m.similarity:.2f})")

    # --- Matched skills ---
    print("\n── Matched skills ──────────────────────────────────")
    print("  " + ", ".join(report.matched) if report.matched else "  none")

    # --- Resume-only ---
    print("\n── On resume, not in JD ────────────────────────────")
    print("  " + ", ".join(report.resume_only) if report.resume_only else "  none")
