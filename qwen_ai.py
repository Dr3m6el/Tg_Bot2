import os
import httpx
from dotenv import load_dotenv

load_dotenv()

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
MODEL = "qwen/qwen3-235b-a22b"

async def ask_qwen(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "TelegramBot"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты — полезный ассистент, помогающий с учебными вопросами."},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
if __name__ == "__main__":
    import asyncio
    async def test():
        res = await ask_qwen("Привет, это тест.")
        print(res)
    asyncio.run(test())
