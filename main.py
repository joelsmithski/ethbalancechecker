import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# This is the /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working!")

# Entry point
async def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot is polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
