from supabase import create_client
import os
from datetime import datetime
from dotenv import load_dotenv
import re

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def extract_facts_from_message(message: str) -> dict:
    """
    Простейший пример извлечения фактов из текста.
    Распознаёт имя и город по шаблонам.
    """
    memory_update = {}

    # Имя
    name_match = re.search(r"(?:меня зовут|я)\s+([А-Яа-яA-Za-z]+)", message.lower())
    if name_match:
        memory_update["имя"] = name_match.group(1).capitalize()

    # Город
    city_match = re.search(r"я из\s+([А-Яа-яA-Za-z]+)", message.lower())
    if city_match:
        memory_update["город"] = city_match.group(1).capitalize()

    return memory_update

def get_or_create_memory(user_id: int) -> dict:
    """
    Получает память пользователя, если её нет — создаёт запись с пустой памятью.
    """
    # Попытка получить память
    result = supabase.table("memory").select("memory").eq("user_id", user_id).execute()
    
    # Если записи нет, создаем её с пустой памятью
    if len(result.data) == 0:
        # Создаём пустую запись
        supabase.table("memory").upsert({
            "user_id": user_id,
            "memory": {},
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        return {}  # Возвращаем пустой словарь

    # Если запись существует, возвращаем память
    return result.data[0]["memory"]

def update_memory(user_id: int, memory_update: dict):
    """
    Обновляет память пользователя, комбинируя старую и новую информацию.
    """
    # Получаем или создаём память для пользователя
    existing_memory = get_or_create_memory(user_id)
    
    # Обновляем память, комбинируя старую и новую информацию
    updated_memory = {**existing_memory, **memory_update}
    
    # Обновляем или создаём запись в базе данных
    supabase.table("memory").upsert({
        "user_id": user_id,
        "memory": updated_memory,
        "updated_at": datetime.utcnow().isoformat()
    }).execute()

def analyze_and_update_memory(user_id: int, message: str, role: str = "user"):
    """
    Анализирует сообщение и обновляет память пользователя.
    Обрабатываются только сообщения от пользователя (role="user").
    """
    if role != "user":
        return

    memory_update = extract_facts_from_message(message)
    if memory_update:
        update_memory(user_id, memory_update)
