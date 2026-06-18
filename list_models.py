import httpx, os
from dotenv import load_dotenv
load_dotenv()

r = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
)
print(r.json())
