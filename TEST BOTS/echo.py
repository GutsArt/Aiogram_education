from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def process_start_command(message: Message):
    await message.answer("Привет!\nМеня зовут Эхо-бот!\nНапиши мне что-нибудь")


@dp.message(Command("help"))
async def process_help_command(message: Message):
    await message.answer(
        "Напиши мне что-нибудь, и я пришлю тебе твое сообщение обратно!"
    )


@dp.message()
async def send_echo(message: Message):
    await message.reply(text=message.text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
