# https://www.gamerpower.com/api-read

import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT_TOKEN, ADMIN_CHAT_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_GAMES_API = "https://www.gamerpower.com/api/giveaways?platform=epic-games-store"

# список id раздач, чтобы не повторять уведомления
known_giveaways = set()


async def fetch_free_games():
    """Получить список раздач из API"""
    try:
        resp = requests.get(FREE_GAMES_API, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к API: {e}")
        return []


def format_game_info(game):
    """Форматирование информации об игре"""
    title = game.get("title", "No title")
    worth = game.get("worth", "N/A")

    description = game.get("description", "No description")
    logging.info(f"Описание игры: {description}")

    status = game.get("status", "N/A")
    date = game.get("end_date", "N/A")

    game_url = game.get("open_giveaway_url", "")
    try:
        slug = game_url.split("open/")[-1].split("-epic-games")[0]
        game_url = f"https://store.epicgames.com/en-US/browse?q={slug}"
    except Exception as e:
        logging.error(f"Ошибка при формировании URL игры: {e}")
        game_url = "https://store.epicgames.com/en-US/free-games"

    return (
        f"• <code>{title}</code> - {status} (до {date})\n"
        f"💰 <b>Стоимость:</b> {worth}\n"
        f"📝 <b>Описание:</b> {description}\n"
        f"🔗 <a href=\"{game_url}\">Epic Games</a>\n\n"
    )


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Теперь я буду уведомлять тебя о новых бесплатных играх.")
    print(f"Твой chat.id: {message.chat.id}")


@dp.message(Command("info"))
async def send_free_games_info(message: Message):
    """Команда /info — вручную показывает список бесплатных игр"""
    games = await fetch_free_games()
    if not games:
        await message.answer("🎮 Сейчас нет бесплатных игр в Epic Games Store.")
        return

    reply_text = "🎮 Бесплатные игры сейчас в Epic Games Store:\n\n"
    for game in games:
        reply_text += format_game_info(game)

    await message.answer(reply_text, parse_mode="HTML")


async def check_updates():
    """Фоновая задача — раз в час проверяет новые раздачи"""
    global known_giveaways
    while True:
        logging.info("Проверка обновлений...")
        games = await fetch_free_games()
        if not games:
            await asyncio.sleep(3600)
            continue

        new_games = []
        for game in games:
            game_id = game.get("id")
            if game_id not in known_giveaways:
                known_giveaways.add(game_id)
                new_games.append(game)

        if new_games:
            text = "🆕 Новые бесплатные игры в Epic Games Store!\n\n"
            for g in new_games:
                text += format_game_info(g)
            try:
                await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения: {e}")

        await asyncio.sleep(3600)  # ждать 1 час (3600 сек)


async def main():
    """Запуск бота и фоновой проверки"""
    asyncio.create_task(check_updates())  # запуск фоновой проверки
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Бот запущен")
    asyncio.run(main())

