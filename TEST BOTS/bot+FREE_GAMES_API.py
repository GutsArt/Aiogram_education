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
        # if resp.status_code != 200:
        #     await message.answer("Не удалось получить данные о бесплатных играх.")
        #     return
        games  = resp.json()
        if not games:
            await message.answer("🎮 Сейчас нет бесплатных игр в Epic Games Store.")
            return

        reply_text  = "🎮 Бесплатные игры сейчас в Epic Games Store:\n\n"
        for game in games:
            title = game.get("title", "No title")
            status = game.get("status", "N/A")
            date = game.get("end_date", "N/A")

            game_url = game.get("open_giveaway_url", "N/A")
            search_query = game_url.split("open/")[-1].split("-epic-games")[0]
            game_url = f"https://store.epicgames.com/en-US/browse?q={search_query}"

            reply_text += (f"• {title} - {status} (до {date})\n  [Epic Games]({game_url})\n\n")

        await message.answer(reply_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка при получении данных: {e}")
        await message.answer("Произошла ошибка при получении информации. Попробуйте позже.")

if __name__ == "__main__":
    logging.info("Бот запущен")
    dp.run_polling(bot)
