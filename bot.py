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

# ================== ВСПОМОГАТЕЛЬНОЕ ==================

def is_admin(message: Message):
    return message.from_user.id == OWNER_ID and message.chat.id == GROUP_ID

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

# ================== HELP ==================

@dp.message(Command("help"))
async def help_cmd(message: Message):
    text = "📜 Команды:\n\n"

    if message.from_user.id == OWNER_ID:
        text += (
            "👑 Админ:\n"
            "/mute 10m\n"
            "/unmute\n"
            "/ban 1d\n"
            "/permaban\n"
            "/warn\n"
            "/warn 2-12 (2 месяца бан)\n"
            "+100 / -50\n\n"
        )

    text += (
        "🌟 Общие:\n"
        "/rep\n\n"
        "🎭 Интерактив (ответом на сообщение):\n"
        "пожать\nобнять\nпоцеловать\nрука\nударить\nнакричать\n"
    )

    await message.answer(text)

# ================== WARN ==================

@dp.message(Command("warn"))
async def warn_user(message: Message):
    if not is_admin(message):
        return
    
    if not message.reply_to_message:
        return await message.answer("Ответь на сообщение.")

    user = message.reply_to_message.from_user
    args = message.text.split()

    if len(args) > 1 and "-" in args[1]:
        months = int(args[1].split("-")[0])
        until = datetime.now() + timedelta(days=30 * months)
        await bot.ban_chat_member(message.chat.id, user.id, until_date=until)
        return await message.answer(f"🚫 Бан на {months} мес.")

    warnings_db[user.id] = warnings_db.get(user.id, 0) + 1
    count = warnings_db[user.id]

    if count == 1:
        until = datetime.now() + timedelta(minutes=15)
        await bot.restrict_chat_member(
            message.chat.id,
            user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await message.answer("⚠ 1 предупреждение → мут 15 мин")

    elif count == 2:
        until = datetime.now() + timedelta(hours=2)
        await bot.restrict_chat_member(
            message.chat.id,
            user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await message.answer("⚠ 2 предупреждение → мут 2 часа")

    elif count >= 3:
        until = datetime.now() + timedelta(days=30)
        await bot.ban_chat_member(message.chat.id, user.id, until_date=until)
        warnings_db[user.id] = 0
        await message.answer("🚫 3 предупреждение → бан 30 дней")

# ================== REP VIEW ==================

@dp.message(Command("rep"))
async def rep_view(message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user

    if message.from_user.id != OWNER_ID:
        now = time.time()
        last = rep_view_cooldown.get(message.from_user.id, 0)
        if now - last < 60:
            return await message.answer("⏳ КД 1 минута.")
        rep_view_cooldown[message.from_user.id] = now

    rep = reputation_db.get(user.id, 0)
    await message.answer(f"⭐ Репутация {user.full_name}: {rep}")

# ================== REP CHANGE ==================

@dp.message()
async def rep_change(message: Message):
    if not message.reply_to_message:
        return
    if not message.text:
        return

    text = message.text.strip()

    if re.fullmatch(r"[+-]\d+", text):
        target = message.reply_to_message.from_user

        if target.id == message.from_user.id:
            return await message.answer("❌ Нельзя себе менять репутацию.")

        value = int(text)

        if message.from_user.id != OWNER_ID:
            now = time.time()
            last = rep_change_cooldown.get(message.from_user.id, 0)
            if now - last < 10:
                return await message.answer("⏳ КД 10 секунд.")
            rep_change_cooldown[message.from_user.id] = now

            if abs(value) > 1:
                return await message.answer("Можно только +1 или -1.")

        reputation_db[target.id] = reputation_db.get(target.id, 0) + value

        await message.answer(
            f"⭐ Репутация {target.full_name} теперь {reputation_db[target.id]}"
        )

# ================== ИНТЕРАКТИВ ==================

actions = {
    "пожать": "🤝 {a} жмет руку {b}",
    "обнять": "🤗 {a} обнимает {b}",
    "поцеловать": "💋 {a} целует {b}",
    "рука": "🫴 {a} подает руку помощи {b}",
    "ударить": "👊 {a} ударил {b}",
    "накричать": "😡 {a} накричал на {b}",
}

@dp.message()
async def interactive(message: Message):
    if not message.reply_to_message:
        return
    if message.text and message.text.lower() in actions:
        a = message.from_user.full_name
        b = message.reply_to_message.from_user.full_name
        await message.answer(actions[message.text.lower()].format(a=a, b=b))

# ================== АНТИСПАМ ==================

@dp.message()
async def anti_spam(message: Message):
    if message.from_user.id == OWNER_ID:
        return

    user_id = message.from_user.id
    now = time.time()

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
        await message.answer("🚫 Спам → мут 5 минут")

# ================== МАТ-ФИЛЬТР ==================

@dp.message()
async def bad_word_filter(message: Message):
    if message.from_user.id == OWNER_ID:
        return
    if not message.text:
        return

    replaced = message.text

    for bad, good in bad_words.items():
        pattern = re.compile(bad, re.IGNORECASE)
        replaced = pattern.sub(good, replaced)

    if replaced != message.text:
        await message.delete()
        await message.answer(
            f"✏ {message.from_user.full_name} имел в виду:\n{replaced}"
        )

# ================== WELCOME / BYE ==================

welcome_list = [
    "🔥 Добро пожаловать, {name}!",
    "👋 {name} залетел!",
    "🎉 Новый участник — {name}",
    "⚡ {name} теперь с нами!",
    "🌟 Встречаем {name}",
    "💎 {name} в чате!",
    "🚀 {name} ворвался!",
    "🛡 Рад видеть, {name}",
    "👑 {name} присоединился",
    "✨ Добро пожаловать {name}"
]

bye_list = [
    "😢 {name} ушел...",
    "👋 {name} покинул чат",
    "🚪 {name} вышел",
    "💨 {name} исчез",
    "⚰ {name} нас покинул",
    "📤 {name} вышел",
    "❌ {name} больше не с нами",
    "🥀 {name} ушел",
    "🌫 {name} растворился",
    "🛫 {name} улетел"
]

rules = "\n\n📜 Правила:\n1. Без спама\n2. Без оскорблений\n3. Уважение"

@dp.message()
async def member_events(message: Message):
    if message.new_chat_members:
        for m in message.new_chat_members:
            text = random.choice(welcome_list).format(name=m.full_name)
            await message.answer(text + rules)

    if message.left_chat_member:
        text = random.choice(bye_list).format(name=message.left_chat_member.full_name)
        await message.answer(text)

# ================== START ==================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
