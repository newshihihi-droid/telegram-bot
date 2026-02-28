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
GROUP_ID = -1001234567890  # <-- Вставь свой ID группы

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- DATA ----------------
DATA_FILE = "bot_data.json"


warnings_db = {}
reputation_db = {}
rep_cooldown = {}
message_tracker = {}

SPAM_LIMIT = 5
SPAM_TIME = 4  # секунд

bad_words = {
    "дурак": "солнышко",
    "идиот": "гений",
    "лох": "чемпион",
    "тупой": "умничка"
}

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
    if not match: return None
    val, unit = int(match.group(1)), match.group(2)
    return {"s": timedelta(seconds=val), "m": timedelta(minutes=val),
            "h": timedelta(hours=val), "d": timedelta(days=val)}.get(unit)

def load_data():
    global warnings_db, reputation_db
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                warnings_db, reputation_db = {}, {}
                return
            data = json.loads(content)
            warnings_db = {int(k): v for k, v in data.get("warnings", {}).items()}
            reputation_db = {int(k): v for k, v in data.get("reputation", {}).items()}
    except FileNotFoundError:
        warnings_db, reputation_db = {}, {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"warnings": warnings_db, "reputation": reputation_db}, f, ensure_ascii=False, indent=2)

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

    # MUTE
    if cmd == "mute":
        args = message.text.split()
        if len(args)<2: return await message.answer("Пример: /mute 10m")
        delta = parse_time(args[1])
        if not delta: return await message.answer("Формат: 10s / 10m / 1h / 2d")
        await bot.restrict_chat_member(message.chat.id, user_id,
                                       ChatPermissions(can_send_messages=False),
                                       until_date=datetime.now()+delta)
        await message.answer(f"🔇 Мут на {args[1]}")

    # UNMUTE
    elif cmd=="unmute":
        await bot.restrict_chat_member(message.chat.id, user_id,
                                       ChatPermissions(can_send_messages=True))
        await message.answer("✅ Мут снят")

    # WARN
    elif cmd=="warn":
        warnings_db[user_id] = warnings_db.get(user_id,0)+1
        count = warnings_db[user_id]
        await message.answer(f"⚠ Варн. Всего: {count}")
        if count>=3:
            await bot.restrict_chat_member(message.chat.id, user_id,
                                           ChatPermissions(can_send_messages=False),
                                           until_date=datetime.now()+timedelta(minutes=30))
            warnings_db[user_id]=0
            await message.answer("🚫 3 варна → мут 30 минут")
        save_data()

    # BAN
    elif cmd=="ban":
        args = message.text.split()
        if len(args)<2: return await message.answer("Пример: /ban 1d")
        delta = parse_time(args[1])
        if not delta: return await message.answer("Формат: 10m / 3h / 2d")
        await bot.ban_chat_member(message.chat.id, user_id, until_date=datetime.now()+delta)
        await message.answer(f"🚫 Бан на {args[1]}")

    # PERMABAN
    elif cmd=="permaban":
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer("⛔ Перманентный бан")

# ---------------- RULES / HELP ----------------
@dp.message(Command("rules"))
async def rules_cmd(message: types.Message):
    await message.answer(rules_text)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "/rules — правила чата\n"
        "/rep — твоя репутация\n"
        "Модерация (только для админа): /mute /unmute /warn /ban /permaban"
    )

# ---------------- REP ----------------
@dp.message(Command("rep"))
async def rep(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    if user_id in rep_cooldown:
        if now-rep_cooldown[user_id] < timedelta(seconds=10):
            return await message.answer("⏳ КД 10 секунд.")
    rep_cooldown[user_id]=now
    rep = reputation_db.get(user_id,0)
    await message.answer(f"⭐ Репутация {message.from_user.first_name}: {rep}")

# ---------------- UNIVERSAL HANDLER ----------------
@dp.message()
async def universal(message: types.Message):
    user_id = message.from_user.id
    text = message.text or ""

    # --- ANTI-SPAM ---
    if user_id != OWNER_ID:
        now = time.time()
        message_tracker[user_id] = [t for t in message_tracker.get(user_id,[]) if now-t<SPAM_TIME]
        message_tracker[user_id].append(now)
        if len(message_tracker[user_id])>=SPAM_LIMIT:
            await bot.restrict_chat_member(message.chat.id, user_id,
                                           ChatPermissions(can_send_messages=False),
                                           until_date=datetime.now()+timedelta(minutes=5))
            message_tracker[user_id].clear()
            return await message.answer("🚫 Спам → мут 5 минут")

    # --- BAD WORDS ---
    for bad, good in bad_words.items():
        if re.search(bad, text, re.IGNORECASE):
            await message.delete()
            await message.answer(f"✏ {message.from_user.first_name} имел в виду: {re.sub(bad, good, text, flags=re.IGNORECASE)}")
            return

    # --- REP CHANGE ---
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        # запрещаем менять себе репутацию
        if target_id != user_id:
            if text == "+": 
                reputation_db[target_id] = reputation_db.get(target_id,0)+1
                await message.answer(f"👍 +1 реп {message.reply_to_message.from_user.first_name}")
            elif text == "-": 
                reputation_db[target_id] = reputation_db.get(target_id,0)-1
                await message.answer(f"👎 -1 реп {message.reply_to_message.from_user.first_name}")
            elif re.match(r"^[+-]\d+$", text) and is_admin(message):
                val = int(text)
                reputation_db[target_id] = reputation_db.get(target_id,0)+val
                await message.answer(f"⭐ Репутация {message.reply_to_message.from_user.first_name} изменена на {val}")
            save_data()

            # --- INTERACTIVE ---
            if text.lower() in actions:
                await message.answer(f"{message.from_user.first_name} {actions[text.lower()]} {message.reply_to_message.from_user.first_name}")

    # --- WELCOME / BYE ---
    if message.new_chat_members:
        for u in message.new_chat_members:
            await message.answer(f"{random.choice(welcome_list).format(name=u.first_name)}{rules_text}")
    if message.left_chat_member:
        u = message.left_chat_member
        await message.answer(f"{random.choice(bye_list).format(name=u.first_name)}")

# ---------------- START ----------------
async def main():
    load_data()

    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())