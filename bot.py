import asyncio
import re
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

warnings_db = {}


# --- Проверка владельца ---
def is_owner(message: Message):
    return message.from_user.id == OWNER_ID


# --- Парсер времени ---
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


# --- MUTE ---
@dp.message(Command("mute"))
async def mute_user(message: Message):
    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Пример: /mute 20m")
        return

    delta = parse_time(args[1])
    if not delta:
        await message.answer("Формат: 10s / 20m / 3h / 2d")
        return

    user_id = message.reply_to_message.from_user.id
    until_date = datetime.now() + delta

    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=user_id,
        permissions={"can_send_messages": False},
        until_date=until_date
    )

    await message.answer(f"🔇 Замучен на {args[1]}")


# --- UNMUTE ---
@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя.")
        return

    user_id = message.reply_to_message.from_user.id

    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=user_id,
        permissions={
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True
        }
    )

    await message.answer("✅ Мут снят")


# --- WARN ---
@dp.message(Command("warn"))
async def warn_user(message: Message):
    if not is_owner(message):
        return

    if not message.reply_to_message:
        await message.answer("Ответь на сообщение пользователя.")
        return

    user_id = message.reply_to_message.from_user.id
    warnings_db[user_id] = warnings_db.get(user_id, 0) + 1
    count = warnings_db[user_id]

    await message.answer(f"⚠ Предупреждение. Всего: {count}")

    if count >= 3:
        until_date = datetime.now() + timedelta(minutes=30)

        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions={"can_send_messages": False},
            until_date=until_date
        )

        warnings_db[user_id] = 0
        await message.answer("🚫 3 варна → мут 30 минут")


# --- START ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

