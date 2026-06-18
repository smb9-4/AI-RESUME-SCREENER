# AI Resume Analyzer

An AI-powered resume analysis tool that goes beyond a basic GPT wrapper. It combines NLP, semantic embeddings, and LLM feedback to give structured, actionable insights on how well a resume matches a job description.

---

## What it does

- **keyword extraction** — matches resume skills against JD keywords, mimicking real hiring software
- **Semantic matching** — uses sentence embeddings to catch synonym-level matches keyword scoring misses
- **Skill gap detection** — identifies missing skills, prioritized by how critical they are in the JD
- **Per-bullet LLM feedback** — scores each experience bullet on action verb, measurability, and JD relevance, then rewrites weak ones

---

## Project structure

```
AiResumeScreener/
├── llm.py               # LLM feedback engine (Groq / Ollama)
├── skill_gap.py         # Skill gap detection with semantic soft-matching
├── semantic_match.py    # Sentence embedding + cosine similarity scorer
├── nlp_extractor.py     # spaCy-based keyword and skill extraction
├── test_llm.py          # Test script for LLM bullet feedback
├── test_skill_gap.py    # Test script for skill gap detection
├── skills.json          # Skills taxonomy (technical / tools / soft / domain)
├── skills_list.json     # Extended skills reference
├── resume.pdf           # Sample resume for testing
├── jd.txt               # Sample job description for testing
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## Tech stack

| Component | Library | Cost |
|---|---|---|
| NLP extraction | spaCy + en_core_web_sm | Free |
| Semantic matching | sentence-transformers (MiniLM) | Free |
| Skill gap detection | scikit-learn + numpy | Free |
| LLM feedback | Groq API (Llama 3.3) | Free tier |
| LLM alternative | Ollama (local) | Free, offline |
| PDF parsing | pdfplumber | Free |

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/AIresume_analyser.git
cd AIresume_analyser/AiResumeScreener
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**3. Configure environment**
```bash
cp .env.example .env
```

Edit `.env`:
```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Get a free Groq API key at [console.groq.com](https://console.groq.com) — no credit card required.

**4. Run tests**
```bash
python test_skill_gap.py   # Test skill gap detection
python test_llm.py         # Test LLM bullet feedback
```

---

## Using Ollama (fully offline, no API key)

```bash
# Install Ollama from https://ollama.com
ollama pull llama3

# Update .env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## How the AI analysis works

### 1. NLP extraction (spaCy)
Reads raw text and identifies skills, noun phrases, and entities using part-of-speech tagging. Skills are matched against a taxonomy of 500+ known skills across four categories: technical, tools, soft, and domain.

### 2. Semantic matching (sentence-transformers)
Converts resume and JD into 384-dimensional vectors using `all-MiniLM-L6-v2`. Cosine similarity between the two vectors gives a 0–100 semantic match score — catches cases where the resume says "built APIs" and the JD says "REST development."

### 3. Skill gap detection
Compares JD skill set against resume skill set using set difference. Gaps are weighted by frequency (skills mentioned 3+ times in JD are marked critical). Semantic soft-matching then checks if any resume skill is close enough to a gap (threshold: 0.82 cosine similarity) before marking it a true gap.

### 4. Per-bullet LLM feedback
Each experience bullet is sent individually to the LLM with a structured prompt. The model scores it 1–10 across three dimensions — action verb, measurable outcome, JD relevance — and returns a suggestion and rewritten version as JSON.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` or `ollama` |
| `GROQ_API_KEY` |GROK API HERE |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model ID |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Ollama model name |
| `SOFT_MATCH_THRESHOLD` | `0.82` | Cosine similarity cutoff for soft skill matching |
| `SKILLS_TAXONOMY` | `data/skills.json` | Path to skills taxonomy file |

---

## Requirements

```
httpx
python-dotenv
spacy
sentence-transformers
scikit-learn
numpy
pdfplumber
python-docx
fpdf2
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "add your feature"`
4. Push to your fork: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT
