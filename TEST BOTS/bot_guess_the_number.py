from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ATTEMPTS = 5

users: dict = {}

def get_random_number() -> int:
    import random
    return random.randint(1, 100)

# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(CommandStart()) # or Command(commands='start')
async def process_start_command(message: Message):
    await message.answer(
        'Привет!\nДавайте сыграем в игру "Угадай число"?\n\n'
        'Чтобы получить правила игры и список доступных '
        'команд - отправьте команду /help'
    )

    # users - добавляем его в словарь если его там нет
    if message.from_user.id not in users:
        users[message.from_user.id] = {
            'in_game': False,
            'secret_number': None,
            'attempts': None,
            'total_games': 0,
            'wins': 0
        }


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(
        'Правила игры:\n\n'
        'Я загадываю число от 1 до 100, а вам нужно его угадать\n' 
        f'У вас есть {ATTEMPTS} попыток\n\n'
        'Доступные команды:\n'
        '/help - правила игры и список команд\n'
        '/cancel - выйти из игры\n'
        '/stat - посмотреть статистику\n\n'
        'Давай сыграем?'
    )


# Этот хэндлер будет срабатывать на команду "/stat"
@dp.message(Command(commands='stat'))
async def process_stat_command(message: Message):
    await message.answer(
        'Всего игр сыграно: '
        f'{users[message.from_user.id]["total_games"]}\n'
        f'Игр выиграно: {users[message.from_user.id]["wins"]}'
    )


# Этот хэндлер будет срабатывать на команду "/cancel"
@dp.message(Command(commands='cancel'))
async def process_cancel_command(message: Message):
    if users[message.from_user.id]['in_game']:
        users[message.from_user.id]['in_game'] = False
        await message.answer(
            'Вы вышли из игры. Если захотите сыграть '
            'снова - напишите об этом'
        )
    else:
        await message.answer(
            'А мы и так с вами не играем. '
            'Может, сыграем разок?'
        )


# Этот хэндлер будет срабатывать на согласие пользователя сыграть в игру
@dp.message(F.text.lower().in_(['да', 'давай', 'игра',
                                'играть', 'хочу', 'yes', 'y', 'ok']))
async def process_positive_answer(message: Message):
    if not users[message.from_user.id]['in_game']:
        users[message.from_user.id]['in_game'] = True
        users[message.from_user.id]['secret_number'] = get_random_number()
        users[message.from_user.id]['attempts'] = ATTEMPTS
        await message.answer(
            'Ура!\n\nЯ загадал число от 1 до 100, '
            'попробуй угадать!'
        )
    else:
        await message.answer(
            'Пока мы играем в игру я могу '
            'реагировать только на числа от 1 до 100 '
            'и команды /cancel и /stat'
        )


# Этот хэндлер будет срабатывать на отказ пользователя сыграть в игру
@dp.message(F.text.lower().in_(['нет', 'не', 'не хочу', 'no', 'n']))
async def process_negative_answer(message: Message):
    if not users[message.from_user.id]['in_game']:
        await message.answer(
            'Жаль :(\n\n' \
            'Если захотите поиграть - просто напишите об этом'
        )
    else:
        await message.answer(
            'Мы же сейчас с вами играем. Присылайте, пожалуйста, числа от 1 до 100'
        )


# Этот хэндлер будет срабатывать на отправку пользователем чисел от 1 до 100
@dp.message(lambda x: x.text and x.text.isdigit() and 1 <= int(x.text) <= 100)
async def process_numbers_answer(message: Message):
    if users[message.from_user.id]['in_game']:
        if int(message.text) == users[message.from_user.id]['secret_number']:
            users[message.from_user.id]['in_game'] = False
            users[message.from_user.id]['total_games'] += 1
            users[message.from_user.id]['wins'] += 1
            await message.answer(
                'Ура!!! Вы угадали число!\n\n'
                'Может, сыграем еще?'
            )
        elif int(message.text) > users[message.from_user.id]['secret_number']:
            users[message.from_user.id]['attempts'] -= 1
            await message.answer('Мое число меньше')
        elif int(message.text) < users[message.from_user.id]['secret_number']:
            users[message.from_user.id]['attempts'] -= 1
            await message.answer('Мое число больше')

        if users[message.from_user.id]['attempts'] == 0:
            users[message.from_user.id]['in_game'] = False
            users[message.from_user.id]['total_games'] += 1
            await message.answer(
                'К сожалению, у вас больше не осталось попыток. Вы проиграли :(\n\n'
                f'Мое число было {users[message.from_user.id]["secret_number"]}\n\n'
                'Давайте сыграем еще?'
            )
    else:
        await message.answer('Мы еще не играем. Хотите сыграть?')


# Этот хэндлер будет срабатывать на остальные любые сообщения
@dp.message()
async def process_other_answers(message: Message):
    if users[message.from_user.id]['in_game']:
        await message.answer(
            'Мы же сейчас с вами играем. Присылайте, пожалуйста, числа от 1 до 100'
        )
    else:
        await message.answer(
            'Я довольно ограниченный бот, давайте просто сыграем в игру?'
        )


if __name__ == '__main__':
    dp.run_polling(bot)
# Улучшения, которые можно внести в этого бота

# При перезапуске бота словарь users обнуляется и все состояния всех пользователей, соответственно, сбрасываются. Самое простое решение такой проблемы - периодически сохранять словарь в файл, а потом, при перезапуске бота считывать его из файла. Для этого подойдёт, например, библиотека pickle. Но вообще, такое решение не очень хорошее. Лучше - для хранения состояний пользователей использовать базу данных или FSMContext на базе персистентного хранилища (например, Redis). Об этом мы будем говорить в других уроках.

# Интерфейс взаимодействия с ботом довольно скучный. Взаимодействие происходит только с помощью команд и текстовых сообщений. Можно было бы добавить кнопок, стикеров, возможно, даже каких-нибудь картинок в награду за победу и так далее. Действительно, улучшить юзер-интерфейс не проблема и навыки из следующих уроков помогут в этом, если вы захотите сделать этого бота повеселее.

# Весь код бота хранится в одном файле. И хоть для такого мини-проекта это вполне обоснованно, то для проектов побольше код обязательно нужно будет разделять на модули и пакеты, чтобы самим в нём не запутаться.

# Токен бота хранится в открытом виде в исполняемом файле. Очень нежелательно хранить секреты в файлах, которыми вы можете делиться с кем-то или выкладывать на GitHub, потому что, имея доступ к секретам, кто-нибудь может от имени вашего бота творить всякое нехорошее. Секреты принято хранить отдельно в защищённом месте, а в исполняемых файлах описывать способы как эти секреты безопасно получить. Обязательно об этом поговорим в дальнейшем.

# Наш бот никак не обрабатывает возможные ошибки. Если пользователь, например, заблокирует бота во время взаимодействия, возникнет исключение BotBlocked. Конечно, в случае нашего бота, пользователь должен быть очень быстрым, чтобы успеть заблокировать бота до того, как тот отправит ему сообщение, но, как говорится, было бы желание. Сломать можно что угодно. И хорошим тоном считается наличие в коде обработчиков возможных исключений и ошибок.

# У бота нет никаких настроек. А что если вы захотели, чтобы попыток было не 5, а больше? А если хотите, чтобы диапазон загадываемых чисел был другим? Хотя бы минимальные настройки боту не повредили бы. Это только владелец бота может залезть в код и поменять настройки, а пользователи, получающие к нему доступ через приложение Telegram, такой возможности не имеют.

# Отсутствует возможность соревноваться с другими пользователями. Ведь было бы неплохо периодически вызывать табличку со статистикой лучших игроков. Пусть этот бот и не такой интересный, но в других, более продвинутых играх, такая статистика добавляет соревновательного интереса.
