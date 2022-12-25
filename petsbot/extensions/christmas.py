import base64
import json
import random
import uuid
from . import redis_connection_pool
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

PRESENTS = ["Steam Deck", "MacBook", "Nintendo Switch", "Chocolate", "Slippers", "Train Set", "Pokémon Game", "Coal", "Money", "Android Phone", "iPhone", "Wheel & Pedals", "Controller", "Mechanical Keyboard", "Monitor", "Yubikey", "Cheese"]
NAMES = ["Melissa", "Liam", "Ari", "Alexia", "Zack", "Astrid", "Aurora", "Marissa", "Daniel", "Brandon", "Ryan", "Justin", "Ashley", "Gabrielle", "Stefan", "Paul", "Dave"]
COMMON = ["glass of milk", "carrot", "cookie", "candy cane", "some gingerbread men", "some fudge", "some tinsel", "some holly", "wreath", "some ribbon", "some sleigh bells", "wrapping paper", "partrich"]
UNCOMMON = ["christmas jumper", "some stocking stuffers", "christmas stocking", "gingerbread house", "minature snowman", "santa hat", "humbug hat", "some mistletoe", "yule log", "three french hens"]
RARE = ["minature sleigh", "roast turkey", "ornament", "snowglobe", "glass of hot chocolate", "some christmas pudding", "two turtle doves", "four calling birds", "seven swans"]
EPIC = ["some gold", "some frankincense", "some myrrh", "elf on the shelf", "five golden rings", "six geese"]

async def handle_present_command(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool, decode_responses=True)
    # We only want some people to activate the present command
    if update.message.from_user.username == "estrofem":
        await present_message(update, context, redis, True)
        await update.message.delete()

async def handle_leaderboard_command(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool, decode_responses=True)
    values = redis.hgetall("xmas.leaderboard")
    leaderboard = {}
    for key, val in sorted(values.items(), key=lambda l: int(l[1]), reverse=True):
        member = await update.message.chat.get_member(int(key))
        leaderboard[escape_markdown(member.user.first_name, version=2)] = int(val)

    users = list(leaderboard.keys())
    values = list(leaderboard.values())
    output = ""
    for x in range(0, min(len(leaderboard), 8)):
        output += f"*{x + 1}\.* {users[x]} \({values[x]}\)\n"
    await update.message.chat.send_message(
        f"*These players have the most items so far:*\n\n{'Nobody is yet on the leaderboard' if len(output) == 0 else output}",
        parse_mode="MarkdownV2"
    )

async def handle_present_callback(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool, decode_responses=True)

    data = json.loads(update.callback_query.data)
    from_user = update.callback_query.from_user.id
    if not redis.hexists("xmas.presents_map", update.callback_query.message.id):
        await update.callback_query.answer("Sorry, can't find this message in my database.")
        return

    saved_data = json.loads(redis.hget("xmas.presents_map", update.callback_query.message.id))
    if saved_data["hash"] != data["data"]:
        await update.callback_query.message.edit_text(
            f"*{escape_markdown(update.callback_query.from_user.first_name, version=2)}* scared *{saved_data['name']}* off\! They asked for: *{saved_data['want']}*, however they were given something else\!",
            parse_mode="MarkdownV2",
            reply_markup=None
        )
        redis.hdel("xmas.presents_map", update.callback_query.message.id)
        return

    # Item grade?
    rarity = random.choices(['c', 'u', 'r', 'e'], [600, 200, 125, 75])
    if rarity[0] == 'e':
        return_item = random.choice(EPIC) + ' (Epic)'
    elif rarity[0] == 'r':
        return_item = random.choice(RARE) + ' (Rare)'
    elif rarity[0] == 'u':
        return_item = random.choice(UNCOMMON) + ' (Uncommon)'
    else:
        return_item = random.choice(COMMON) + ' (Common)'

    item_response = redis.hget(f"xmas.items.{from_user}", return_item)
    has_item = item_response is not None and int(item_response) > 0
    redis.hset(f"xmas.items.{from_user}", return_item, 1)
    items = redis.hgetall(f"xmas.items.{from_user}")

    redis.hset("xmas.leaderboard", from_user, sum(map(lambda i: int(i), items.values())))
    has_item_output = f"*{escape_markdown(update.callback_query.from_user.first_name, version=2)}* does not already have this item, so gets a point on the leaderboard\."
    if has_item:
        has_item_output = f"Sadly, *{escape_markdown(update.callback_query.from_user.first_name, version=2)}* already has this item\."

    await update.callback_query.message.edit_text(
        f"*{escape_markdown(update.callback_query.from_user.first_name, version=2)}* gave *{saved_data['name']}* what they wanted which was: *{saved_data['want']}*\.\n\n*{saved_data['name']}*, in thanks, gives back {'some' if return_item.startswith('some ') else 'a'} *{escape_markdown(return_item.replace('some ', ''), version=2)}* in return\! {has_item_output}",
        parse_mode="MarkdownV2",
        reply_markup=None
    )
    redis.hdel("xmas.presents_map", update.callback_query.message.id)

async def handle_present_message(update: Update, context: CallbackContext):
    redis = Redis(connection_pool=redis_connection_pool, decode_responses=True)
    last_user_id = int(redis.get("last_from_id"))
    if last_user_id != update.message.from_user.id or last_user_id is None:
        await present_message(update, context, redis, False)

async def present_message(update: Update, context: CallbackContext, redis: Redis, ignore_probability_check: bool):
    redis.set("last_from_id", update.message.from_user.id)
    number = random.randrange(1, 1000)
    if number <= 20 or ignore_probability_check:
        output_receiver_name = random.choice(NAMES)
        output_receiver_want = random.choice(PRESENTS)
        output_receiver_hash = hash(output_receiver_want)
        presents_without_want = [x for x in PRESENTS if x != output_receiver_want]
        choices = random.sample(presents_without_want, 3)
        choices.append(output_receiver_want)
        random.shuffle(choices)
        ch_data = list(map(lambda c: hash(c) if c != output_receiver_want else output_receiver_hash, choices))
        keyboard = [
            [
                InlineKeyboardButton(choices[0], callback_data=json.dumps({'type': 'xmas.present', 'data': ch_data[0]})),
                InlineKeyboardButton(choices[1], callback_data=json.dumps({'type': 'xmas.present', 'data': ch_data[1]}))
            ], [
                InlineKeyboardButton(choices[2], callback_data=json.dumps({'type': 'xmas.present', 'data': ch_data[2]})),
                InlineKeyboardButton(choices[3], callback_data=json.dumps({'type': 'xmas.present', 'data': ch_data[3]}))
            ]
        ]
        message = await update.message.chat.send_message(
            f"*New Present Drop\!*\n\n*{output_receiver_name}* would like to receive: *{output_receiver_want}*\!",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        redis.hset("xmas.presents_map", message.id, json.dumps({"hash": output_receiver_hash, "want": output_receiver_want, "name": output_receiver_name}))
