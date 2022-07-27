import json

import requests
from . import redis_connection_pool
from bs4 import BeautifulSoup
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update
from telegram.ext import CallbackContext
from urllib.parse import urlsplit

session = requests.Session()

def twfix_dismiss_button(only_allow_from: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="Dismiss",
            callback_data=json.dumps({ 'type': 'twfix.dismiss', 'allow_from': only_allow_from })
        )
    )

def fix_twitter_url(url: str) -> str | None:
    parts = urlsplit(url)

    if parts.netloc != "twitter.com":
        return None

    soup = BeautifulSoup(session.get(url, headers={"User-Agent": "Googlebot"}).text, "html.parser")

    # Case 1: Multiple images
    images = {x["content"] for x in soup.select("meta[itemProp='contentUrl']")}
    if len(images) > 1:
        return f"https://c.vxtwitter.com{parts.path}"

    # Case 2: Video
    image = soup.select_one("meta[property='og:image']")
    if image and "pbs.twimg.com/ext_tw_video_thumb" in image["content"]:
        return f"https://vxtwitter.com{parts.path}"

    return None

async def handle_twfix_command(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool)

    if context.args[0] == "opt-out":
        redis.hset("twfix_opt_out", update.message.from_user.id, 1)
        await update.message.reply_text("Okay, I won't automatically fix twitter links you send to this group.")
    elif context.args[0] == "opt-in":
        redis.hdel("twfix_opt_out", update.message.from_user.id, 0)
        await update.message.reply_text("Okay, I will now automatically fix twitter links you send to this group.")
    else:
        twfix_url = fix_twitter_url(context.args[0])
        await update.message.reply_markdown_v2(f"[TwitFixed\!]({twfix_url})" if twfix_url is not None else "Not a valid twitter link\.", reply_markup=twfix_dismiss_button(update.message.from_user.id))

async def handle_twfix_dismiss(update: Update, context: CallbackContext):
    data = json.loads(update.callback_query.data)
    if data["allow_from"] != update.callback_query.from_user.id:
        await update.callback_query.answer(text="You can't do that, only the OP can do that.")
        return
    await update.callback_query.delete_message()
    await update.callback_query.answer(text="Okay, I have now deleted the message.")

async def handle_twfix_message(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool)

    opted_out = redis.hget("twfix_opt_out", update.message.from_user.id)
    if opted_out is None:
        for entity in update.message.entities:
            if entity.type == MessageEntity.TEXT_LINK:
                twfix_url = fix_twitter_url(context.args[0])
                if (twfix_url is not None):
                    await update.message.reply_markdown_v2(f"[TwitFixed\!]({twfix_url})", reply_markup=twfix_dismiss_button(update.message.from_user.id))
            elif entity.type == MessageEntity.URL:
                for part in update.message.text.split(" "):
                    twfix_url = fix_twitter_url(part)
                    if (twfix_url is not None):
                        await update.message.reply_markdown_v2(f"[TwitFixed\!]({twfix_url})", reply_markup=twfix_dismiss_button(update.message.from_user.id))
