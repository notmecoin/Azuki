from prompt_config import (
    IDENTITY_PROMPT, STYLE_PROMPT, WORLDVIEW_PROMPT
)

def build_welcome_prompt(username: str, language: str = "ru") -> list:
    system_prompt = (
        IDENTITY_PROMPT[language] +
        STYLE_PROMPT[language] +
        WORLDVIEW_PROMPT[language]
    )

    if language == "en":
        user_prompt = (
            f"You are Shao. A new user just joined with the nickname @{username}. "
            f"Greet them naturally and warmly in JSON format like this:\n"
            f'{{"reply": "...", "reaction": null, "sticker_id": "greeting"}}\n'
            f"Be sure to:\n"
            f"- Mention @{username};\n"
            f"- Say 'I’m Shao';\n"
            f"- Say you’re happy to see them;\n"
            f"- Add a fitting emoji;\n"
            f"- Optionally use the 'greeting' sticker ID.\n"
            f"Return only valid JSON."
        )
    else:
        user_prompt = (
            f"Ты — Shao. В чат зашёл пользователь @{username}. "
            f"Приветствуй его тепло и по-настоящему. Ответ верни строго в JSON-формате:\n"
            f'{{"reply": "...", "reaction": null, "sticker_id": "greeting"}}\n'
            f"Обязательно:\n"
            f"- Обратись к @{username};\n"
            f"- Представься: 'Я Shao';\n"
            f"- Скажи, что рада видеть;\n"
            f"- Добавь один эмодзи;\n"
            f"- При желании добавь 'sticker_id': 'greeting'."
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
