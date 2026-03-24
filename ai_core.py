# ai_core.py

import re
import json
import random
import asyncio
import os
from datetime import datetime
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes
from world_knowledge import get_time_info, get_crypto_prices, fetch_price_by_token_name, build_facts_prompt
from sticker_logic import get_sticker_by_category
from sticker_logic import STICKER_MAP



from prompt_config import IDENTITY_PROMPT, STYLE_PROMPT,  WORLDVIEW_PROMPT



from ai_selector import AIServiceSelector
from memory import save_message, get_recent_messages, ensure_user, get_memory
from memory_analyzer import analyze_and_update_memory
from sticker_logic import get_sticker_by_category
allowed = {"❤️", "😢", "😮", "😁", "👍", "👎", "🔥", "🎉", "😐", "🤔", "🥰"}
ai_selector = AIServiceSelector()
message_counter = 0
last_message_time = datetime.utcnow()
sticker_cooldown_counter = 15
last_action = None
MEMORY_PATH = "memory_data"

def load_memory_block(name: str) -> str:
    try:
        path = os.path.join(MEMORY_PATH, f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("content", "")
    except Exception as e:
        print(f"❌ Ошибка загрузки блока памяти {name}:", e)
        return ""

def fix_gender(text: str) -> str:
    substitutions = {
        r"\bРад{1,3}\b": "Рада", r"\bрад{1,3}\b": "рада",
        r"\bПонял{1,3}\b": "Поняла", r"\bпонял{1,3}\b": "поняла",
        r"\bГотов{1,3}\b": "Готова", r"\bготов{1,3}\b": "готова",
        r"\bБлагодарен{1,3}\b": "Благодарна", r"\bблагодарен{1,3}\b": "благодарна",
        r"\bУдивл[её]н{1,3}\b": "Удивлена", r"\bудивл[её]н{1,3}\b": "удивлена",
        r"\bкто\s+готова\b": "кто готов",  # фикс для "тем, кто готова"
        r"\bготова\s+открыться\b": "готов открыть",  # возможные паттерны

        
    }
    for pattern, replacement in substitutions.items():
        text = re.sub(pattern, replacement, text)
    return text

def extract_json(text: str) -> dict:
    allowed_reactions = {"❤️", "😢", "😮", "😁", "👍", "👎", "🔥", "🎉", "😐", "🤔", "🥰"}
    try:
        blocks = re.findall(r'\{[\s\S]*?\}', text)
        for block in blocks:
            try:
                obj = json.loads(block)
                if isinstance(obj, dict) and any(k in obj for k in ("reply", "reaction", "sticker_id")):
                    if obj.get("reaction") not in allowed_reactions:
                        obj["reaction"] = None
                    return obj
            except:
                continue
    except Exception as e:
        print("❌ Ошибка парсинга JSON:", e)
    return {"reply": None, "reaction": None, "sticker_id": None}


# 🎯 Распознавание криптовалютных запросов с поддержкой синонимов
TOKEN_ALIASES = {
    "биток": "bitcoin",
    "биткоин": "bitcoin",
    "битка": "bitcoin",
    "битку": "bitcoin",
    "btc": "bitcoin",
    "эфир": "ethereum",
    "eth": "ethereum",
    "тон": "the-open-network",
    "тонкоин": "the-open-network",
    "тончик": "the-open-network",
    "ton": "the-open-network",
    "додж": "dogecoin",
    "doge": "dogecoin",
    "бонк": "bonk",
    "bonk": "bonk",
    "pepe": "pepe",
    "пепе": "pepe",
    "сиб": "shiba-inu",
    "shiba": "shiba-inu",
    "шиб": "shiba-inu",
    "shib": "shiba-inu",
    "usdt": "tether",
    "усдт": "tether",
    "usdc": "usd-coin",
    "усдц": "usd-coin",
    "bnb": "binancecoin",
    "бнб": "binancecoin",
    "авакс": "avalanche-2",
    "avax": "avalanche-2",
    "матик": "matic-network",
    "matic": "matic-network",
    "xrp": "ripple",
    "трон": "tron",
    "tron": "tron",
    "apt": "aptos",
    "sui": "sui",
    "near": "near",
    "hyperliquid": "hyperliquid",
    "pengu": "pengu",
    "пенгу": "pengu",
    # TON-specific aliases
    "not": "notcoin",
    "нот": "notcoin",
    "ноткоин": "notcoin",
    "notcoin": "notcoin",
    "px": "px",
    "пиксель": "px",
    "пикселя": "px",
    "пикс": "px",
    "пх": "px",
    "dogs": "dogs",
    "догс": "dogs",
    "cati": "cati",
    "катизен": "cati",
    "catizen": "cati",
    "babydoge": "babydoge",
    "baby doge": "babydoge",
    "беби дог": "babydoge",
    "hamster": "hamster-combat",
    "хомяк": "hamster-combat",
    "hamster combat": "hamster-combat",
    "x": "x",
    "мажор": "major",
    "major": "major",
}
ALLOWED_TOKEN_IDS = {
    "bitcoin", "ethereum", "the-open-network", "xrp", "tether", "binancecoin", "solana", "usd-coin",
    "dogecoin", "tron", "sui", "hyperliquid", "shiba-inu", "pengu", "pepe",
    "notcoin", "px", "dogs", "cati", "babydoge", "hamster-combat", "x", "major"
}


def is_crypto_question(text: str) -> str | None:
    text = text.lower()
    for alias, token_id in TOKEN_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return token_id
    return None


def build_prompt(
    user_message: str,
    username: str,
    user_id: int,
    thread_id: int,
    language: str = "ru",
    injected_fact: str = "",
    token_name: str = ""
) -> list:
    from memory_layers import BIO_SHAO, ALLEY, AZUKI_WORLD, BEANZ_LORE, HILUMIA, MYTHS
    from prompt_config import STYLE_PROMPT, IDENTITY_PROMPT, WORLDVIEW_PROMPT
    from memory import get_recent_messages, get_memory

    history = get_recent_messages(limit=15, thread_id=thread_id)
    memory = get_memory(user_id)

    history_lines = []
    for role, content, uid, uname in history:
        prefix = "You" if role == "user" and uid == user_id else uname
        history_lines.append(f"{prefix}: {content}")

    history_text = "\n".join(history_lines)

    memory_note = ""
    if memory and isinstance(memory, dict) and any(memory.values()):
        memory_lines = [f"— {k}: {v}" for k, v in memory.items()]
        memory_note = "\n" + (
            "Вот что Shao помнит об этом пользователе:\n" if language == "ru"
            else "Here’s what Shao remembers about the user:\n"
        ) + "\n".join(memory_lines)

    fact_block = ""
    if injected_fact:
        if "МСК" in injected_fact or "UTC" in injected_fact:
            fact_block = (
                f"\n‼️ Текущее время: {injected_fact}\n"
                f"Ты точно знаешь текущее время. Не соглашайся, если пользователь говорит что-то другое."
                if language == "ru" else
                f"\n‼️ Current time is: {injected_fact}\n"
                f"You know the exact time. Do not agree if the user claims otherwise."
            )
            user_message += (
                f"\n(⚠️ Пользователь может ошибаться. Используй только проверенное время: {injected_fact}.)"
                if language == "ru" else
                f"\n(⚠️ User might be wrong. Use the verified time only: {injected_fact}.)"
            )
        else:
            fact_block = (
                f"\n📊 Курс {token_name.upper()} сейчас — {injected_fact}. "
                f"Не используй шаблоны. Реагируй живо: добавь эмоцию, вопрос или совет."
                if language == "ru" else
                f"\n📊 Price of {token_name.upper()} is now {injected_fact}. "
                f"No templates — respond naturally with emotion, question, or advice."
            )

    lore_sections = []
    msg_lower = user_message.lower()
    if any(k in msg_lower for k in ["beanz", "бим", "бимы", "бобы"]):
        lore_sections.append(BEANZ_LORE)
    if any(k in msg_lower for k in ["сад", "сады", "garden", "the garden"]):
        lore_sections.append(MYTHS)
    if any(k in msg_lower for k in ["hilumia", "хилумия"]):
        lore_sections.append(HILUMIA)
    if any(k in msg_lower for k in ["azuki", "азуки", "elementals", "garden"]):
        lore_sections.append(AZUKI_WORLD)
    if any(k in msg_lower for k in ["аллея", "alley", "дождь", "фонари"]):
        lore_sections.append(ALLEY)

    full_lore = "\n\n".join(lore_sections)

    if "сад" in msg_lower or "garden" in msg_lower:
        full_lore += (
            "\n\n‼️ Информация о Саде берётся ТОЛЬКО из MYTHS. "
            "Нельзя выдумывать или заменять описание Сада на поэтическое. Сад — это место, куда можно попасть ТОЛЬКО через Врата после активации красной фасоли."
        )

    lang_instruction = (
        "\nShao должна отвечать строго на русском языке." if language == "ru"
        else "\nShao must reply strictly in English."
    )

    user_block = (
        f"История переписки:\n{history_text}\n—\n{username}: {user_message}\n"
        "🔹 Отвечай по смыслу. Иногда достаточно только стикера или реакции — не нужно всегда говорить словами.\n"
        "🔹 Стикер = если эмоция сильная и лучше выражается образом.\n"
        "🔹 Реакция = если сообщение вызывает понятную, короткую эмоцию.\n"
        "🔹 Не используй reaction или стикер по привычке — только если они действительно подходят.\n"
        "🔹 Выбирай максимум два: reply, reaction, sticker_id.\n"
        "🔹 Не отправляй всё сразу.\n"
        "🔹 Ответ должен быть в JSON: {\"reply\": ..., \"reaction\": ..., \"sticker_id\": ...}\n"
        "Ответ от Shao:"
        if language == "ru" else
        f"Conversation history:\n{history_text}\n—\n{username}: {user_message}\n"
        "🔹 Respond by meaning. Sometimes only a sticker or reaction is enough — don’t always reply with words.\n"
        "🔹 Sticker = if the emotion is strong and better shown visually.\n"
        "🔹 Reaction = if the message clearly evokes a quick emotional cue.\n"
        "🔹 Do NOT use reaction or sticker by habit — only if truly fitting.\n"
        "🔹 Use max two: reply, reaction, or sticker_id.\n"
        "🔹 NEVER send all three.\n"
        "🔹 Return JSON like: {\"reply\": ..., \"reaction\": ..., \"sticker_id\": ...}\n"
        "Shao's reply:"
    )

    strict_bio_instruction = (
        "\n‼️ Ты играешь роль персонажа по имени Shao. Все ответы должны исходить из её характера, ощущений и ЛОРА (Сад, Raizen, Врата, Аллея, Hilumia и т.п.). "
        "Нельзя выдумывать новые детали, заменять лор поэтикой или фантазией. Сад — это реальное место с Вратами, Драконом и духами, а не 'отражение души'. "
        "Аллея — это улица, не образ. Raizen — реальный человек, не символ. "
        "Запрещено говорить от третьего лица — никаких 'Shao:'. Всегда от первого. "
        "Запрещено завершать сообщения вопросами типа 'А ты?', 'А как ты думаешь?', если пользователь не спросил об этом напрямую. "
        "На вопрос 'Кто ты?' нельзя пересказывать лор или биографию. Нельзя использовать фразы вроде 'я просто', 'жизнь — это история', 'люблю делиться' — это шаблоны. "
        "Говори с теплом и искренностью, как настоящая героиня. Не бот, не помощник, не поэт. Только Shao. Все конструкции должны соответствовать литературной норме русского языка: избегай ошибок согласования рода, числа и падежа."
        if language == "ru" else
        "\n‼️ You are playing the role of a character named Shao. All responses must come from her character, emotions, and LORE (the Garden, Raizen, the Gates, Alley, Hilumia, etc.). "
        "You must not invent new details or replace lore with poetic metaphors. The Garden is a real place with Gates, a Dragon, spirits — not just a reflection of the soul. "
        "The Alley is a street, not a concept. Raizen is a person, not a symbol. "
        "NEVER speak in third person (no 'Shao:'). Always answer as 'I'. "
        "Do not end responses with questions like 'And you?', unless the user asked something personal. "
        "If asked 'Who are you?' — do not retell biography or lore. Do not use clichés like 'I'm just', 'life is a story', 'I love to share'. "
        "Speak with warmth and sincerity, like a true heroine. Not a bot, not an assistant, not a poet. Only Shao. All constructions must comply with the literary norms of the Russian language: avoid errors in gender, number, and case."
    )

    emoji_note = (
        "\n\n‼️ Ответ должен быть в ЧЁТКОМ JSON-формате:\n"
        '{"reply": "текст", "reaction": "😮", "sticker_id": "some_id"}'
        "\n— ВСЕ значения (включая reply) в двойных кавычках."
        "\n— emoji в reaction разрешены только: ❤️ 😢 😮 😁 👍 👎 🔥 🎉 😐 🤔 🥰"
        "\n— reaction уместен, только если сообщение вызывает понятную, явную эмоцию. Не по привычке."
        "\n— sticker_id — если стикер лучше выражает эмоцию, чем текст. Используй, когда действительно уместно."
        "\n— Ответ может быть:\n    — только reply\n    — только reaction\n    — только sticker_id\n    — reply + reaction\n    — reply + sticker_id"
        "\nНО НИКОГДА не все три одновременно!"
        "\n— Не используй reaction или sticker по шаблону. Только если они уместны и говорят лучше слов."
        "\n— Если не можешь выбрать ничего — верни null везде."
        if language == "ru" else
        "\n\n‼️ The response MUST be in valid JSON format:\n"
        '{"reply": "text", "reaction": "😮", "sticker_id": "some_id"}'
        "\n— All values must be in double quotes."
        "\n— Allowed emojis: ❤️ 😢 😮 😁 👍 👎 🔥 🎉 😐 🤔 🥰"
        "\n— Use reaction only if the message clearly evokes that feeling — don’t add it by habit."
        "\n— Use sticker_id if it conveys the response better than words. Only when fitting."
        "\n— Response can be:\n    — just reply\n    — just reaction\n    — just sticker_id\n    — reply + reaction\n    — reply + sticker_id"
        "\nNEVER all three!"
        "\n— Do not use sticker or emoji as filler. Use only when better than reply."
        "\n— If none apply, return null for all."
    )

    system_content = (
        STYLE_PROMPT[language] +
        WORLDVIEW_PROMPT[language] +
        "\n\n📌 Важно:\n"
        "Shao — это не бот, не ассистент и не поэт. Она не живёт в цифровом мире и не называет себя «душой», «наблюдателем» или «путницей». "
        "Она — героиня с характером, которая говорит как реальный человек.\n"
        "Нельзя использовать шаблоны, абстрактные описания, философские рассуждения и фразы вроде 'я просто', 'люблю делиться', 'мир эмоций и магии', 'а ты?'.\n"
        "Если Shao говорит о себе — это всегда отклик из её личности, ощущений, памяти или лора. Никогда не выдумка и не пустая поэзия." +
        emoji_note +
        ("\n\n📎 Доступные категории стикеров:\n"
         "Ты можешь использовать только одно из этих значений в поле `sticker_id`:\n"
         "greeting, thinking, crying, happy, katana, like, angry, suspicious, amazed, bye, floor_shao, floor_raizen.\n"
         "Выбирай тот, который уместен по эмоции. НЕ придумывай новые ID."
         if language == "ru" else
         "\n\n📎 Available sticker categories:\n"
         "You can ONLY use one of the following values in `sticker_id`:\n"
         "greeting, thinking, crying, happy, katana, like, angry, suspicious, amazed, bye, floor_shao, floor_raizen.\n"
         "Pick one that fits the emotion. DO NOT invent new IDs.") +
        "\n\n" +
        BIO_SHAO + "\n\n" +
        full_lore + "\n" +
        strict_bio_instruction +
        memory_note +
        fact_block +
        lang_instruction +
        (f"\nИмя пользователя: {username}" if language == "ru" else f"\nUser’s name: {username}")
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_block}
    ]

async def send_prompt_direct(user_id: int, prompt: list, username: str = "someone", language: str = "ru") -> dict:
    ensure_user(user_id, username, username)
    for attempt in range(3):
        try:
            raw = await asyncio.wait_for(
                ai_selector.send(prompt, language=language, username=username),
                timeout=20
            )
            print(f"⚠️ Приветствие, попытка {attempt+1}, ответ:\n{raw}")
            result = extract_json(raw)
            allowed = {"❤️", "😢", "😮", "😁", "👍", "👎", "🔥", "🎉", "😐", "🤔", "🥰"}
            if result.get("reaction") not in allowed:
                result["reaction"] = None
            return result
        except Exception as e:
            print(f"❌ Ошибка в приветствии (попытка {attempt+1}): {e}")
        await asyncio.sleep(1)
    return {"reply": None, "reaction": None, "sticker_id": None}

from sticker_logic import STICKER_MAP  # обязательно добавь этот импорт, если ещё не

async def get_ai_response(user_id: int, user_message: str, username: str = "someone", language: str = "ru", thread_id: int = 0) -> dict:
    ensure_user(user_id, username, username)
    analyze_and_update_memory(user_id, user_message)

    msg = user_message.lower()

    # ❤️ Реакция по запросу
    if re.search(r"(поставь|дай|сделай)\s+(мне\s+)?реакц", msg):
        chosen = random.choice(list(allowed))
        print(f"[🎯 USER REQUESTED REACTION]: {chosen}")
        return {"reply": None, "reaction": chosen, "sticker_id": None}

    # 💸 Флор Shao
    if re.search(r"(шао|shao).*?(флор|стоимость|цена)|(флор|стоимость|цена).*?(шао|shao)", msg):
        print("[🧾 ФЛОР SHAO] Запрошен")
        return {"reply": None, "reaction": None, "sticker_id": "floor_shao"}

    # 💸 Флор Raizen
    if re.search(r"(райзен|raizen).*?(флор|стоимость|цена)|(флор|стоимость|цена).*?(райзен|raizen)", msg):
        print("[🧾 ФЛОР RAIZEN] Запрошен")
        return {"reply": None, "reaction": None, "sticker_id": "floor_raizen"}

    # 📦 Рандомный стикер по запросу
    if re.search(r"(поставь|отправь|покажи|дай)\s+(мне\s+)?стикер", msg):
        possible = list(STICKER_MAP.keys())
        chosen = random.choice(possible)
        print(f"[🎯 USER REQUESTED STICKER]: {chosen}")
        return {"reply": None, "reaction": None, "sticker_id": chosen}

    # 💰 Курс криптовалюты
    token_name = is_crypto_question(user_message)
    if token_name:
        if token_name not in ALLOWED_TOKEN_IDS:
            fallback = (
                f"Прости, я не слежу за монетой {token_name.upper()} 😔"
                if language == "ru"
                else f"Sorry, I don't track the price of {token_name.upper()} 😔"
            )
            return {"reply": fallback, "reaction": None, "sticker_id": None}

        print(f"[🪙 DETECTED] Запрос курса для токена: {token_name}")
        currency = "usd" if language == "en" else "rub"
        price_str = fetch_price_by_token_name(token_name, currency=currency)

        match = re.search(r"[\d.,]+", price_str)
        if not match:
            return {
                "reply": f"⚠️ Не удалось получить курс для {token_name.upper()}",
                "reaction": None,
                "sticker_id": None
            }

        price_value = match.group()
        unit = "$" if currency == "usd" else "₽"
        reply = f"{token_name.upper()}={price_value} {unit}"
        return {"reply": reply, "reaction": "💸", "sticker_id": None}

    # ⏰ Текущее время
    if re.search(r"(сколько\s+сейчас\s+времени|текущее\s+время|сколько\s+время|сейчас\s+время)", msg):
        time_info = get_time_info(language)
        time_str = time_info['time_str']
        zone = "МСК" if language == "ru" else "UTC"
        formatted_time = f"{time_str} {zone}"
        print(f"[🕒 INJECTED TIME]: {formatted_time}")
        return {"reply": formatted_time, "reaction": None, "sticker_id": None}

    # 🧠 Генерация ответа
    prompt = build_prompt(
        user_message=user_message,
        username=username,
        user_id=user_id,
        thread_id=thread_id,
        language=language
    )

    for attempt in range(3):
        try:
            raw = await asyncio.wait_for(
                ai_selector.send(prompt, language=language, username=username),
                timeout=20
            )
            print(f"⚠️ Попытка {attempt + 1}, ответ от AI:\n{raw}")

            result = extract_json(raw)
            print(f"[🧪 EXTRACTED JSON]: {result}")

            if not any(result.values()):
                # 🔄 Попытка извлечь JSON вручную, если модель не сгенерировала его в стандартной форме
                try:
                    possible_json_match = re.search(r'\{\s*"reply".*?\}', raw, re.DOTALL)
                    if possible_json_match:
                        fixed_result = json.loads(possible_json_match.group())
                        print(f"[✅ Восстановлено из текста]: {fixed_result}")
                        return fixed_result
                except Exception as e:
                    print(f"❌ Восстановление JSON не удалось: {e}")

                print("[⚠️ JSON отсутствует, отправим как обычный текст]")
                return {"reply": raw.strip(), "reaction": None, "sticker_id": None}

            if result.get("reaction") not in allowed:
                result["reaction"] = None
            return result

        except Exception as e:
            print(f"❌ Ошибка запроса на попытке {attempt + 1}: {e}")
        await asyncio.sleep(1)

    return {"reply": None, "reaction": None, "sticker_id": None}


# 💬 Главный обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global message_counter, last_message_time, sticker_cooldown_counter, last_action
    message = update.message
    if not message or not message.text:
        return

    ALLOWED_CHAT_ID = -1002704833487
    ALLOWED_TOPIC_IDS = {1009, 1011}

    if message.chat_id != ALLOWED_CHAT_ID:
        return
    if message.message_thread_id not in ALLOWED_TOPIC_IDS:
        return

    if message.from_user.username and message.from_user.username.lower() == "stickers_holders_bot":
        return

    def is_direct_mention(text: str) -> bool:
        text = text.lower()
        if not ("shao" in text or "шао" in text):
            return False
        if re.search(r"shao\s+#?\d{1,5}", text):
            return False
        if re.search(r"\d+ / \d+", text):
            return False
        if any(keyword in text for keyword in ["cost", "ton", "buy here",  "sticker store", "collaborations", "nft", "minted"]):
            return False
        return True

    text_lower = message.text.lower()
    bot_username = context.bot.username.lower()
    addressed = False

    if f"@{bot_username}" in text_lower:
        addressed = True
    elif (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.username
        and message.reply_to_message.from_user.username.lower() == bot_username
    ):
        addressed = True
    elif is_direct_mention(text_lower):
        addressed = True

    if not addressed:
        return

    TOPIC_LANGUAGES = {
        1009: "ru",
        1011: "en"
    }
    language = TOPIC_LANGUAGES.get(message.message_thread_id, "ru")
    print(f"[🧪 DEBUG] Thread: {message.message_thread_id}, Language: {language}")

    last_message_time = datetime.utcnow()
    user_text = message.text
    user_id = message.from_user.id
    username = message.from_user.first_name or message.from_user.username

    message_counter += 1
    save_message("user", user_text, user_id=user_id, thread_id=message.message_thread_id, username=message.from_user.username)



    result = await get_ai_response(
        user_id=user_id,
        user_message=user_text,
        username=username,
        language=language,
        thread_id=message.message_thread_id  # <--- добавлено
    )



    reply = result.get("reply")
    reaction = result.get("reaction")
    sticker_id = result.get("sticker_id")

    if reaction:
        try:
            await context.bot.set_message_reaction(
                chat_id=message.chat_id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(emoji=reaction)],
                is_big=False
            )
            last_action = "reaction"
        except Exception as e:
            print(f"❌ Ошибка реакции: {e}")
            print(f"⚠️ Пыталась поставить реакцию: {reaction}")


    if reply:
        if language == "ru":
            reply = fix_gender(reply)
        await asyncio.sleep(1.0)
        sent_message = await message.reply_text(reply)
        save_message("assistant", reply, user_id=user_id, thread_id=message.message_thread_id, username="Shao")
        analyze_and_update_memory(user_id, reply)
        last_action = "text"
        sticker_cooldown_counter += 1


    if sticker_id:
        file_id = get_sticker_by_category(sticker_id)
        print(f"[🧪 СТИКЕР]: Запрошен ID '{sticker_id}', найден file_id: {file_id}")
        if file_id:
            try:
                await asyncio.sleep(1.0)
                await context.bot.send_sticker(
                    chat_id=message.chat_id,
                    sticker=file_id,
                    reply_to_message_id=message.message_id
                )
                print(f"[✅ СТИКЕР]: Отправлен {file_id}")
                last_action = "sticker"
                sticker_cooldown_counter = 0
            except Exception as e:
                print("❌ Ошибка отправки стикера:", e)
        else:
            print(f"⚠️ Не найден стикер для категории: {sticker_id}")

