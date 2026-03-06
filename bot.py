import asyncio
import re
import os

import json
import random
import time

from datetime import datetime, timedelta


from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.filters import Command



# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- DATA ----------------
DATA_FILE = "bot_data.json"


warnings_db = {}
reputation_db = {}
rep_cooldown = {}
message_tracker = {}

message_stats = {}

SPAM_LIMIT = 5
SPAM_TIME = 4

rules_text = """
📜 Правила чата:

1. Без спама
2. Без оскорблений
3. Без рекламы
4. Уважайте друг друга
"""

actions = {
    "пожать": "🤝 жмет руку",
    "обнять": "🤗 обнимает",
    "поцеловать": "💋 целует",
    "рука": "🫱 подает руку помощи",
    "ударить": "👊 бьет",
    "накричать": "😡 кричит на"
}

welcome_list = [
    "🔥 Добро пожаловать, {name}!",
    "👋 {name} залетел!",
    "🎉 Новый участник — {name}",
    "⚡ {name} теперь с нами!",
    "🌟 Встречаем {name}",
    "💎 {name} в чате!",

]

bye_list = [
    "😢 {name} ушел...",
    "👋 {name} покинул чат",
    "🚪 {name} вышел",
    "💨 {name} исчез",
]

# ---------------- HELPERS ----------------
def is_admin(message: types.Message):
    return message.from_user and message.from_user.id in [OWNER_ID]

def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str)
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    return {
        "s": timedelta(seconds=val),
        "m": timedelta(minutes=val),
        "h": timedelta(hours=val),
        "d": timedelta(days=val)
    }.get(unit)

def load_data():
    global warnings_db, reputation_db, message_stats
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                warnings_db, reputation_db, message_stats = {}, {}, {}
                return

            data = json.loads(content)

            warnings_db = {int(k): v for k, v in data.get("warnings", {}).items()}
            reputation_db = {int(k): v for k, v in data.get("reputation", {}).items()}
            message_stats = {int(k): v for k, v in data.get("messages", {}).items()}

    except FileNotFoundError:
        warnings_db, reputation_db, message_stats = {}, {}, {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "warnings": warnings_db,
            "reputation": reputation_db,
            "messages": message_stats
        }, f, ensure_ascii=False, indent=2)


# ---------------- MODERATION ----------------
@dp.message(Command(commands=["mute"]))
@dp.message(Command(commands=["unmute"]))
@dp.message(Command(commands=["warn"]))
@dp.message(Command(commands=["ban"]))
@dp.message(Command(commands=["permaban"]))
async def moderation(message: types.Message):

    if not is_admin(message) or not message.reply_to_message:
        return await message.answer("Ответь на сообщение пользователя.")

    user_id = message.reply_to_message.from_user.id
    cmd = message.text.split()[0].replace("/", "")


    if cmd == "mute":
        args = message.text.split()
        if len(args) < 2:
            return await message.answer("Пример: /mute 10m")

        delta = parse_time(args[1])

        if not delta:
            return await message.answer("Формат: 10s / 10m / 1h / 2d")

        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + delta
        )

        await message.answer(f"🔇 Мут на {args[1]}")

    elif cmd == "unmute":

        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(can_send_messages=True)
        )

        await message.answer("✅ Мут снят")

    elif cmd == "warn":

        warnings_db[user_id] = warnings_db.get(user_id, 0) + 1
        count = warnings_db[user_id]

        await message.answer(f"⚠ Варн. Всего: {count}")

        if count >= 3:

            await bot.restrict_chat_member(
                message.chat.id,
                user_id,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(minutes=30)
            )

            warnings_db[user_id] = 0

            await message.answer("🚫 3 варна → мут 30 минут")

        save_data()

    elif cmd == "ban":

        args = message.text.split()

        if len(args) < 2:
            return await message.answer("Пример: /ban 1d")

        delta = parse_time(args[1])

        if not delta:
            return await message.answer("Формат: 10m / 3h / 2d")

        await bot.ban_chat_member(
            message.chat.id,
            user_id,
            until_date=datetime.now() + delta
        )

        await message.answer(f"🚫 Бан на {args[1]}")

    elif cmd == "permaban":

        await bot.ban_chat_member(message.chat.id, user_id)

        await message.answer("⛔ Перманентный бан")


# ---------------- KICK RANGE ----------------
@dp.message(Command("kickrange"))
async def kickrange(message: types.Message):

    if not is_admin(message):
        return

    members = await bot.get_chat_administrators(message.chat.id)

    admins = [m.user.id for m in members]

    kicked = 0

    async for member in bot.get_chat_members(message.chat.id):

        if member.user.id not in admins and not member.user.is_bot:

            try:
                await bot.ban_chat_member(message.chat.id, member.user.id)
                await bot.unban_chat_member(message.chat.id, member.user.id)
                kicked += 1
            except:
                pass

    await message.answer(f"⚡ Кикнуто пользователей: {kicked}")


# ---------------- RULES / HELP ----------------
@dp.message(Command("rules"))
async def rules_cmd(message: types.Message):
    await message.answer(rules_text)


@dp.message(Command("help"))
async def help_cmd(message: types.Message):

    await message.answer(
        "📜 Команды бота\n\n"

        "Основное:\n"
        "/rules — правила\n"
        "/rep — твоя репутация\n"
        "/userinfo — информация о пользователе\n\n"

        "Топы:\n"
        "/toprep — топ репутации\n"
        "/toplist — топ активности\n"
        "/toplist day\n"
        "/toplist week\n"
        "/toplist month\n"
        "/toplist year\n\n"

        "Интерактив:\n"
        "обнять\n"
        "пожать\n"
        "поцеловать\n"
        "рука\n"
        "ударить\n"
        "накричать\n\n"

        "Модерация:\n"
        "/mute\n"
        "/unmute\n"
        "/warn\n"
        "/ban\n"
        "/permaban\n"
        "/kickrange"
    )


# ---------------- REP ----------------
@dp.message(Command("rep"))
async def rep(message: types.Message):

    user_id = message.from_user.id
    now = datetime.now()

    if user_id in rep_cooldown:
        if now - rep_cooldown[user_id] < timedelta(seconds=10):
            return await message.answer("⏳ КД 10 секунд.")

    rep_cooldown[user_id] = now

    rep = reputation_db.get(user_id, 0)

    await message.answer(
        f"⭐ Репутация {message.from_user.first_name}: {rep}"
    )


# ---------------- USER INFO ----------------
@dp.message(Command("userinfo"))
async def userinfo(message: types.Message):

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user

    uid = user.id

    rep = reputation_db.get(uid, 0)
    warns = warnings_db.get(uid, 0)

    messages = 0

    if uid in message_stats:
        messages = sum(message_stats[uid].values())

    text = (
        f"👤 {user.first_name}\n"
        f"🆔 ID: {uid}\n\n"
        f"⭐ Репутация: {rep}\n"
        f"⚠ Варны: {warns}\n"
        f"💬 Сообщений: {messages}"
    )

    await message.answer(text)


# ---------------- TOP REP ----------------
@dp.message(Command("toprep"))
async def toprep(message: types.Message):

    if not reputation_db:
        return await message.answer("Нет данных.")

    top = sorted(
        reputation_db.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    text = "🏆 Топ репутации\n\n"

    for i, (uid, rep) in enumerate(top, 1):

        try:
            user = await bot.get_chat(uid)
            name = user.first_name
        except:
            name = str(uid)

        text += f"{i}. {name} — {rep}\n"

    await message.answer(text)


# ---------------- TOP LIST ----------------
@dp.message(Command("toplist"))
async def toplist(message: types.Message):

    args = message.text.split()
    period = "all"

    if len(args) > 1:
        period = args[1]

    now = datetime.now()

    stats = {}

    for uid, days in message_stats.items():

        total = 0

        for day, count in days.items():

            day_dt = datetime.strptime(day, "%Y-%m-%d")

            if period == "day":
                if day_dt.date() == now.date():
                    total += count

            elif period == "week":
                if (now - day_dt).days <= 7:
                    total += count

            elif period == "month":
                if (now - day_dt).days <= 30:
                    total += count

            elif period == "year":
                if (now - day_dt).days <= 365:
                    total += count

            else:
                total += count

        stats[uid] = total

    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]

    text = "🏆 Топ активности\n\n"

    for i, (uid, msgs) in enumerate(top, 1):

        try:
            user = await bot.get_chat(uid)
            name = user.first_name
        except:
            name = str(uid)

        text += f"{i}. {name} — {msgs}\n"

    await message.answer(text)


# ---------------- UNIVERSAL HANDLER ----------------
@dp.message()
async def universal(message: types.Message):

    user_id = message.from_user.id
    text = message.text or ""

    # --- MESSAGE TRACKER ---
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in message_stats:
        message_stats[user_id] = {}

    if today not in message_stats[user_id]:
        message_stats[user_id][today] = 0

    message_stats[user_id][today] += 1

    # --- ANTI-SPAM ---
    if user_id != OWNER_ID:

        now = time.time()

        message_tracker[user_id] = [
            t for t in message_tracker.get(user_id, [])
            if now - t < SPAM_TIME
        ]

        message_tracker[user_id].append(now)

        if len(message_tracker[user_id]) >= SPAM_LIMIT:

            await bot.restrict_chat_member(
                message.chat.id,
                user_id,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(minutes=5)
            )

            message_tracker[user_id].clear()

            return await message.answer("🚫 Спам → мут 5 минут")

    # --- REP CHANGE ---
    if message.reply_to_message:

        target_id = message.reply_to_message.from_user.id

        if target_id != user_id:

            if text == "+":
                reputation_db[target_id] = reputation_db.get(target_id, 0) + 1
                await message.answer(
                    f"👍 +1 реп {message.reply_to_message.from_user.first_name}"
                )

            elif text == "-":
                reputation_db[target_id] = reputation_db.get(target_id, 0) - 1
                await message.answer(
                    f"👎 -1 реп {message.reply_to_message.from_user.first_name}"
                )

            elif re.match(r"^[+-]\d+$", text) and is_admin(message):

                val = int(text)

                reputation_db[target_id] = reputation_db.get(target_id, 0) + val

                await message.answer(
                    f"⭐ Репутация {message.reply_to_message.from_user.first_name} изменена на {val}"
                )

            save_data()

            # --- INTERACTIVE ---
            if text.lower() in actions:

                await message.answer(
                    f"{message.from_user.first_name} {actions[text.lower()]} {message.reply_to_message.from_user.first_name}"
                )

    # --- WELCOME / BYE ---
    if message.new_chat_members:

        for u in message.new_chat_members:
            await message.answer(
                f"{random.choice(welcome_list).format(name=u.first_name)}{rules_text}"
            )

    if message.left_chat_member:

        u = message.left_chat_member

        await message.answer(
            f"{random.choice(bye_list).format(name=u.first_name)}"
        )


# ---------------- START ----------------
async def main():

    load_data()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())