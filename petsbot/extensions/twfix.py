import json

import requests
from . import redisConnPool
from bs4 import BeautifulSoup
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update
from telegram.ext import CallbackContext
from urllib.parse import urlsplit

session = requests.Session()

def dismissButton(onlyAllowFrom: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="Dismiss",
            callback_data=json.dumps({ 'type': 'twfix.dismiss', 'allow_from': onlyAllowFrom })
        )
    )

def fixTwitterUrl(url: str) -> (bool, str):
    parts = urlsplit(url)

    if parts.netloc != "twitter.com":
        return (False, "")

    soup = BeautifulSoup(session.get(url, headers={"User-Agent": "Googlebot"}).text, "html.parser")

    # Case 1: Multiple images
    images = {x["content"] for x in soup.select("meta[itemProp='contentUrl']")}
    if len(images) > 1:
        return (True, "https://c.vxtwitter.com/%s" % parts.path.strip('/'))

    # Case 2: Video
    image = soup.select_one("meta[property='og:image']")
    if image and "pbs.twimg.com/ext_tw_video_thumb" in image["content"]:
        return (True, "https://vxtwitter.com/%s" % parts.path.strip('/'))

    # Case 3: Query string
    if parts.query:
        return (True, "https://twitter.com/%s" % parts.path.strip('/'))

    return (False, "")

async def handleTwfixCommand(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redisConnPool)

    if context.args[0] == "opt-out":
        redis.hset("twfix_opt_out", update.message.from_user.id, 1)
        await update.message.reply_text("Okay, I won't automatically fix twitter links you send to this group.")
    elif context.args[0] == "opt-in":
        redis.hdel("twfix_opt_out", update.message.from_user.id, 0)
        await update.message.reply_text("Okay, I will now automatically fix twitter links you send to this group.")
    else:
        twfixUrl = fixTwitterUrl(context.args[0])
        await update.message.reply_markdown_v2("[TwitFixed\!](%s)" % twfixUrl[1] if twfixUrl[1] else "Not a valid twitter link\.", reply_markup=dismissButton(update.message.from_user.id))

async def handleTwfixDismiss(update: Update, context: CallbackContext):
    data = json.loads(update.callback_query.data)
    if data["allow_from"] != update.callback_query.from_user.id:
        await update.callback_query.answer(text="You can't do that, only the OP can do that.")
        return
    await update.callback_query.delete_message()
    await update.callback_query.answer(text="Okay, I have now deleted the message.")

async def handleTwfixMessage(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redisConnPool)

    isOptedOut = redis.hget("twfix_opt_out", update.message.from_user.id)
    if isOptedOut is None:
        for entity in update.message.entities:
            if entity.type == MessageEntity.TEXT_LINK:
                twfixUrl = twfixUrl = fixTwitterUrl(context.args[0])
                if (twfixUrl[1]):
                    await update.message.reply_markdown_v2("[TwitFixed\!](%s)" % twfixUrl[1], reply_markup=dismissButton(update.message.from_user.id))
            elif entity.type == MessageEntity.URL:
                for part in update.message.text.split(" "):
                    twfixUrl = fixTwitterUrl(part)
                    if (fixTwitterUrl(part)[0]):
                        await update.message.reply_markdown_v2("[TwitFixed\!](%s)" % twfixUrl[1], reply_markup=dismissButton(update.message.from_user.id))
