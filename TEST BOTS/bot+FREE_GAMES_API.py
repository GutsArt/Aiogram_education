# https://www.gamerpower.com/api-read

import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton # for buttons
import json
from pathlib import Path

from config import BOT_TOKEN, ADMIN_CHAT_ID


KNOWN_FILE = "known_giveaways.json"
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




async def fetch_free_games():
    """Получить список раздач из API"""
    async with aiohttp.ClientSession() as session:
        async with session.get(FREE_GAMES_API, timeout=10) as resp:
            if resp.status != 200:
                logging.error(f"Ошибка при запросе к API: {resp.status}")
                return []
            return await resp.json()
        
# Filter to identify real Epic Games Store giveaways        
def is_real_epic_game(game: dict) -> bool:
    # 1. Только полноценные игры
    if game.get("type") != "Game":
        return False

    # # 2. Платформа должна включать Epic Games Store
    # platforms = game.get("platforms", "").lower()
    # if "epic games store" not in platforms:
    #     return False

    # 3. Отсекаем партнёров и мусор
    blacklist = [
        "alienware",
        "dungeonloot",
        "key",
        "pack",
        "dlc",
        "beta",
        "early access",
    ]

    title = game.get("title", "").lower()
    url = game.get("gamerpower_url", "").lower()

    for word in blacklist:
        if word in title or word in url:
            return False

    return True


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
    # Optional: filter to only real Epic Games Store games
    # games = await fetch_free_games()
    games = [g for g in await fetch_free_games() if is_real_epic_game(g)]

    if not games:
        await message.answer("🎮 Сейчас нет бесплатных игр в Epic Games Store.")
        return

    reply_text = "🎮 Бесплатные игры сейчас в Epic Games Store:\n\n"
    for game in games:
        reply_text += format_game_info(game)

    await message.answer(reply_text, parse_mode="HTML")


@dp.message(Command("links"))
async def links_cmd(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📷 Webcam Rathausmarkt",
                url="https://grassau.com/webcams/rathaus_hh"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎲 Monopoly Online",
                url="https://richup.io/"
            )
        ],
        [
            InlineKeyboardButton(
                text="♟ Chess.com",
                url="https://www.chess.com/de/play/online"
            ),
            InlineKeyboardButton(
                text="♞ Lichess",
                url="https://lichess.org/de"
            )
        ]
    ])

    await message.answer(
        "🔗 <b>Полезные ссылки</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.errors()
async def global_error_handler(update, exception):
    logging.error(f"Ошибка: {exception} при обработке {update}")
    return True  # чтобы бот не упал


def load_known_giveaways() -> set[int]:
    if not Path(KNOWN_FILE).exists():
        logging.info("Файл known_giveaways.json не найден — стартуем с пустого списка")
        return set()

    try:
        with open(KNOWN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logging.info(f"Загружено {len(data)} известных раздач")
            return set(data)
    except Exception as e:
        logging.error(f"Ошибка чтения {KNOWN_FILE}: {e}")
        return set()
    
# список id раздач, чтобы не повторять уведомления
known_giveaways = load_known_giveaways()

def save_known_giveaways():
    try:
        with open(KNOWN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(known_giveaways), f, indent=2)
    except Exception as e:
        logging.error(f"Ошибка записи {KNOWN_FILE}: {e}")


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
            # Optional: skip non-Epic games
            if not is_real_epic_game(game):
                continue 

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
                save_known_giveaways()
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

