from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import CallbackContext
from telegram.error import BadRequest

async def handle_pronouns_command(update: Update, context: CallbackContext):
    if "/" not in context.args[0]:
        await update.message.reply_text("Please put at least one '/' in your pronouns.")
        return

    try:
        user = await update.message.chat.get_member(update.message.from_user.id)
        if user.status != ChatMemberStatus.ADMINISTRATOR and user.status != ChatMemberStatus.OWNER:
            await update.message.chat.promote_member(update.message.from_user.id, can_manage_video_chats=True)

        await update.message.chat.set_administrator_custom_title(update.message.from_user.id, context.args[0])
    except BadRequest as error:
        await update.message.reply_text(f"Error: BadRequest: {error}")
    else:
        await update.message.reply_text("Okay, I have set your admin title to these pronouns.")
