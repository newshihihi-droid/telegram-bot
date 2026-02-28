import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN не найден в переменных окружения")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Бот запущен и работает ✅")

@dp.message(Command("test"))
async def test_cmd(message: Message):
    await message.answer("Тест прошёл успешно 🚀")

@dp.message()
async def echo(message: Message):
    await message.answer(f"Ты написал: {message.text}")

async def main():
    print("BOT STARTED SUCCESSFULLY")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
