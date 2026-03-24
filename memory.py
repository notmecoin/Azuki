from supabase import create_client
import os
from datetime import datetime
from dotenv import load_dotenv
import json
import re

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def ensure_user(user_id: int, username: str = None, first_name: str = None):
    """Создаёт пользователя в базе, если его ещё нет"""
    existing = supabase.table("users").select("id").eq("id", user_id).execute()
    if not existing.data:
        supabase.table("users").insert({
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "last_seen_at": datetime.utcnow().isoformat()
        }).execute()
    else:
        supabase.table("users").update({
            "last_seen_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()

def save_message(role: str, content: str, user_id: int = None, thread_id: int = None, username: str = None):
    """Сохраняет сообщение в таблицу messages, включая имя пользователя"""
    supabase.table("messages").insert({
        "role": role,
        "content": content,
        "user_id": user_id,
        "thread_id": thread_id,
        "username": username,
        "created_at": datetime.utcnow().isoformat()
    }).execute()


def get_recent_messages(limit=15, user_id=None, thread_id=None):
    """
    Возвращает последние N сообщений по треду или пользователю
    в формате [(role, content, user_id, username), ...]
    """
    query = supabase.table("messages").select("role, content, user_id, username").order("created_at", desc=True).limit(limit)
    if thread_id is not None:
        query = query.eq("thread_id", thread_id)
    elif user_id is not None:
        query = query.eq("user_id", user_id)

    result = query.execute()
    return [(m["role"], m["content"], m.get("user_id", 0), m.get("username", "User")) for m in reversed(result.data or [])]


def get_memory(user_id: int) -> dict:
    """Извлекает память пользователя из таблицы memory"""
    result = supabase.table("memory").select("memory").eq("user_id", user_id).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]["memory"]
    return {}

def update_memory(user_id: int, memory_update: dict):
    """Обновляет память пользователя (upsert)"""
    existing = get_memory(user_id)
    updated = {**existing, **memory_update}
    supabase.table("memory").upsert({
        "user_id": user_id,
        "memory": updated,
        "updated_at": datetime.utcnow().isoformat()
    }).execute()

def get_settings(user_id: int):
    """Получает настройки пользователя"""
    result = supabase.table("settings").select("*").eq("user_id", user_id).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return {}

def update_settings(user_id: int, **fields):
    """Обновляет настройки пользователя"""
    supabase.table("settings").upsert({
        "user_id": user_id,
        **fields
    }).execute()
