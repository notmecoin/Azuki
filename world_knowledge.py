# world_knowledge.py

from datetime import datetime
import pytz
import requests

MOSCOW_TZ = pytz.timezone("Europe/Moscow")
UTC_TZ = pytz.utc

# Алиасы для токенов
TOKEN_ALIASES = {
    "bitcoin": ["биток", "битка", "биткоин", "btc", "биткойн"],
    "ethereum": ["эфир", "эфириум", "eth"],
    "toncoin": ["тон", "тончик", "ton"]
}

# Извлечение токена из текста
def extract_token_from_message(text: str) -> str | None:
    text = text.lower()
    for token, aliases in TOKEN_ALIASES.items():
        for alias in aliases:
            if alias in text:
                return token
    return None


def get_time_info(language="ru"):
    tz = UTC_TZ if language == "en" else MOSCOW_TZ
    now = datetime.now(tz)
    hour = now.hour

    if 5 <= hour < 12:
        part = "утро" if language == "ru" else "morning"
    elif 12 <= hour < 18:
        part = "день" if language == "ru" else "afternoon"
    elif 18 <= hour < 23:
        part = "вечер" if language == "ru" else "evening"
    else:
        part = "ночь" if language == "ru" else "night"

    return {
        "time_str": now.strftime("%H:%M"),
        "date_str": now.strftime("%d.%m.%Y") if language == "ru" else now.strftime("%Y-%m-%d"),
        "part_of_day": part
    }


def fetch_price_by_token_name(name: str, currency: str = "rub") -> str:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": name.lower().strip(),
            "vs_currencies": currency.lower().strip()
        }
        headers = {
            "accept": "application/json"
        }

        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        if name.lower() in data:
            price = data[name.lower()][currency.lower()]
            # Только отформатированная цифра
            formatted = f"{price:,.6f}" if price < 1 else f"{price:,.2f}"
            symbol = "$" if currency == "usd" else "₽"
            return f"{formatted} {symbol}"
        else:
            return None  # или raise
    except Exception as e:
        print(f"❌ Ошибка при получении курса для {name}: {e}")
        return None




def get_crypto_prices() -> str:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,toncoin",
            "vs_currencies": "rub"
        }
        headers = {"accept": "application/json"}

        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        btc = data.get("bitcoin", {}).get("rub")
        eth = data.get("ethereum", {}).get("rub")
        ton = data.get("toncoin", {}).get("rub")

        result = []
        if btc is not None:
            result.append(f"BTC: {btc}₽")
        if eth is not None:
            result.append(f"ETH: {eth}₽")
        if ton is not None:
            result.append(f"TON: {ton}₽")

        return "\n".join(result)

    except Exception as e:
        print("❌ Ошибка получения курса CoinGecko:", e)
        return "Данные недоступны."


def build_facts_prompt(language: str, user_message: str) -> str:
    facts = []

    try:
        current_time = get_time_info(language)
        if language == "ru":
            facts.append(f"Сейчас {current_time['time_str']} по МСК ({current_time['part_of_day']}).")
        else:
            facts.append(f"Current time is {current_time['time_str']} UTC ({current_time['part_of_day']}).")
    except Exception as e:
        print("❌ Ошибка времени:", e)

    try:
        facts.append(get_crypto_prices())
    except Exception as e:
        print("❌ Ошибка базового курса:", e)

    token = extract_token_from_message(user_message)
    if token:
        print(f"[🪙 DETECTED] Запрос курса для токена: {token}")
        try:
            facts.append("\n🔍 Запрошенный курс:\n" + fetch_price_by_token_name(token, currency="usd" if language == "en" else "rub"))
        except Exception as e:
            print("❌ Ошибка запроса по имени токена:", e)

    return "\n\n" + "\n".join(facts) + "\n"
