import asyncio
import re
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = -1001234567890  # <-- ВСТАВЬ ID ГРУППЫ

bot = Bot(token=TOKEN)
dp = Dispatcher()

warnings_db = {}
reputation_db = {}
rep_cooldown = {}

rules_text = """
📜 Правила чата:

1. Без спама
2. Без оскорблений
3. Без рекламы
4. Уважайте друг друга
"""


# ---------------- ДОСТУП ----------------
def is_admin(message: Message):
    user_id = None

    if message.from_user:
        user_id = message.from_user.id

    if message.sender_chat:
        user_id = message.sender_chat.id

    return user_id in [OWNER_ID, GROUP_ID]


# ---------------- ПАРСЕР ВРЕМЕНИ ----------------
def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str)
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

    return None


# ---------------- МОДЕРАЦИЯ ----------------
@dp.message(Command("mute", "unmute", "warn", "ban", "permaban"))
async def moderation_commands(message: Message):

    if not is_admin(message):
        return

    cmd = message.text.split()[0].replace("/", "")

    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя.")
        return

    user_id = message.reply_to_message.from_user.id

    # MUTE
    if cmd == "mute":
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Пример: /mute 20m")
            return

        delta = parse_time(args[1])
        if not delta:
            await message.answer("Формат: 10s / 20m / 3h / 2d")
            return

        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + delta
        )

        await message.answer(f"🔇 Мут на {args[1]}")

    # UNMUTE
    elif cmd == "unmute":
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await message.answer("✅ Мут снят")

    # WARN
    elif cmd == "warn":
        warnings_db[user_id] = warnings_db.get(user_id, 0) + 1
        count = warnings_db[user_id]

        await message.answer(f"⚠ Варн. Всего: {count}")

        if count >= 3:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(minutes=30)
            )
            warnings_db[user_id] = 0
            await message.answer("🚫 3 варна → мут 30 минут")

    # BAN
    elif cmd == "ban":
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Пример: /ban 3d")
            return

        delta = parse_time(args[1])
        if not delta:
            await message.answer("Формат: 10m / 3h / 2d")
            return

        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            until_date=datetime.now() + delta
        )
        await message.answer(f"🚫 Бан на {args[1]}")

    # PERMABAN
    elif cmd == "permaban":
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=user_id
        )
        await message.answer("⛔ Перманентный бан")


# ---------------- RULES ----------------
@dp.message(Command("rules"))
async def rules(message: Message):
    await message.answer(rules_text)


# ---------------- REP ----------------
@dp.message(Command("rep"))
async def check_rep(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    if user_id in rep_cooldown:
        if now - rep_cooldown[user_id] < timedelta(minutes=10):
            await message.answer("⏳ КД 10 минут.")
            return

    rep_cooldown[user_id] = now
    rep = reputation_db.get(user_id, 0)

    await message.answer(f"⭐ Твоя репутация: {rep}")


# ---------------- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ----------------
@dp.message()
async def universal_handler(message: Message):

    # приветствие
    if message.new_chat_members:
        for user in message.new_chat_members:
            await message.answer(f"👋 Добро пожаловать, {user.first_name}!")

    if message.left_chat_member:
        user = message.left_chat_member
        await message.answer(f"😢 {user.first_name} покинул чат.")

    # если есть reply
    if message.reply_to_message:

        target_id = message.reply_to_message.from_user.id

        # --- РЕПУТАЦИЯ ---
        if message.text:

            # Админ может выдавать любое число
            match = re.match(r"^([+-])(\d+)$", message.text)
            if match and is_admin(message):
                sign, number = match.groups()
                number = int(number)

                if sign == "+":
                    reputation_db[target_id] = reputation_db.get(target_id, 0) + number
                else:
                    reputation_db[target_id] = reputation_db.get(target_id, 0) - number

                await message.answer(f"⭐ Репутация изменена на {number}")
                return

            # Обычные пользователи только + или -
            if message.text == "+":
                reputation_db[target_id] = reputation_db.get(target_id, 0) + 1
                await message.answer("👍 +1 репутация")

            elif message.text == "-":
                reputation_db[target_id] = reputation_db.get(target_id, 0) - 1
                await message.answer("👎 -1 репутация")

        # --- ИНТЕРАКТИВ ---
        actions = {
            "пожать": "🤝 жмет руку",
            "обнять": "🤗 обнимает",
            "поцеловать": "💋 целует",
            "рука": "🫱 подает руку помощи",
            "ударить": "👊 бьет",
            "накричать": "😡 кричит на"
        }

        if message.text and message.text.lower() in actions:
            sender = message.from_user.first_name
            target = message.reply_to_message.from_user.first_name
            await message.answer(f"{sender} {actions[message.text.lower()]} {target}")


# ---------------- START ----------------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
