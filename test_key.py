import httpx, os
from dotenv import load_dotenv
load_dotenv()

r = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
    json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
)
print(r.status_code, r.text)
