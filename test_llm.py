from llm import analyze_bullets

jd_text = """
Software Engineer

Requirements:

Programming Languages:
- Python
- Java
- Go

Backend:
- FastAPI
- REST APIs
- GraphQL
- Microservices

Databases:
- PostgreSQL
- MongoDB
- Redis

Cloud & DevOps:
- Docker
- Kubernetes
- Terraform
- Jenkins
- GitHub Actions
- Kafka

Tools:
- Git
- Linux

Concepts:
- Distributed Systems
- System Design
- CI/CD

Soft Skills:
- Communication
- Collaboration
- Stakeholder Management
- Problem Solving

Nice to Have:
- AWS
- GCP
- Azure
"""

bullets = [
    "Developed REST APIs using FastAPI and PostgreSQL, serving over 50,000 requests per day.",
    
    "Built scalable backend microservices and integrated Kafka-based asynchronous communication to improve throughput by 30%.",

    "Containerized applications with Docker and automated deployments using GitHub Actions and Jenkins CI/CD pipelines.",

    "Implemented Redis caching and optimized database queries, reducing API response time by 40%.",

    "Designed and maintained MongoDB and PostgreSQL databases for high availability and reliability.",

    "Collaborated with cross-functional teams and stakeholders to gather requirements and deliver production-ready features.",

    "Worked on Linux environments using Git for version control and followed software engineering best practices.",

    "Contributed to distributed system architecture and improved application scalability using microservice design principles.",

    "Deployed applications on AWS cloud infrastructure and monitored system performance.",

    "Participated in code reviews, debugging, and performance optimization to ensure maintainable and efficient software."
]

result = analyze_bullets(bullets, jd_text)

print("\nAverage Score:", result.avg_score)

for i, feedback in enumerate(result.bullets, 1):
    print("\n---------------------------")
    print("Bullet", i)
    print("Original  :", feedback.bullet)
    print("Score     :", feedback.score)
    print("Action Verb :", feedback.action_verb)
    print("Measurable  :", feedback.measurable)
    print("JD Relevant :", feedback.jd_relevant)
    print("Suggestion :", feedback.suggestion)
    print("Improved   :", feedback.improved)