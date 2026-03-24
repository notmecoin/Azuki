from telegram import Update
from telegram.ext import ContextTypes
from ai_core import handle_message  # заменили core_handler на ai_core

agent_enabled = False
message_queue = []
MY_USER_ID = 5022015335


async def toggle_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global agent_enabled, message_queue

    if update.message.from_user.id != MY_USER_ID:
        await update.message.reply_text("У тебя нет прав для управления ботом.")
        return

    if context.args and context.args[0].lower() == "on":
        agent_enabled = True
        await update.message.reply_text("Агент включен. Я буду отвечать на все сообщения.")
        for msg in message_queue:
            await handle_message(msg, context)
        message_queue.clear()

    elif context.args and context.args[0].lower() == "off":
        agent_enabled = False
        await update.message.reply_text("Агент выключен. Я больше не отвечаю на сообщения.")
    else:
        await update.message.reply_text("Используй команду /agent on или /agent off.")


async def agent_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global agent_enabled

    if not update.message or not update.message.text:
        return

    if not agent_enabled:
        print(f"🔴 Агент выключен. Сообщение от @{update.message.from_user.username} сохранено в очередь.")
        message_queue.append(update)
        return

    await handle_message(update, context)
