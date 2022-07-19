from . import redisConnPool
from redis import Redis
from telegram import MessageEntity, Update
from telegram.ext import CallbackContext
from urllib.parse import urlsplit

def fixTwitterUrl(url: str) -> (bool, str):
    parts = urlsplit(url)
    if (parts.netloc == "twitter.com"):
        return (True, "https://vxtwitter.com/%s" % parts.path.strip('/'))
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
        await update.message.reply_markdown_v2("[TwitFixed\!](%s)" % twfixUrl[1] if twfixUrl[1] else "Not a valid twitter link\.")

async def handleTwfixMessage(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redisConnPool)

    isOptedOut = redis.hget("twfix_opt_out", update.message.from_user.id)
    if isOptedOut is None:
        for entity in update.message.entities:
            if entity.type == MessageEntity.TEXT_LINK:
                twfixUrl = twfixUrl = fixTwitterUrl(context.args[0])
                if (twfixUrl[1]):
                    await update.message.reply_markdown_v2("[TwitFixed\!](%s)" % twfixUrl[1])
            elif entity.type == MessageEntity.URL:
                for part in update.message.text.split(" "):
                    twfixUrl = fixTwitterUrl(part)
                    if (fixTwitterUrl(part)[0]):
                        await update.message.reply_markdown_v2("[TwitFixed\!](%s)" % twfixUrl[1])