import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import (
    Application, MessageHandler, filters, ContextTypes, CommandHandler
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Sticker
from ai_core import handle_message, get_ai_response, fix_gender, send_prompt_direct
from agent_control import toggle_agent, agent_router
from prompt_welcome import build_welcome_prompt
from memory import ensure_user
from sticker_logic import update_dynamic_stickers  # ✅ правильное обновление

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
video_path = "media/IMG_5029.mp4"

ALLOWED_CHAT_ID = -1002704833487
GENERAL_THREAD_ID = None

# 📦 Лог стикеров
async def log_sticker_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker: Sticker = update.message.sticker
    print("🧾 Получен стикер:")
    print(f"file_id: {sticker.file_id}")
    print(f"file_unique_id: {sticker.file_unique_id}")
    print(f"emoji: {sticker.emoji}")
    print(f"set_name: {sticker.set_name}")
    print(f"width: {sticker.width}, height: {sticker.height}")
    print(f"is_animated: {sticker.is_animated}, is_video: {sticker.is_video}")

# 📍 Проверка — адресовано ли сообщение боту
def is_addressed_to_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.message
    if not message or not message.text:
        return False

    bot_username = context.bot.username.lower()

    if f"@{bot_username}" in message.text.lower():
        return True

    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.username.lower() == bot_username:
            return True

    return False

# 💬 Обработчик только если сообщение адресовано боту
async def selective_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_addressed_to_bot(update, context):
        await handle_message(update, context)

# 🎉 Приветствие новых участников
async def welcome_on_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.new_chat_members:
        return

    if message.chat_id != ALLOWED_CHAT_ID:
        return

    thread_id = message.message_thread_id
    print(f"[🧪 DEBUG] New member in thread: {thread_id}")

    for user in message.new_chat_members:
        ensure_user(user.id, user.first_name, user.username)
        username = user.username or f"id{user.id}"

        if thread_id == 1009:
            language = "ru"
        elif thread_id == 1011:
            language = "en"
        elif thread_id is None:
            language = "en"
        else:
            language = "ru"

        prompt = build_welcome_prompt(username, language=language)
        result = await send_prompt_direct(user.id, prompt, username=username, language=language)

        reply = result.get("reply")
        if not reply:
            return
        if language == "ru":
            reply = fix_gender(reply)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⛩️ Chat rules", url="https://t.me/c/2704833487/1279/1281")]
        ])

        try:
            with open(video_path, "rb") as video_file:
                await context.bot.send_video(
                    chat_id=ALLOWED_CHAT_ID,
                    message_thread_id=thread_id,
                    video=video_file,
                    caption=reply,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
        except Exception as e:
            print("❌ Ошибка при отправке приветственного видео:", e)

# 🔁 Циклическое обновление стикеров каждые 5 минут
async def sticker_updater_loop(bot):
    while True:
        await update_dynamic_stickers(bot)
        await asyncio.sleep(300)

# 🚀 Основной запуск
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    asyncio.create_task(sticker_updater_loop(app.bot))  # 🔁 Автообновление
    await update_dynamic_stickers(app.bot)              # ⚡ Первичный вызов
    print("[🚀] Стикеры обновлены при запуске")

    app.add_handler(CommandHandler("agent", toggle_agent))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_on_new_chat_members))
    app.add_handler(MessageHandler(filters.Sticker.ALL, log_sticker_info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.run_polling()

if __name__ == '__main__':
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(main())
    else:
        loop.run_until_complete(main())
