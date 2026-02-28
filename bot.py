import asyncio
import os
import re
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

warnings_db = {}
reputation_db = {}
rep_view_cooldown = {}
rep_change_cooldown = {}
message_tracker = defaultdict(list)

SPAM_LIMIT = 5
SPAM_TIME = 4

bad_words = {
    "дурак": "солнышко",
    "идиот": "гений",
    "лох": "чемпион",
    "тупой": "умничка"
}



def is_admin(message: Message):
    return message.from_user.id == OWNER_ID and message.chat.id == GROUP_ID

# ================= ADMIN COMMANDS =================

@dp.message(Command("mute"))
async def mute_cmd(message: Message):
    if not is_admin(message):
        return
    if not message.reply_to_message:
        return await message.answer("Ответь на сообщение.")
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Пример: /mute 10m")

    match = re.match(r"(\d+)([mh])", args[1])
    if not match:
        return await message.answer("Формат: 10m / 2h")

    value, unit = match.groups()
    value = int(value)

    delta = timedelta(minutes=value) if unit == "m" else timedelta(hours=value)
    until = datetime.now() + delta

    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await message.answer("🔇 Мут выдан")

@dp.message(Command("unmute"))
async def unmute_cmd(message: Message):
    if not is_admin(message):
        return
    if not message.reply_to_message:
        return
    
    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        ChatPermissions(can_send_messages=True)
    )
    await message.answer("✅ Мут снят")

@dp.message(Command("ban"))
async def ban_cmd(message: Message):
    if not is_admin(message):
        return
    if not message.reply_to_message:
        return


    user = message.reply_to_message.from_user
    args = message.text.split()

    if len(args) < 2:
        return await message.answer("Пример: /ban 1d")

    match = re.match(r"(\d+)([d])", args[1])
    if not match:
        return

    value = int(match.group(1))
    until = datetime.now() + timedelta(days=value)

    await bot.ban_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        until_date=until
    )
    await message.answer("🚫 Бан выдан")

@dp.message(Command("permaban"))
async def permaban_cmd(message: Message):
    if not is_admin(message):
        return
    if not message.reply_to_message:
        return

    await bot.ban_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id
    )
    await message.answer("💀 Перманентный бан")

# ================= ONE MAIN MESSAGE HANDLER =================

@dp.message()
async def main_handler(message: Message):

    if not message.text:
        return

    text = message.text.strip()

    # ==== АНТИСПАМ ====
    if message.from_user.id != OWNER_ID:
        now = time.time()
        user_id = message.from_user.id

        message_tracker[user_id] = [
            t for t in message_tracker[user_id] if now - t < SPAM_TIME
        ]
        message_tracker[user_id].append(now)

        if len(message_tracker[user_id]) >= SPAM_LIMIT:
            until = datetime.now() + timedelta(minutes=5)
            await bot.restrict_chat_member(
                message.chat.id,
                user_id,
                ChatPermissions(can_send_messages=False),
                until_date=until
            )
            message_tracker[user_id].clear()
            return await message.answer("🚫 Спам → мут 5 минут")

    # ==== ФИЛЬТР МАТА ====
    if message.from_user.id != OWNER_ID:
        replaced = text
        for bad, good in bad_words.items():
            pattern = re.compile(bad, re.IGNORECASE)
            replaced = pattern.sub(good, replaced)

        if replaced != text:
            await message.delete()
            return await message.answer(
                f"✏ {message.from_user.full_name} имел в виду:\n{replaced}"
            )

    # ==== РЕПУТАЦИЯ ИЗМЕНЕНИЕ ====
    if message.reply_to_message and re.fullmatch(r"[+-]\d+", text):
        target = message.reply_to_message.from_user

        if target.id == message.from_user.id:
            return await message.answer("❌ Нельзя себе.")

        value = int(text)

        if message.from_user.id != OWNER_ID:
            now = time.time()
            last = rep_change_cooldown.get(message.from_user.id, 0)
            if now - last < 10:
                return await message.answer("⏳ КД 10 секунд.")
            rep_change_cooldown[message.from_user.id] = now

            if abs(value) > 1:
                return await message.answer("Можно только +1/-1.")

        reputation_db[target.id] = reputation_db.get(target.id, 0) + value
        return await message.answer(
            f"⭐ Репутация {target.full_name}: {reputation_db[target.id]}"
        )

    # ==== ИНТЕРАКТИВ ====
    actions = {
        "пожать": "🤝 {a} жмет руку {b}",
        "обнять": "🤗 {a} обнимает {b}",
        "поцеловать": "💋 {a} целует {b}",
        "рука": "🫴 {a} подает руку помощи {b}",
        "ударить": "👊 {a} ударил {b}",
        "накричать": "😡 {a} накричал на {b}",
    }

    if message.reply_to_message and text.lower() in actions:
        a = message.from_user.full_name
        b = message.reply_to_message.from_user.full_name
        return await message.answer(actions[text.lower()].format(a=a, b=b))

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    