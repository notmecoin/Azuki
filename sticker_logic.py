import random
from telegram import Bot

# 📦 Название Telegram стикерпакa
FLOOR_PACK_NAME = "stickers_prices_by_tonundrwrld_stickers_bot"

# 🔁 Динамически обновляемые стикеры
DYNAMIC_STICKERS = {
    "floor_shao": None,
    "floor_raizen": None
}

# 📌 Уникальные file_unique_id — они не меняются
FLOOR_UNIQUE_IDS = {
    "floor_shao": "AgAD9oUAAtic2Es",
    "floor_raizen": "AgADD3cAAkMw4Es"
}

# 📦 Статичные стикеры
STICKER_MAP = {
    "greeting": "CAACAgIAAxkBAAMHaFLS9d0Zgujmi5LJNqvQeTb3sB4AAgx5AAIOgGBKbXosP5frkwI2BA",
    "thinking": "CAACAgIAAxkBAAMIaFLS9xgymQxFBfI9Mprs3xhrij0AAjlvAAJSx2BKiWEn1wAB5b7aNgQ",
    "crying": "CAACAgIAAxkBAAMJaFLS-e6QeSvdwqXPjFguyRh5sEgAAtxyAAKYaWBKg9tAGSnfT5Q2BA",
    "happy": "CAACAgIAAxkBAAMFaFLQ2xQV_Dz5s29486u0x2rswDsAAl90AAJ1dWBK5B1-1lG85fY2BA",
    "katana": "CAACAgIAAxkBAAMLaFLS_Vc6y9qX7_pkJBr8-mKvyuQAAtZyAAKZymhKq-CjzsX5wio2BA",
    "like": "CAACAgIAAxkBAAMMaFLS_8RwlitdtzNt-nNm6aI4pU8AAll5AALBAmBKKjv7cJv7RiM2BA",
    "angry": "CAACAgIAAxkBAAMNaFLTAbyfxqGhiKCIAzY8EUlES6MAAtmAAAI2zWFKE0zv2OE1KGg2BA",
    "suspicious": "CAACAgIAAxkBAAMOaFLTAlaUBeo1jr1atSNMIVuT9PUAAm5xAAJyQ2hKgDCwXjMGnTA2BA",
    "amazed": "CAACAgIAAxkBAAMPaFLTBX2J3q6Ntw7kPmC6TBJ6WsIAAqhsAALa32hKi3ISf2ttZmY2BA",
    "bye": "CAACAgIAAxkBAAMQaFLTB8dKykzL2Gg7zhtqzSnUmXcAAut0AAL7NGlKGw4reXHSrwM2BA"
}

def get_sticker_by_category(category: str) -> str | None:
    """Возвращает file_id стикера по категории."""
    return DYNAMIC_STICKERS.get(category) or STICKER_MAP.get(category)

def update_dynamic_sticker(category: str, file_id: str) -> None:
    """Ручное обновление file_id для динамического стикера."""
    if category in DYNAMIC_STICKERS:
        DYNAMIC_STICKERS[category] = file_id

async def update_dynamic_stickers(bot: Bot):
    """Обновляет file_id для стикеров с floor_shao и floor_raizen по уникальному ID."""
    try:
        sticker_set = await bot.get_sticker_set(FLOOR_PACK_NAME)
        updated = []
        for sticker in sticker_set.stickers:
            for key, unique_id in FLOOR_UNIQUE_IDS.items():
                if sticker.file_unique_id == unique_id:
                    DYNAMIC_STICKERS[key] = sticker.file_id
                    updated.append(key)
        print(f"[🚀] Стикеры обновлены при запуске: {updated}")
    except Exception as e:
        print(f"❌ Ошибка при обновлении стикеров: {type(e).__name__}: {e}")
