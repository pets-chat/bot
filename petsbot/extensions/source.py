from telegram import Update
from telegram.ext import CallbackContext

async def handle_source_command(update: Update, context: CallbackContext):
    await update.message.reply_markdown_v2(
        "The source for this bot can be found [here](https://github.com/pets-chat/bot)\.",
        disable_web_page_preview=True,
    )
