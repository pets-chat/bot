import asyncio
import redis
import json
import os
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler

from extensions.twfix import handle_twfix_command, handle_twfix_dismiss, handle_twfix_message
from extensions.source import handle_source_command

def main() -> None:
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("twfix", handle_twfix_command))
    app.add_handler(CommandHandler("source", handle_source_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_twfix_message))

    app.add_handler(CallbackQueryHandler(handle_twfix_dismiss, lambda d: json.loads(d)["type"] == "twfix.dismiss"))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()