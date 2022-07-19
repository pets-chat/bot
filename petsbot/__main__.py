import asyncio
import redis
import os
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler

from extensions.twfix import handleTwfixCommand, handleTwfixMessage
from extensions.source import handleSourceCommand

def main() -> None:
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("twfix", handleTwfixCommand))
    app.add_handler(CommandHandler("source", handleSourceCommand))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handleTwfixMessage))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()