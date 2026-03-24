import os
import asyncio
import nest_asyncio  # ✅ добавляем
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8150027485:AAGmhBZVo8mRXA6gXsE7S5goTgn_zTmdsCw"
MY_USER_ID = 5022015335  # Твой Telegram ID

async def handle_important_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    if message.from_user.id != MY_USER_ID:
        return

    if "++" in message.text.lower():
        chat_id = message.chat_id
        thread_id = message.message_thread_id

        print("📌 Получено важное сообщение!")
        print(f"📣 chat_id: {chat_id}")
        print(f"🧵 message_thread_id: {thread_id}")
        print(f"👥 chat title: {update.effective_chat.title}")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.ALL, handle_important_message))
    print("🤖 Бот запущен. Напиши 'важно реагировать' в нужной теме.")
    await app.run_polling()

# 👇 фиксим loop для Windows
if __name__ == "__main__":
    try:
        nest_asyncio.apply()
    except:
        pass

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(main())
    else:
        loop.run_until_complete(main())
