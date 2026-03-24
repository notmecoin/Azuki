from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_or_create_user(user_id, first_name=None, username=None):
    existing = supabase.table("users").select("*").eq("id", user_id).execute()
    if not existing.data:
        supabase.table("users").insert({
            "id": user_id,
            "first_name": first_name,
            "username": username
        }).execute()

def save_message(user_id, role, content):
    supabase.table("messages").insert({
        "user_id": user_id,
        "role": role,
        "content": content
    }).execute()

def get_last_messages(user_id, limit=5):
    result = supabase.table("messages").select("role, content")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(limit).execute()
    return result.data[::-1]

def get_memory(user_id):
    result = supabase.table("memory").select("memory").eq("user_id", user_id).single().execute()
    return result.data["memory"] if result.data else {}

def update_memory(user_id, memory: dict):
    from datetime import datetime
    supabase.table("memory").upsert({
        "user_id": user_id,
        "memory": memory,
        "updated_at": datetime.utcnow().isoformat()
    }).execute()

def get_settings(user_id):
    result = supabase.table("settings").select("*").eq("user_id", user_id).single().execute()
    return result.data or {}

def update_settings(user_id, **fields):
    supabase.table("settings").upsert({
        "user_id": user_id,
        **fields
    }).execute()
