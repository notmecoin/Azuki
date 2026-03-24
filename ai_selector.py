import os
import asyncio
from openai import OpenAI  # OpenAI SDK v1

from prompt_config import (
    IDENTITY_PROMPT, STYLE_PROMPT,  WORLDVIEW_PROMPT
)

OPENAI_MODEL = "gpt-4o-mini"
OPENAI_BASE_URL = "https://api.proxyapi.ru/openai/v1"  # 👈 для ProxyAPI

class AIServiceSelector:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=OPENAI_BASE_URL
        )

    def build_system_prompt(self, username="someone", language="ru") -> str:
        identity = IDENTITY_PROMPT[language]
        style = STYLE_PROMPT[language]
        worldview = WORLDVIEW_PROMPT[language]

        if language == "en":
            rules = (
                "\n‼️ Never use <think>, never describe the answer process. Generate only JSON.\n"
                f"\nUser name: {username}"
                "\nShao must respond strictly in English."
            )
        else:
            rules = (
                "\n‼️ Никогда не используй <think>, не описывай процесс ответа. Генерируй сразу JSON без лишнего текста.\n"
                f"\nИмя пользователя: {username}"
                "\nShao должна отвечать строго на русском языке."
            )

        return identity + style + worldview + rules

    def detect_language(self, messages: list) -> str:
        for m in messages:
            if "Shao must respond strictly in English." in m.get("content", ""):
                return "en"
        return "ru"

    def extract_username(self, messages: list) -> str:
        for m in messages:
            content = m.get("content", "")
            if "Имя пользователя:" in content:
                return content.split("Имя пользователя:")[-1].strip()
            if "User name:" in content:
                return content.split("User name:")[-1].strip()
        return "someone"

    async def send(self, messages: list, language="ru", username="someone") -> str:
        try:

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
                top_p=0.9
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"⚠️ Ошибка OpenAI API: {e}")
            return '{"reply": null, "reaction": null, "sticker_id": null}'

    async def send_text(self, prompt: str, language="ru", username="someone") -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": self.build_system_prompt(username=username, language=language)
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.8,
                max_tokens=100,
                top_p=0.9
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️ Ошибка OpenAI API: {e}")
            return "..."
