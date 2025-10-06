# import asyncio


# async def main():
#     print("Hello World!")

# asyncio.run(main())

# from typeguard import typechecked

# @typechecked
# def get_something_1(arg_1: int | float, arg_2: list[int | float], arg_3: str | None = None) -> int:
#     print(type(arg_1))
#     print(arg_1)
#     print(type(arg_2))
#     print(arg_2)
#     print(type(arg_3))
#     print(arg_3)
#     return 1

# get_something_1(5.0, [1, 2, 3.1], "QW")
# get_something_1(5.0, [1, 2, 3.1])

import asyncio
import time


async def send_mail(num):
    print(f'Улетело сообщение {num}')
    await asyncio.sleep(1)  # Имитация отправки сообщения по сети
    print(f'Сообщение {num} доставлено')


async def main():
    for i in range(10):
        await send_mail(i)
    

start_time = time.time()
asyncio.run(main())
print(f'Время выполнения программы: {time.time() - start_time} с')