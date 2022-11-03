import json
import uuid

import requests
from . import redis_connection_pool
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update
from telegram.ext import CallbackContext
from urllib.parse import urlsplit

session = requests.Session()

class TwitterAPIError(Exception):
    pass

def twfix_dismiss_button(only_allow_from: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="Dismiss",
            callback_data=json.dumps({ 'type': 'twfix.dismiss', 'allow_from': only_allow_from })
        )
    )

def fix_twitter_url(url: str, force: bool = False) -> str | None:
    parts = urlsplit(url)

    if parts.netloc != "twitter.com":
        return None

    tweet_id = parts.path.rstrip("/").split("/")[-1]
    csrf_token = uuid.uuid4().hex

    r = session.get(
        url=f"https://api.twitter.com/1.1/statuses/show/{tweet_id}.json",
        params={
            "tweet_mode": "extended",
        },
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "x-csrf-token": csrf_token
        },
        cookies={
            "ct0": csrf_token
        }
    )
    try:
        tweet = r.json()
    except json.JSONDecodeError:
        r.raise_for_status()
    if "errors" in tweet:
        raise TwitterAPIError(tweet["errors"])

    # Case 1: Multiple images
    if len(tweet.get("entities", {}).get("media", [])) > 1:
        return f"https://c.vxtwitter.com{parts.path}"

    # Case 2: Video
    if tweet.get("extended_entities", {}).get("media") and tweet["extended_entities"]["media"][0]["type"] == "video":
        return f"https://vxtwitter.com{parts.path}"

    # Case 3: Manual fix requested
    if force:
        return f"https://vxtwitter.com{parts.path}"

    return None

async def handle_twfix_command(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool)

    if context.args and context.args[0] == "opt-out":
        redis.hset("twfix_opt_out", update.message.from_user.id, 1)
        await update.message.reply_text("Okay, I won't automatically fix twitter links you send to this group.")
    elif context.args and context.args[0] == "opt-in":
        redis.hdel("twfix_opt_out", update.message.from_user.id, 0)
        await update.message.reply_text("Okay, I will now automatically fix twitter links you send to this group.")
    else:
        if context.args:
            url = context.args[0]
        elif update.message.reply_to_message:
            url = update.message.reply_to_message.text
        twfix_url = fix_twitter_url(url, force=True)
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
