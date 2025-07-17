import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise SystemExit("BOT_TOKEN not configured")
TOKEN = TOKEN.strip()

logging.basicConfig(level=logging.DEBUG)

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    print("START received from", update.effective_user.id)
    await update.message.reply_text("Привет! Бот работает.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

