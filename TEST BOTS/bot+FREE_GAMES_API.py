# https://www.gamerpower.com/api-read

import logging
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_GAMES_API = "https://www.gamerpower.com/api/giveaways?platform=epic-games-store"  # пример API

@dp.message(Command(commands="info"))
async def send_free_games_info(message: Message):
    try:
        resp = requests.get(FREE_GAMES_API, timeout=10)
        resp.raise_for_status()
        games  = resp.json()
        if not games:
            await message.answer("Не удалось найти информацию о бесплатных играх сейчас.")
            return
        
        text_lines = ["🎮 Бесплатные игры сейчас:\n"]
        for game in games:
            title = game.get("title", "No title")
            status = game.get("status", "N/A")
            date = game.get("end_date", "N/A")
            game_url = game.get("open_giveaway_url", "N/A")
            text_lines.append(f"{title} — {status}\nДата: {date}")
            if game_url:
                text_lines.append(f"Ссылка: {game_url}")
            text_lines.append("")  # пустая строка между играми
        
        await message.answer("\n".join(text_lines))
    except Exception as e:
        logging.error(f"Ошибка при получении данных: {e}")
        await message.answer("Произошла ошибка при получении информации. Попробуйте позже.")

if __name__ == "__main__":
    logging.info("Бот запущен")
    dp.run_polling(bot)
