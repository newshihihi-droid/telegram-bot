import asyncio
import os
import re
import json
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATA =================
DATA_FILE = "bot_data.json"

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

actions = {
    "пожать": "🤝 {a} жмет руку {b}",
    "обнять": "🤗 {a} обнимает {b}",
    "поцеловать": "💋 {a} целует {b}",
    "рука": "🫴 {a} подает руку помощи {b}",
    "ударить": "👊 {a} ударил {b}",
    "накричать": "😡 {a} накричал на {b}",
}

# ================= HELPERS =================
def is_admin(message: Message):
    return message.from_user.id == OWNER_ID and message.chat.id == GROUP_ID

def save_data():
    data = {
        "warnings": warnings_db,
        "reputation": reputation_db
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    global warnings_db, reputation_db
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            warnings_db = {int(k): v for k, v in data.get("warnings", {}).items()}
            reputation_db = {int(k): v for k, v in data.get("reputation", {}).items()}
    except FileNotFoundError:
        pass

def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str)
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)
    if unit == "s": return timedelta(seconds=value)
    if unit == "m": return timedelta(minutes=value)
    if unit == "h": return timedelta(hours=value)
    if unit == "d": return timedelta(days=value)

# ================= ADMIN COMMANDS =================
@dp.message(Command("mute"))
async def mute_cmd(message: Message):
    if not is_admin(message) or not message.reply_to_message:
        return
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Пример: /mute 10m")
    delta = parse_time(args[1])
    if not delta:
        return await message.answer("Формат: 10m / 2h")
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
    if not is_admin(message) or not message.reply_to_message:
        return
    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        ChatPermissions(can_send_messages=True)
    )
    await message.answer("✅ Мут снят")

@dp.message(Command("ban"))
async def ban_cmd(message: Message):
    if not is_admin(message) or not message.reply_to_message:
        return
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Пример: /ban 1d")
    delta = parse_time(args[1])
    if not delta:
        return
    until = datetime.now() + delta
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
    await message.answer("🚫 Бан выдан")

@dp.message(Command("permaban"))
async def permaban_cmd(message: Message):
    if not is_admin(message) or not message.reply_to_message:
        return
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer("💀 Перманентный бан")

# ================= WARN =================
@dp.message(Command("warn"))
async def warn_cmd(message: Message):
    if not is_admin(message) or not message.reply_to_message:
        return
    user = message.reply_to_message.from_user
    args = message.text.split()
    if len(args) > 1 and "-" in args[1]:
        months = int(args[1].split("-")[0])
        until = datetime.now() + timedelta(days=30*months)
        await bot.ban_chat_member(message.chat.id, user.id, until_date=until)
        return await message.answer(f"🚫 Бан на {months} мес.")
    warnings_db[user.id] = warnings_db.get(user.id,0)+1
    count = warnings_db[user.id]
    if count == 1:
        until = datetime.now() + timedelta(minutes=15)
        await bot.restrict_chat_member(message.chat.id, user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer("⚠ 1 предупреждение → мут 15 мин")
    elif count == 2:
        until = datetime.now() + timedelta(hours=2)
        await bot.restrict_chat_member(message.chat.id, user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer("⚠ 2 предупреждение → мут 2 часа")
    else:
        until = datetime.now() + timedelta(days=30)
        await bot.ban_chat_member(message.chat.id, user.id, until_date=until)
        warnings_db[user.id]=0
        await message.answer("🚫 3 предупреждение → бан 30 дней")
    save_data()

# ================= MAIN HANDLER =================
@dp.message()
async def main_handler(message: Message):
    if not message.text:
        return
    text = message.text.strip()
    user_id = message.from_user.id

    # ---- ANTI-SPAM ----
    if user_id != OWNER_ID:
        now = time.time()
        message_tracker[user_id] = [t for t in message_tracker[user_id] if now-t<SPAM_TIME]
        message_tracker[user_id].append(now)
        if len(message_tracker[user_id]) >= SPAM_LIMIT:
            until = datetime.now() + timedelta(minutes=5)
            await bot.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until)
            message_tracker[user_id].clear()
            return await message.answer("🚫 Спам → мут 5 минут")

    # ---- BAD WORD FILTER ----
    if user_id != OWNER_ID:
        replaced = text
        for bad, good in bad_words.items():
            replaced = re.sub(bad, good, replaced, flags=re.IGNORECASE)
        if replaced != text:
            await message.delete()
            return await message.answer(f"✏ {message.from_user.full_name} имел в виду:\n{replaced}")

    # ---- REP CHANGE ----
    if message.reply_to_message and re.fullmatch(r"[+-]\d+", text):
        target = message.reply_to_message.from_user
        if target.id == user_id:
            return await message.answer("❌ Нельзя себе.")
        value = int(text)
        if user_id != OWNER_ID:
            now = time.time()
            last = rep_change_cooldown.get(user_id,0)
            if now-last<10:
                return await message.answer("⏳ КД 10 секунд.")
            rep_change_cooldown[user_id]=now
            if abs(value)>1:
                return await message.answer("Можно только +1/-1.")
        reputation_db[target.id] = reputation_db.get(target.id,0)+value
        save_data()
        return await message.answer(f"⭐ Репутация {target.full_name}: {reputation_db[target.id]}")

    # ---- INTERACTIVE ----
    if message.reply_to_message and text.lower() in actions:
        a = message.from_user.full_name
        b = message.reply_to_message.from_user.full_name
        return await message.answer(actions[text.lower()].format(a=a,b=b))

# ================= REP VIEW =================
@dp.message(Command("rep"))
async def rep_view(message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    uid = message.from_user.id
    if uid != OWNER_ID:
        now = time.time()
        last = rep_view_cooldown.get(uid,0)
        if now-last<60:
            return await message.answer("⏳ КД 1 минута.")
        rep_view_cooldown[uid]=now
    rep = reputation_db.get(user.id,0)
    await message.answer(f"⭐ Репутация {user.full_name}: {rep}")

# ================= WELCOME / BYE =================
@dp.message()
async def member_events(message: Message):
    if message.new_chat_members:
        for m in message.new_chat_members:
            text = random.choice(welcome_list).format(name=m.full_name)
            await message.answer(text + rules)
    if message.left_chat_member:
        text = random.choice(bye_list).format(name=message.left_chat_member.full_name)
        await message.answer(text)

# ================= HELP =================
@dp.message(Command("help"))
async def help_cmd(message: Message):
    text="📜 Команды:\n\n"
    if message.from_user.id==OWNER_ID:
        text+="👑 Админ:\n/mute 10m\n/unmute\n/ban 1d\n/permaban\n/warn\n/warn 2-12 (2 мес бан)\n+100 / -50\n\n"
    text+="🌟 Общие:\n/rep\n\n🎭 Интерактив (ответом на сообщение):\nпожать\nобнять\nпоцеловать\nрука\nударить\nнакричать\n"
    await message.answer(text)

# ================= START =================
async def main():
    load_data()
    await bot.delete_webhook()
    await dp.start_polling(bot)

if __name__=="__main__":
    
    asyncio.run(main())
