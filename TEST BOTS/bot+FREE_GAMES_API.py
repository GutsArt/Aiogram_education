# https://www.gamerpower.com/api-read

import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT_TOKEN, ADMIN_CHAT_ID

CHECK_INTERVAL = 3600  # 1 час


class ColorFormatter(logging.Formatter):
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    def format(self, record):
        color = self.RESET
        if record.levelno >= logging.ERROR:
            color = self.RED
        elif record.levelno >= logging.WARNING:
            color = self.YELLOW

        message = super().format(record)
        return f"{color}{message}{self.RESET}"


file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setLevel(logging.WARNING)  # Только WARNING и выше

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)  # INFO и выше в консоль

# Настраиваем формат
file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
color_formatter = ColorFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
file_handler.setFormatter(file_formatter)
stream_handler.setFormatter(color_formatter)

# Настраиваем корневой логгер
logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_GAMES_API = "https://www.gamerpower.com/api/giveaways?platform=epic-games-store"

# список id раздач, чтобы не повторять уведомления
known_giveaways = set()


async def fetch_free_games():
    """Получить список раздач из API"""
    async with aiohttp.ClientSession() as session:
        async with session.get(FREE_GAMES_API, timeout=10) as resp:
            if resp.status != 200:
                logging.error(f"Ошибка при запросе к API: {resp.status}")
                return []
            return await resp.json()


def format_game_info(game):
    """Форматирование информации об игре"""
    title = game.get("title", "No title")
    worth = game.get("worth", "N/A")

    description = game.get("description", "No description")
    logging.info(f"Описание игры: {description}")

    status = game.get("status", "N/A")
    date = game.get("end_date", "N/A")

    game_url = game.get("open_giveaway_url", "")
    # try:
    #     slug = game_url.split("open/")[-1].split("-epic-games")[0]
    #     game_url = f"https://store.epicgames.com/en-US/browse?q={slug}"
    # except Exception as e:
    #     logging.error(f"Ошибка при формировании URL игры: {e}")
    #     game_url = "https://store.epicgames.com/en-US/free-games"

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


@dp.errors()
async def global_error_handler(update, exception):
    logging.error(f"Ошибка: {exception} при обработке {update}")
    return True  # чтобы бот не упал


async def check_updates():
    """Фоновая задача — раз в час проверяет новые раздачи"""
    global known_giveaways
    while True:
        logging.info("Проверка обновлений...")
        games = await fetch_free_games()
        if not games:
            await asyncio.sleep(CHECK_INTERVAL)
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
                await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения: {e}\n{text[:1_000]}")

        await asyncio.sleep(CHECK_INTERVAL) # ждать 1 час (3600 сек)


async def main():
    """Запуск бота и фоновой проверки"""
    asyncio.create_task(check_updates())  # запуск фоновой проверки
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Бот запущен")
    asyncio.run(main())

